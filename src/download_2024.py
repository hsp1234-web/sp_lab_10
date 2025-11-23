import requests
import os

TARGET_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "taifex_raw")
os.makedirs(TARGET_DIR, exist_ok=True)

url = "https://www.taifex.com.tw/cht/3/futDataDown"
payload = {'down_type': '2', 'his_year': '2024'}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.taifex.com.tw/cht/3/dlFutDailyMarketView'
}

print("Downloading 2024 data...")
response = requests.post(url, data=payload, headers=headers, stream=True)
response.raise_for_status()

filename = "2024_fut.zip"
file_path = os.path.join(TARGET_DIR, filename)

with open(file_path, 'wb') as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)

print(f"Successfully downloaded: {filename}")
print(f"File size: {os.path.getsize(file_path)} bytes")
