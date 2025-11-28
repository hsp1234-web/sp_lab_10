import sqlite3
import sys

db_path = r"c:\SP_DOC\sp_lab_v10\project_analysis.db"
output_path = r"c:\SP_DOC\sp_lab_v10\inspect_output.txt"

with open(output_path, 'w', encoding='utf-8') as f:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        f.write(f"Database: {db_path}\n")
        f.write(f"Found {len(tables)} tables.\n")
        
        for table_name in tables:
            table = table_name[0]
            f.write(f"\n--- Table: {table} ---\n")
            
            # Get schema
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            f.write(f"Columns: {col_names}\n")
            
            # Get first 5 rows
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                rows = cursor.fetchall()
                if rows:
                    f.write("Sample Data:\n")
                    for row in rows:
                        f.write(f"{row}\n")
                else:
                    f.write("Table is empty.\n")
            except Exception as e:
                f.write(f"Error reading data from {table}: {e}\n")

        conn.close()

    except Exception as e:
        f.write(f"Error connecting to database: {e}\n")
