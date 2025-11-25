import yfinance as yf
import sys
import os

log_file = os.path.join(os.path.dirname(__file__), "debug_log.txt")

def log(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

log("Starting debug script")
try:
    log(f"yfinance version: {yf.__version__}")
    
    ticker = "TX=F"
    log(f"Downloading {ticker}...")
    data = yf.download(ticker, start="2024-01-01", end="2024-01-10", progress=False)
    
    log(f"Data shape: {data.shape}")
    if data.empty:
        log("Data is empty")
    else:
        log("Data found")
        log(str(data.head()))
        
except Exception as e:
    log(f"Error: {e}")

log("End of script")
