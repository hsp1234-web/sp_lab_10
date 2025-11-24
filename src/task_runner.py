# -*- coding: utf-8 -*-
"""
任務執行器 (Task Runner)

這個模組負責接收從 main.py 解析來的任務配置，並根據
指定的 `action` 來執行具體的函式。
"""

import os
import time
import pandas as pd
from rich.console import Console

# --- 核心邏輯導入 ---
from src.fetch import fetch_stock_data
from src.clean import clean_data
from src.feat import calculate_features
from src.sp_signal import generate_signals, generate_buy_and_hold_signals, adjust_signals_for_execution
from src.backtest import run_backtest
from src.stats import calculate_backtest_stats
from src.viz import plot_equity_curve


class TaskRunner:
    """
    TaskRunner 類別負責執行一個完整的任務。
    它會迭代任務中的每一個步驟，並調度到對應的處理函式。
    """
    def __init__(self):
        """
        初始化 TaskRunner。
        """
        self.console = Console()

        # --- 設定基礎路徑 ---
        self.base_dir = os.getcwd()
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.raw_data_dir = os.path.join(self.data_dir, 'raw')
        self.processed_data_dir = os.path.join(self.data_dir, 'processed')

        # --- 確保目錄存在 ---
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.processed_data_dir, exist_ok=True)

    def run(self, steps):
        """
        執行一個包含多個步驟的任務。
        """
        total_steps = len(steps)
        self.console.print(f"解析到 {total_steps} 個執行步驟。")

        for i, step in enumerate(steps):
            action = step.get('action')
            if not action:
                self.console.print(f"[bold red]錯誤：[/bold red] 步驟 {i+1} 缺少 'action' 參數。")
                return False

            self.console.print(f"\n--- [ 步驟 {i+1}/{total_steps} ] ---")
            self.console.print(f"  ▶️  執行動作: [bold yellow]{action}[/bold yellow]")

            handler = getattr(self, f"_{action}", self._unsupported_action)
            success = handler(step)

            if not success:
                self.console.print(f"[bold red]❌ 步驟 {i+1} ('{action}') 執行失敗。[/bold red] 中止任務。")
                return False

            self.console.print(f"[bold green]✅ 步驟 {i+1} ('{action}') 執行成功。[/bold green]")

        return True

    def _unsupported_action(self, params):
        """
        處理不支援的 action 類型。
        """
        action = params.get('action')
        self.console.print(f"[bold red]錯誤：[/bold red] 不支援的動作類型 '{action}'。")
        return False

    # ----------------------------------------------------------------------------
    # Action 處理函式
    # ----------------------------------------------------------------------------

    def _download_data(self, params):
        """
        處理 'download_data' 動作。
        """
        symbols = params.get('symbols', [])
        if not symbols:
            self.console.print("  [bold yellow]警告：[/bold yellow] 未提供任何股票代碼 (symbols)，跳過下載。")
            return True

        self.console.print(f"  📥  準備為 {len(symbols)} 個股票代碼下載數據...")

        start_date = params.get('start_date', '2000-01-01')
        end_date = params.get('end_date', pd.Timestamp.now().strftime('%Y-%m-%d'))

        for symbol in symbols:
            self.console.print(f"    - 正在下載 [cyan]{symbol}[/cyan] ({start_date} to {end_date})...", end="")
            df = fetch_stock_data(symbol, start_date, end_date)

            if df.empty:
                self.console.print(" [bold red]失敗[/bold red]")
                continue

            output_path = os.path.join(self.raw_data_dir, f"{symbol}.parquet")
            df.to_parquet(output_path)
            self.console.print(f" [bold green]成功[/bold green] ({len(df)} 筆資料) -> {output_path}")

        return True

    def _backtest(self, params):
        """
        處理 'backtest' 動作。
        執行從數據處理到回測結束的完整流程。
        """
        # --- 1. 獲取參數 ---
        symbol = params.get('symbol')
        strategy_name = params.get('strategy_name', 'buy_and_hold')
        output_path = params.get('output_path', os.path.join('output', 'default_backtest'))

        # --- 參數驗證 ---
        if not symbol:
            self.console.print("[bold red]錯誤：[/bold red] backtest 動作缺少 'symbol' 參數。")
            return False

        raw_data_path = os.path.join(self.raw_data_dir, f"{symbol}.parquet")
        if not os.path.exists(raw_data_path):
            self.console.print(f"[bold red]錯誤：[/bold red] 找不到原始數據檔案：{raw_data_path}。請先執行 download_data。")
            return False

        # --- 確保輸出目錄存在 ---
        os.makedirs(output_path, exist_ok=True)
        self.console.print(f"  📂  結果將儲存至: {output_path}")

        # --- 2. 數據處理 ---
        self.console.print("  - [1/5] 正在處理數據...")
        raw_df = pd.read_parquet(raw_data_path)
        clean_df = clean_data(raw_df)
        features_df = calculate_features(clean_df)
        self.console.print("    ✅ 數據清洗與特徵計算完成。")

        # --- 3. 訊號生成 ---
        self.console.print(f"  - [2/5] 正在根據策略 '{strategy_name}' 生成訊號...")
        if strategy_name == 'volatility':
            # --- 修正：移除了不存在的 use_sma_filter 參數 ---
            ideal_signals_df = generate_signals(features_df, high_vol_trend=-1)
            executable_signals_df = adjust_signals_for_execution(ideal_signals_df)
        elif strategy_name == 'buy_and_hold':
            executable_signals_df = generate_buy_and_hold_signals(features_df)
        else:
            self.console.print(f"[bold red]錯誤：[/bold red] 不支援的策略名稱 '{strategy_name}'。")
            return False
        self.console.print("    ✅ 交易訊號生成完成。")

        # --- 4. 執行回測 ---
        self.console.print("  - [3/5] 正在執行回測模擬...")
        # 暫時使用舊 main.py 的預設參數
        init_capital = 100000.0
        pos_size = 100
        cost_params = {'fee_per_trade': 1.5, 'slippage_pct': 0.0001}

        trade_log, equity_curve = run_backtest(
            price_data=features_df,
            signals=executable_signals_df['signal'],
            init_cap=init_capital,
            pos_size=pos_size,
            cost_mode='simple',
            cost_params=cost_params
        )
        trade_log_path = os.path.join(output_path, 'trade_log.csv')
        trade_log.to_csv(trade_log_path)
        self.console.print(f"    ✅ 回測完成，交易日誌已儲存至 {trade_log_path}")

        # --- 5. 計算與視覺化 ---
        self.console.print("  - [4/5] 正在計算績效指標...")
        performance_metrics = calculate_backtest_stats(
            trade_log=trade_log,
            equity_curve=equity_curve,
            initial_capital=init_capital
        )

        equity_curve_path = os.path.join(output_path, 'equity_curve.jpg')
        plot_equity_curve(equity_curve, equity_curve_path, performance_metrics)
        self.console.print(f"    ✅ 權益曲線圖已儲存至 {equity_curve_path}")

        # --- 6. 顯示報告 ---
        self.console.print("  - [5/5] 最終績效報告:")
        self.console.print("\n" + "="*25 + " 績效報告 " + "="*25)
        for metric, value in performance_metrics.items():
            if isinstance(value, float):
                self.console.print(f"  {metric:<20}: {value:.4f}")
            else:
                self.console.print(f"  {metric:<20}: {value}")
        self.console.print("="*62 + "\n")

        return True


    def _analyze_results(self, params):
        """
        處理 'analyze_results' 動作。
        (Placeholder)
        """
        source = params.get('source_folder', 'N/A')
        self.console.print(f"  📊  (模擬) 正在分析來自 {source} 的結果...")
        time.sleep(1) # 模擬計算時間
        self.console.print(f"  📊  (模擬) 結果分析完成，報告已生成於 {params.get('report_name', 'N/A')}")
        return True
