import requests
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# FinMind API Token (provided by user)
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0xMS0yMiAwODoxMzoxOCIsInVzZXJfaWQiOiJzdXBlcmhzcCIsImlwIjoiMTE0LjQ3LjE5My4yMDQiLCJleHAiOjE3NjQzNzUxOTh9.d9K6EsOA0YAtAuP_RC84yYD4DXco5awHQYQoZCaQCUk"

RAW_DATA_DIR = Path("data/raw")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

def fetch_taiwan_futures_index(start_date, end_date):
    """
    Fetch Taiwan Futures Index data from FinMind API.
    Dataset: TaiwanFuturesDaily (台指期每日資料)
    """
    url = "https://api.finmindtrade.com/api/v4/data"
    
    params = {
        'dataset': 'TaiwanFuturesDaily',
        'data_id': 'TX',  # TX = 台指期 (Taiwan Stock Index Futures)
        'start_date': start_date,
        'end_date': end_date,
        'token': FINMIND_TOKEN
    }
    
    logging.info(f"Fetching Taiwan Futures data from {start_date} to {end_date}...")
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] != 200:
            logging.error(f"API returned error: {data.get('msg', 'Unknown error')}")
            return None
            
        df = pd.DataFrame(data['data'])
        
        if df.empty:
            logging.warning(f"No data returned for {start_date} to {end_date}")
            return None
            
        logging.info(f"Successfully fetched {len(df)} rows")
        logging.info(f"Columns: {df.columns.tolist()}")
        logging.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
        
        return df
        
    except Exception as e:
        logging.error(f"Failed to fetch data: {e}")
        return None

def fetch_institutional_investors(start_date, end_date):
    """
    Fetch institutional investors data (三大法人).
    Dataset: TaiwanFuturesInstitutionalInvestors
    """
    url = "https://api.finmindtrade.com/api/v4/data"
    
    params = {
        'dataset': 'TaiwanFuturesInstitutionalInvestors',
        'data_id': 'TX',
        'start_date': start_date,
        'end_date': end_date,
        'token': FINMIND_TOKEN
    }
    
    logging.info(f"Fetching institutional investors data...")
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] != 200:
            logging.error(f"API returned error: {data.get('msg', 'Unknown error')}")
            return None
            
        df = pd.DataFrame(data['data'])
        
        if df.empty:
            logging.warning("No institutional investors data returned")
            return None
            
        logging.info(f"Successfully fetched {len(df)} rows of institutional data")
        
        return df
        
    except Exception as e:
        logging.error(f"Failed to fetch institutional data: {e}")
        return None

def fetch_usdtwd_exchange_rate(start_date, end_date):
    """
    Fetch USD/TWD exchange rate.
    Dataset: TaiwanExchangeRate
    """
    url = "https://api.finmindtrade.com/api/v4/data"
    
    params = {
        'dataset': 'TaiwanExchangeRate',
        'data_id': 'USD',
        'start_date': start_date,
        'end_date': end_date,
        'token': FINMIND_TOKEN
    }
    
    logging.info(f"Fetching USD/TWD exchange rate...")
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] != 200:
            logging.error(f"API returned error: {data.get('msg', 'Unknown error')}")
            return None
            
        df = pd.DataFrame(data['data'])
        
        if df.empty:
            logging.warning("No exchange rate data returned")
            return None
            
        logging.info(f"Successfully fetched {len(df)} rows of exchange rate data")
        
        return df
        
    except Exception as e:
        logging.error(f"Failed to fetch exchange rate: {e}")
        return None

def main():
    # Fetch data for the last 3 years
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')
    
    logging.info(f"=== Starting FinMind Data Fetch ===")
    logging.info(f"Date range: {start_date} to {end_date}")
    
    # 1. Fetch Taiwan Futures Index (TX)
    futures_df = fetch_taiwan_futures_index(start_date, end_date)
    if futures_df is not None:
        output_path = RAW_DATA_DIR / "TWII_futures.csv"
        futures_df.to_csv(output_path, index=False, encoding='utf-8')
        logging.info(f"Saved futures data to {output_path}")
    
    # 2. Fetch Institutional Investors data
    institutional_df = fetch_institutional_investors(start_date, end_date)
    if institutional_df is not None:
        output_path = RAW_DATA_DIR / "institutional_investors.csv"
        institutional_df.to_csv(output_path, index=False, encoding='utf-8')
        logging.info(f"Saved institutional data to {output_path}")
    
    # 3. Fetch USD/TWD Exchange Rate
    usdtwd_df = fetch_usdtwd_exchange_rate(start_date, end_date)
    if usdtwd_df is not None:
        output_path = RAW_DATA_DIR / "USDTWD.csv"
        usdtwd_df.to_csv(output_path, index=False, encoding='utf-8')
        logging.info(f"Saved exchange rate data to {output_path}")
    
    logging.info("=== Data fetch complete ===")

if __name__ == "__main__":
    main()
