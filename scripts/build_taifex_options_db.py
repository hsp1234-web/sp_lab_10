# -*- coding: utf-8 -*-
"""
台灣期貨交易所選擇權資料庫建置腳本

此腳本會：
1. 解壓縮所有選擇權 ZIP 檔案
2. 讀取 CSV 檔案並轉換為統一格式
3. 匯入到 DuckDB 資料庫
"""
import duckdb
import pandas as pd
from pathlib import Path
import traceback
import time
import numpy as np
import zipfile
import sys
import io

# 匯入 tqdm 進度條
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("警告: 未安裝 tqdm，將使用簡單進度顯示")
    print("建議執行: pip install tqdm")

# 設定 Windows 終端機編碼
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def run_migration():
    """執行選擇權資料庫遷移"""
    project_root = Path(__file__).parent.parent
    log_path = project_root / "data" / "options_migration_log.txt"
    
    with open(log_path, 'w', encoding='utf-8') as log:
        try:
            start_time = time.time()
            
            # Paths
            zip_dir = project_root / "data" / "taifex_options_raw"
            db_path = project_root / "data" / "taifex_options.db"
            
            log.write(f"Starting options migration at {time.ctime()}\n")
            print("=" * 70)
            print("  台灣期貨交易所選擇權資料庫建置工具")
            print("=" * 70)
            print(f"來源目錄: {zip_dir}")
            print(f"資料庫位置: {db_path}")
            print("=" * 70)
            print()
            
            # Connect to DuckDB (如果檔案被鎖定，先嘗試關閉)
            try:
                con = duckdb.connect(str(db_path))
            except Exception as e:
                if "already open" in str(e) or "locked" in str(e).lower():
                    print("警告: 資料庫檔案可能被其他程序使用")
                    print("請關閉其他可能使用資料庫的程序，或稍後再試")
                    print(f"錯誤: {e}")
                    return
                raise
            
            # Drop existing table if exists
            con.execute("DROP TABLE IF EXISTS options_data")
            
            # Define Schema explicitly
            schema_sql = """
            CREATE TABLE options_data (
                Date VARCHAR,
                Symbol VARCHAR,
                Expiry VARCHAR,
                StrikePrice DOUBLE,
                OptionType VARCHAR,
                Open DOUBLE,
                High DOUBLE,
                Low DOUBLE,
                Close DOUBLE,
                Volume DOUBLE,
                SettlementPrice DOUBLE,
                OpenInterest DOUBLE,
                BestBid DOUBLE,
                BestAsk DOUBLE,
                HistHigh DOUBLE,
                HistLow DOUBLE,
                IsPaused VARCHAR,
                Session VARCHAR,
                Change VARCHAR
            )
            """
            con.execute(schema_sql)
            log.write("Created table options_data with explicit schema.\n")
            print("已建立資料表: options_data")
            
            # Column mapping (中文欄位名稱 -> 英文欄位名稱)
            col_map = {
                '交易日期': 'Date',
                '契約': 'Symbol',
                '到期月份(週別)': 'Expiry',
                '履約價': 'StrikePrice',
                '買賣權': 'OptionType',
                '開盤價': 'Open',
                '最高價': 'High',
                '最低價': 'Low',
                '收盤價': 'Close',
                '成交量': 'Volume',
                '結算價': 'SettlementPrice',
                '未沖銷契約數': 'OpenInterest',
                '最後最佳買價': 'BestBid',
                '最後最佳賣價': 'BestAsk',
                '歷史最高價': 'HistHigh',
                '歷史最低價': 'HistLow',
                '是否因訊息面暫停交易': 'IsPaused',
                '交易時段': 'Session',
                '漲跌': 'Change'
            }
            
            target_columns = [
                'Date', 'Symbol', 'Expiry', 'StrikePrice', 'OptionType',
                'Open', 'High', 'Low', 'Close', 'Volume', 'SettlementPrice',
                'OpenInterest', 'BestBid', 'BestAsk', 'HistHigh', 'HistLow',
                'IsPaused', 'Session', 'Change'
            ]
            
            # 取得所有 ZIP 檔案
            zip_files = sorted(list(zip_dir.glob('*.zip')))
            total_zips = len(zip_files)
            total_rows = 0
            total_csv_files = 0
            
            # 先計算總 CSV 檔案數（用於進度條）
            print("正在掃描 ZIP 檔案內容...")
            total_csv_count = 0
            zip_csv_counts = {}
            for zip_file in zip_files:
                try:
                    with zipfile.ZipFile(zip_file, 'r') as z:
                        csv_count = len([f for f in z.namelist() if f.endswith('.csv')])
                        zip_csv_counts[zip_file] = csv_count
                        total_csv_count += csv_count
                except:
                    zip_csv_counts[zip_file] = 0
            
            print(f"\n找到 {total_zips} 個 ZIP 檔案，共 {total_csv_count} 個 CSV 檔案")
            print("=" * 70)
            print("開始處理...")
            print("=" * 70)
            print()
            
            # 使用進度條
            processed_csv = 0
            overall_start = time.time()
            
            if HAS_TQDM:
                # 設定 tqdm 的參數，確保在 Windows 上正常顯示
                pbar = tqdm(
                    total=total_csv_count,
                    desc="處理進度",
                    unit="檔案",
                    ncols=120,
                    mininterval=0.5,  # 至少每 0.5 秒更新一次
                    maxinterval=1.0,  # 最多每 1 秒更新一次
                    ascii=True,  # 使用 ASCII 字符，避免編碼問題
                    disable=False
                )
            else:
                print(f"開始處理 {total_csv_count} 個 CSV 檔案...")
                print()
            
            for zip_idx, zip_file in enumerate(zip_files, 1):
                zip_start = time.time()
                year = zip_file.stem.split('_')[0]
                
                if HAS_TQDM:
                    # 更新進度條描述
                    pbar.set_description(f"處理 {year} 年")
                else:
                    print(f"\n[ZIP {zip_idx}/{total_zips}] {year} 年 ({zip_file.name})")
                    print("-" * 70)
                
                log.write(f"[ZIP {zip_idx}/{total_zips}] Processing {zip_file.name}...\n")
                
                try:
                    with zipfile.ZipFile(zip_file, 'r') as z:
                        csv_files = [f for f in z.namelist() if f.endswith('.csv')]
                        csv_files.sort()
                        
                        for csv_idx, csv_name in enumerate(csv_files, 1):
                            csv_start = time.time()
                            # 只顯示檔名，不顯示完整路徑
                            csv_display = csv_name.split('/')[-1] if '/' in csv_name else csv_name
                            
                            if HAS_TQDM:
                                # 簡化顯示，避免過度更新
                                short_name = csv_display[:15] + "..." if len(csv_display) > 15 else csv_display
                                pbar.set_postfix_str(f"{year}年: {short_name}")
                            else:
                                elapsed = time.time() - overall_start
                                avg_time = elapsed / max(processed_csv, 1)
                                remaining = (total_csv_count - processed_csv) * avg_time
                                progress_pct = (processed_csv / total_csv_count * 100) if total_csv_count > 0 else 0
                                print(f"  [{csv_idx}/{len(csv_files)}] {csv_display}... "
                                      f"(整體: {processed_csv}/{total_csv_count}, {progress_pct:.1f}%, "
                                      f"預估剩餘: {remaining/60:.1f}分鐘)", end=" ", flush=True)
                            
                            try:
                                # 讀取 CSV (使用 big5 編碼)
                                content = z.read(csv_name)
                                text = content.decode('big5', errors='replace')
                                
                                # 使用 StringIO 讀取
                                from io import StringIO
                                df = pd.read_csv(StringIO(text), na_values=['-'], keep_default_na=False)
                                
                                # 重新命名欄位
                                df.rename(columns=col_map, inplace=True)
                                
                                # 確保所有目標欄位都存在
                                for col in target_columns:
                                    if col not in df.columns:
                                        df[col] = np.nan
                                
                                # 選擇並排序欄位
                                df = df[target_columns]
                                
                                # 處理數值欄位
                                numeric_cols = [
                                    'StrikePrice', 'Open', 'High', 'Low', 'Close', 'Volume',
                                    'SettlementPrice', 'OpenInterest', 'BestBid', 'BestAsk',
                                    'HistHigh', 'HistLow'
                                ]
                                for col in numeric_cols:
                                    if col in df.columns:
                                        # 處理 '-' 和空值
                                        df[col] = df[col].replace(['-', ''], np.nan)
                                        df[col] = pd.to_numeric(df[col], errors='coerce')
                                
                                # 處理字串欄位
                                string_cols = ['Date', 'Symbol', 'Expiry', 'OptionType', 'IsPaused', 'Session', 'Change']
                                for col in string_cols:
                                    if col in df.columns:
                                        df[col] = df[col].astype(str).replace(['nan', 'None'], None)
                                
                                # 清理空白
                                for col in df.columns:
                                    if df[col].dtype == 'object':
                                        df[col] = df[col].str.strip() if df[col].notna().any() else df[col]
                                
                                # 過濾掉完全空白的行
                                df = df.dropna(how='all')
                                
                                if len(df) > 0:
                                    # Register view
                                    con.register('df_view', df)
                                    
                                    # Insert
                                    con.execute("INSERT INTO options_data SELECT * FROM df_view")
                                    
                                    rows = len(df)
                                    total_rows += rows
                                    total_csv_files += 1
                                    processed_csv += 1
                                    elapsed = time.time() - csv_start
                                    
                                    if HAS_TQDM:
                                        # 更新進度條，顯示關鍵資訊
                                        pbar.update(1)
                                        # 簡化 postfix，避免編碼問題
                                        pbar.set_postfix_str(f"{year}年 | {rows:,}筆 | {elapsed:.1f}s")
                                    else:
                                        print(f"✓ ({rows:,} 筆, {elapsed:.1f}s)")
                                    
                                    log.write(f"  [{csv_idx}/{len(csv_files)}] {csv_name}: {rows} rows in {elapsed:.2f}s\n")
                                    
                                    con.unregister('df_view')
                                else:
                                    processed_csv += 1
                                    if HAS_TQDM:
                                        pbar.update(1)
                                        pbar.set_postfix_str(f"{year}年 | 跳過(無資料)")
                                    else:
                                        print("跳過 (無資料)")
                                
                            except Exception as e:
                                processed_csv += 1
                                if HAS_TQDM:
                                    pbar.update(1)
                                    pbar.set_postfix_str(f"{year}年 | 錯誤: {str(e)[:30]}")
                                else:
                                    print(f"錯誤: {e}")
                                log.write(f"  Error processing {csv_name}: {e}\n")
                                log.write(traceback.format_exc())
                        
                        zip_elapsed = time.time() - zip_start
                        if HAS_TQDM:
                            # 在進度條中顯示年份完成資訊
                            pbar.write(f"  {year} 年完成 ({len(csv_files)} 個 CSV, {zip_elapsed:.1f}s)")
                        else:
                            print(f"\n  {year} 年完成 (總計 {len(csv_files)} 個 CSV, {zip_elapsed:.1f}s)")
                            print()
                
                except Exception as e:
                    if not HAS_TQDM:
                        print(f"✗ ZIP 檔案處理失敗: {e}")
                    log.write(f"Error processing {zip_file.name}: {e}\n")
                    log.write(traceback.format_exc())
            
            if HAS_TQDM:
                pbar.close()
            
            # Final verification
            count = con.execute("SELECT COUNT(*) FROM options_data").fetchone()[0]
            year_range = con.execute("SELECT MIN(Date), MAX(Date) FROM options_data").fetchone()
            
            log.write(f"\nMigration complete.\n")
            log.write(f"Total ZIP files processed: {total_zips}\n")
            log.write(f"Total CSV files processed: {total_csv_files}\n")
            log.write(f"Total rows processed: {total_rows}\n")
            log.write(f"Total rows in DB: {count}\n")
            log.write(f"Date range: {year_range[0]} to {year_range[1]}\n")
            log.write(f"Total time: {time.time() - start_time:.2f}s\n")
            
            con.close()
            
            print("=" * 70)
            print("資料庫建置完成！")
            print(f"  處理 ZIP 檔案: {total_zips} 個")
            print(f"  處理 CSV 檔案: {total_csv_files} 個")
            print(f"  總資料筆數: {count:,} 筆")
            if year_range[0] and year_range[1]:
                print(f"  日期範圍: {year_range[0]} 至 {year_range[1]}")
            print(f"  資料庫位置: {db_path}")
            print("=" * 70)
            print(f"\n詳細日誌: {log_path}")
            
        except Exception as e:
            log.write(f"Critical Error: {e}\n")
            log.write(traceback.format_exc())
            print(f"嚴重錯誤: {e}")
            print(f"詳細日誌: {log_path}")

if __name__ == "__main__":
    run_migration()

