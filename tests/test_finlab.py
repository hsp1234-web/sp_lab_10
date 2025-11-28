import requests
import json

# FINLAB API測試
api_key = "wnFW0KT5etgpNr6IKZI05kNyRrMQDrIeoaplJBlRc+Twz+RWciylMCjm0jvtL0n5#free"

try:
    # 測試基本API
    url = "https://api.finlab.tw/v1/data"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(url, headers=headers, timeout=10)
    print(f"API狀態碼: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("API可用!")
        print("返回數據類型:", type(data))
        if isinstance(data, dict) and len(str(data)) < 500:
            print("數據內容:", data)
    else:
        print(f"API錯誤: {response.text}")

except Exception as e:
    print(f"API測試失敗: {str(e)}")

# 檢查FINLAB文檔網站
try:
    doc_response = requests.get("https://api.finlab.tw/docs", timeout=10)
    print(f"文檔網站狀態: {doc_response.status_code}")
    if doc_response.status_code == 200:
        print("文檔網站可訪問")
        # 尋找關鍵字
        content = doc_response.text.lower()
        if 'quant' in content or '量化' in content:
            print("✓ 包含量化交易相關內容")
        if 'taiwan' in content or '台灣' in content:
            print("✓ 包含台灣市場相關內容")
except Exception as e:
    print(f"文檔檢查失敗: {str(e)}")

