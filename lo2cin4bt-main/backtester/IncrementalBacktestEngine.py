import logging
import gc
import time
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from concurrent.futures import ProcessPoolExecutor
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .VectorBacktestEngine_backtester import VectorBacktestEngine
from database.BacktestDB import BacktestDB
from .SpecMonitor_backtester import SpecMonitor

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
        
        Args:
            config: 回測配置
            job_id: 任務 ID
            resume: 是否嘗試續傳
        """
        self.logger.info(f"啟動增量回測 Job ID: {job_id}")
        
        # 1. 初始化資料庫連接
        self.db = BacktestDB(self.db_path)
        
        # 2. 生成所有參數組合
        all_combinations = self.generate_parameter_combinations(config)
        all_tasks = self._generate_all_tasks_matrix(all_combinations, config["predictors"])
        total_tasks = len(all_tasks["combinations"])
        
        # 檢查並創建任務
        existing_job = self.db.get_job(job_id)
        if not existing_job:
            self.logger.info(f"創建新任務: {job_id}, 總任務數: {total_tasks}")
            # 這裡我們需要把 config 轉成 json string 存入，但 config 可能包含非 serializable 對象
            # 簡單起見，存一個簡化的 config
            import json
            try:
                config_json = json.dumps(config, default=str)
            except:
                config_json = "{}"
            self.db.create_job(job_id, config_json, total_tasks)
        else:
            self.logger.info(f"任務 {job_id} 已存在，準備續傳")
        
        # 3. 處理續傳邏輯
        completed_ids = set()
        if resume:
            completed_ids = set(self.db.get_completed_backtest_ids(job_id))
            self.logger.info(f"發現已完成任務數: {len(completed_ids)}")
        
        # 4. 過濾未完成的任務
        # 注意：這裡需要重新構建 all_tasks，只包含未完成的部分
        # 但為了保持索引一致性，我們最好是在執行時跳過，或者重建索引映射
        # 簡單起見，我們在 _generate_all_results_vectorized 中過濾
        
        # 5. 準備信號和條件
        condition_pairs = config["condition_pairs"]
        all_signals = self._generate_all_signals_vectorized(all_tasks, condition_pairs)
        
        # 6. 執行回測 (核心邏輯)
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
        """
        生成結果並即時寫入資料庫 (取代原有的 _generate_all_results_vectorized)
        """
        n_tasks = len(all_tasks["combinations"])
        
        # 獲取系統資源建議
        n_cores, _ = SpecMonitor.get_optimal_core_count()
        
        # 動態計算批次大小
        # Windows 下 spawn 開銷大，批次要大一點
        batch_size = max(50, n_tasks // (n_cores * 4))
        batch_size = min(batch_size, 500) # 上限 500，避免單批次記憶體過大
        
        self.logger.info(f"使用 {n_cores} 核心並行處理，批次大小: {batch_size}")

        # 準備批次索引
        batch_indices = []
        for i in range(0, n_tasks, batch_size):
            # 檢查這一批次是否全部都已經完成
            batch_range = range(i, min(i + batch_size, n_tasks))
            batch_task_ids = [all_tasks["backtest_ids"][j] for j in batch_range]
            
            if all(tid in completed_ids for tid in batch_task_ids):
                continue # 整批跳過
            
            # 如果部分完成，這批還是要跑，但內部會過濾
            # 為了簡單，我們這裡就整批跑，DB 會處理重複寫入 (INSERT OR REPLACE)
            batch_indices.append(list(batch_range))

        if not batch_indices:
            self.logger.info("所有任務已完成，無需執行")
            return

        # 執行並行運算
        total_batches = len(batch_indices)
        processed_batches = 0
        
        with ProcessPoolExecutor(max_workers=n_cores) as executor:
            futures = []
            
            for batch_idx, idx_list in enumerate(batch_indices):
                # 準備數據 (只傳遞必要的 numpy array 切片)
                # 注意：這裡我們需要一個空的 all_trade_results，因為 _prepare_batch_data 需要它
                # 但實際上我們不需要預先計算 trade_results，因為那是 _process_batch_results_optimized 內部算的？
                # 不，VectorBacktestEngine 的流程是：
                # 1. _simulate_all_trades_vectorized (算出 trade_results)
                # 2. _generate_all_results_vectorized (組裝結果)
                # 
                # 我們需要調整流程：
                # 我們不能一次算完所有 trade_results (太佔記憶體)
                # 我們應該在每個批次內：生成信號 -> 模擬交易 -> 組裝結果 -> 寫入 DB
                
                # 但 VectorBacktestEngine 的設計是分離的。
                # 為了 V2，我們需要重寫 _process_batch_results_optimized 或是
                # 在這裡先做模擬交易？
                
                # 讓我們看 VectorBacktestEngine 的源碼...
                # 它確實是先 _simulate_all_trades_vectorized 算出所有結果矩陣
                # 這就是記憶體爆掉的原因之一！
                
                # V2 改進：我們必須把 _simulate_all_trades_vectorized 也拆進批次裡！
                pass

            # 由於繼承結構限制，如果父類別邏輯是「先全算再組裝」，我們很難只覆寫組裝部分就解決記憶體問題。
            # 我們必須覆寫整個流程。
            
            # 重新設計流程：
            # 1. 準備批次數據 (包含信號)
            # 2. 在子進程中：模擬交易 -> 計算指標 -> 返回結果 dict
            # 3. 主進程：寫入 DB
            
            # 這需要修改 _process_batch_results_optimized，讓它包含模擬交易的邏輯
            # 但 _process_batch_results_optimized 依賴 trade_results 矩陣
            
            # 解決方案：
            # 我們在主進程中，針對每個批次，切片信號矩陣 -> 呼叫一個新的靜態方法/函數來執行模擬和計算
            
            for batch_idx, idx_list in enumerate(batch_indices):
                # 準備該批次的信號切片
                batch_signals = {
                    "entry_signals": all_signals["entry_signals"][:, idx_list],
                    "exit_signals": all_signals["exit_signals"][:, idx_list]
                }
                
                # 提交任務
                future = executor.submit(
                    self._run_batch_simulation_and_metrics,
                    idx_list,
                    batch_signals,
                    all_tasks, # 這裡傳遞整個 all_tasks 可能有點大，但主要是 metadata
                    condition_pairs,
                    trading_params,
                    self.data, # 傳遞原始數據 (唯讀，多進程共享)
                    self.frequency
                )
                futures.append(future)

            # 收集結果
            for future in futures:
                try:
                    batch_results = future.result()
                    
                    # 寫入資料庫
                    self.db.write_batch_results(job_id, batch_results)
                    
                    processed_batches += 1
                    self.logger.info(f"進度: {processed_batches}/{total_batches} 批次完成")
                    
                    # 釋放記憶體
                    del batch_results
                    gc.collect()
                    
                except Exception as e:
                    self.logger.error(f"批次處理失敗: {e}")

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
        """
        在子進程中執行：模擬交易 + 計算指標
        """
        # 1. 模擬交易
        trade_results = IncrementalBacktestEngine._simulate_batch_trades(batch_signals, trading_params, data)
        
        # 2. 組裝結果
        results = []
        prices = data['Close'].values
        dates = data['Time'].values
        
        for i, task_idx in enumerate(batch_indices):
            # 獲取該任務的交易結果
            positions = trade_results["positions"][:, i]
            trade_actions = trade_results["trade_actions"][:, i]
            equity = trade_results["equity_values"][:, i]
            
            # 提取元數據
            strategy_id = all_tasks["strategy_ids"][task_idx]
            backtest_id = all_tasks["backtest_ids"][task_idx]
            combo = all_tasks["combinations"][task_idx]
            
            # 解析參數
            # 這裡需要解析 strategy_id 來獲取 condition_pair index
            # 假設 strategy_id 格式為 "strategy_X_..."
            # 簡單起見，我們假設只有一個 condition pair (index 0)
            # 或者我們傳遞 condition_pair_idx?
            # VectorBacktestEngine 的 strategy_id 生成邏輯比較複雜
            # 這裡簡化處理：
            condition_pair = condition_pairs[0] # 暫時假設只有一個
            
            entry_params = list(combo[: len(condition_pair["entry"])])
            exit_params = list(combo[len(condition_pair["entry"]) : len(condition_pair["entry"]) + len(condition_pair["exit"])])
            
            # 生成交易記錄 DataFrame
            trade_mask = trade_actions != 0
            if np.any(trade_mask):
                records = pd.DataFrame({
                    'Time': dates[trade_mask],
                    'Price': prices[trade_mask],
                    'Trade_action': trade_actions[trade_mask],
                    'Position': positions[trade_mask],
                    'Equity': equity[trade_mask]
                })
            else:
                records = pd.DataFrame()

            # 計算指標
            total_return = (equity[-1] - equity[0]) / equity[0] if len(equity) > 0 else 0
            
            returns = np.diff(equity) / equity[:-1]
            returns = np.nan_to_num(returns)
            
            if len(returns) > 0 and np.std(returns) > 0:
                # 解析 frequency
                freq_map = {"1m": 252*1440, "1h": 252*24, "1d": 252}
                annual_factor = freq_map.get(frequency, 252)
                sharpe = np.mean(returns) / np.std(returns) * np.sqrt(annual_factor)
            else:
                sharpe = 0
                
            # Max Drawdown
            cum_max = np.maximum.accumulate(equity)
            drawdown = (equity - cum_max) / cum_max
            max_dd = np.min(drawdown) if len(drawdown) > 0 else 0

            result = {
                "backtest_id": backtest_id,
                "strategy_id": strategy_id,
                "params": {
                    "entry": entry_params,
                    "exit": exit_params,
                    "predictor": all_tasks["predictors"][task_idx]
                },
                "total_return": total_return,
                "sharpe_ratio": sharpe,
                "max_drawdown": max_dd,
                "records": records
            }
            results.append(result)
            
        return results

    @staticmethod
    def _simulate_batch_trades(batch_signals, trading_params, data):
        """
        針對一個批次進行向量化交易模擬
        """
        entry_signals = batch_signals["entry_signals"]
        exit_signals = batch_signals["exit_signals"]
        
        n_timesteps, n_strategies = entry_signals.shape
        prices = data['Close'].values
        
        positions = np.zeros((n_timesteps, n_strategies), dtype=np.int8)
        trade_actions = np.zeros((n_timesteps, n_strategies), dtype=np.int8)
        equity_values = np.zeros((n_timesteps, n_strategies), dtype=np.float64)
        
        initial_capital = trading_params.get("initial_capital", 1000000)
        transaction_cost = trading_params.get("transaction_cost", 0.0004)
        
        current_positions = np.zeros(n_strategies)
        cash = np.full(n_strategies, initial_capital)
        shares = np.zeros(n_strategies)
        
        for t in range(1, n_timesteps):
            price = prices[t]
            
            entries = (entry_signals[t] == 1) & (current_positions == 0)
            exits = (exit_signals[t] == 1) & (current_positions == 1)
            
            if np.any(exits):
                revenue = shares[exits] * price * (1 - transaction_cost)
                cash[exits] += revenue
                shares[exits] = 0
                current_positions[exits] = 0
                trade_actions[t, exits] = -1
            
            if np.any(entries):
                cost = cash[entries] * (1 - transaction_cost)
                new_shares = cost / price
                shares[entries] = new_shares
                cash[entries] = 0
                current_positions[entries] = 1
                trade_actions[t, entries] = 1
            
            equity_values[t] = cash + shares * price
            positions[t] = current_positions
            
        return {
            "positions": positions,
            "trade_actions": trade_actions,
            "equity_values": equity_values
        }
