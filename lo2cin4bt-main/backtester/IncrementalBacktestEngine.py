import logging
import gc
import time
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from concurrent.futures import ProcessPoolExecutor
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .VectorBacktestEngine_backtester import VectorBacktestEngine
from database.BacktestDB import BacktestDB
from .SpecMonitor_backtester import SpecMonitor

def calculate_and_print_monthly_stats(
    equity: np.ndarray,
    dates: np.ndarray,
    backtest_id: str,
    params: dict
):
    """
    計算並打印月度績效統計，用於即時回饋。
    """
    if len(equity) < 2 or np.all(equity == equity[0]):
        return # 如果沒有足夠數據或權益無變化，則不顯示

    df = pd.DataFrame({'equity': equity}, index=pd.to_datetime(dates))

    # 按月重採樣
    monthly_returns = df['equity'].resample('M').last().pct_change().fillna(0)

    if monthly_returns.empty:
        return

    # 計算累計月度回報
    cumulative_monthly_returns = (1 + monthly_returns).cumprod() - 1

    # 計算月度最大回撤
    def monthly_drawdown(series):
        cum_max = series.cummax()
        drawdown = (series - cum_max) / cum_max
        return drawdown.min()

    monthly_dd = df['equity'].groupby(pd.Grouper(freq='M')).apply(monthly_drawdown).fillna(0)

    # 使用 Rich 創建美觀的表格
    console = Console()
    table = Table(
        title=f"[bold cyan]快速回饋: {backtest_id}[/bold cyan]\n[dim]參數: {params}[/dim]",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("月份", style="dim", width=12)
    table.add_column("月度報酬率", justify="right")
    table.add_column("累計報酬率", justify="right")
    table.add_column("月度最大回撤", justify="right")

    for date, ret in monthly_returns.items():
        month_str = date.strftime('%Y-%m')
        cum_ret = cumulative_monthly_returns.get(date, 0)
        dd = monthly_dd.get(date, 0)

        # 根據正負值設定顏色
        ret_style = "green" if ret > 0 else "red" if ret < 0 else ""
        cum_ret_style = "green" if cum_ret > 0 else "red" if cum_ret < 0 else ""
        dd_style = "red" if dd < 0 else ""

        # Helper to apply style only when style is not empty
        def style_text(text, style):
            return f"[{style}]{text}[/{style}]" if style else text

        table.add_row(
            month_str,
            style_text(f"{ret:+.2%}", ret_style),
            style_text(f"{cum_ret:+.2%}", cum_ret_style),
            style_text(f"{dd:.2%}", dd_style)
        )

    console.print(table)


class IncrementalBacktestEngine(VectorBacktestEngine):
    """
    增量式回測引擎 (V2)
    
    繼承自 VectorBacktestEngine，但針對增量執行進行了優化：
    1. 支援斷點續傳 (Resume)
    2. 結果即時寫入資料庫 (DuckDB)
    3. 記憶體使用量極低 (不累積結果)
    4. 移除互動式選單依賴
    """

    def __init__(self, data: pd.DataFrame, frequency: str, db_path: str):
        super().__init__(data, frequency)
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.console = Console()

    def run_backtests(
        self, 
        config: Dict[str, Any], 
        job_id: str,
        resume: bool = True
    ) -> None:
        """
        執行增量回測
        """
        self.logger.info(f"啟動增量回測 Job ID: {job_id}")
        
        self.db = BacktestDB(self.db_path)
        
        all_combinations = self.generate_parameter_combinations(config)
        all_tasks = self._generate_all_tasks_matrix(all_combinations, config["predictors"])
        total_tasks = len(all_tasks["combinations"])
        
        existing_job = self.db.get_job(job_id)
        if not existing_job:
            self.logger.info(f"創建新任務: {job_id}, 總任務數: {total_tasks}")
            self.db.create_job(job_id, config, total_tasks)
        else:
            self.logger.info(f"任務 {job_id} 已存在，準備續傳")
        
        completed_ids = set()
        if resume:
            completed_ids = set(self.db.get_completed_backtest_ids(job_id))
            self.logger.info(f"發現已完成任務數: {len(completed_ids)}")
        
        condition_pairs = config["condition_pairs"]
        all_signals = self._generate_all_signals_vectorized(all_tasks, condition_pairs)
        
        self._generate_and_save_results(
            job_id,
            all_tasks,
            all_signals,
            condition_pairs,
            config.get("trading", {}),
            completed_ids
        )
        
        self.db.close()
        self.logger.info("回測任務完成")

    def _generate_and_save_results(
        self,
        job_id: str,
        all_tasks: Dict[str, Any],
        all_signals: Dict[str, Any],
        condition_pairs: List[Dict[str, Any]],
        trading_params: Dict[str, Any],
        completed_ids: set
    ) -> None:
        n_tasks = len(all_tasks["combinations"])
        n_cores, _ = SpecMonitor.get_optimal_core_count()
        batch_size = max(1, n_tasks // (n_cores * 4)) # 確保批次大小至少為 1
        batch_size = min(batch_size, 500)
        
        self.logger.info(f"使用 {n_cores} 核心並行處理，批次大小: {batch_size}")

        batch_indices = []
        for i in range(0, n_tasks, batch_size):
            batch_range = range(i, min(i + batch_size, n_tasks))
            batch_task_ids = [all_tasks["backtest_ids"][j] for j in batch_range]
            
            if all(tid in completed_ids for tid in batch_task_ids):
                continue
            
            batch_indices.append(list(batch_range))

        if not batch_indices:
            self.logger.info("所有任務已完成，無需執行")
            return

        total_batches = len(batch_indices)
        processed_batches = 0
        
        with ProcessPoolExecutor(max_workers=n_cores) as executor:
            futures = []
            
            for idx_list in batch_indices:
                batch_signals = {
                    "entry_signals": all_signals["entry_signals"][:, idx_list],
                    "exit_signals": all_signals["exit_signals"][:, idx_list]
                }
                
                future = executor.submit(
                    self._run_batch_simulation_and_metrics,
                    idx_list,
                    batch_signals,
                    all_tasks,
                    condition_pairs,
                    trading_params,
                    self.data,
                    self.frequency
                )
                futures.append(future)

            for future in futures:
                try:
                    batch_results = future.result()
                    self.db.write_batch_results(job_id, batch_results)
                    processed_batches += 1
                    self.logger.info(f"進度: {processed_batches}/{total_batches} 批次完成")
                    del batch_results
                    gc.collect()
                except Exception as e:
                    self.logger.error(f"批次處理失敗: {e}", exc_info=True)

    @staticmethod
    def _run_batch_simulation_and_metrics(
        batch_indices: List[int],
        batch_signals: Dict[str, np.ndarray],
        all_tasks: Dict[str, Any],
        condition_pairs: List[Dict[str, Any]],
        trading_params: Dict[str, Any],
        data: pd.DataFrame,
        frequency: str
    ) -> List[Dict[str, Any]]:
        trade_results = IncrementalBacktestEngine._simulate_batch_trades(batch_signals, trading_params, data)
        results = []
        prices = data['Close'].values
        dates = data['Time'].values
        
        for i, task_idx in enumerate(batch_indices):
            equity = trade_results["equity_values"][:, i]
            backtest_id = all_tasks["backtest_ids"][task_idx]
            combo = all_tasks["combinations"][task_idx]
            
            condition_pair = condition_pairs[0]

            # 修正：combo 的元素是完整的參數字典，而不是純量值。
            # 我們直接從 combo 中提取這些字典，而不是錯誤地從 condition_pair 解析。
            num_entry_conditions = len(condition_pair['entry'])
            num_exit_conditions = len(condition_pair['exit'])

            entry_param_objects = combo[:num_entry_conditions]
            exit_param_objects = combo[num_entry_conditions : num_entry_conditions + num_exit_conditions]

            # 假設每個條件對應一個參數字典。
            # 如果 entry_param_objects 為空，則 entry_params 為空字典。
            entry_params = entry_param_objects[0] if entry_param_objects else {}
            exit_params = exit_param_objects[0] if exit_param_objects else {}
            
            # *** 新增功能：即時回饋 ***
            entry_params_dict = entry_params.params.__dict__ if hasattr(entry_params, 'params') else {}
            exit_params_dict = exit_params.params.__dict__ if hasattr(exit_params, 'params') else {}
            calculate_and_print_monthly_stats(equity, dates, backtest_id, {**entry_params_dict, **exit_params_dict})
            
            # (以下為原有的績效計算邏輯)
            trade_actions = trade_results["trade_actions"][:, i]
            trade_mask = trade_actions != 0
            records = pd.DataFrame()
            if np.any(trade_mask):
                records = pd.DataFrame({
                    'Time': dates[trade_mask],
                    'Price': prices[trade_mask],
                    'Trade_action': trade_actions[trade_mask]
                })

            total_return = (equity[-1] - equity[0]) / equity[0] if len(equity) > 1 and equity[0] != 0 else 0
            returns = np.diff(equity) / equity[:-1] if len(equity) > 1 else np.array([])
            returns = np.nan_to_num(returns)
            
            sharpe = 0
            if len(returns) > 0 and np.std(returns) > 0:
                freq_map = {"1m": 252*1440, "1h": 252*24, "1d": 252}
                annual_factor = freq_map.get(frequency, 252)
                sharpe = np.mean(returns) / np.std(returns) * np.sqrt(annual_factor)
                
            cum_max = np.maximum.accumulate(equity)
            drawdown = (equity - cum_max) / cum_max if np.all(cum_max > 0) else np.zeros_like(equity)
            max_dd = np.min(drawdown) if len(drawdown) > 0 else 0

            result = {
                "backtest_id": backtest_id,
                "strategy_id": all_tasks["strategy_ids"][task_idx],
                "params": {"entry": entry_params, "exit": exit_params},
                "total_return": total_return,
                "sharpe_ratio": sharpe,
                "max_drawdown": max_dd,
                "records": records
            }
            results.append(result)
            
        return results

    @staticmethod
    def _simulate_batch_trades(batch_signals, trading_params, data):
        entry_signals = batch_signals["entry_signals"]
        exit_signals = batch_signals["exit_signals"]
        n_timesteps, n_strategies = entry_signals.shape
        prices = data['Close'].values
        
        equity_values = np.full((n_timesteps, n_strategies), trading_params.get("initial_capital", 1000000), dtype=np.float64)
        trade_actions = np.zeros((n_timesteps, n_strategies), dtype=np.int8)
        
        current_positions = np.zeros(n_strategies, dtype=np.int8)
        cash = np.full(n_strategies, equity_values[0, 0])
        shares = np.zeros(n_strategies)
        transaction_cost_pct = trading_params.get("transaction_cost", 0.0005)

        for t in range(1, n_timesteps):
            equity_values[t] = equity_values[t-1]
            price = prices[t]
            
            if price <= 0: continue # 跳過無效價格

            exits = (exit_signals[t] == 1) & (current_positions == 1)
            if np.any(exits):
                revenue = shares[exits] * price * (1 - transaction_cost_pct)
                cash[exits] += revenue
                shares[exits] = 0
                current_positions[exits] = 0
                trade_actions[t, exits] = -1

            entries = (entry_signals[t] == 1) & (current_positions == 0)
            if np.any(entries):
                cost = cash[entries] * (1 - transaction_cost_pct)
                new_shares = cost / price
                shares[entries] = new_shares
                cash[entries] = 0
                current_positions[entries] = 1
                trade_actions[t, entries] = 1
            
            equity_values[t] = cash + shares * price
            
        return {"equity_values": equity_values, "trade_actions": trade_actions}
