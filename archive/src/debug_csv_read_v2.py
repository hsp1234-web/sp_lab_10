import pandas as pd
from pathlib import Path

def debug_read():
    csv_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\taifex_extracted\2024_fut.csv")
    output_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\debug_read_log.txt")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("--- Reading with utf-8 ---\n")
        try:
            df = pd.read_csv(csv_path, encoding='utf-8', nrows=5)
            f.write(f"Columns: {list(df.columns)}\n")
            f.write(f"First row values: {df.iloc[0].tolist()}\n")
            f.write(f"First row dict: {df.iloc[0].to_dict()}\n")
        except Exception as e:
            f.write(f"Error: {e}\n")

        f.write("\n--- Reading with utf-8-sig ---\n")
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig', nrows=5)
            f.write(f"Columns: {list(df.columns)}\n")
            f.write(f"First row values: {df.iloc[0].tolist()}\n")
            f.write(f"First row dict: {df.iloc[0].to_dict()}\n")
        except Exception as e:
            f.write(f"Error: {e}\n")

if __name__ == "__main__":
    debug_read()
