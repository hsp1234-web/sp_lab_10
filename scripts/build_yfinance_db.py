# -*- coding: utf-8 -*-
"""
從 yfinance 獲取數據並建立一個 DuckDB 資料庫 (ETL 流程)

這個腳本會執行以下操作：
1. 定義一個股票/ETF 列表 (tickers)。
2. 建立或連接到一個位於 data/yfinance.db 的 DuckDB 資料庫。
3. 創建一個名為 'ohlcv' 的表，用於儲存所有 Ticker 的日線數據。
4. 迭代 Ticker 列表：
   a. (Extract) 使用 yfinance 下載該 Ticker 的歷史數據。
   b. (Transform) 重建一個乾淨、標準化的 DataFrame。
   c. (Load) 將數據寫入 DuckDB 資料庫。
"""
import duckdb
import yfinance as yf
import pandas as pd
from pathlib import Path

# --- 設定 ---
# 定義我們要研究的 Ticker 列表
TICKERS = [
    'SPY',       # S&P 500 ETF
    'QQQ',       # Nasdaq 100 ETF
    'TLT',       # 20+ Year Treasury Bond ETF
    'GLD',       # Gold ETF
    '0050.TW'    # 台灣 50 ETF
]

# 定義數據庫路徑
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "yfinance.db"
TABLE_NAME = 'ohlcv'

def build_database():
    """
    執行完整的數據庫建構流程。
    """
    print("--- 開始建構 yfinance 數據庫 (ETL 模式) ---")

    DB_DIR.mkdir(exist_ok=True)

    # 連接到 DuckDB
    con = duckdb.connect(str(DB_PATH))

    # 創建表 (如果已存在，則先刪除)
    print(f"正在準備資料表 '{TABLE_NAME}'...")
    con.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    con.execute(f"""
        CREATE TABLE {TABLE_NAME} (
            Time TIMESTAMP,
            Open DOUBLE,
            High DOUBLE,
            Low DOUBLE,
            Close DOUBLE,
            Volume BIGINT,
            Symbol VARCHAR
        )
    """)
    print("✅ 資料表創建成功。")

    # 迭代處理每個 Ticker
    for ticker in TICKERS:
        print(f"\n--- 正在處理 Ticker: {ticker} ---")
        try:
            # 1. (E) Extract: 提取原始數據
            print(f"  [1/3] 正在從 yfinance 下載數據...")
            yf_data = yf.download(ticker, start="2000-01-01", progress=False, auto_adjust=False)

            if yf_data.empty:
                print(f"  ⚠️  警告：'{ticker}' 的數據為空，跳過此 Ticker。")
                continue

            # 2. (T) Transform: 重建一個乾淨、標準化的 DataFrame
            print(f"  [2/3] 正在重建並標準化 DataFrame...")

            # 創建一個新的、結構完全可控的 DataFrame
            data = pd.DataFrame()
            data['Time'] = yf_data.index
            data['Open'] = yf_data['Open'].values
            data['High'] = yf_data['High'].values
            data['Low'] = yf_data['Low'].values
            data['Close'] = yf_data['Close'].values
            data['Volume'] = yf_data['Volume'].values
            data['Symbol'] = ticker

            # 移除包含 NaN 數據的行 (yfinance 可能會返回一些不完整的數據)
            data.dropna(inplace=True)

            # 3. (L) Load: 載入數據到 DuckDB
            print(f"  [3/3] 正在將 {len(data)} 筆數據寫入資料庫...")
            con.register('df_view', data)
            con.execute(f"INSERT INTO {TABLE_NAME} SELECT * FROM df_view")
            con.unregister('df_view')

            print(f"✅ Ticker '{ticker}' 處理完成。")

        except Exception as e:
            print(f"  ❌ 錯誤：在處理 '{ticker}' 時發生問題。")
            print(f"     錯誤詳情：{e}")

    # 驗證數據
    print("\n--- 數據庫建構完成，正在進行最終驗證 ---")
    total_rows = con.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
    print(f"✅ 數據庫 '{DB_PATH.name}' 總共包含 {total_rows} 筆數據。")

    print("\n--- 各 Ticker 筆數統計 ---")
    summary = con.execute(f"SELECT Symbol, COUNT(*) as Count FROM {TABLE_NAME} GROUP BY Symbol ORDER BY Symbol").df()
    print(summary)

    # 關閉連接
    con.close()
    print("\n數據庫連接已關閉。")

if __name__ == "__main__":
    build_database()
