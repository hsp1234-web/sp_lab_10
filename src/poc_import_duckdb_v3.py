import duckdb
import pandas as pd
from pathlib import Path
import traceback

def run_poc():
    log_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\poc_log_v3.txt")
    
    with open(log_path, 'w', encoding='utf-8') as log:
        try:
            # Paths
            project_root = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1")
            csv_path = project_root / "data" / "taifex_extracted" / "2024_fut.csv"
            db_path = project_root / "data" / "taifex_poc.db"
            
            log.write(f"Reading CSV from: {csv_path}\n")
            
            if not csv_path.exists():
                log.write("Error: CSV file does not exist!\n")
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
            log.write(f"Connected to DuckDB at: {db_path}\n")

            # Load data with fix
            log.write("Loading data into DuckDB raw_data...\n")
            
            # Use index_col=False to prevent column shifting
            # Use na_values=['-'] to handle missing data represented as '-'
            df = pd.read_csv(csv_path, encoding='utf-8', index_col=False, na_values=['-'])
            
            log.write(f"Pandas read successful. Shape: {df.shape}\n")
            log.write(f"Columns: {list(df.columns)}\n")
            
            # Rename columns
            df.rename(columns=col_map, inplace=True)
            log.write(f"Renamed columns: {list(df.columns)}\n")
            
            # Ensure numeric columns are numeric
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Change', 'Volume', 'SettlementPrice', 'OpenInterest', 'BestBid', 'BestAsk', 'HistHigh', 'HistLow']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Clean up ChangePercent (remove %)
            if 'ChangePercent' in df.columns:
                df['ChangePercent'] = df['ChangePercent'].astype(str).str.replace('%', '', regex=False)
                df['ChangePercent'] = pd.to_numeric(df['ChangePercent'], errors='coerce')

            # Register as virtual table
            con.register('df_view', df)
            
            # Create table from view
            log.write("Creating table futures_data...\n")
            con.execute("CREATE OR REPLACE TABLE futures_data AS SELECT * FROM df_view")
            
            # Verify
            count = con.execute("SELECT COUNT(*) FROM futures_data").fetchone()[0]
            log.write(f"Total rows in database: {count}\n")
            
            # Sample data
            sample = con.execute("SELECT * FROM futures_data WHERE Symbol='TX' LIMIT 5").fetchdf()
            log.write("Sample Data (TX):\n")
            log.write(sample.to_string())
            log.write("\n")

            con.close()
            log.write("POC Complete.\n")
            
        except Exception as e:
            log.write(f"Error during POC: {e}\n")
            log.write(traceback.format_exc())

if __name__ == "__main__":
    run_poc()
