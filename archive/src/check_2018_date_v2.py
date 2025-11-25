import pandas as pd
from pathlib import Path

def check_date():
    csv_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\taifex_extracted\2018_fut.csv")
    output_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\check_2018_date.txt")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        df = pd.read_csv(csv_path, encoding='utf-8', index_col=False, nrows=5)
        f.write(str(df['交易日期'].tolist()))

if __name__ == "__main__":
    check_date()
