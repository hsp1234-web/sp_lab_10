import sqlite3
import pandas as pd
import sys

# Set encoding to utf-8 for stdout
sys.stdout.reconfigure(encoding='utf-8')

db_path = r"c:\SP_DOC\sp_lab_v10\project_analysis.db"

try:
    conn = sqlite3.connect(db_path)
    
    print("--- Category Distribution ---")
    cat_df = pd.read_sql_query("SELECT category, COUNT(*) as count FROM analysis GROUP BY category ORDER BY count DESC", conn)
    print(cat_df.to_string(index=False))
    
    print("\n--- Sample Reasons (Non-Zero) ---")
    reason_df = pd.read_sql_query("SELECT file_id, summary, reason FROM analysis WHERE reason != '0' AND reason IS NOT NULL LIMIT 5", conn)
    print(reason_df.to_string(index=False))

    print("\n--- Files with Category but No Decision ---")
    undecided_df = pd.read_sql_query("""
        SELECT f.filename, a.category 
        FROM files f 
        JOIN analysis a ON f.id = a.file_id 
        WHERE a.keep_decision = '0' AND a.category IS NOT NULL
        LIMIT 10
    """, conn)
    print(undecided_df.to_string(index=False))

    conn.close()

except Exception as e:
    print(f"Error: {e}")
