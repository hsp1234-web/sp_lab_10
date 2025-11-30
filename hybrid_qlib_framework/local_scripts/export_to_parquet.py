import duckdb
import pandas as pd
import os
from datetime import datetime

# Configuration
DB_PATH = r'data/taifex.db'
OUTPUT_DIR = r'hybrid_qlib_framework/data_export'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'taifex_daily.parquet')

def export_data():
    print(f"Connecting to database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return

    con = duckdb.connect(DB_PATH)
    
    # Query to fetch data and rename columns for Qlib compatibility
    # Qlib expects: symbol (instrument), date, open, high, low, close, volume
    query = """
    SELECT 
        Symbol as instrument,
        Date as date,
        Open as open,
        High as high,
        Low as low,
        Close as close,
        Volume as volume
    FROM futures_data
    WHERE Symbol = 'TX'  -- Exporting TX (Taifex Futures) for now as the minimal model
    ORDER BY Date
    """
    
    # Optimized for Low RAM: Use DuckDB's native COPY command
    # This streams data directly from DB to Parquet file without loading everything into Python/Pandas memory.
    export_query = f"""
    COPY (
        {query}
    ) TO '{OUTPUT_FILE}' (FORMAT PARQUET);
    """
    
    print("Executing native DuckDB export (Low RAM mode)...")
    try:
        con.execute(export_query)
        print(f"Export successful to {OUTPUT_FILE}")
        
        # Verification (Optional: just check file exists and size)
        if os.path.exists(OUTPUT_FILE):
            size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
            print(f"File created. Size: {size_mb:.2f} MB")
            
            # Quick peek using DuckDB (efficiently)
            print("\n--- Data Verification (First 5 rows) ---")
            print(con.execute(f"SELECT * FROM '{OUTPUT_FILE}' LIMIT 5").fetchdf())
        
    except Exception as e:
        print(f"Error during export: {e}")
    finally:
        con.close()

if __name__ == "__main__":
    export_data()
