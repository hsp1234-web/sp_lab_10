import yfinance as yf
import pandas as pd

def test_ticker(ticker):
    print(f"--- Testing {ticker} ---")
    try:
        # Try fetching a small amount of data
        data = yf.download(ticker, period="5d", progress=False)
        if data.empty:
            print(f"❌ {ticker}: Empty DataFrame returned.")
        else:
            print(f"✅ {ticker}: Successfully fetched {len(data)} rows.")
            print(data.head())
    except Exception as e:
        print(f"❌ {ticker}: Error - {e}")

if __name__ == "__main__":
    print("Checking yfinance version...")
    print(f"yfinance version: {yf.__version__}")
    
    # Test a major US ticker (usually most stable)
    test_ticker("SPY")
    
    # Test the target Taiwan ticker
    test_ticker("0050.TW")
    
    # Test another Taiwan ticker to see if it's specific to 0050
    test_ticker("2330.TW")
