import sqlite3
import pandas as pd

print("=== 檢查台指期與選擇權數據庫結構 ===")

# 檢查台指期數據
print("\n--- 台指期數據 ---")
conn_fut = sqlite3.connect('data/taifex.db')
cursor_fut = conn_fut.cursor()

# 查看所有表
cursor_fut.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables_fut = cursor_fut.fetchall()
print("台指期數據庫中的表:", [t[0] for t in tables_fut])

# 檢查futures表結構
try:
    cursor_fut.execute("PRAGMA table_info(futures)")
    columns_fut = cursor_fut.fetchall()
    print("futures表欄位:")
    for col in columns_fut[:10]:
        print(f"  {col[1]} ({col[2]})")
except:
    print("futures表不存在，嘗試其他表名")

# 查看數據樣本
try:
    query = "SELECT * FROM futures ORDER BY date DESC LIMIT 3"
    df_fut = pd.read_sql(query, conn_fut)
    print("\n台指期數據樣本:")
    print(df_fut.head())
except Exception as e:
    print(f"台指期數據查詢失敗: {e}")

conn_fut.close()

# 檢查選擇權數據
print("\n--- 台指選擇權數據 ---")
conn_opt = sqlite3.connect('data/taifex_options.db')
cursor_opt = conn_opt.cursor()

# 查看所有表
cursor_opt.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables_opt = cursor_opt.fetchall()
print("選擇權數據庫中的表:", [t[0] for t in tables_opt])

# 檢查options表結構
try:
    cursor_opt.execute("PRAGMA table_info(options)")
    columns_opt = cursor_opt.fetchall()
    print("options表欄位:")
    for col in columns_opt[:15]:
        print(f"  {col[1]} ({col[2]})")
except Exception as e:
    print(f"options表結構查詢失敗: {e}")

# 查看數據樣本
try:
    query_opt = "SELECT date, contract, strike, call_put, close, volume FROM options ORDER BY date DESC LIMIT 5"
    df_opt = pd.read_sql(query_opt, conn_opt)
    print("\n台指選擇權數據樣本:")
    print(df_opt.head())
except Exception as e:
    print(f"選擇權數據查詢失敗: {e}")

conn_opt.close()

print("\n=== 數據檢查完成 ===")