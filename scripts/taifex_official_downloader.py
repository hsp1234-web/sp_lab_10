#!/usr/bin/env python3
"""
台灣期貨交易所官方資料下載器

支援最新的官方資料格式：
- Put/Call比資料 (使用日期範圍查詢)
- 選擇權每日Delta值
- 期貨每日行情
- 選擇權每日行情
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
from typing import List, Dict, Optional, Tuple
import pandas as pd


class TaifexOfficialDownloader:
    """
    台灣期貨交易所官方資料下載器

    支援最新的官方資料下載格式
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

        # 設定目錄
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data" / "taifex_official"
        self.temp_dir = self.data_dir / "temp"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # 官方下載URL
        self.base_url = "https://www.taifex.com.tw"

        # 設定請求標頭 (模擬瀏覽器)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.taifex.com.tw/cht/3/dlPcRatioDown',
        }

    def download_pcr_data(self, start_date: str, end_date: str) -> bool:
        """
        下載Put/Call比資料

        Args:
            start_date: 開始日期 (YYYY/MM/DD格式)
            end_date: 結束日期 (YYYY/MM/DD格式)

        Returns:
            bool: 下載是否成功
        """
        try:
            self.logger.info(f"下載Put/Call比資料: {start_date} 到 {end_date}")

            # PCR下載URL
            url = f"{self.base_url}/cht/3/dlPcRatioDown"

            # 準備表單資料
            payload = {
                'down_type': '',  # 空的表示使用日期範圍
                'queryStartDate': start_date,
                'queryEndDate': end_date
            }

            self.logger.info(f"請求參數: {payload}")

            # 發送POST請求
            response = requests.post(url, data=payload, headers=self.headers, timeout=60, stream=True)
            response.raise_for_status()

            # 檢查回應內容類型
            content_type = response.headers.get('Content-Type', '')

            # 如果是CSV資料（直接回傳）
            if 'text/csv' in content_type or 'text/html' in content_type or 'ms950' in content_type:
                # 直接處理CSV內容
                csv_content = response.text

                if not csv_content.strip():
                    self.logger.warning("PCR資料為空")
                    return False

                # 儲存CSV檔案
                filename = f"pcr_{start_date.replace('/', '')}_{end_date.replace('/', '')}.csv"
                file_path = self.data_dir / filename

                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    f.write(csv_content)

                self.logger.info(f"Put/Call比資料下載完成: {filename}")

                # 處理CSV資料
                self._process_pcr_csv_file(file_path)

                return True

            # 如果是ZIP檔案
            elif self._is_zip_file(response.content):
                # 處理ZIP檔案的邏輯保持不變
                filename = f"pcr_{start_date.replace('/', '')}_{end_date.replace('/', '')}.zip"
                file_path = self.data_dir / filename

                with open(file_path, 'wb') as f:
                    f.write(response.content)

                file_size = file_path.stat().st_size
                self.logger.info(f"Put/Call比資料下載完成: {filename} ({file_size:,} bytes)")

                self._process_pcr_zip(file_path, start_date, end_date)

                return True
            else:
                self.logger.warning(f"未知的內容類型: {content_type}")
                # 儲存內容以便檢查
                error_file = self.temp_dir / f"pcr_unknown_{start_date.replace('/', '')}_{end_date.replace('/', '')}.txt"
                with open(error_file, 'wb') as f:
                    f.write(response.content)
                self.logger.info(f"未知內容已儲存至: {error_file}")
                return False

            # 產生檔案名稱
            filename = f"pcr_{start_date.replace('/', '')}_{end_date.replace('/', '')}.zip"
            file_path = self.data_dir / filename

            # 儲存檔案
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = file_path.stat().st_size
            self.logger.info(f"Put/Call比資料下載完成: {filename} ({file_size:,} bytes)")

            # 處理下載的資料
            self._process_pcr_zip(file_path, start_date, end_date)

            return True

        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP錯誤 {e.response.status_code}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"下載Put/Call比資料失敗: {e}")
            return False

    def download_options_delta(self, date: str) -> bool:
        """
        下載選擇權每日Delta值

        Args:
            date: 日期 (YYYYMMDD格式)

        Returns:
            bool: 下載是否成功
        """
        try:
            self.logger.info(f"下載選擇權Delta值: {date}")

            # Delta值下載URL
            url = f"{self.base_url}/cht/3/dlOptDailyDelta"

            # 準備表單資料
            payload = {
                'down_type': '2',  # 每日下載類型
                'queryDate': date
            }

            # 更新Referer
            headers = self.headers.copy()
            headers['Referer'] = f'{self.base_url}/cht/3/dlOptDailyDelta'

            # 發送POST請求
            response = requests.post(url, data=payload, headers=headers, timeout=60, stream=True)
            response.raise_for_status()

            # 檢查回應內容類型
            content_type = response.headers.get('Content-Type', '')

            # 如果是CSV資料（直接回傳）
            if 'text/csv' in content_type or 'text/html' in content_type or 'ms950' in content_type:
                # 直接處理CSV內容
                csv_content = response.text

                if not csv_content.strip():
                    self.logger.warning(f"選擇權Delta值資料為空: {date}")
                    return False

                # 儲存CSV檔案
                filename = f"options_delta_{date}.csv"
                file_path = self.data_dir / filename

                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    f.write(csv_content)

                self.logger.info(f"選擇權Delta值下載完成: {filename}")

                # 處理CSV資料
                self._process_options_delta_csv_file(file_path)

                return True

            # 如果是ZIP檔案
            elif self._is_zip_file(response.content):
                # 處理ZIP檔案的邏輯保持不變
                filename = f"options_delta_{date}.zip"
                file_path = self.data_dir / filename

                with open(file_path, 'wb') as f:
                    f.write(response.content)

                file_size = file_path.stat().st_size
                self.logger.info(f"選擇權Delta值下載完成: {filename} ({file_size:,} bytes)")

                self._process_options_delta_zip(file_path, date)

                return True
            else:
                self.logger.warning(f"未知的內容類型: {content_type} - {date}")
                # 儲存內容以便檢查
                error_file = self.temp_dir / f"delta_unknown_{date}.txt"
                with open(error_file, 'wb') as f:
                    f.write(response.content)
                self.logger.info(f"未知內容已儲存至: {error_file}")
                return False

            return True

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.info(f"選擇權Delta值資料不存在: {date} (可能是非交易日)")
            else:
                self.logger.error(f"HTTP錯誤 {e.response.status_code}: {date}")
            return False
        except Exception as e:
            self.logger.error(f"下載選擇權Delta值失敗: {e}")
            return False

    def download_daily_futures(self, date: str) -> bool:
        """
        下載期貨每日行情

        Args:
            date: 日期 (YYYYMMDD格式)

        Returns:
            bool: 下載是否成功
        """
        try:
            self.logger.info(f"下載期貨每日行情: {date}")

            # 期貨每日行情下載URL
            url = f"{self.base_url}/cht/3/dlFutDailyMarketView"

            # 準備表單資料
            payload = {
                'down_type': '2',  # 每日下載
                'queryDate': date
            }

            headers = self.headers.copy()
            headers['Referer'] = f'{self.base_url}/cht/3/dlFutDailyMarketView'

            response = requests.post(url, data=payload, headers=headers, timeout=60, stream=True)
            response.raise_for_status()

            if not self._is_zip_file(response.content):
                self.logger.warning(f"期貨每日行情下載失敗: {date}")
                return False

            filename = f"futures_daily_{date}.zip"
            file_path = self.data_dir / filename

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = file_path.stat().st_size
            self.logger.info(f"期貨每日行情下載完成: {filename} ({file_size:,} bytes)")

            self._process_futures_zip(file_path, date)

            return True

        except Exception as e:
            self.logger.error(f"下載期貨每日行情失敗: {e}")
            return False

    def download_daily_options(self, date: str) -> bool:
        """
        下載選擇權每日行情

        Args:
            date: 日期 (YYYYMMDD格式)

        Returns:
            bool: 下載是否成功
        """
        try:
            self.logger.info(f"下載選擇權每日行情: {date}")

            url = f"{self.base_url}/cht/3/dlOptDailyMarketView"

            payload = {
                'down_type': '2',  # 每日下載
                'queryDate': date
            }

            headers = self.headers.copy()
            headers['Referer'] = f'{self.base_url}/cht/3/dlOptDailyMarketView'

            response = requests.post(url, data=payload, headers=headers, timeout=60, stream=True)
            response.raise_for_status()

            if not self._is_zip_file(response.content):
                self.logger.warning(f"選擇權每日行情下載失敗: {date}")
                return False

            filename = f"options_daily_{date}.zip"
            file_path = self.data_dir / filename

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = file_path.stat().st_size
            self.logger.info(f"選擇權每日行情下載完成: {filename} ({file_size:,} bytes)")

            self._process_options_zip(file_path, date)

            return True

        except Exception as e:
            self.logger.error(f"下載選擇權每日行情失敗: {e}")
            return False

    def download_institutional_data(self, date: str) -> bool:
        """
        下載三大法人資料

        Args:
            date: 日期 (YYYYMMDD格式)

        Returns:
            bool: 下載是否成功
        """
        try:
            self.logger.info(f"下載三大法人資料: {date}")

            url = f"{self.base_url}/cht/3/dl3InstiiDown"

            payload = {
                'down_type': '2',  # 每日下載
                'queryDate': date
            }

            headers = self.headers.copy()
            headers['Referer'] = f'{self.base_url}/cht/3/dl3InstiiDown'

            response = requests.post(url, data=payload, headers=headers, timeout=60, stream=True)
            response.raise_for_status()

            if not self._is_zip_file(response.content):
                self.logger.warning(f"三大法人資料下載失敗: {date}")
                return False

            filename = f"institutional_{date}.zip"
            file_path = self.data_dir / filename

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = file_path.stat().st_size
            self.logger.info(f"三大法人資料下載完成: {filename} ({file_size:,} bytes)")

            self._process_institutional_zip(file_path, date)

            return True

        except Exception as e:
            self.logger.error(f"下載三大法人資料失敗: {e}")
            return False

    def _is_zip_file(self, content: bytes) -> bool:
        """檢查是否為ZIP檔案"""
        return len(content) >= 4 and content[:4] == b'PK\x03\x04'

    def _process_pcr_csv_file(self, csv_path: Path):
        """處理PCR CSV檔案"""
        try:
            # 讀取CSV內容
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            # 如果內容看起來像CSV資料
            if ',' in content and '\n' in content:
                # 儲存處理後的檔案
                processed_file = self.data_dir / f"processed_{csv_path.name}"
                # 複製檔案（已經是處理過的格式）
                import shutil
                shutil.copy2(csv_path, processed_file)

                self.logger.info(f"PCR CSV檔案處理完成: {processed_file.name}")

                # 清理原始檔案
                csv_path.unlink()

        except Exception as e:
            self.logger.error(f"處理PCR CSV檔案失敗: {e}")

    def _process_pcr_zip(self, zip_path: Path, start_date: str, end_date: str):
        """處理PCR ZIP檔案"""
        try:
            extract_dir = self.temp_dir / f"pcr_{start_date.replace('/', '')}_{end_date.replace('/', '')}"
            extract_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)

            # 處理CSV檔案
            for csv_file in extract_dir.glob("*.csv"):
                self._process_pcr_csv(csv_file)

            # 清理
            import shutil
            shutil.rmtree(extract_dir)
            zip_path.unlink()

        except Exception as e:
            self.logger.error(f"處理PCR ZIP檔案失敗: {e}")

    def _process_options_delta_zip(self, zip_path: Path, date: str):
        """處理選擇權Delta值 ZIP檔案"""
        try:
            extract_dir = self.temp_dir / f"delta_{date}"
            extract_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)

            for csv_file in extract_dir.glob("*.csv"):
                self._process_options_delta_csv(csv_file)

            # 清理
            import shutil
            shutil.rmtree(extract_dir)
            zip_path.unlink()

        except Exception as e:
            self.logger.error(f"處理選擇權Delta值 ZIP檔案失敗: {e}")

    def _process_futures_zip(self, zip_path: Path, date: str):
        """處理期貨每日行情 ZIP檔案"""
        try:
            extract_dir = self.temp_dir / f"futures_{date}"
            extract_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)

            for csv_file in extract_dir.glob("*.csv"):
                self._process_futures_csv(csv_file)

            # 清理
            import shutil
            shutil.rmtree(extract_dir)
            zip_path.unlink()

        except Exception as e:
            self.logger.error(f"處理期貨每日行情 ZIP檔案失敗: {e}")

    def _process_options_zip(self, zip_path: Path, date: str):
        """處理選擇權每日行情 ZIP檔案"""
        try:
            extract_dir = self.temp_dir / f"options_{date}"
            extract_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)

            for csv_file in extract_dir.glob("*.csv"):
                self._process_options_csv(csv_file)

            # 清理
            import shutil
            shutil.rmtree(extract_dir)
            zip_path.unlink()

        except Exception as e:
            self.logger.error(f"處理選擇權每日行情 ZIP檔案失敗: {e}")

    def _process_institutional_zip(self, zip_path: Path, date: str):
        """處理三大法人資料 ZIP檔案"""
        try:
            extract_dir = self.temp_dir / f"institutional_{date}"
            extract_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)

            for csv_file in extract_dir.glob("*.csv"):
                self._process_institutional_csv(csv_file)

            # 清理
            import shutil
            shutil.rmtree(extract_dir)
            zip_path.unlink()

        except Exception as e:
            self.logger.error(f"處理三大法人資料 ZIP檔案失敗: {e}")

    def _process_pcr_csv(self, csv_path: Path):
        """處理PCR CSV檔案"""
        try:
            # 嘗試不同的編碼
            encodings = ['utf-8-sig', 'big5', 'cp950']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None or df.empty:
                self.logger.warning(f"無法讀取PCR CSV檔案: {csv_path}")
                return

            # 儲存處理後的資料
            processed_file = self.data_dir / f"processed_pcr_{csv_path.stem}.csv"
            df.to_csv(processed_file, index=False, encoding='utf-8-sig')

            self.logger.info(f"PCR資料處理完成: {processed_file.name}")

        except Exception as e:
            self.logger.error(f"處理PCR CSV檔案失敗: {e}")

    def _process_options_delta_csv_file(self, csv_path: Path):
        """處理選擇權Delta值 CSV檔案"""
        try:
            # 讀取CSV內容
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            # 如果內容看起來像CSV資料
            if ',' in content and '\n' in content:
                # 儲存處理後的檔案
                processed_file = self.data_dir / f"processed_{csv_path.name}"
                # 複製檔案（已經是處理過的格式）
                import shutil
                shutil.copy2(csv_path, processed_file)

                self.logger.info(f"選擇權Delta值CSV檔案處理完成: {processed_file.name}")

                # 清理原始檔案
                csv_path.unlink()

        except Exception as e:
            self.logger.error(f"處理選擇權Delta值CSV檔案失敗: {e}")

    def _process_options_delta_csv(self, csv_path: Path):
        """處理選擇權Delta值 CSV檔案"""
        try:
            encodings = ['utf-8-sig', 'big5', 'cp950']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None or df.empty:
                self.logger.warning(f"無法讀取選擇權Delta值 CSV檔案: {csv_path}")
                return

            # 儲存處理後的資料
            processed_file = self.data_dir / f"processed_delta_{csv_path.stem}.csv"
            df.to_csv(processed_file, index=False, encoding='utf-8-sig')

            self.logger.info(f"選擇權Delta值資料處理完成: {processed_file.name}")

        except Exception as e:
            self.logger.error(f"處理選擇權Delta值 CSV檔案失敗: {e}")

    def _process_futures_csv(self, csv_path: Path):
        """處理期貨每日行情 CSV檔案"""
        try:
            encodings = ['utf-8-sig', 'big5', 'cp950']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None or df.empty:
                self.logger.warning(f"無法讀取期貨每日行情 CSV檔案: {csv_path}")
                return

            # 儲存處理後的資料
            processed_file = self.data_dir / f"processed_futures_{csv_path.stem}.csv"
            df.to_csv(processed_file, index=False, encoding='utf-8-sig')

            self.logger.info(f"期貨每日行情資料處理完成: {processed_file.name}")

        except Exception as e:
            self.logger.error(f"處理期貨每日行情 CSV檔案失敗: {e}")

    def _process_options_csv(self, csv_path: Path):
        """處理選擇權每日行情 CSV檔案"""
        try:
            encodings = ['utf-8-sig', 'big5', 'cp950']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None or df.empty:
                self.logger.warning(f"無法讀取選擇權每日行情 CSV檔案: {csv_path}")
                return

            # 儲存處理後的資料
            processed_file = self.data_dir / f"processed_options_{csv_path.stem}.csv"
            df.to_csv(processed_file, index=False, encoding='utf-8-sig')

            self.logger.info(f"選擇權每日行情資料處理完成: {processed_file.name}")

        except Exception as e:
            self.logger.error(f"處理選擇權每日行情 CSV檔案失敗: {e}")

    def _process_institutional_csv(self, csv_path: Path):
        """處理三大法人資料 CSV檔案"""
        try:
            encodings = ['utf-8-sig', 'big5', 'cp950']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None or df.empty:
                self.logger.warning(f"無法讀取三大法人資料 CSV檔案: {csv_path}")
                return

            # 儲存處理後的資料
            processed_file = self.data_dir / f"processed_institutional_{csv_path.stem}.csv"
            df.to_csv(processed_file, index=False, encoding='utf-8-sig')

            self.logger.info(f"三大法人資料處理完成: {processed_file.name}")

        except Exception as e:
            self.logger.error(f"處理三大法人資料 CSV檔案失敗: {e}")

    def download_recent_data(self, days_back: int = 30):
        """
        下載最近的資料

        Args:
            days_back: 回溯天數
        """
        self.logger.info(f"開始下載最近 {days_back} 天的資料")

        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # 轉換為台灣期貨交易所的日期格式
        start_str = start_date.strftime('%Y/%m/%d')
        end_str = end_date.strftime('%Y/%m/%d')

        # 下載PCR資料 (使用日期範圍)
        self.logger.info("下載Put/Call比資料...")
        self.download_pcr_data(start_str, end_str)

        # 下載每日資料
        current = start_date
        while current <= end_date:
            date_str = current.strftime('%Y%m%d')

            # 檢查是否為交易日 (跳過週六日)
            if current.weekday() < 5:
                self.logger.info(f"處理交易日: {date_str}")

                # 下載各類型資料
                self.download_daily_futures(date_str)
                self.download_daily_options(date_str)
                self.download_options_delta(date_str)
                self.download_institutional_data(date_str)

                # 禮貌性延遲
                time.sleep(2)

            current += timedelta(days=1)

        self.logger.info("最近資料下載完成")


