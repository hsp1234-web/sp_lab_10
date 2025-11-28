import requests

# FINLAB搜索和測試
print("開始搜索FINLAB服務...")

# 測試可能的FINLAB URL
test_urls = [
    "https://www.finlab.tw/",
    "https://finlab.tw/",
    "https://api.finlab.tw/",
    "https://finlab.tw/docs",
    "https://api.finlab.tw/docs",
]

for url in test_urls:
    try:
        response = requests.get(url, timeout=10)
        print(f"URL: {url} - 狀態: {response.status_code}")
        if response.status_code == 200:
            content = response.text.lower()
            if 'finlab' in content:
                print("  * 包含FINLAB相關內容")
            if 'api' in content:
                print("  * 包含API說明")
            if '量化' in content or 'quant' in content:
                print("  * 包含量化交易內容")
            if '台灣' in content or 'taiwan' in content:
                print("  * 包含台灣市場內容")
            if 'free' in content:
                print("  * 提及免費服務")
    except Exception as e:
        print(f"URL: {url} - 錯誤: {str(e)[:50]}")

# 測試API金鑰
print("\n測試API金鑰...")
api_key = "wnFW0KT5etgpNr6IKZI05kNyRrMQDrIeoaplJBlRc+Twz+RWciylMCjm0jvtL0n5#free"

test_endpoints = [
    "https://api.finlab.tw/v1/data",
    "https://api.finlab.tw/v1/stock",
    "https://api.finlab.tw/v1/taiwan",
]

for endpoint in test_endpoints:
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(endpoint, headers=headers, timeout=10)
        print(f"端點: {endpoint} - 狀態: {response.status_code}")
        if response.status_code == 200:
            print("  * API可正常使用!")
            break
    except Exception as e:
        print(f"端點: {endpoint} - 錯誤: {str(e)[:50]}")

print("\nFINLAB搜索完成")
