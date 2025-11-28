# -*- coding: utf-8 -*-
"""
檢查本金保護區間策略所需數據
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
import pandas as pd
from pathlib import Path

def check_futures_data():
    """檢查台指期數據"""
    print("=== 台指期數據檢查 ===")

    try:
        con = duckdb.connect('data/taifex.db')

        # 檢查數據結構
        schema = con.execute("DESCRIBE futures_data").fetchall()
        print("數據庫結構:")
        for col in schema:
            print(f"  {col[0]}: {col[1]}")

        # 檢查數據樣本
        df = con.execute("""
            SELECT Date, Symbol, Open, High, Low, Close, Volume
            FROM futures_data
            WHERE Symbol = 'TX'
            ORDER BY Date DESC
            LIMIT 10
        """).fetchdf()

        print("\n最新數據樣本:")
        print(df.head())

        # 檢查數據期間
        date_range = con.execute("""
            SELECT MIN(Date) as start_date, MAX(Date) as end_date, COUNT(*) as total_records
            FROM futures_data
            WHERE Symbol = 'TX' AND Close IS NOT NULL
        """).fetchone()

        print("\n數據統計:")
        print(f"  開始日期: {date_range[0]}")
        print(f"  結束日期: {date_range[1]}")
        print(f"  總記錄數: {date_range[2]}")

        con.close()
        return True

    except Exception as e:
        print(f"台指期數據檢查失敗: {e}")
        return False

def check_pcr_data():
    """檢查PCR數據"""
    print("\n=== PCR數據檢查 ===")

    try:
        pcr_file = Path('data/taifex_official/processed_pcr_20251028_20251127.csv')

        if not pcr_file.exists():
            print("PCR數據文件不存在")
            return False

        df = pd.read_csv(pcr_file)
        print("PCR數據結構:")
        print(df.info())

        print("\nPCR數據樣本:")
        print(df.head())

        print("\n數據統計:")
        print(f"  數據期間: {df['date'].min()} 到 {df['date'].max()}")
        print(f"  PCR範圍: {df['pcr'].min():.3f} 到 {df['pcr'].max():.3f}")
        print(f"  平均PCR: {df['pcr'].mean():.3f}")

        return True

    except Exception as e:
        print(f"PCR數據檢查失敗: {e}")
        return False

def check_options_data():
    """檢查選擇權數據"""
    print("\n=== 選擇權數據檢查 ===")

    try:
        con = duckdb.connect('data/taifex_options.db')

        # 檢查數據結構
        schema = con.execute("DESCRIBE options_data").fetchall()
        print("選擇權數據庫結構:")
        for col in schema:
            print(f"  {col[0]}: {col[1]}")

        # 檢查數據樣本
        df = con.execute("""
            SELECT *
            FROM options_data
            ORDER BY date DESC
            LIMIT 5
        """).fetchdf()

        print("\n最新選擇權數據樣本:")
        print(df.head())

        con.close()
        return True

    except Exception as e:
        print(f"選擇權數據檢查失敗: {e}")
        return False

def check_macro_data():
    """檢查宏觀經濟數據"""
    print("\n=== 宏觀數據檢查 ===")

    try:
        # 檢查FRED API數據緩存
        cache_file = Path('data/cache/api_cache.sqlite')
        if cache_file.exists():
            con = duckdb.connect(str(cache_file))
            tables = con.execute("SHOW TABLES").fetchall()
            print("API緩存中的數據表:")
            for table in tables:
                count = con.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                print(f"  {table[0]}: {count} 條記錄")

            # 檢查VIX數據
            try:
                vix_df = con.execute("SELECT * FROM vix_data ORDER BY date DESC LIMIT 5").fetchdf()
                print("\nVIX數據樣本:")
                print(vix_df.head())
            except:
                print("VIX數據不存在")

            con.close()
        else:
            print("API緩存文件不存在")

        return True

    except Exception as e:
        print(f"宏觀數據檢查失敗: {e}")
        return False

if __name__ == "__main__":
    print("=== 本金保護區間策略數據檢查 ===")
    print("=" * 50)

    # 切換到專案根目錄
    os.chdir(Path(__file__).parent.parent)

    results = []
    results.append(("台指期數據", check_futures_data()))
    results.append(("PCR數據", check_pcr_data()))
    results.append(("選擇權數據", check_options_data()))
    results.append(("宏觀數據", check_macro_data()))

    print("\n" + "=" * 50)
    print("數據檢查總結:")
    for name, success in results:
        status = "[通過]" if success else "[失敗]"
        print(f"  {name}: {status}")

    success_count = sum(results)
    print(f"\n總計: {success_count}/{len(results)} 項數據檢查通過")
