import duckdb
import pandas as pd
from pathlib import Path
import traceback
import time
import numpy as np

def run_migration():
    # Use dynamic paths relative to the script's location
    project_root = Path(__file__).parent.parent
    log_path = project_root / "data" / "migration_log_v2.txt"
    
    with open(log_path, 'w', encoding='utf-8') as log:
        try:
            start_time = time.time()
            
            # Paths
            source_dir = project_root / "data" / "taifex_extracted"
            db_path = project_root / "data" / "taifex.db"
            
            log.write(f"Starting migration v2 at {time.ctime()}\n")
            
            # Connect to DuckDB
            con = duckdb.connect(str(db_path))
            
            # Drop existing table if exists
            con.execute("DROP TABLE IF EXISTS futures_data")
            
            # Define Schema explicitly
            schema_sql = """
            CREATE TABLE futures_data (
                Date VARCHAR,
                Symbol VARCHAR,
                Expiry VARCHAR,
                Open DOUBLE,
                High DOUBLE,
                Low DOUBLE,
                Close DOUBLE,
                Change DOUBLE,
                ChangePercent DOUBLE,
                Volume DOUBLE,
                SettlementPrice DOUBLE,
                OpenInterest DOUBLE,
                BestBid DOUBLE,
                BestAsk DOUBLE,
                HistHigh DOUBLE,
                HistLow DOUBLE,
                IsPaused VARCHAR,
                Session VARCHAR,
                SpreadVolume DOUBLE
            )
            """
            con.execute(schema_sql)
            log.write("Created table futures_data with explicit schema.\n")
            
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
            
            target_columns = [
                'Date', 'Symbol', 'Expiry', 'Open', 'High', 'Low', 'Close', 
                'Change', 'ChangePercent', 'Volume', 'SettlementPrice', 'OpenInterest', 
                'BestBid', 'BestAsk', 'HistHigh', 'HistLow', 'IsPaused', 'Session', 'SpreadVolume'
            ]

            csv_files = sorted(list(source_dir.glob('*.csv')))
            total_files = len(csv_files)
            total_rows = 0
            
            for i, csv_file in enumerate(csv_files, 1):
                file_start = time.time()
                log.write(f"[{i}/{total_files}] Processing {csv_file.name}...")
                
                try:
                    # Read CSV
                    df = pd.read_csv(csv_file, encoding='utf-8', index_col=False, na_values=['-'])
                    
                    # Rename columns
                    df.rename(columns=col_map, inplace=True)
                    
                    # Add missing columns
                    for col in target_columns:
                        if col not in df.columns:
                            df[col] = np.nan
                            
                    # Select and order columns
                    df = df[target_columns]
                    
                    # Ensure numeric columns
                    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Change', 'Volume', 'SettlementPrice', 'OpenInterest', 'BestBid', 'BestAsk', 'HistHigh', 'HistLow', 'SpreadVolume']
                    for col in numeric_cols:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Clean up ChangePercent
                    if 'ChangePercent' in df.columns:
                        df['ChangePercent'] = df['ChangePercent'].astype(str).str.replace('%', '', regex=False)
                        df['ChangePercent'] = pd.to_numeric(df['ChangePercent'], errors='coerce')
                        
                    # Ensure string columns
                    string_cols = ['Date', 'Symbol', 'Expiry', 'IsPaused', 'Session']
                    for col in string_cols:
                        df[col] = df[col].astype(str).replace('nan', None)

                    # Register view
                    con.register('df_view', df)
                    
                    # Insert
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
            print("Migration script v2 finished.")
            
        except Exception as e:
            log.write(f"Critical Error: {e}\n")
            log.write(traceback.format_exc())

if __name__ == "__main__":
    run_migration()
