#!/usr/bin/env python3
"""
檢查數據庫內容
"""

import duckdb
import pandas as pd

def check_database():
    # 檢查數據庫內容
    con = duckdb.connect('data/taifex.db')

    # 查看表結構
    print('=== 表結構 ===')
    tables = con.execute('SHOW TABLES').fetchall()
    print('Tables:', tables)

    # 查看 futures_data 表結構
    print('\n=== futures_data 表結構 ===')
    schema = con.execute('DESCRIBE futures_data').fetchall()
    for col in schema:
        print(col)

    # 查看數據樣本
    print('\n=== 數據樣本 (前5行) ===')
    sample = con.execute('SELECT * FROM futures_data LIMIT 5').fetchdf()
    print(sample)

    # 查看符號統計
    print('\n=== 符號統計 ===')
    symbols = con.execute('SELECT Symbol, COUNT(*) as count FROM futures_data GROUP BY Symbol ORDER BY count DESC LIMIT 10').fetchdf()
    print(symbols)

    # 查看日期範圍
    print('\n=== 日期範圍 ===')
    dates = con.execute('SELECT MIN(Date) as min_date, MAX(Date) as max_date FROM futures_data').fetchall()
    print('Date range:', dates)

    con.close()

if __name__ == "__main__":
    check_database()

