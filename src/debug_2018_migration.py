import duckdb
import pandas as pd
from pathlib import Path
import traceback
import numpy as np

def debug_2018():
    csv_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\taifex_extracted\2018_fut.csv")
    log_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\debug_2018_log.txt")
    
    with open(log_path, 'w', encoding='utf-8') as log:
        try:
            log.write(f"Processing {csv_path.name}...\n")
            
            # Column mapping
            col_map = {
                '交易日期': 'Date',
                '契約': 'Symbol',
                '到期月份(週別)': 'Expiry',
                '開盤價': 'Open',
                '最高價': 'High',
                '最低價': 'Low',
                '收盤價': 'Close',
                '漲跌價': 'Change',
                '漲跌%': 'ChangePercent',
                '成交量': 'Volume',
                '結算價': 'SettlementPrice',
                '未沖銷契約數': 'OpenInterest',
                '最後最佳買價': 'BestBid',
                '最後最佳賣價': 'BestAsk',
                '歷史最高價': 'HistHigh',
                '歷史最低價': 'HistLow',
                '是否因訊息面暫停交易': 'IsPaused',
                '交易時段': 'Session',
                '價差對單式委託成交量': 'SpreadVolume'
            }
            
            target_columns = [
                'Date', 'Symbol', 'Expiry', 'Open', 'High', 'Low', 'Close', 
                'Change', 'ChangePercent', 'Volume', 'SettlementPrice', 'OpenInterest', 
                'BestBid', 'BestAsk', 'HistHigh', 'HistLow', 'IsPaused', 'Session', 'SpreadVolume'
            ]

            # Read CSV
            df = pd.read_csv(csv_path, encoding='utf-8', index_col=False, na_values=['-'])
            log.write(f"Read successful. Columns: {list(df.columns)}\n")
            
            # Rename columns
            df.rename(columns=col_map, inplace=True)
            
            # Add missing columns
            for col in target_columns:
                if col not in df.columns:
                    df[col] = np.nan
                    
            # Select and order columns
            df = df[target_columns]
            
            # Ensure numeric columns
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Change', 'Volume', 'SettlementPrice', 'OpenInterest', 'BestBid', 'BestAsk', 'HistHigh', 'HistLow', 'SpreadVolume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Clean up ChangePercent
            if 'ChangePercent' in df.columns:
                df['ChangePercent'] = df['ChangePercent'].astype(str).str.replace('%', '', regex=False)
                df['ChangePercent'] = pd.to_numeric(df['ChangePercent'], errors='coerce')
                
            # Ensure string columns
            string_cols = ['Date', 'Symbol', 'Expiry', 'IsPaused', 'Session']
            for col in string_cols:
                df[col] = df[col].astype(str).replace('nan', None)

            log.write("Processing complete. No errors.\n")
            
        except Exception as e:
            log.write(f"Error: {e}\n")
            log.write(traceback.format_exc())

if __name__ == "__main__":
    debug_2018()
