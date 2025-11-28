#!/usr/bin/env python3
"""
檢查FinMind資料庫內容
"""

import duckdb
import pandas as pd

def check_finmind_db():
    """檢查FinMind資料庫"""
    try:
        conn = duckdb.connect('data/finmind.db')

        # 檢查資料筆數
        df_count = conn.execute('SELECT COUNT(*) as count FROM ohlcv').fetchdf()
        print(f'FinMind資料庫總筆數: {df_count.iloc[0,0]}')

        # 檢查資料範圍
        df_range = conn.execute('SELECT MIN(Time) as start_date, MAX(Time) as end_date FROM ohlcv').fetchdf()
        print(f'資料日期範圍: {df_range.iloc[0,0]} ~ {df_range.iloc[0,1]}')

        # 檢查最近5筆資料
        df_recent = conn.execute('SELECT * FROM ohlcv ORDER BY Time DESC LIMIT 5').fetchdf()
        print('\n最近5筆資料:')
        print(df_recent)

        # 檢查欄位結構
        df_schema = conn.execute("DESCRIBE ohlcv").fetchdf()
        print('\n資料表結構:')
        print(df_schema)

        conn.close()

        return True

    except Exception as e:
        print(f'檢查失敗: {e}')
        return False

if __name__ == "__main__":
    print("檢查FinMind資料庫...")
    success = check_finmind_db()

    if success:
        print("\n結論: FinMind資料庫建置成功!")
    else:
        print("\n結論: FinMind資料庫建置失敗")
