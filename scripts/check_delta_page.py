#!/usr/bin/env python3
"""
檢查台灣期貨交易所Delta資料下載頁面的結構
"""

import requests
from pathlib import Path

def check_delta_page():
    # 檢查台灣期貨交易所Delta資料下載頁面的實際結構
    url = 'https://www.taifex.com.tw/cht/3/dlOptDailyDelta'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        print(f"檢查頁面: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {len(response.text)} characters")

        # 檢查是否有表單
        if 'form' in response.text.lower():
            print("✓ 發現表單元素")
        else:
            print("✗ 未發現表單元素")

        # 檢查是否有下載連結
        if 'download' in response.text.lower() or 'csv' in response.text.lower():
            print("✓ 發現下載相關元素")
        else:
            print("✗ 未發現下載相關元素")

        # 檢查是否有JavaScript
        if 'javascript' in response.text.lower() or 'onclick' in response.text.lower():
            print("✓ 發現JavaScript元素")
        else:
            print("✗ 未發現JavaScript元素")

        # 儲存頁面內容以供檢查
        html_file = Path('data/taifex_official/delta_page.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"頁面已儲存至 {html_file}")

        # 檢查是否有實際的資料表格
        lines = response.text.split('\n')
        data_lines = [line for line in lines if '<td>' in line or '<tr>' in line]
        if data_lines:
            print(f"✓ 發現 {len(data_lines)} 個可能的資料行")
        else:
            print("✗ 未發現資料表格")

    except Exception as e:
        print(f"錯誤: {e}")

def test_delta_post():
    """測試POST請求"""
    url = 'https://www.taifex.com.tw/cht/3/dlOptDailyDelta'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.taifex.com.tw/cht/3/dlOptDailyDelta',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # 使用session來保持連線狀態
    session = requests.Session()
    session.headers.update(headers)

    # 先訪問頁面
    try:
        session.get(url, timeout=30)
        print("已建立session並訪問頁面")
    except Exception as e:
        print(f"訪問頁面失敗: {e}")

    # 測試不同的參數組合
    payloads = [
        {'down_type': '2', 'queryDate': '20241126'},
        {'down_type': '', 'queryDate': '20241126'},
        {'down_type': '2', 'queryStartDate': '20241126', 'queryEndDate': '20241126'},
    ]

    for i, payload in enumerate(payloads, 1):
        print(f"\n測試POST請求 {i}: {payload}")
        try:
            response = session.post(url, data=payload, timeout=30)
            print(f"Status: {response.status_code}")
            content_type = response.headers.get('Content-Type', 'N/A')
            print(f"Content-Type: {content_type}")
            print(f"Content-Length: {len(response.text)}")

            # 檢查是否為CSV（包含我們程式碼中的所有檢查條件）
            if ('text/csv' in content_type or
                'text/html' in content_type or
                'ms950' in content_type):
                print("✓ 返回可能的CSV資料!")
                # 檢查內容是否真的是CSV
                if ',' in response.text and len(response.text) > 100:
                    return response.text
                else:
                    print("內容不符合CSV格式")
            elif len(response.text) < 1000:  # 可能是錯誤訊息
                print(f"回應內容: {response.text[:500]}")
            else:
                print("返回HTML頁面")

        except Exception as e:
            print(f"POST請求失敗: {e}")

    return None

def test_other_endpoints():
    """測試其他類似的API端點"""
    endpoints = [
        ('選擇權每日行情', 'https://www.taifex.com.tw/cht/3/dlOptDailyMarketView'),
        ('期貨每日行情', 'https://www.taifex.com.tw/cht/3/dlFutDailyMarketView'),
        ('三大法人資料', 'https://www.taifex.com.tw/cht/3/dl3InstiiDown'),
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for name, url in endpoints:
        print(f"\n測試 {name}: {url}")
        payload = {'down_type': '2', 'queryDate': '20241126'}

        try:
            response = requests.post(url, data=payload, headers=headers, timeout=30)
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")

            if 'text/csv' in response.headers.get('Content-Type', ''):
                print("✓ 成功獲取CSV資料!")
                return name, response.text
            else:
                print("返回HTML頁面")

        except Exception as e:
            print(f"錯誤: {e}")

    return None, None

if __name__ == "__main__":
    print("=" * 60)
    print("檢查台灣期貨交易所Delta資料下載頁面")
    print("=" * 60)

    check_delta_page()

    print("\n" + "=" * 60)
    print("測試POST請求")
    print("=" * 60)

    csv_data = test_delta_post()
    if csv_data:
        print("\n成功獲取CSV資料!")
        with open('data/taifex_official/delta_test.csv', 'w', encoding='utf-8') as f:
            f.write(csv_data)
        print("CSV資料已儲存至 data/taifex_official/delta_test.csv")
    else:
        print("\n未能獲取Delta CSV資料")

    print("\n" + "=" * 60)
    print("測試其他API端點")
    print("=" * 60)

    name, csv_data = test_other_endpoints()
    if csv_data:
        print(f"\n{name} 成功獲取CSV資料!")
        filename = f"data/taifex_official/sample_{name.replace(' ', '_')}.csv"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(csv_data[:5000])  # 只儲存前5000字元作為樣本
        print(f"樣本資料已儲存至 {filename}")
    else:
        print("\n其他端點也未能獲取CSV資料")
