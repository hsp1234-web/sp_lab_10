"""檢查 Parquet 檔案的欄位結構 - 輸出到檔案版本"""
import pandas as pd
import os

file_path = 'lo2cin4bt-main/records/backtester/20251124_SPY_SPY_Demo_Close_54824e94_.parquet'
output_file = 'output/column_check_result.txt'

# 確保 output 目錄存在
os.makedirs('output', exist_ok=True)

try:
    df = pd.read_parquet(file_path)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("📋 檔案結構檢查\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"總記錄數: {len(df):,} 筆\n\n")
        
        f.write("所有欄位名稱:\n")
        for i, col in enumerate(df.columns, 1):
            f.write(f"  {i}. {col}\n")
        
        f.write(f"\n資料型態:\n")
        f.write(str(df.dtypes) + "\n")
        
        f.write(f"\n前 5 筆資料:\n")
        f.write(df.head().to_string() + "\n")
        
        f.write(f"\n{'=' * 80}\n")
        f.write("✅ 檢查完成！結果已儲存至 output/column_check_result.txt\n")
    
    print(f"✅ 結果已儲存至: {output_file}")
    
except Exception as e:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"❌ 錯誤: {e}\n")
        import traceback
        f.write(traceback.format_exc())
    print(f"❌ 發生錯誤，詳情請查看: {output_file}")
