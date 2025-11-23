import duckdb
import pandas as pd
from pathlib import Path

def verify_migration():
    db_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\taifex.db")
    output_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\full_verification.txt")
    
    try:
        con = duckdb.connect(str(db_path))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== Full Migration Verification ===\n\n")
            
            # Total Rows
            count = con.execute("SELECT COUNT(*) FROM futures_data").fetchone()[0]
            f.write(f"Total Rows: {count}\n\n")
            
            # Rows by Year (extract year from Date string 'YYYY/MM/DD')
            f.write("=== Rows by Year ===\n")
            # Date format is YYYY/MM/DD. We can use substring.
            # Try to cast to date first to ensure validity, or just substring.
            # Let's use substring for safety: substr(Date, 1, 4)
            year_counts = con.execute("""
                SELECT substr(Date, 1, 4) as Year, COUNT(*) as Count 
                FROM futures_data 
                GROUP BY Year 
                ORDER BY Year
            """).fetchdf()
            f.write(year_counts.to_string())
            f.write("\n\n")
            
            # Sample 1998
            f.write("=== Sample 1998 Data ===\n")
            sample_1998 = con.execute("SELECT * FROM futures_data WHERE Date LIKE '1998%' LIMIT 5").fetchdf()
            f.write(sample_1998.to_string())
            f.write("\n\n")
            
            # Sample 2024
            f.write("=== Sample 2024 Data ===\n")
            sample_2024 = con.execute("SELECT * FROM futures_data WHERE Date LIKE '2024%' LIMIT 5").fetchdf()
            f.write(sample_2024.to_string())
            f.write("\n\n")
            
        print(f"Verification output written to {output_path}")
        con.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_migration()
