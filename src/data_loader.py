# -*- coding: utf-8 -*-
import pandas as pd
import re
from src.fetch import fetch_stock_data

def _rename_ohlc_columns(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Standardize OHLC column names.
    """
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    new_cols = {}
    for col in df.columns:
        clean_col = re.sub(rf'[._]{re.escape(ticker)}', '', col, flags=re.IGNORECASE)
        new_cols[col] = clean_col
    df.rename(columns=new_cols, inplace=True)

    df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)

    return df

def load_and_process_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch and process stock data.
    """
    print(f"[Data] Fetching data for {ticker} ({start_date} to {end_date})...")
    data = fetch_stock_data(ticker, start_date, end_date)
    
    if data.empty:
        print(f"[Data] Warning: No data found for {ticker}.")
        return pd.DataFrame()

    data = _rename_ohlc_columns(data, ticker)
    print(f"[Data] Successfully loaded {len(data)} rows.")
    return data
