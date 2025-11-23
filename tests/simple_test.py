# -*- coding: utf-8 -*-
"""
簡化版回測測試腳本 - 用於診斷問題
"""
import yfinance as yf
import pandas as pd
import numpy as np

print("=== 步驟 1: 測試數據抓取 ===")
# 測試多個股票代碼
tickers = ['SPY', '0050.TW', '^TWII']
for ticker in tickers:
    print(f"\n測試 {ticker}...")
    try:
        data = yf.download(ticker, start='2023-01-01', end='2023-12-31', progress=False)
        if data.empty:
            print(f"  ❌ {ticker}: 無數據")
        else:
            print(f"  ✅ {ticker}: 成功抓取 {len(data)} 筆資料")
            print(f"     日期範圍: {data.index[0]} 到 {data.index[-1]}")
    except Exception as e:
        print(f"  ❌ {ticker}: 錯誤 - {e}")

print("\n=== 步驟 2: 測試 pandas-ta ===")
try:
    import pandas_ta as ta
    print(f"✅ pandas-ta 版本: {ta.version}")
    
    # 測試基本指標計算
    test_data = yf.download('SPY', period='1mo', progress=False)
    if not test_data.empty:
        test_data.ta.sma(length=10, append=True)
        print(f"✅ 成功計算 SMA 指標")
except Exception as e:
    print(f"❌ pandas-ta 測試失敗: {e}")

print("\n=== 測試完成 ===")
