import duckdb
import pandas as pd
from pathlib import Path

def verify_poc():
    db_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\taifex_poc.db")
    output_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\poc_verification.txt")
    
    try:
        con = duckdb.connect(str(db_path))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== Table Info ===\n")
            tables = con.execute("SHOW TABLES").fetchall()
            f.write(f"Tables: {tables}\n\n")
            
            f.write("=== Column Info ===\n")
            cols = con.execute("DESCRIBE futures_data").fetchdf()
            f.write(cols.to_string())
            f.write("\n\n")
            
            f.write("=== Sample Data (TX) ===\n")
            sample = con.execute("SELECT * FROM futures_data WHERE Symbol='TX' LIMIT 5").fetchdf()
            f.write(sample.to_string())
            f.write("\n\n")
            
            f.write("=== Row Count ===\n")
            count = con.execute("SELECT COUNT(*) FROM futures_data").fetchone()[0]
            f.write(f"Total rows: {count}\n")
            
        print(f"Verification output written to {output_path}")
        con.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_poc()
