import os
import pandas as pd
import yfinance as yf

# 設定下載參數
TICKER = "TX=F"  # 台指期貨代號（Yahoo Finance）
START_DATE = "1998-01-01"
END_DATE = "2025-12-31"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "taifex_raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"開始下載 {TICKER} 從 {START_DATE} 到 {END_DATE} ...")

data = yf.download(TICKER, start=START_DATE, end=END_DATE, progress=False)
if data.empty:
    print("⚠️ 下載失敗或無資料")
else:
    # 儲存為 Parquet（gzip 壓縮）
    parquet_path = os.path.join(OUTPUT_DIR, "tx_1998_2025.parquet")
    data.to_parquet(parquet_path, compression="gzip")
    print(f"✅ 下載完成，資料筆數: {len(data)}")
    print(f"已儲存至: {parquet_path}")
