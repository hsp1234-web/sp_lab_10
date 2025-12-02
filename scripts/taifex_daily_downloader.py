#!/usr/bin/env python3
"""
台灣期貨交易所每日資料自動下載器

基於官方提供的免費資料來源：
- 期貨每日行情
- 選擇權每日行情
- Put/Call比
- 三大法人資料
"""

import requests
import os
import sys
import time
import zipfile
import io
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional


class TaifexDailyDownloader:
    """
    台灣期貨交易所每日資料下載器

    自動下載最新的交易資料並整合到資料庫
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

        # 設定目錄
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data" / "taifex_daily"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 官方下載URL
        self.base_url = "https://www.taifex.com.tw/file/taifex/Dailydownload"

        # 設定請求標頭
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def download_daily_data(self, date: str, data_type: str) -> bool:
        """
        下載指定日期和類型的資料

        Args:
            date: 日期字串 (YYYYMMDD格式)
            data_type: 資料類型 ('futures', 'options', 'pcr', 'institutional')

        Returns:
            bool: 下載是否成功
        """
        try:
            # 根據資料類型確定URL
            if data_type == 'futures':
                url = f"{self.base_url}/CSV/Daily_{date}.zip"
                filename = f"futures_{date}.zip"
            elif data_type == 'options':
                url = f"{self.base_url}/OPTIONCSV/Daily_{date}.zip"
                filename = f"options_{date}.zip"
            elif data_type == 'pcr':
                url = f"{self.base_url}/PCSV/Daily_{date}.zip"
                filename = f"pcr_{date}.zip"
            elif data_type == 'institutional':
                url = f"{self.base_url}/3CSV/Daily_{date}.zip"
                filename = f"institutional_{date}.zip"
            else:
                self.logger.error(f"不支援的資料類型: {data_type}")
                return False

            self.logger.info(f"下載 {data_type} 資料: {date}")

            # 下載檔案
            response = requests.get(url, headers=self.headers, timeout=30, stream=True)
            response.raise_for_status()

            # 檢查是否為有效的ZIP檔案
            if not self._is_zip_file(response.content):
                self.logger.warning(f"下載的檔案不是有效的ZIP: {date} {data_type}")
                return False

            # 儲存檔案
            file_path = self.data_dir / filename
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = file_path.stat().st_size
            self.logger.info(f"成功下載: {filename} ({file_size:,} bytes)")

            # 解壓縮並處理資料
            self._process_zip_file(file_path, date, data_type)

            return True

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.info(f"資料不存在 (可能是非交易日): {date} {data_type}")
            else:
                self.logger.error(f"HTTP錯誤 {e.response.status_code}: {date} {data_type}")
            return False
        except Exception as e:
            self.logger.error(f"下載失敗 {date} {data_type}: {e}")
            return False

    def _is_zip_file(self, content: bytes) -> bool:
        """檢查是否為ZIP檔案"""
        return len(content) >= 4 and content[:4] == b'PK\x03\x04'

    def _process_zip_file(self, zip_path: Path, date: str, data_type: str):
        """
        處理下載的ZIP檔案

        Args:
            zip_path: ZIP檔案路徑
            date: 日期字串
            data_type: 資料類型
        """
        try:
            extract_dir = self.data_dir / f"extracted_{data_type}_{date}"
            extract_dir.mkdir(exist_ok=True)

            # 解壓縮檔案
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # 處理解壓縮後的CSV檔案
            for csv_file in extract_dir.glob("*.csv"):
                self._process_csv_file(csv_file, date, data_type)

            # 清理臨時檔案
            import shutil
            shutil.rmtree(extract_dir)
            zip_path.unlink()  # 刪除原始ZIP檔案

        except Exception as e:
            self.logger.error(f"處理ZIP檔案失敗 {zip_path}: {e}")

    def _process_csv_file(self, csv_path: Path, date: str, data_type: str):
        """
        處理CSV資料檔案

        Args:
            csv_path: CSV檔案路徑
            date: 日期字串
            data_type: 資料類型
        """
        try:
            import pandas as pd

            # 根據檔案類型選擇編碼
            encodings = ['utf-8-sig', 'big5', 'cp950']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None or df.empty:
                self.logger.warning(f"無法讀取CSV檔案: {csv_path}")
                return

            # 新增日期欄位
            df['date'] = date
            df['data_type'] = data_type

            # 儲存處理後的資料
            processed_file = self.data_dir / f"processed_{data_type}_{date}_{csv_path.stem}.csv"
            df.to_csv(processed_file, index=False, encoding='utf-8-sig')

            self.logger.info(f"處理完成: {processed_file.name} ({len(df)} 筆記錄)")

        except Exception as e:
            self.logger.error(f"處理CSV檔案失敗 {csv_path}: {e}")

    def download_date_range(self, start_date: str, end_date: str,
                          data_types: List[str] = None) -> Dict[str, int]:
        """
        下載指定日期範圍的資料

        Args:
            start_date: 開始日期 (YYYYMMDD)
            end_date: 結束日期 (YYYYMMDD)
            data_types: 要下載的資料類型清單

        Returns:
            Dict[str, int]: 各資料類型的成功下載數量
        """
        if data_types is None:
            data_types = ['futures', 'options', 'pcr', 'institutional']

        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')

        results = {data_type: 0 for data_type in data_types}
        total_days = (end - start).days + 1
        processed_days = 0

        self.logger.info(f"開始下載資料: {start_date} 到 {end_date}")
        self.logger.info(f"資料類型: {', '.join(data_types)}")

        current = start
        while current <= end:
            date_str = current.strftime('%Y%m%d')
            processed_days += 1

            self.logger.info(f"處理日期: {date_str} ({processed_days}/{total_days})")

            # 檢查是否為交易日 (簡單檢查：跳過週六日)
            if current.weekday() >= 5:  # 週六日
                self.logger.info("跳過非交易日")
                current += timedelta(days=1)
                continue

            # 下載各類型資料
            for data_type in data_types:
                if self.download_daily_data(date_str, data_type):
                    results[data_type] += 1

                # 禮貌性延遲
                time.sleep(1)

            current += timedelta(days=1)

        # 輸出統計結果
        self.logger.info("下載完成統計:")
        for data_type, count in results.items():
            self.logger.info(f"  {data_type}: {count} 個檔案")

        return results

    def get_available_dates(self, days_back: int = 30) -> List[str]:
        """
        獲取可用的交易日期清單

        Args:
            days_back: 回溯天數

        Returns:
            List[str]: 交易日期清單 (YYYYMMDD格式)
        """
        dates = []
        today = datetime.now()

        for i in range(days_back):
            date = today - timedelta(days=i)
            # 跳過週六日
            if date.weekday() < 5:
                dates.append(date.strftime('%Y%m%d'))

        return dates

    def update_recent_data(self, days_back: int = 30):
        """
        更新最近的資料

        Args:
            days_back: 回溯天數
        """
        dates = self.get_available_dates(days_back)
        if dates:
            start_date = dates[-1]  # 最舊的日期
            end_date = dates[0]     # 最新的日期

            self.logger.info(f"更新最近 {days_back} 天的資料")
            self.download_date_range(start_date, end_date)


def create_update_script():
    """
    建立自動更新腳本
    """
    script_content = '''#!/usr/bin/env python3
"""
台灣期貨交易所資料自動更新腳本

