"""
資料範圍檢查腳本
用於檢查 taifex 資料庫和 parquet 檔案的時間範圍
"""
import sqlite3
import os
import sys

def check_sqlite_data():
    """檢查 SQLite 資料庫"""
    db_path = r"c:\SP_DOC\sp_lab_v10\data\taifex.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫: {db_path}")
        return
    
    print(f"✅ 找到資料庫: {db_path}")
    print(f"📊 檔案大小: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 列出所有資料表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"📋 資料表列表: {tables}\n")
        
        # 檢查每個資料表的資料範圍
        for table in tables:
            try:
                # 嘗試查詢日期欄位
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"\n🔍 資料表: {table}")
                print(f"   欄位: {columns}")
                
                # 嘗試找出日期欄位
                date_col = None
                for col in ['date', 'Date', 'DATE', 'datetime', 'timestamp']:
                    if col in columns:
                        date_col = col
                        break
                
                if date_col:
                    cursor.execute(f"SELECT MIN({date_col}), MAX({date_col}), COUNT(*) FROM {table}")
                    min_date, max_date, count = cursor.fetchone()
                    print(f"   📅 時間範圍: {min_date} 到 {max_date}")
                    print(f"   📊 總筆數: {count:,}")
                else:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   📊 總筆數: {count:,}")
                    
            except Exception as e:
                print(f"   ⚠️  查詢失敗: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 資料庫錯誤: {e}")

def check_parquet_data():
    """檢查 Parquet 檔案"""
    parquet_path = r"c:\SP_DOC\sp_lab_v10\hybrid_qlib_framework\data_export\taifex_daily.parquet"
    
    if not os.path.exists(parquet_path):
        print(f"\n❌ 找不到 Parquet 檔案: {parquet_path}")
        return
    
    print(f"\n\n{'='*60}")
    print(f"✅ 找到 Parquet 檔案: {parquet_path}")
    print(f"📊 檔案大小: {os.path.getsize(parquet_path) / 1024:.2f} KB\n")
    
    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path)
        
        print(f"📋 欄位列表: {list(df.columns)}")
        print(f"📊 資料形狀: {df.shape}")
        
        # 檢查索引或日期欄位
        if 'date' in df.columns:
            print(f"📅 時間範圍: {df['date'].min()} 到 {df['date'].max()}")
        elif hasattr(df.index, 'min'):
            print(f"📅 索引範圍: {df.index.min()} 到 {df.index.max()}")
        
        print(f"\n🔍 前5筆資料:")
        print(df.head())
        
    except ImportError:
        print("⚠️  需要安裝 pandas 和 pyarrow: pip install pandas pyarrow")
    except Exception as e:
        print(f"❌ Parquet 讀取錯誤: {e}")

if __name__ == "__main__":
    print("🚀 開始檢查 TAIFEX 資料...")
    print("="*60)
    check_sqlite_data()
    check_parquet_data()
    print("\n" + "="*60)
    print("✅ 檢查完成！")
