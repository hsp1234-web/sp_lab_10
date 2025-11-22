# -*- coding: utf-8 -*-
"""
此模組提供從 yfinance 下載股票歷史數據的功能。
"""
import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    從 yfinance 下載指定股票在特定期間內的歷史數據。

    Args:
        ticker (str): 股票代碼, 例如 '0050.TW' 或 '^GSPC'。
        start_date (str): 數據開始日期, 格式 'YYYY-MM-DD'。
        end_date (str): 數據結束日期, 格式 'YYYY-MM-DD'。

    Returns:
        pd.DataFrame: 包含 OHLCV 數據的 DataFrame。
                      如果下載失敗則返回一個空的 DataFrame。
    """
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            print(f"警告：找不到 {ticker} 在 {start_date} 到 {end_date} 期間的數據。")
        return data
    except Exception as e:
        print(f"下載 {ticker} 數據時發生錯誤: {e}")
        return pd.DataFrame()

if __name__ == '__main__':
    # 這段程式碼只有在 `python src/fetch.py` 被直接執行時才會觸發
    # 用於快速測試函式功能
    print("--- 測試 fetch_stock_data 函式 ---")
    gspc_data = fetch_stock_data('^GSPC', '2023-01-01', '2023-12-31')
    if not gspc_data.empty:
        print("成功獲取 S&P 500 (^GSPC) 數據：")
        print(gspc_data.head())

    print("\n--- 測試一個無效的股票代碼 ---")
    invalid_data = fetch_stock_data('INVALIDTICKERXYZ', '2023-01-01', '2023-12-31')
    print(f"無效股票代碼的返回結果是否為空 DataFrame: {invalid_data.empty}")