每日定時執行，更新最新的交易資料
"""

import sys
import logging
from pathlib import Path

# 添加專案路徑
sys.path.append(str(Path(__file__).parent.parent))

from scripts.taifex_daily_downloader import TaifexDailyDownloader

def main():
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/taifex_daily_update.log'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)

    try:
        logger.info("開始更新台灣期貨交易所每日資料")

        # 初始化下載器
        downloader = TaifexDailyDownloader(logger)

        # 更新最近30天的資料
        downloader.update_recent_data(days_back=30)

        logger.info("每日資料更新完成")

    except Exception as e:
        logger.error(f"資料更新失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    # 儲存腳本
    scripts_dir = Path(__file__).parent
    with open(scripts_dir / 'taifex_daily_update.py', 'w', encoding='utf-8') as f:
        f.write(script_content)

    print("已建立自動更新腳本: scripts/taifex_daily_update.py")


if __name__ == "__main__":
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 建立更新腳本
    create_update_script()

    # 測試下載器
    downloader = TaifexDailyDownloader()

    # 測試下載最近5天的資料
    print("測試下載最近5天的資料...")
    results = downloader.download_date_range('20241120', '20241126')

    print("\\n測試結果:")
    for data_type, count in results.items():
        print(f"  {data_type}: {count} 個檔案成功下載")

    print("\\n台灣期貨交易所每日下載器測試完成")

















