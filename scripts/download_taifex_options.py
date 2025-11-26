# -*- coding: utf-8 -*-
"""
台灣期貨交易所選擇權資料下載腳本

此腳本用於下載台灣期貨交易所的選擇權年度交易行情資料。
資料來源：https://www.taifex.com.tw/cht/3/dlOptDailyMarketView
"""
import requests
import os
import time
import random
import sys
from pathlib import Path

# 設定 Windows 終端機編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration
BASE_URL = "https://www.taifex.com.tw"
PROJECT_ROOT = Path(__file__).parent.parent
TARGET_DIR = PROJECT_ROOT / "data" / "taifex_options_raw"
START_YEAR = 2001  # 根據網站提供的選項，最早可追溯到 2001 年
END_YEAR = 2024

os.makedirs(TARGET_DIR, exist_ok=True)

def download_options_year(year):
    """
    下載指定年份的選擇權年度交易行情資料
    
    Args:
        year (int): 年份 (2001-2024)
    
    Returns:
        bool: 下載是否成功
    """
    print(f"正在處理年份: {year}")
    
    # 根據 Network 面板確認的選擇權年度下載 URL
    url = f"{BASE_URL}/cht/3/optDataDown"
    
    # 年度下載的參數（根據實際 Form Data 確認）
    payload = {
        'down_type': '2',  # 年度下載類型
        'his_year': str(year)
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': f'{BASE_URL}/cht/3/dlOptDailyMarketView'
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        
        # 檢查回應內容類型
        content_type = response.headers.get('Content-Type', '')
        
        # 判斷是否為 ZIP 檔案
        # 年度下載的 Content-Type 是 application/octet-stream
        is_zip = (
            'zip' in content_type.lower() or 
            'octet-stream' in content_type.lower() or
            response.content[:4] == b'PK\x03\x04'
        )
        
        if is_zip:
            # 從 Content-Disposition 取得檔名，或使用預設檔名
            # 根據實際下載，檔名格式為 {year}_opt.zip
            filename = f"{year}_opt.zip"
            if "Content-Disposition" in response.headers:
                cd = response.headers["Content-Disposition"]
                if "filename=" in cd:
                    filename = cd.split("filename=")[1].strip('"').strip("'")
            
            file_path = TARGET_DIR / filename
            
            # 如果檔案已存在，跳過下載
            if file_path.exists():
                print(f"檔案已存在，跳過: {filename}")
                return True
            
            # 儲存檔案
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = file_path.stat().st_size
            print(f"成功下載: {filename} ({file_size:,} bytes)")
            return True
        else:
            # 如果不是 ZIP 檔案，可能是錯誤訊息
            print("警告: 回應內容不是 ZIP 檔案，可能是錯誤訊息")
            print(f"Content-Type: {content_type}")
            try:
                print(f"回應前 200 字元: {response.text[:200]}")
            except:
                print(f"回應內容 (bytes): {response.content[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"下載失敗 {year}: {e}")
        return False
    except Exception as e:
        print(f"發生錯誤 {year}: {e}")
        return False

def main():
    """
    主程式：下載指定年份範圍的選擇權資料
    """
    print("=" * 70)
    print("  台灣期貨交易所選擇權資料下載工具")
    print("=" * 70)
    print(f"目標目錄: {TARGET_DIR}")
    print(f"下載年份範圍: {START_YEAR} - {END_YEAR}")
    print("=" * 70)
    print()
    
    total_years = END_YEAR - START_YEAR + 1
    success_count = 0
    fail_count = 0
    skipped_count = 0
    
    for idx, year in enumerate(range(START_YEAR, END_YEAR + 1), 1):
        # 顯示進度
        progress = f"[{idx}/{total_years}]"
        print(f"{progress} 正在處理 {year} 年...", end=" ")
        
        # 檢查檔案是否已存在
        file_path = TARGET_DIR / f"{year}_opt.zip"
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"✓ 已存在 ({file_size:,} bytes)")
            skipped_count += 1
            continue
        
        success = download_options_year(year)
        if success:
            success_count += 1
            print(f"✓ 完成")
            # 禮貌性延遲，避免對伺服器造成負擔
            time.sleep(random.uniform(1, 3))
        else:
            fail_count += 1
            print(f"✗ 失敗，重試中...")
            time.sleep(5)
            # 重試一次
            if download_options_year(year):
                success_count += 1
                fail_count -= 1
                print(f"✓ 重試成功")
            else:
                print(f"✗ 重試失敗")
    
    print()
    print("=" * 70)
    print(f"下載完成！")
    print(f"  成功: {success_count} 個年份")
    print(f"  跳過: {skipped_count} 個年份 (已存在)")
    print(f"  失敗: {fail_count} 個年份")
    print(f"檔案存放位置: {TARGET_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()

