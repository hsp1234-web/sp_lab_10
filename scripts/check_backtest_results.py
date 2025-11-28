#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 Chandelier 回測結果的指令稿
"""
import sys
import os
import io
import duckdb
from pathlib import Path

# 設置 UTF-8 輸出
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', line_buffering=True)

def main():
    db_path = Path('records/chandelier_backtest.db')
    
    if not db_path.exists():
        print(f"[ERR] 資料庫不存在: {db_path}")
        return
    
    try:
        con = duckdb.connect(str(db_path))
        
        # 列出所有表格
        print("\n===== 回測資料庫表格 =====")
        tables = con.execute("SHOW TABLES;").fetchdf()
        print(f"表格數量: {len(tables)}")
        print(tables.to_string())
        
        if len(tables) == 0:
            print("\n[INFO] 資料庫為空，尚無表格")
            con.close()
            return
        
        table_names = tables['name'].tolist()
        
        # 逐表檢查
        for tbl in table_names:
            print(f"\n===== 表: {tbl} =====")
            
            # 檢查列數
            cols = con.execute(f"PRAGMA table_info('{tbl}');").fetchdf()
            print(f"列名: {cols['name'].tolist()}")
            
            # 統計行數
            count = con.execute(f"SELECT COUNT(*) AS cnt FROM {tbl};").fetchdf()
            row_count = int(count['cnt'].values[0])
            print(f"行數: {row_count}")
            
            if row_count > 0:
                # 預覽前 5 行
                print(f"\n預覽 (前 5 行):")
                preview = con.execute(f"SELECT * FROM {tbl} LIMIT 5;").fetchdf()
                print(preview.to_string())
        
        con.close()
        print("\n[OK] 檢查完成")
        
    except Exception as e:
        print(f"[ERR] 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

