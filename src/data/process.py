"""
Clean and merge FinMind data into master_dataset.csv
"""
import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

def calculate_rsi(series, period=14):
    """Calculate RSI indicator"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(series, window=20, num_std=2):
    """Calculate Bollinger Bands"""
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    return sma, upper, lower

def calculate_zscore(series, window=60):
    """Calculate Z-Score"""
    mean = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    zscore = (series - mean) / std
    return zscore

def main():
    logging.info("=== Starting data cleaning and merging ===")
    
    # 1. Load Taiwan Futures Index data
    logging.info("Loading Taiwan Futures Index data...")
    futures_path = RAW_DATA_DIR / "TWII_futures.csv"
    
    if not futures_path.exists():
        logging.error(f"Futures data not found at {futures_path}")
        return
    
    df_futures = pd.read_csv(futures_path)
    logging.info(f"Loaded {len(df_futures)} rows of futures data")
    logging.info(f"Columns: {df_futures.columns.tolist()}")
    
    # Rename columns to match expected format
    # FinMind columns: date, contract_date, open, high, low, close, volume, open_interest, etc.
    df = df_futures.rename(columns={
        'date': 'Date',
        'open': 'TWII_Open',
        'high': 'TWII_High',
        'low': 'TWII_Low',
        'close': 'TWII_Close',
        'volume': 'Volume'
    })
    print("\n=== Master Dataset Summary ===")
    print(df[['Date', 'TWII_Close', 'Volume', 'RSI_14', 'Foreign_Investor_Net', 'USDTWD_Close']].describe())
    print(f"\nFirst 5 rows:")
    print(df.head())
    print(f"\nLast 5 rows:")
    print(df.tail())
    
    logging.info("=== Data cleaning and merging complete ===")

if __name__ == "__main__":
    main()
