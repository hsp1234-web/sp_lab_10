# -*- coding: utf-8 -*-
"""檢查選擇權資料庫狀態"""
import duckdb
from pathlib import Path
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

db_path = Path('data/taifex_options.db')

if not db_path.exists():
    print(f"資料庫檔案不存在: {db_path}")
    print("請先執行: python scripts/build_taifex_options_db.py")
    sys.exit(1)

try:
    con = duckdb.connect(str(db_path))
    count = con.execute('SELECT COUNT(*) FROM options_data').fetchone()[0]
    year_range = con.execute('SELECT MIN(Date), MAX(Date) FROM options_data').fetchone()
    
    print(f"資料庫狀態:")
    print(f"  總資料筆數: {count:,} 筆")
    if year_range[0] and year_range[1]:
        print(f"  日期範圍: {year_range[0]} 至 {year_range[1]}")
    
    # 檢查各年份資料量
    year_counts = con.execute("""
        SELECT SUBSTR(Date, 1, 4) as Year, COUNT(*) as Count
        FROM options_data
        GROUP BY Year
        ORDER BY Year
    """).fetchdf()
    
    print(f"\n各年份資料量:")
    print(year_counts.to_string(index=False))
    
    con.close()
except Exception as e:
    print(f"錯誤: {e}")
    print("資料表可能不存在，請執行建置腳本")

