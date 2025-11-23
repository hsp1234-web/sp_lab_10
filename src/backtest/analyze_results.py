"""分析回測結果的簡單腳本"""
import pandas as pd
import pyarrow.parquet as pq
import json
import glob
import os

# 自動找到最新的 Parquet 檔案
parquet_dir = 'lo2cin4bt-main/records/backtester'
parquet_files = glob.glob(os.path.join(parquet_dir, '*.parquet'))
if not parquet_files:
    print("❌ 找不到任何回測結果檔案！")
    exit(1)

# 取得最新的檔案
parquet_file = max(parquet_files, key=os.path.getmtime)
print(f"📂 讀取檔案: {os.path.basename(parquet_file)}\n")

table = pq.read_table(parquet_file)
df = table.to_pandas()

print("=" * 80)
print("📊 回測結果分析報告")
print("=" * 80)

# 基本統計
print(f"\n【基本資訊】")
print(f"總交易筆數: {len(df)}")
print(f"資料欄位: {', '.join(df.columns)}")
print(f"時間範圍: {df['Time'].min()} 至 {df['Time'].max()}")

# 交易統計
if 'Trade_action' in df.columns:
    trades = df[df['Trade_action'] == 1]
    print(f"\n【交易統計】")
    print(f"實際交易次數: {len(trades)}")
    
    if 'Position' in df.columns:
        buys = df[(df['Trade_action'] == 1) & (df['Position'] == 1)]
        sells = df[(df['Trade_action'] == 1) & (df['Position'] == -1)]
        print(f"買入次數: {len(buys)}")
        print(f"賣出次數: {len(sells)}")

# 績效統計
if 'Total_equity' in df.columns:
    initial_equity = df['Total_equity'].iloc[0]
    final_equity = df['Total_equity'].iloc[-1]
    total_return = ((final_equity - initial_equity) / initial_equity) * 100
    
    print(f"\n【績效表現】")
    print(f"初始資金: ${initial_equity:,.2f}")
    print(f"最終資金: ${final_equity:,.2f}")
    print(f"總報酬率: {total_return:.2f}%")
    print(f"最大權益: ${df['Total_equity'].max():,.2f}")
    print(f"最小權益: ${df['Total_equity'].min():,.2f}")

# 顯示前 10 筆交易
print(f"\n【前 10 筆記錄】")
print(df.head(10).to_string())

# 讀取元數據
print(f"\n{'=' * 80}")
print("📋 回測配置 (Metadata)")
print("=" * 80)
meta = table.schema.metadata
if meta:
    for k, v in meta.items():
        key = k.decode('utf-8')
        value = v.decode('utf-8')
        
        # 如果是 JSON，嘗試美化輸出
        if key == 'batch_metadata':
            try:
                batch_data = json.loads(value)
                print(f"\n{key}:")
                for item in batch_data:
                    print(f"  - Backtest ID: {item.get('Backtest_id', 'N/A')}")
                    print(f"    策略: {item.get('Strategy', 'N/A')}")
                    print(f"    頻率: {item.get('Frequency', 'N/A')}")
                    print(f"    標的: {item.get('Asset', 'N/A')}")
                    print(f"    手續費: {item.get('Transaction_cost', 'N/A')}")
            except:
                print(f"{key}: {value[:200]}...")
        else:
            print(f"{key}: {value}")

print(f"\n{'=' * 80}")
print("✅ 分析完成")
print("=" * 80)
