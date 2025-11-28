import sqlite3
import pandas as pd

db_path = r"c:\SP_DOC\sp_lab_v10\project_analysis.db"
output_path = r"c:\SP_DOC\sp_lab_v10\organization_analysis.txt"

try:
    conn = sqlite3.connect(db_path)
    
    # 1. Category Distribution
    print("--- Category Distribution ---")
    cat_df = pd.read_sql_query("SELECT category, COUNT(*) as count FROM analysis GROUP BY category ORDER BY count DESC", conn)
    print(cat_df.to_string(index=False))
    
    # 2. Reason Analysis (Sample of non-empty reasons)
    print("\n--- Sample Reasons (Non-Zero) ---")
    reason_df = pd.read_sql_query("SELECT file_id, summary, reason FROM analysis WHERE reason != '0' AND reason IS NOT NULL LIMIT 10", conn)
    print(reason_df.to_string(index=False))

    # 3. Files with Category but No Decision
    print("\n--- Files with Category but No Decision (Potential for Auto-Move) ---")
    undecided_df = pd.read_sql_query("""
        SELECT f.filename, a.category, a.reason 
        FROM files f 
        JOIN analysis a ON f.id = a.file_id 
        WHERE a.keep_decision = '0' AND a.category IS NOT NULL
        LIMIT 20
    """, conn)
    print(undecided_df.to_string(index=False))

    conn.close()

except Exception as e:
    print(f"Error: {e}")
