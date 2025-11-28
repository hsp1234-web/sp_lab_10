"""
台灣期貨交易所官方資料整合模組

整合台灣期貨交易所提供的免費官方資料：
- 期貨每日行情
- 選擇權每日行情
- Put/Call比
- 三大法人資料
- 每筆成交資料
"""

import pandas as pd
import requests
import zipfile
import io
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import duckdb


class TaifexDataIntegrator:
    """
    台灣期貨交易所資料整合器

    主要功能：
    1. 下載官方免費資料
    2. 解析並標準化資料格式
    3. 整合到本地資料庫
    4. 提供統一的查詢介面
    """

    def __init__(self, data_dir: str = "data/taifex_official", logger: Optional[logging.Logger] = None):
        self.data_dir = data_dir
        self.logger = logger or logging.getLogger(__name__)

        # 建立資料目錄
        os.makedirs(data_dir, exist_ok=True)

        # 官方資料下載URL
        self.base_url = "https://www.taifex.com.tw/file/taifex/Dailydownload"

        # 資料庫連接
        self.db_path = "data/taifex_official.db"
        self.conn = duckdb.connect(self.db_path)

        # 初始化資料庫表格
        self._init_database()

    def _init_database(self):
        """初始化資料庫表格"""
        try:
            # 期貨資料表
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS futures_daily (
                    date VARCHAR,
                    symbol VARCHAR,
                    open DOUBLE,
                    high DOUBLE,
                    low DOUBLE,
                    close DOUBLE,
                    volume DOUBLE,
                    settlement_price DOUBLE,
                    open_interest DOUBLE,
                    PRIMARY KEY (date, symbol)
                )
            """)

            # 選擇權資料表
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS options_daily (
                    date VARCHAR,
                    symbol VARCHAR,
                    expiry VARCHAR,
                    strike_price DOUBLE,
                    option_type VARCHAR,
                    open DOUBLE,
                    high DOUBLE,
                    low DOUBLE,
                    close DOUBLE,
                    volume DOUBLE,
                    settlement_price DOUBLE,
                    open_interest DOUBLE,
                    delta DOUBLE,
                    PRIMARY KEY (date, symbol, expiry, strike_price, option_type)
                )
            """)

            # Put/Call比資料表
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS pcr_ratio (
                    date VARCHAR,
                    symbol VARCHAR,
                    call_volume DOUBLE,
                    put_volume DOUBLE,
                    pcr_ratio DOUBLE,
                    PRIMARY KEY (date, symbol)
                )
            """)

            # 三大法人資料表
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS institutional_investors (
                    date VARCHAR,
                    investor_type VARCHAR,
                    long_position DOUBLE,
                    short_position DOUBLE,
                    net_position DOUBLE,
                    PRIMARY KEY (date, investor_type)
                )
            """)

            self.logger.info("資料庫初始化完成")

        except Exception as e:
            self.logger.error(f"資料庫初始化失敗: {e}")
            raise

    def download_futures_data(self, date: str) -> bool:
        """
        下載指定日期的期貨資料

        Args:
            date: 日期字串 (YYYYMMDD格式)

        Returns:
            bool: 下載是否成功
        """
        try:
            # 期貨每日行情下載URL
            url = f"{self.base_url}/CSV/Daily_{date}.zip"

            self.logger.info(f"下載期貨資料: {date}")

            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                self.logger.warning(f"無法下載期貨資料: {date}")
                return False

            # 解析ZIP檔案
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                for filename in zf.namelist():
                    if filename.endswith('.csv'):
                        with zf.open(filename) as f:
                            df = pd.read_csv(f, encoding='big5')

                            # 標準化欄位名稱
                            df = self._standardize_futures_columns(df)

                            # 新增日期欄位
                            df['date'] = date

                            # 儲存到資料庫
                            self._save_futures_data(df)

            return True

        except Exception as e:
            self.logger.error(f"下載期貨資料失敗: {e}")
            return False

    def download_options_data(self, date: str) -> bool:
        """
        下載指定日期的選擇權資料
        """
        try:
            # 選擇權每日行情下載URL
            url = f"{self.base_url}/OPTIONCSV/Daily_{date}.zip"

            self.logger.info(f"下載選擇權資料: {date}")

            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                self.logger.warning(f"無法下載選擇權資料: {date}")
                return False

            # 解析ZIP檔案
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                for filename in zf.namelist():
                    if filename.endswith('.csv'):
                        with zf.open(filename) as f:
                            df = pd.read_csv(f, encoding='big5')

                            # 標準化欄位名稱
                            df = self._standardize_options_columns(df)

                            # 新增日期欄位
                            df['date'] = date

                            # 儲存到資料庫
                            self._save_options_data(df)

            return True

        except Exception as e:
            self.logger.error(f"下載選擇權資料失敗: {e}")
            return False

    def download_pcr_data(self, date: str) -> bool:
        """
        下載Put/Call比資料
        """
        try:
            # PCR資料下載URL
            url = f"{self.base_url}/PCSV/Daily_{date}.zip"

            self.logger.info(f"下載PCR資料: {date}")

            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                self.logger.warning(f"無法下載PCR資料: {date}")
                return False

            # 解析ZIP檔案
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                for filename in zf.namelist():
                    if filename.endswith('.csv'):
                        with zf.open(filename) as f:
                            df = pd.read_csv(f, encoding='big5')

                            # 處理PCR資料
                            pcr_data = self._process_pcr_data(df, date)

                            # 儲存到資料庫
                            self._save_pcr_data(pcr_data)

            return True

        except Exception as e:
            self.logger.error(f"下載PCR資料失敗: {e}")
            return False

    def _standardize_futures_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """標準化期貨資料欄位名稱"""
        column_mapping = {
            '商品代號': 'symbol',
            '開盤價': 'open',
            '最高價': 'high',
            '最低價': 'low',
            '收盤價': 'close',
            '成交量': 'volume',
            '結算價': 'settlement_price',
            '未沖銷契約數': 'open_interest'
        }

        df = df.rename(columns=column_mapping)

        # 保留必要的欄位
        required_cols = ['symbol', 'open', 'high', 'low', 'close', 'volume', 'settlement_price', 'open_interest']
        df = df[required_cols]

        return df

    def _standardize_options_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """標準化選擇權資料欄位名稱"""
        column_mapping = {
            '商品代號': 'symbol',
            '到期月份(週別)': 'expiry',
            '履約價': 'strike_price',
            '買賣權': 'option_type',
            '開盤價': 'open',
            '最高價': 'high',
            '最低價': 'low',
            '收盤價': 'close',
            '成交量': 'volume',
            '結算價': 'settlement_price',
            '未沖銷契約數': 'open_interest',
            'Delta': 'delta'
        }

        df = df.rename(columns=column_mapping)

        # 處理選擇權類型
        df['option_type'] = df['option_type'].map({'買權': 'Call', '賣權': 'Put'})

        # 保留必要的欄位
        required_cols = ['symbol', 'expiry', 'strike_price', 'option_type',
                        'open', 'high', 'low', 'close', 'volume',
                        'settlement_price', 'open_interest', 'delta']
        df = df[required_cols]

        return df

    def _process_pcr_data(self, df: pd.DataFrame, date: str) -> List[Dict]:
        """處理PCR資料"""
        pcr_records = []

        try:
            # 假設資料格式包含買權和賣權的成交量
            # 這裡需要根據實際資料格式調整
            for _, row in df.iterrows():
                record = {
                    'date': date,
                    'symbol': row.get('商品代號', ''),
                    'call_volume': row.get('買權成交量', 0),
                    'put_volume': row.get('賣權成交量', 0),
                    'pcr_ratio': row.get('賣權成交量', 0) / max(row.get('買權成交量', 1), 1)
                }
                pcr_records.append(record)

        except Exception as e:
            self.logger.error(f"處理PCR資料失敗: {e}")

        return pcr_records

    def _save_futures_data(self, df: pd.DataFrame):
        """儲存期貨資料到資料庫"""
        try:
            # 使用INSERT OR REPLACE處理重複資料
            for _, row in df.iterrows():
                self.conn.execute("""
                    INSERT OR REPLACE INTO futures_daily
                    (date, symbol, open, high, low, close, volume, settlement_price, open_interest)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['date'], row['symbol'], row['open'], row['high'], row['low'],
                    row['close'], row['volume'], row['settlement_price'], row['open_interest']
                ))

        except Exception as e:
            self.logger.error(f"儲存期貨資料失敗: {e}")

    def _save_options_data(self, df: pd.DataFrame):
        """儲存選擇權資料到資料庫"""
        try:
            for _, row in df.iterrows():
                self.conn.execute("""
                    INSERT OR REPLACE INTO options_daily
                    (date, symbol, expiry, strike_price, option_type, open, high, low, close,
                     volume, settlement_price, open_interest, delta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['date'], row['symbol'], row['expiry'], row['strike_price'], row['option_type'],
                    row['open'], row['high'], row['low'], row['close'], row['volume'],
                    row['settlement_price'], row['open_interest'], row['delta']
                ))

        except Exception as e:
            self.logger.error(f"儲存選擇權資料失敗: {e}")

    def _save_pcr_data(self, pcr_records: List[Dict]):
        """儲存PCR資料到資料庫"""
        try:
            for record in pcr_records:
                self.conn.execute("""
                    INSERT OR REPLACE INTO pcr_ratio
                    (date, symbol, call_volume, put_volume, pcr_ratio)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    record['date'], record['symbol'],
                    record['call_volume'], record['put_volume'], record['pcr_ratio']
                ))

        except Exception as e:
            self.logger.error(f"儲存PCR資料失敗: {e}")

    def get_futures_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """查詢期貨資料"""
        try:
            query = """
                SELECT * FROM futures_daily
                WHERE symbol = ? AND date BETWEEN ? AND ?
                ORDER BY date
            """

            df = self.conn.execute(query, [symbol, start_date, end_date]).fetchdf()
            return df

        except Exception as e:
            self.logger.error(f"查詢期貨資料失敗: {e}")
            return pd.DataFrame()

    def get_options_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """查詢選擇權資料"""
        try:
            query = """
                SELECT * FROM options_daily
                WHERE symbol = ? AND date BETWEEN ? AND ?
                ORDER BY date, expiry, strike_price
            """

            df = self.conn.execute(query, [symbol, start_date, end_date]).fetchdf()
            return df

        except Exception as e:
            self.logger.error(f"查詢選擇權資料失敗: {e}")
            return pd.DataFrame()

    def get_pcr_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """查詢PCR資料"""
        try:
            query = """
                SELECT * FROM pcr_ratio
                WHERE symbol = ? AND date BETWEEN ? AND ?
                ORDER BY date
            """

            df = self.conn.execute(query, [symbol, start_date, end_date]).fetchdf()
            return df

        except Exception as e:
            self.logger.error(f"查詢PCR資料失敗: {e}")
            return pd.DataFrame()

    def bulk_download_historical_data(self, start_date: str, end_date: str, data_types: List[str] = None):
        """
        批量下載歷史資料

        Args:
            start_date: 開始日期 (YYYYMMDD)
            end_date: 結束日期 (YYYYMMDD)
            data_types: 要下載的資料類型 ['futures', 'options', 'pcr']
        """
        if data_types is None:
            data_types = ['futures', 'options', 'pcr']

        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        current = start

        success_count = 0
        total_count = 0

        while current <= end:
            date_str = current.strftime('%Y%m%d')

            # 檢查是否為交易日 (簡單檢查，實際應查詢交易日曆)
            if current.weekday() < 5:  # 週一到週五
                total_count += len(data_types)

                for data_type in data_types:
                    try:
                        if data_type == 'futures':
                            if self.download_futures_data(date_str):
                                success_count += 1
                        elif data_type == 'options':
                            if self.download_options_data(date_str):
                                success_count += 1
                        elif data_type == 'pcr':
                            if self.download_pcr_data(date_str):
                                success_count += 1

                        self.logger.info(f"進度: {success_count}/{total_count}")

                    except Exception as e:
                        self.logger.error(f"下載 {data_type} 資料失敗 ({date_str}): {e}")

            current += timedelta(days=1)

        self.logger.info(f"批量下載完成: {success_count}/{total_count} 成功")


def create_data_update_script():
    """
    建立自動資料更新腳本
    """
    script_content = '''#!/usr/bin/env python3
"""
台灣期貨交易所資料自動更新腳本

每日定時執行，更新最新的交易資料
"""

import sys
import os
from datetime import datetime, timedelta
import logging

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.taifex_data_integration import TaifexDataIntegrator

def main():
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/taifex_data_update.log'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)

    try:
        logger.info("開始更新台灣期貨交易所資料")

        # 初始化整合器
        integrator = TaifexDataIntegrator()

        # 更新最近30天的資料
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')

        # 下載所有資料類型
        integrator.bulk_download_historical_data(
            start_str, end_str,
            data_types=['futures', 'options', 'pcr']
        )

        logger.info("資料更新完成")

    except Exception as e:
        logger.error(f"資料更新失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    # 儲存腳本
    os.makedirs('scripts', exist_ok=True)
    with open('scripts/update_taifex_data.py', 'w', encoding='utf-8') as f:
        f.write(script_content)

    # 設定執行權限
    os.chmod('scripts/update_taifex_data.py', 0o755)


if __name__ == "__main__":
    # 建立資料更新腳本
    create_data_update_script()

    # 使用範例
    integrator = TaifexDataIntegrator()

    # 測試單日資料下載
    test_date = "20241201"  # 請根據實際交易日調整

    print("測試資料下載...")
    integrator.download_futures_data(test_date)
    integrator.download_options_data(test_date)
    integrator.download_pcr_data(test_date)

    print("測試資料查詢...")
    futures_data = integrator.get_futures_data("TX", "20241201", "20241201")
    print(f"期貨資料筆數: {len(futures_data)}")

    options_data = integrator.get_options_data("TXO", "20241201", "20241201")
    print(f"選擇權資料筆數: {len(options_data)}")

    pcr_data = integrator.get_pcr_data("TXO", "20241201", "20241201")
    print(f"PCR資料筆數: {len(pcr_data)}")

    print("台灣期貨交易所資料整合模組測試完成")