def create_update_script():
    """建立自動更新腳本"""
    script_content = '''#!/usr/bin/env python3
"""
台灣期貨交易所官方資料自動更新腳本

每日定時執行，更新最新的交易資料
"""

import sys
import logging
from pathlib import Path

# 添加專案路徑
sys.path.append(str(Path(__file__).parent.parent))

from scripts.taifex_official_downloader import TaifexOfficialDownloader

def main():
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/taifex_official_update.log'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)

    try:
        logger.info("開始更新台灣期貨交易所官方資料")

        # 初始化下載器
        downloader = TaifexOfficialDownloader(logger)

        # 更新最近30天的資料
        downloader.download_recent_data(days_back=30)

        logger.info("官方資料更新完成")

    except Exception as e:
        logger.error(f"資料更新失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    # 儲存腳本
    scripts_dir = Path(__file__).parent
    with open(scripts_dir / 'taifex_official_update.py', 'w', encoding='utf-8') as f:
        f.write(script_content)

    print("已建立自動更新腳本: scripts/taifex_official_update.py")


if __name__ == "__main__":
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 建立更新腳本
    create_update_script()

    # 測試下載器
    downloader = TaifexOfficialDownloader()

    print("測試台灣期貨交易所官方資料下載器...")

    # 測試PCR資料下載
    print("\\n測試Put/Call比資料下載...")
    pcr_result = downloader.download_pcr_data('2025/10/28', '2025/11/27')
    print(f"PCR資料下載: {'成功' if pcr_result else '失敗'}")

    # 測試選擇權Delta值下載
    print("\\n測試選擇權Delta值下載...")
    delta_result = downloader.download_options_delta('20241126')
    print(f"選擇權Delta值下載: {'成功' if delta_result else '失敗'}")

    print("\\n台灣期貨交易所官方資料下載器測試完成")
    print("\\n可用指令:")
    print("- python scripts/taifex_official_downloader.py  # 測試所有功能")
    print("- python scripts/taifex_official_update.py     # 自動更新最近資料")
