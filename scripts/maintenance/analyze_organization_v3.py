import sqlite3
import pandas as pd
import sys

db_path = r"c:\SP_DOC\sp_lab_v10\project_analysis.db"
output_path = r"c:\SP_DOC\sp_lab_v10\organization_analysis_v3.txt"

with open(output_path, 'w', encoding='utf-8') as f:
    try:
        conn = sqlite3.connect(db_path)
        
        f.write("--- Category Distribution ---\n")
        cat_df = pd.read_sql_query("SELECT category, COUNT(*) as count FROM analysis GROUP BY category ORDER BY count DESC", conn)
        f.write(cat_df.to_string(index=False))
        
        f.write("\n\n--- Sample Reasons (Non-Zero) ---\n")
        reason_df = pd.read_sql_query("SELECT file_id, summary, reason FROM analysis WHERE reason != '0' AND reason IS NOT NULL LIMIT 5", conn)
        f.write(reason_df.to_string(index=False))

        f.write("\n\n--- Files with Category but No Decision ---\n")
        undecided_df = pd.read_sql_query("""
            SELECT f.filename, a.category 
            FROM files f 
            JOIN analysis a ON f.id = a.file_id 
            WHERE a.keep_decision = '0' AND a.category IS NOT NULL
            LIMIT 10
        """, conn)
        f.write(undecided_df.to_string(index=False))

        conn.close()

    except Exception as e:
        f.write(f"Error: {e}\n")
