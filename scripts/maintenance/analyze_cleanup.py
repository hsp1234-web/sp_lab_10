import sqlite3
import os

db_path = r"c:\SP_DOC\sp_lab_v10\project_analysis.db"
output_path = r"c:\SP_DOC\sp_lab_v10\cleanup_analysis.txt"

with open(output_path, 'w', encoding='utf-8') as f:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Count decisions
        f.write("--- Decision Distribution ---\n")
        cursor.execute("SELECT keep_decision, COUNT(*) FROM analysis GROUP BY keep_decision")
        decisions = cursor.fetchall()
        for decision, count in decisions:
            f.write(f"{decision}: {count}\n")
            
        # 2. Check coverage
        cursor.execute("SELECT COUNT(*) FROM files")
        total_files_in_db = cursor.fetchone()[0]
        f.write(f"\nTotal files in DB: {total_files_in_db}\n")
        
        # 3. List some files marked for deletion (or not 'Keep')
        f.write("\n--- Sample Files to NOT Keep ---\n")
        # Assuming '保留' means Keep. Checking for anything else.
        cursor.execute("""
            SELECT f.filepath, a.keep_decision, a.reason 
            FROM files f 
            JOIN analysis a ON f.id = a.file_id 
            WHERE a.keep_decision != '保留' 
            LIMIT 10
        """)
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                f.write(f"File: {row[0]}\nDecision: {row[1]}\nReason: {row[2]}\n\n")
        else:
            f.write("No files found with decision other than '保留' (Keep).\n")

        # 4. Verify a few paths exist
        f.write("\n--- Path Verification ---\n")
        cursor.execute("SELECT filepath FROM files LIMIT 5")
        paths = cursor.fetchall()
        for p in paths:
            real_path = os.path.join(r"c:\SP_DOC\sp_lab_v10", p[0])
            exists = os.path.exists(real_path)
            f.write(f"{p[0]}: {'Exists' if exists else 'MISSING'}\n")

        conn.close()

    except Exception as e:
        f.write(f"Error analyzing database: {e}\n")
