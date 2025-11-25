import requests
import os
import time
import random

# Configuration
BASE_URL = "https://www.taifex.com.tw"
TARGET_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "taifex_raw")
START_YEAR = 2009
END_YEAR = 2024  # 2025 data not available yet (year not complete)

os.makedirs(TARGET_DIR, exist_ok=True)

def download_year(year):
    print(f"Processing Year: {year}")
    url = "https://www.taifex.com.tw/cht/3/futDataDown"
    payload = {
        'down_type': '2',
        'his_year': str(year)
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.taifex.com.tw/cht/3/dlFutDailyMarketView'
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers, stream=True)
        response.raise_for_status()
        
        # Determine filename
        filename = f"Futures_Daily_{year}.zip"
        if "Content-Disposition" in response.headers:
            cd = response.headers["Content-Disposition"]
            if "filename=" in cd:
                filename = cd.split("filename=")[1].strip('"')
        
        file_path = os.path.join(TARGET_DIR, filename)
        
        if os.path.exists(file_path):
            print(f"File exists, skipping: {filename}")
            return True

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Successfully downloaded: {filename}")
        return True
    except Exception as e:
        print(f"Failed to download {year}: {e}")
        return False

def main():
    print(f"Starting download for range {START_YEAR}-{END_YEAR} to {TARGET_DIR}")
    for year in range(START_YEAR, END_YEAR + 1):
        success = download_year(year)
        if success:
            time.sleep(random.uniform(1, 3)) # Be polite
        else:
            print(f"Retrying {year} once...")
            time.sleep(5)
            download_year(year)

if __name__ == "__main__":
    main()
