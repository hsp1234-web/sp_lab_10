import duckdb
import os

db_path = "records/backtest_v2.db"
output_file = "v2_verification.txt"

try:
    if not os.path.exists(db_path):
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Database not found at {db_path}")
        exit(0)

    conn = duckdb.connect(db_path)
    
    # Get job info
    jobs = conn.execute("SELECT * FROM jobs").fetchall()
    
    # Get results count
    count = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    
    # Get sample results
    samples = conn.execute("SELECT backtest_id, metrics FROM results LIMIT 3").fetchall()
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Database found: {db_path}\n")
        f.write("-" * 20 + "\n")
        f.write(f"Jobs: {jobs}\n")
        f.write(f"Total Results: {count}\n")
        f.write("-" * 20 + "\n")
        f.write("Sample Results:\n")
        for s in samples:
            f.write(f"{s}\n")
            
    conn.close()
    print(f"Verification written to {output_file}")

except Exception as e:
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Error: {e}")
