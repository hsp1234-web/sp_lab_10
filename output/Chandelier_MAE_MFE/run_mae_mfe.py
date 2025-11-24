import os
import sys
import pandas as pd
import logging
import traceback

# Setup logging to file
log_file = "debug_run.log"
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')
logger = logging.getLogger("MAE_MFE_Runner")

def log_print(msg):
    print(msg)
    logger.info(msg)

log_print("Script started...")

def run_mae_mfe_analysis():
    log_print("Function run_mae_mfe_analysis started...")
    
    # 設定輸出目錄
    output_dir = os.path.join("output", "MAE_MFE_Analysis")
    os.makedirs(output_dir, exist_ok=True)
    log_print(f"Output directory: {output_dir}")
    
    # 1. 載入數據
    log_print("Step 1: Data Loading...")
    try:
        # 由於專案結構問題 (lo2cin4bt-main 帶有連字號)，我們需要調整 sys.path
        sys.path.append(os.path.join(os.getcwd(), "lo2cin4bt-main"))
        
        import duckdb
        db_path = r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\taifex.db"
        
        if not os.path.exists(db_path):
            log_print(f"Database not found at {db_path}")
            return

        con = duckdb.connect(db_path)
        # 查詢 TX 資料
        query = """
            SELECT Date as Time, Open, High, Low, Close, Volume 
            FROM futures_data 
            WHERE Symbol='TX' 
            ORDER BY Date
        """
        df = con.execute(query).fetchdf()
        con.close()
        
        df['Time'] = pd.to_datetime(df['Time'])
        df = df.set_index('Time')
        
        log_print(f"Data loaded: {len(df)} rows")
        
    except Exception as e:
        log_print(f"Data loading failed: {e}")
        logger.error(traceback.format_exc())
        return

    # 2. 執行回測
    log_print("Step 2: Backtesting...")
    try:
        from backtester.Chandelier_Indicator_backtester import ChandelierIndicator
        
        # 設定參數
        params = {'length': 22, 'multiplier': 3.0}
        
        # 初始化指標
        indicator = ChandelierIndicator(df, params, logger=logger)
        
        # 產生信號
        signals = indicator.generate_signals()
        df['Signal'] = signals
        
        # 模擬交易 (簡化版)
        trades = []
        position = 0
        entry_price = 0
        entry_time = None
        
        signal_counts = {1: 0, -1: 0, 0: 0}
        
        for i in range(1, len(df)):
            current_time = df.index[i]
            current_price = df['Close'].iloc[i]
            signal = df['Signal'].iloc[i]
            
            if signal != 0:
                signal_counts[signal] = signal_counts.get(signal, 0) + 1
            
            # 進場 (多單)
            if signal > 0 and position == 0:
                position = 1
                entry_price = current_price
                entry_time = current_time
            
            # 進場 (空單)
            elif signal < 0 and position == 0:
                position = -1
                entry_price = current_price
                entry_time = current_time
                
            # 出場 (多單轉空 或 平倉)
            elif (signal < 0 and position == 1) or (signal > 0 and position == -1):
                # 記錄交易
                exit_price = current_price
                exit_time = current_time
                pnl = (exit_price - entry_price) * position
                ret = pnl / entry_price
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': exit_time,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'type': position, # 1 for Long, -1 for Short
                    'return': ret
                })
                
                # 反手
                position = 1 if signal > 0 else -1
                entry_price = current_price
                entry_time = current_time
        
                position = signal
                entry_price = current_price
                entry_time = current_time
        
        log_print(f"Signal counts in loop: {signal_counts}")
        
        # Debug: check first few signals
        non_zero_signals = df[df['Signal'] != 0]['Signal'].head(10)
        log_print(f"First 10 non-zero signals:\n{non_zero_signals}")
        
        trades_df = pd.DataFrame(trades)
        log_print(f"Backtest complete: {len(trades_df)} trades")
        
        # 儲存交易記錄
        trades_df.to_csv(os.path.join(output_dir, "trades.csv"), index=False)
        
    except Exception as e:
        log_print(f"Backtest failed: {e}")
        logger.error(traceback.format_exc())
        return

    # 3. MAE/MFE 分析
    log_print("Step 3: MAE/MFE Analysis...")
    try:
        from metricstracker.MAEMFE_Analyser_metricstracker import MAEMFEAnalyser
        
        analyser = MAEMFEAnalyser(trades_df, df, logger=logger)
        analyzed_trades = analyser.analyze()
        
        # 儲存分析結果
        analyzed_trades.to_csv(os.path.join(output_dir, "trades_with_maemfe.csv"), index=False)
        
        # 產生統計摘要 (繁體中文)
        stats = analyser.get_summary_stats()
        summary_md = f"""# MAE/MFE 分析報告

## 統計摘要
- **總交易次數**: {len(analyzed_trades)}
- **平均 MAE (最大不利幅度)**: {stats.get('Avg MAE', 0):.4f} ({stats.get('Avg MAE', 0)*100:.2f}%)
- **平均 MFE (最大有利幅度)**: {stats.get('Avg MFE', 0):.4f} ({stats.get('Avg MFE', 0)*100:.2f}%)
- **最大 MAE**: {stats.get('Max MAE', 0):.4f}
- **最大 MFE**: {stats.get('Max MFE', 0):.4f}
- **Edge Ratio (優勢比率)**: {stats.get('Edge Ratio', 0):.2f} (MFE/MAE)

## 策略說明
本報告基於 **吊燈停損 (Chandelier Stop)** 策略進行回測與分析。
- **商品**: TX (台指期)
- **參數**: Length=22, Multiplier=3.0
- **分析期間**: {df.index[0].date()} 至 {df.index[-1].date()}

## 建議
- 若 Edge Ratio > 1，表示策略具有正期望值潛力。
- 觀察 MAE 分布，可設定合理的停損點 (例如 MAE 的 75% 分位數)。
- 觀察 MFE 分布，可設定分批停利點。
"""
        with open(os.path.join(output_dir, "analysis_report.md"), "w", encoding="utf-8") as f:
            f.write(summary_md)
        log_print("Analysis report saved.")
            
    except Exception as e:
        log_print(f"Analysis failed: {e}")
        logger.error(traceback.format_exc())
        return

    # 4. 生成圖表
    log_print("Step 4: Visualization...")
    try:
        from plotter.MAEMFE_plotter import plot_mae_mfe
        
        fig = plot_mae_mfe(analyzed_trades)
        plot_path = os.path.join(output_dir, "maemfe_charts.html")
        fig.write_html(plot_path)
        log_print(f"Charts saved to {plot_path}")
        
    except Exception as e:
        log_print(f"Visualization failed: {e}")
        logger.error(traceback.format_exc())
        return

    log_print(f"Success! Results saved to {output_dir}")

if __name__ == "__main__":
    run_mae_mfe_analysis()
