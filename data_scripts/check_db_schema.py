import sqlite3

# 檢查數據庫結構
conn = sqlite3.connect('data/taifex.db')

# 查看所有表
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("數據庫中的表:")
for table in tables:
    print(f"  {table[0]}")

# 查看futures表的結構
cursor.execute("PRAGMA table_info(futures)")
columns = cursor.fetchall()
print("\nfutures表欄位:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# 查看最近的數據
cursor.execute("SELECT * FROM futures ORDER BY date DESC LIMIT 5")
recent_data = cursor.fetchall()
print("\n最近5筆數據:")
for row in recent_data:
    print(f"  {row}")

conn.close()

