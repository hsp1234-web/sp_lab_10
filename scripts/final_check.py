#!/usr/bin/env python3
"""
最終專案狀態檢查
"""

import duckdb
import os

def check_databases():
    """檢查所有資料庫狀態"""
    print("=== 資料庫狀態檢查 ===")

    databases = [
        ('data/taifex.db', '歷史期貨資料'),
        ('data/taifex_options.db', '歷史選擇權資料'),
        ('data/taifex_recent_data.db', '近期官方資料'),
        ('data/finmind.db', 'FinMind補充資料')
    ]

    for db_path, description in databases:
        if os.path.exists(db_path):
            try:
                conn = duckdb.connect(db_path)
                tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                print(f"[OK] {description} ({db_path}): {len(tables)}個表格")

                for table_name in tables:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_name[0]}").fetchone()[0]
                    print(f"  - {table_name[0]}: {count:,}筆記錄")

                conn.close()
            except Exception as e:
                print(f"[ERROR] {description}: 錯誤 - {e}")
        else:
            print(f"[MISSING] {description}: 檔案不存在")

def check_scripts():
    """檢查重要腳本"""
    print("\n=== 重要腳本檢查 ===")

    scripts = [
        ('scripts/build_taifex_recent_db.py', '近期資料庫建置'),
        ('scripts/taifex_official_downloader.py', '官方資料下載'),
        ('scripts/build_finmind_db.py', 'FinMind資料建置'),
        ('src/integrated_strategy.py', '整合策略框架')
    ]

    for script_path, description in scripts:
        if os.path.exists(script_path):
            print(f"[OK] {description}: {script_path}")
        else:
            print(f"[MISSING] {description}: 檔案不存在 - {script_path}")

def check_recent_logs():
    """檢查最近的開發日誌"""
    print("\n=== 開發日誌檢查 ===")

    log_dir = "docs/logs/2025-11"
    if os.path.exists(log_dir):
        logs = [f for f in os.listdir(log_dir) if f.endswith('.md')]
        logs.sort(reverse=True)  # 最新的在前面

        print(f"[OK] 開發日誌目錄: {log_dir}")
        print(f"[OK] 日誌檔案數量: {len(logs)}")

        if logs:
            print("[OK] 最新日誌:")
            for i, log in enumerate(logs[:3]):  # 顯示前3個
                print(f"  {i+1}. {log}")
    else:
        print("[MISSING] 開發日誌目錄不存在")

if __name__ == "__main__":
    print("SP Lab V10 最終狀態檢查")
    print("=" * 50)

    check_databases()
    check_scripts()
    check_recent_logs()

    print("\n" + "=" * 50)
    print("檢查完成！")
    print("詳細交接文件請參考: docs/HANDOVER_DOCUMENT.md")
