#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 taifex.db 數據品質的腳本
"""
import sys
import os
import io
import duckdb

# 設置 UTF-8 輸出
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', line_buffering=True)

def main():
    print("🔍 檢查 taifex.db 數據品質...")

    try:
        con = duckdb.connect('data/taifex.db')

        # 檢查異常低價數據
        print("\n=== 異常低價數據 (Close < 100) ===")
        abnormal_low = con.execute("""
            SELECT Date, Close, High, Low, Volume
            FROM futures_data
            WHERE Symbol = 'TX' AND Close < 100 AND Close > 0
            ORDER BY Date
            LIMIT 20
        """).fetchdf()
        print(f"異常低價記錄數: {len(abnormal_low)}")
        print(abnormal_low)

        # 檢查正常高價數據
        print("\n=== 正常高價數據 (Close > 10000) ===")
        normal_high = con.execute("""
            SELECT Date, Close, High, Low, Volume
            FROM futures_data
            WHERE Symbol = 'TX' AND Close > 10000
            ORDER BY Date DESC
            LIMIT 10
        """).fetchdf()
        print(f"正常高價記錄數: {len(normal_high)}")
        print(normal_high)

        # 檢查 2018 年後的數據品質
        print("\n=== 2018 年後數據品質檢查 ===")
        recent_data = con.execute("""
            SELECT
                COUNT(*) as total_2018,
                COUNT(CASE WHEN Close IS NULL OR Close <= 0 THEN 1 END) as bad_close_2018,
                COUNT(CASE WHEN Close < 100 AND Close > 0 THEN 1 END) as abnormal_low_2018,
                MIN(Close) as min_close_2018,
                MAX(Close) as max_close_2018,
                AVG(Close) as avg_close_2018
            FROM futures_data
            WHERE Symbol = 'TX'
            AND strptime(Date, '%Y/%m/%d') >= strptime('2018-01-01', '%Y-%m-%d')
            AND Close IS NOT NULL
        """).fetchdf()
        print("2018年後數據統計:")
        print(recent_data)

        # 檢查 2018 年後的異常數據
        abnormal_2018 = con.execute("""
            SELECT Date, Close, High, Low, Volume
            FROM futures_data
            WHERE Symbol = 'TX'
            AND strptime(Date, '%Y/%m/%d') >= strptime('2018-01-01', '%Y-%m-%d')
            AND Close < 100 AND Close > 0
            ORDER BY Date
            LIMIT 10
        """).fetchdf()
        print(f"\n2018年後異常數據數: {len(abnormal_2018)}")
        if len(abnormal_2018) > 0:
            print(abnormal_2018)
        else:
            print("✅ 2018年後無異常低價數據")

        # 統計總記錄數
        print("\n=== 數據總覽 ===")
        total_count = con.execute("SELECT COUNT(*) as cnt FROM futures_data WHERE Symbol = 'TX'").fetchdf()
        print(f"TX 總記錄數: {total_count['cnt'].values[0]}")

        # 檢查價格範圍統計
        price_stats = con.execute("""
            SELECT
                MIN(Close) as min_close,
                MAX(Close) as max_close,
                AVG(Close) as avg_close,
                COUNT(*) as total_records
            FROM futures_data
            WHERE Symbol = 'TX' AND Close > 0
        """).fetchdf()
        print("價格統計:")
        print(price_stats)

        # 檢查缺失值
        missing_check = con.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN Close IS NULL OR Close <= 0 THEN 1 END) as missing_close,
                COUNT(CASE WHEN High IS NULL OR High <= 0 THEN 1 END) as missing_high,
                COUNT(CASE WHEN Low IS NULL OR Low <= 0 THEN 1 END) as missing_low,
                COUNT(CASE WHEN Volume IS NULL OR Volume <= 0 THEN 1 END) as missing_volume
            FROM futures_data
            WHERE Symbol = 'TX'
        """).fetchdf()
        print("\n缺失值統計:")
        print(missing_check)

        con.close()
        print("\n✅ 數據品質檢查完成")

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

