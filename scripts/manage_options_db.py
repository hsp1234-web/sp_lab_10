# -*- coding: utf-8 -*-
"""
選擇權資料庫管理工具
"""
import sys
import subprocess
import time
from pathlib import Path
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_process(pid):
    """檢查程序是否還在執行"""
    try:
        import psutil
        process = psutil.Process(pid)
        return process.is_running()
    except:
        # 如果沒有 psutil，使用 tasklist
        try:
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True
            )
            return str(pid) in result.stdout
        except:
            return None

def main():
    print("選擇權資料庫管理工具")
    print("=" * 50)
    print()
    print("選項:")
    print("1. 檢查資料庫狀態")
    print("2. 重新建置資料庫（會刪除現有資料）")
    print("3. 檢查是否有程序正在使用資料庫")
    print()
    
    choice = input("請選擇 (1/2/3): ").strip()
    
    if choice == '1':
        from scripts.check_options_db import *
        # 會自動執行檢查
    elif choice == '2':
        db_path = Path('data/taifex_options.db')
        if db_path.exists():
            confirm = input(f"確定要刪除 {db_path} 並重新建置嗎？(y/n): ")
            if confirm.lower() == 'y':
                # 先嘗試關閉可能開啟的連接
                try:
                    import duckdb
                    con = duckdb.connect(str(db_path))
                    con.close()
                except:
                    pass
                # 刪除檔案
                db_path.unlink()
                print("已刪除舊資料庫，開始重新建置...")
                from scripts.build_taifex_options_db import run_migration
                run_migration()
            else:
                print("已取消")
        else:
            print("資料庫不存在，開始建置...")
            from scripts.build_taifex_options_db import run_migration
            run_migration()
    elif choice == '3':
        print("檢查中...")
        # 這裡可以加入檢查邏輯
        print("請使用工作管理員檢查 Python 程序")

if __name__ == "__main__":
    main()

