#!/usr/bin/env python3
"""
準備測試資料 - 只提取 2024-01 單月資料
記憶體優化:使用 DuckDB Streaming,避免一次載入全部資料
支援 CLI 參數以確保可攜性
"""
import duckdb
import sys
import argparse
from pathlib import Path

def prepare_test_data(db_path, output_dir, test_month='2024-01'):
    """
    從 SQLite 提取單月資料,存為 Parquet
    
    Args:
        db_path: taifex.db 路徑
        output_dir: 輸出目錄
        test_month: 測試月份 (格式: YYYY-MM)
    """
    print(f"📊 準備測試資料: {test_month}")
    
    # 建立輸出目錄
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = Path(db_path).resolve()
    if not db_path.exists():
        print(f"❌ 錯誤: 資料庫檔案不存在: {db_path}")
        return None

    # 使用 DuckDB 讀取 SQLite (記憶體友善)
    try:
        conn = duckdb.connect(':memory:')
        
        # 先檢查資料庫結構
        print(f"🔍 檢查資料庫: {db_path}")
        # 安裝並載入 sqlite 擴充套件 (如果需要)
        conn.execute("INSTALL sqlite; LOAD sqlite;")
        
        tables_query = f"SELECT name FROM sqlite_scan('{str(db_path)}', 'sqlite_master') WHERE type='table'"
        tables = conn.execute(tables_query).fetchall()
        table_names = [t[0] for t in tables]
        print(f"📋 可用資料表: {table_names}")
        
        target_table = 'daily_data'
        if target_table not in table_names:
             # 嘗試自動偵測
             if len(table_names) > 0:
                 target_table = table_names[0]
                 print(f"⚠️ 警告: 找不到 'daily_data', 使用 '{target_table}'")
        
        # 查詢單月資料
        query = f"""
            SELECT *
            FROM sqlite_scan('{str(db_path)}', '{target_table}')
            WHERE strftime('%Y-%m', date) = '{test_month}'
            ORDER BY date
        """
        
        print(f"🔍 執行查詢...")
        df = conn.execute(query).fetch_df()
        
        print(f"✅ 提取 {len(df)} 筆資料")
        if len(df) > 0:
            print(f"📅 日期範圍: {df['date'].min()} ~ {df['date'].max()}")
            print(f"📊 欄位: {list(df.columns)}")
            
            # 存為 Parquet
            output_file = output_dir / f"test_data_{test_month.replace('-', '_')}.parquet"
            df.to_parquet(output_file, index=False)
            
            print(f"💾 已儲存: {output_file}")
            print(f"📦 檔案大小: {output_file.stat().st_size / 1024:.2f} KB")
            return output_file
        else:
            print("⚠️ 警告: 沒有找到資料")
            return None
            
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    parser = argparse.ArgumentParser(description='準備測試資料')
    parser.add_argument('--db-path', type=str, default='../data/taifex.db',
                        help='SQLite 資料庫路徑 (預設: ../data/taifex.db)')
    parser.add_argument('--output-dir', type=str, default='./data/test',
                        help='輸出目錄 (預設: ./data/test)')
    parser.add_argument('--month', type=str, default='2024-01',
                        help='測試月份 (預設: 2024-01)')
    
    args = parser.parse_args()
    
    # 嘗試解析相對路徑
    db_path = Path(args.db_path)
    if not db_path.exists():
        # 嘗試在專案內尋找
        project_db_path = Path(__file__).parent.parent / 'data' / 'taifex.db'
        if project_db_path.exists():
            print(f"💡 提示: 在預設路徑找不到 DB, 使用專案內路徑: {project_db_path}")
            db_path = project_db_path
    
    result = prepare_test_data(db_path, args.output_dir, test_month=args.month)
    
    if result:
        print(f"\n✅ 測試資料準備完成!")
    else:
        print(f"\n❌ 測試資料準備失敗")
        sys.exit(1)

if __name__ == '__main__':
    main()
