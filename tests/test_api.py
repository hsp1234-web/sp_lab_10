#!/usr/bin/env python3
import requests

# 測試台灣期貨交易所PCR API
url = 'https://www.taifex.com.tw/cht/3/dlPcRatioDown'
payload = {
    'down_type': '',
    'queryStartDate': '2025/10/28',
    'queryEndDate': '2025/11/27'
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.taifex.com.tw/cht/3/dlPcRatioDown'
}

print('測試PCR API...')
response = requests.post(url, data=payload, headers=headers, timeout=30)
print('狀態碼:', response.status_code)
print('Content-Type:', response.headers.get('Content-Type'))
print('Content-Length:', response.headers.get('Content-Length'))
print('前200個字元:', response.text[:200])
print('前4個bytes:', response.content[:4])

# 檢查是否為ZIP
is_zip = len(response.content) >= 4 and response.content[:4] == b'PK\x03\x04'
print('是否為ZIP檔案:', is_zip)
