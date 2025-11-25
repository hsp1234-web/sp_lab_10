import pandas as pd
import duckdb
from FinMind.data import DataLoader
from pathlib import Path

def build_finmind_db():
    """
    使用 FinMind API 下載台指期數據，並建立一個 DuckDB 資料庫。
    """
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "finmind.db"

    print("--- 開始建構 FinMind 數據庫 ---")

    # 1. 下載數據
    print("正在從 FinMind API 下載台指期近月合約數據...")
    api = DataLoader()
    # 'TX' 是台指期的代碼
    df = api.taiwan_futures_daily(futures_id="TX", start_date="2010-01-01")

    if df.empty:
        print("❌ 錯誤：無法從 FinMind 下載數據。")
        return

    print("FinMind API 返回的欄位名稱：", df.columns)

    # 2. 轉換格式
    print("正在轉換資料格式以符合回測框架需求...")
    # FinMind 的欄位名稱已經很接近我們的需求，只需做一些微調
    df = df.rename(columns={
        "date": "Time",
        "open": "Open",
        "max": "High",
        "min": "Low",
        "close": "Close",
        "volume": "Volume"
    })

    # 增加 Symbol 欄位，以符合我們的資料庫綱要
    df['Symbol'] = 'TX'

    # 選取我們需要的欄位
    required_cols = ['Time', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']
    df = df[required_cols]

    # 確保 Time 欄位是 datetime 格式
    df['Time'] = pd.to_datetime(df['Time'])

    # 3. 寫入 DuckDB
    print(f"正在將 {len(df)} 筆數據寫入資料庫: {db_path}...")
    con = duckdb.connect(str(db_path))
    con.execute("DROP TABLE IF EXISTS ohlcv")
    con.execute("""
        CREATE TABLE ohlcv (
            Time TIMESTAMP,
            Symbol VARCHAR,
            Open DOUBLE,
            High DOUBLE,
            Low DOUBLE,
            Close DOUBLE,
            Volume DOUBLE
        )
    """)
    con.register('df_view', df)
    con.execute("INSERT INTO ohlcv SELECT * FROM df_view")
    con.close()

    print("✅ FinMind 數據庫建構完成。")

if __name__ == "__main__":
    build_finmind_db()
