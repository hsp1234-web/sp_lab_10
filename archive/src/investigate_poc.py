import duckdb
import pandas as pd
from pathlib import Path

def investigate():
    db_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\taifex_poc.db")
    output_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\poc_investigation.txt")
    
    con = duckdb.connect(str(db_path))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Check distinct symbols
        f.write("=== Distinct Symbols (First 20) ===\n")
        syms = con.execute("SELECT DISTINCT Symbol FROM futures_data LIMIT 20").fetchdf()
        f.write(syms.to_string())
        f.write("\n\n")
        
        # Check distinct Session values
        f.write("=== Distinct Session Values ===\n")
        sess = con.execute("SELECT DISTINCT Session FROM futures_data").fetchdf()
        f.write(sess.to_string())
        f.write("\n\n")
        
        # Check a few rows of raw data
        f.write("=== Raw Data Sample (First 5 rows) ===\n")
        raw = con.execute("SELECT * FROM futures_data LIMIT 5").fetchdf()
        f.write(raw.to_string())
        f.write("\n\n")
        
    con.close()
    print(f"Investigation output written to {output_path}")

if __name__ == "__main__":
    investigate()
