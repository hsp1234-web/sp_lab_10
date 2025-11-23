import duckdb
import pandas as pd
from pathlib import Path

def run_poc():
    # Paths
    project_root = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1")
    csv_path = project_root / "data" / "taifex_extracted" / "2024_fut.csv"
    db_path = project_root / "data" / "taifex_poc.db"
    
    print(f"Reading CSV from: {csv_path}")
    
    # Column mapping
    # 交易日期,契約,到期月份(週別),開盤價,最高價,最低價,收盤價,漲跌價,漲跌%,成交量,結算價,未沖銷契約數,...
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

    try:
        # Connect to DuckDB (creates file if not exists)
        con = duckdb.connect(str(db_path))
        print(f"Connected to DuckDB at: {db_path}")

        # Read CSV using Pandas first to handle column renaming easily
        # DuckDB's read_csv is faster but renaming 19 columns with Chinese characters in SQL can be tricky 
        # and might require creating a view or complex CREATE TABLE statement.
        # For POC with one file, Pandas is fine. For full load, we might want to optimize.
        # Actually, let's try to use DuckDB's read_csv_auto for performance, 
        # but we need to handle the Chinese headers.
        
        # Strategy: Read header first to verify, then load.
        # Or just load into a temp table and rename.
        
        print("Loading data into DuckDB...")
        # We use read_csv_auto. We need to specify that the file has a header.
        con.execute(f"CREATE OR REPLACE TABLE raw_data AS SELECT * FROM read_csv_auto('{str(csv_path)}', header=True)")
        
        # Get current column names
        current_cols = [col[0] for col in con.execute("DESCRIBE raw_data").fetchall()]
        print("Original columns:", current_cols)
        
        # Rename columns
        # Note: DuckDB columns might be quoted if they contain special chars.
        # We will create a new clean table.
        
        select_parts = []
        for col in current_cols:
            # Strip whitespace from column name just in case
            clean_col = col.strip()
            if clean_col in col_map:
                select_parts.append(f'"{col}" AS {col_map[clean_col]}')
            else:
                # Keep original if not in map (or drop? better keep for now)
                select_parts.append(f'"{col}"')
        
        select_sql = ", ".join(select_parts)
        
        print("Creating clean table 'futures_data'...")
        con.execute(f"CREATE OR REPLACE TABLE futures_data AS SELECT {select_sql} FROM raw_data")
        
        # Clean up raw table
        con.execute("DROP TABLE raw_data")
        
        # Verify data
        print("\nVerifying data (Top 5 rows for Symbol='TX'):")
        result = con.execute("SELECT * FROM futures_data WHERE Symbol='TX' LIMIT 5").fetchdf()
        print(result)
        
        # Verify row count
        count = con.execute("SELECT COUNT(*) FROM futures_data").fetchone()[0]
        print(f"\nTotal rows in database: {count}")
        
        # Check data types
        print("\nColumn Types:")
        types = con.execute("DESCRIBE futures_data").fetchdf()
        print(types[['column_name', 'column_type']])

        con.close()
        print("\nPOC Complete. Database created successfully.")
        
    except Exception as e:
        print(f"Error during POC: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_poc()
