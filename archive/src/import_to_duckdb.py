import duckdb
import pandas as pd
from pathlib import Path
import traceback
import time

def run_migration():
    log_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\migration_log.txt")
    
    with open(log_path, 'w', encoding='utf-8') as log:
        try:
            start_time = time.time()
            
            # Paths
            project_root = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1")
            source_dir = project_root / "data" / "taifex_extracted"
            db_path = project_root / "data" / "taifex.db"
            
            log.write(f"Starting migration at {time.ctime()}\n")
            log.write(f"Source directory: {source_dir}\n")
            log.write(f"Target database: {db_path}\n")
            
            if not source_dir.exists():
                log.write("Error: Source directory does not exist!\n")
                return

            # Column mapping
            col_map = {
                '交易日期': 'Date',
                '契約': 'Symbol',
                '到期月份(週別)': 'Expiry',
                '開盤價': 'Open',
                '最高價': 'High',
                '最低價': 'Low',
                '收盤價': 'Close',
                '漲跌價': 'Change',
                '漲跌%': 'ChangePercent',
                '成交量': 'Volume',
                '結算價': 'SettlementPrice',
                '未沖銷契約數': 'OpenInterest',
                '最後最佳買價': 'BestBid',
                '最後最佳賣價': 'BestAsk',
                '歷史最高價': 'HistHigh',
                '歷史最低價': 'HistLow',
                '是否因訊息面暫停交易': 'IsPaused',
                '交易時段': 'Session',
                '價差對單式委託成交量': 'SpreadVolume'
            }

            # Connect to DuckDB
            con = duckdb.connect(str(db_path))
            log.write(f"Connected to DuckDB.\n")
            
            # Create table schema first (optional, but good practice)
            # We will let the first file define the schema and then append
            
            csv_files = sorted(list(source_dir.glob('*.csv')))
            total_files = len(csv_files)
            log.write(f"Found {total_files} CSV files.\n")
            
            table_created = False
            total_rows = 0
            
            for i, csv_file in enumerate(csv_files, 1):
                file_start = time.time()
                log.write(f"[{i}/{total_files}] Processing {csv_file.name}...")
                
                try:
                    # Read CSV
                    df = pd.read_csv(csv_file, encoding='utf-8', index_col=False, na_values=['-'])
                    
                    # Rename columns
                    df.rename(columns=col_map, inplace=True)
                    
                    # Ensure numeric columns
                    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Change', 'Volume', 'SettlementPrice', 'OpenInterest', 'BestBid', 'BestAsk', 'HistHigh', 'HistLow']
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Clean up ChangePercent
                    if 'ChangePercent' in df.columns:
                        df['ChangePercent'] = df['ChangePercent'].astype(str).str.replace('%', '', regex=False)
                        df['ChangePercent'] = pd.to_numeric(df['ChangePercent'], errors='coerce')

                    # Register view
                    con.register('df_view', df)
                    
                    if not table_created:
                        con.execute("CREATE OR REPLACE TABLE futures_data AS SELECT * FROM df_view")
                        table_created = True
                    else:
                        con.execute("INSERT INTO futures_data SELECT * FROM df_view")
                    
                    rows = len(df)
                    total_rows += rows
                    elapsed = time.time() - file_start
                    log.write(f" Done ({rows} rows) in {elapsed:.2f}s\n")
                    
                    con.unregister('df_view')
                    
                except Exception as e:
                    log.write(f"\nError processing {csv_file.name}: {e}\n")
                    log.write(traceback.format_exc())
            
            # Final verification
            count = con.execute("SELECT COUNT(*) FROM futures_data").fetchone()[0]
            log.write(f"\nMigration complete.\n")
            log.write(f"Total rows processed: {total_rows}\n")
            log.write(f"Total rows in DB: {count}\n")
            log.write(f"Total time: {time.time() - start_time:.2f}s\n")
            
            con.close()
            print("Migration script finished. Check log for details.")
            
        except Exception as e:
            log.write(f"Critical Error: {e}\n")
            log.write(traceback.format_exc())

if __name__ == "__main__":
    run_migration()
