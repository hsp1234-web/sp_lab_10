import pandas as pd
from pathlib import Path

def debug_read():
    csv_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\taifex_extracted\2024_fut.csv")
    
    print("--- Reading with utf-8 ---")
    try:
        df = pd.read_csv(csv_path, encoding='utf-8', nrows=5)
        print("Columns:", list(df.columns))
        print("First row values:", df.iloc[0].tolist())
        print("First row dict:", df.iloc[0].to_dict())
    except Exception as e:
        print(e)

    print("\n--- Reading with utf-8-sig ---")
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig', nrows=5)
        print("Columns:", list(df.columns))
        print("First row values:", df.iloc[0].tolist())
        print("First row dict:", df.iloc[0].to_dict())
    except Exception as e:
        print(e)

if __name__ == "__main__":
    debug_read()
