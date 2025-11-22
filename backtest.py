# -*- coding: utf-8 -*-
"""
此檔案用於執行、評估並最佳化交易策略的回測。
"""
import warnings
import pandas as pd
from backtesting import Backtest
import re

# 從本地模組導入
from src.fetch import fetch_stock_data
from src.strategy import SupertrendBNFStrategy

# --- 全域設定 ---
warnings.filterwarnings('ignore', category=FutureWarning)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# --- 輔助函式 ---
def _rename_ohlc_columns(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    將 yfinance multi-index 欄位或帶有 ticker 後綴的欄位重新命名為標準 OHLC 名稱。
    例如 'Close_0050.TW' -> 'Close'
    """
    df = df.copy()
    # 處理 multi-index 標頭，例如 yfinance 常見的 ('Close', '0050.TW')
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    # 處理單層級但有後綴的標頭
    new_cols = {}
    for col in df.columns:
        # 使用正則表達式移除常見的 ticker 後綴，例如 '_0050.TW' 或 '.TW'
        clean_col = re.sub(rf'[._]{re.escape(ticker)}', '', col, flags=re.IGNORECASE)
        new_cols[col] = clean_col
    df.rename(columns=new_cols, inplace=True)

    # 確保大小寫一致 (Open, High, Low, Close)
    df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)

    return df

# --- 回測參數 ---
TICKER = '0050.TW'
START_DATE = '2010-01-01'
END_DATE = '2023-12-31'
INITIAL_CASH = 1_000_000
COMMISSION_RATE = .001425 # 台灣股票交易手續費

def run_backtest_and_optimize(ticker, start_date, end_date):
    """
    執行策略回測與參數最佳化。
    """
    print(f"正在為 {ticker} 載入數據，期間從 {start_date} 至 {end_date}...")
    data = fetch_stock_data(ticker, start_date, end_date)
    if data.empty:
        return

    data = _rename_ohlc_columns(data, ticker)

    bt = Backtest(data, SupertrendBNFStrategy,
                  cash=INITIAL_CASH, commission=COMMISSION_RATE)

    print("--- 正在執行參數最佳化 ---")
    stats = bt.optimize(
        bnf_ma_period=range(60, 181, 20),
        bnf_entry_bias=list(pd.Series(range(-10, -2, 1)) / 100.0),
        maximize='Sharpe Ratio',
        constraint=lambda p: p.bnf_ma_period > 30
    )

    print("\n--- 最佳化完成 ---")
    print("最佳參數組合:")
    print(stats._strategy)

    print("\n詳細回測結果 (使用最佳參數):")
    print(stats)

    # 將 ticker 中的 '.' 替換為 '_' 以產生一個更安全的檔案名
    safe_ticker_name = ticker.replace(".", "_")
    plot_filename = f'backtest_results_{safe_ticker_name}_optimized.html'
    bt.plot(filename=plot_filename, open_browser=False)
    print(f"\n詳細報告已儲存至: {plot_filename}")

    equity_curve = stats['_equity_curve']
    monthly_returns = equity_curve['Equity'].resample('ME').last().pct_change()
    max_monthly_loss = monthly_returns.min()
    print("\n--- 風險評估 (使用最佳參數) ---")
    print(f"單月最大虧損: {max_monthly_loss:.2%}")

if __name__ == '__main__':
    run_backtest_and_optimize(TICKER, START_DATE, END_DATE)
