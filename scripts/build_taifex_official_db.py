#!/usr/bin/env python3
"""
台灣期貨交易所官方資料資料庫建置腳本

將下載的官方資料整合到DuckDB資料庫中：
- Put/Call比資料
- 選擇權Delta值
- 期貨每日行情
- 選擇權每日行情
- 三大法人資料
"""

import sys
import os
import pandas as pd
import duckdb
from pathlib import Path
import logging
from typing import Dict, List, Optional
import glob


class TaifexOfficialDBBuilder:
    """
    台灣期貨交易所官方資料資料庫建置器
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

        # 設定路徑
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data" / "taifex_official"
        self.db_path = self.project_root / "data" / "taifex_official.db"

        # 初始化資料庫
        self._init_database()

    def _init_database(self):
        """初始化資料庫表格"""
        try:
            conn = duckdb.connect(str(self.db_path))

            # Put/Call比資料表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pcr_data (
                    date VARCHAR,
                    symbol VARCHAR,
                    call_volume DOUBLE,
                    put_volume DOUBLE,
                    pcr_ratio DOUBLE,
                    total_volume DOUBLE,
                    call_open_interest DOUBLE,
                    put_open_interest DOUBLE,
                    pcr_open_interest DOUBLE,
                    PRIMARY KEY (date, symbol)
                )
            """)

            # 選擇權Delta值資料表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS options_delta (
                    date VARCHAR,
                    symbol VARCHAR,
                    expiry VARCHAR,
                    strike_price DOUBLE,
                    option_type VARCHAR,
                    delta DOUBLE,
                    gamma DOUBLE,
                    theta DOUBLE,
                    vega DOUBLE,
                    rho DOUBLE,
                    PRIMARY KEY (date, symbol, expiry, strike_price, option_type)
                )
            """)

            # 期貨每日行情資料表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS futures_daily (
                    date VARCHAR,
                    symbol VARCHAR,
                    expiry VARCHAR,
                    open DOUBLE,
                    high DOUBLE,
                    low DOUBLE,
                    close DOUBLE,
                    volume DOUBLE,
                    settlement_price DOUBLE,
                    open_interest DOUBLE,
                    change DOUBLE,
                    change_percent DOUBLE,
                    PRIMARY KEY (date, symbol, expiry)
                )
            """)

            # 選擇權每日行情資料表
            conn.execute("""
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
                    best_bid DOUBLE,
                    best_ask DOUBLE,
                    PRIMARY KEY (date, symbol, expiry, strike_price, option_type)
                )
            """)

            # 三大法人資料表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS institutional_investors (
                    date VARCHAR,
                    investor_type VARCHAR,
                    futures_long DOUBLE,
                    futures_short DOUBLE,
                    futures_net DOUBLE,
                    options_long DOUBLE,
                    options_short DOUBLE,
                    options_net DOUBLE,
                    total_long DOUBLE,
                    total_short DOUBLE,
                    total_net DOUBLE,
                    PRIMARY KEY (date, investor_type)
                )
            """)

            conn.close()

            self.logger.info("官方資料庫初始化完成")

        except Exception as e:
            self.logger.error(f"資料庫初始化失敗: {e}")
            raise

    def build_pcr_database(self):
        """建置Put/Call比資料庫"""
        try:
            self.logger.info("建置Put/Call比資料庫...")

            # 尋找所有PCR資料檔案
            pcr_pattern = str(self.data_dir / "processed_pcr_*.csv")
            pcr_files = glob.glob(pcr_pattern)

            if not pcr_files:
                self.logger.warning("未找到PCR資料檔案")
                return

            conn = duckdb.connect(str(self.db_path))
            total_imported = 0

            for csv_file in pcr_files:
                try:
                    self.logger.info(f"處理檔案: {Path(csv_file).name}")

                    # 讀取CSV檔案
                    df = pd.read_csv(csv_file, encoding='utf-8-sig')

                    if df.empty:
                        continue

                    # 標準化欄位名稱 (根據實際資料格式調整)
                    column_mapping = {
                        '日期': 'date',
                        '買權成交量': 'call_volume',
                        '賣權成交量': 'put_volume',
                        '買賣權成交量比率%': 'pcr_ratio',
                        '買權未平倉量': 'call_open_interest',
                        '賣權未平倉量': 'put_open_interest',
                        '買賣權未平倉量比率%': 'pcr_open_interest'
                    }

                    df = df.rename(columns=column_mapping)

                    # 計算總成交量 (如果沒有直接提供)
                    if 'total_volume' not in df.columns:
                        df['total_volume'] = df['call_volume'] + df['put_volume']

                    # 確保symbol欄位存在 (PCR資料可能沒有契約代號，使用預設值)
                    if 'symbol' not in df.columns:
                        df['symbol'] = 'TXO'  # 台灣指數選擇權預設值

                    # 確保必要的欄位
                    required_cols = ['date', 'symbol', 'call_volume', 'put_volume', 'pcr_ratio',
                                   'total_volume', 'call_open_interest', 'put_open_interest', 'pcr_open_interest']

                    # 過濾出存在的欄位
                    existing_cols = [col for col in required_cols if col in df.columns]
                    df = df[existing_cols]

                    if not df.empty:
                        # 匯入資料庫
                        conn.execute("INSERT OR REPLACE INTO pcr_data SELECT * FROM df")

                        total_imported += len(df)
                        self.logger.info(f"已匯入 {len(df)} 筆PCR資料")

                except Exception as e:
                    self.logger.error(f"處理PCR檔案失敗 {csv_file}: {e}")

            conn.close()

            self.logger.info(f"Put/Call比資料庫建置完成，共匯入 {total_imported} 筆資料")

        except Exception as e:
            self.logger.error(f"建置Put/Call比資料庫失敗: {e}")

    def build_options_delta_database(self):
        """建置選擇權Delta值資料庫"""
        try:
            self.logger.info("建置選擇權Delta值資料庫...")

            # 尋找所有Delta資料檔案
            delta_pattern = str(self.data_dir / "processed_delta_*.csv")
            delta_files = glob.glob(delta_pattern)

            if not delta_files:
                self.logger.warning("未找到選擇權Delta值資料檔案")
                return

            conn = duckdb.connect(str(self.db_path))
            total_imported = 0

            for csv_file in delta_files:
                try:
                    self.logger.info(f"處理檔案: {Path(csv_file).name}")

                    df = pd.read_csv(csv_file, encoding='utf-8-sig')

                    if df.empty:
                        continue

                    # 標準化欄位名稱
                    column_mapping = {
                        '交易日期': 'date',
                        '契約代號': 'symbol',
                        '到期月份': 'expiry',
                        '履約價': 'strike_price',
                        '買賣權': 'option_type',
                        'Delta': 'delta',
                        'Gamma': 'gamma',
                        'Theta': 'theta',
                        'Vega': 'vega',
                        'Rho': 'rho'
                    }

                    df = df.rename(columns=column_mapping)

                    # 處理選擇權類型
                    if 'option_type' in df.columns:
                        df['option_type'] = df['option_type'].map({
                            '買權': 'Call',
                            '賣權': 'Put',
                            'C': 'Call',
                            'P': 'Put'
                        })

                    # 確保必要的欄位
                    required_cols = ['date', 'symbol', 'expiry', 'strike_price', 'option_type',
                                   'delta', 'gamma', 'theta', 'vega', 'rho']

                    existing_cols = [col for col in required_cols if col in df.columns]
                    df = df[existing_cols]

                    if not df.empty:
                        conn.execute("INSERT OR REPLACE INTO options_delta SELECT * FROM df")

                        total_imported += len(df)
                        self.logger.info(f"已匯入 {len(df)} 筆Delta資料")

                except Exception as e:
                    self.logger.error(f"處理Delta檔案失敗 {csv_file}: {e}")

            conn.close()

            self.logger.info(f"選擇權Delta值資料庫建置完成，共匯入 {total_imported} 筆資料")

        except Exception as e:
            self.logger.error(f"建置選擇權Delta值資料庫失敗: {e}")

    def build_futures_daily_database(self):
        """建置期貨每日行情資料庫"""
        try:
            self.logger.info("建置期貨每日行情資料庫...")

            futures_pattern = str(self.data_dir / "processed_futures_*.csv")
            futures_files = glob.glob(futures_pattern)

            if not futures_files:
                self.logger.warning("未找到期貨每日行情資料檔案")
                return

            conn = duckdb.connect(str(self.db_path))
            total_imported = 0

            for csv_file in futures_files:
                try:
                    self.logger.info(f"處理檔案: {Path(csv_file).name}")

                    df = pd.read_csv(csv_file, encoding='utf-8-sig')

                    if df.empty:
                        continue

                    # 標準化欄位名稱
                    column_mapping = {
                        '交易日期': 'date',
                        '契約': 'symbol',
                        '到期月份(週別)': 'expiry',
                        '開盤價': 'open',
                        '最高價': 'high',
                        '最低價': 'low',
                        '收盤價': 'close',
                        '成交量': 'volume',
                        '結算價': 'settlement_price',
                        '未沖銷契約數': 'open_interest',
                        '漲跌價': 'change',
                        '漲跌%': 'change_percent'
                    }

                    df = df.rename(columns=column_mapping)

                    required_cols = ['date', 'symbol', 'expiry', 'open', 'high', 'low', 'close',
                                   'volume', 'settlement_price', 'open_interest']

                    existing_cols = [col for col in required_cols if col in df.columns]
                    df = df[existing_cols]

                    if not df.empty:
                        conn.execute("INSERT OR REPLACE INTO futures_daily SELECT * FROM df")

                        total_imported += len(df)
                        self.logger.info(f"已匯入 {len(df)} 筆期貨資料")

                except Exception as e:
                    self.logger.error(f"處理期貨檔案失敗 {csv_file}: {e}")

            conn.close()

            self.logger.info(f"期貨每日行情資料庫建置完成，共匯入 {total_imported} 筆資料")

        except Exception as e:
            self.logger.error(f"建置期貨每日行情資料庫失敗: {e}")

    def build_options_daily_database(self):
        """建置選擇權每日行情資料庫"""
        try:
            self.logger.info("建置選擇權每日行情資料庫...")

            options_pattern = str(self.data_dir / "processed_options_*.csv")
            options_files = glob.glob(options_pattern)

            if not options_files:
                self.logger.warning("未找到選擇權每日行情資料檔案")
                return

            conn = duckdb.connect(str(self.db_path))
            total_imported = 0

            for csv_file in options_files:
                try:
                    self.logger.info(f"處理檔案: {Path(csv_file).name}")

                    df = pd.read_csv(csv_file, encoding='utf-8-sig')

                    if df.empty:
                        continue

                    # 標準化欄位名稱
                    column_mapping = {
                        '交易日期': 'date',
                        '契約': 'symbol',
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
                        '最後最佳買價': 'best_bid',
                        '最後最佳賣價': 'best_ask'
                    }

                    df = df.rename(columns=column_mapping)

                    # 處理選擇權類型
                    if 'option_type' in df.columns:
                        df['option_type'] = df['option_type'].map({
                            '買權': 'Call',
                            '賣權': 'Put',
                            'C': 'Call',
                            'P': 'Put'
                        })

                    required_cols = ['date', 'symbol', 'expiry', 'strike_price', 'option_type',
                                   'open', 'high', 'low', 'close', 'volume',
                                   'settlement_price', 'open_interest']

                    existing_cols = [col for col in required_cols if col in df.columns]
                    df = df[existing_cols]

                    if not df.empty:
                        conn.execute("INSERT OR REPLACE INTO options_daily SELECT * FROM df")

                        total_imported += len(df)
                        self.logger.info(f"已匯入 {len(df)} 筆選擇權資料")

                except Exception as e:
                    self.logger.error(f"處理選擇權檔案失敗 {csv_file}: {e}")

            conn.close()

            self.logger.info(f"選擇權每日行情資料庫建置完成，共匯入 {total_imported} 筆資料")

        except Exception as e:
            self.logger.error(f"建置選擇權每日行情資料庫失敗: {e}")

    def build_institutional_database(self):
        """建置三大法人資料庫"""
        try:
            self.logger.info("建置三大法人資料庫...")

            inst_pattern = str(self.data_dir / "processed_institutional_*.csv")
            inst_files = glob.glob(inst_pattern)

            if not inst_files:
                self.logger.warning("未找到三大法人資料檔案")
                return

            conn = duckdb.connect(str(self.db_path))
            total_imported = 0

            for csv_file in inst_files:
                try:
                    self.logger.info(f"處理檔案: {Path(csv_file).name}")

                    df = pd.read_csv(csv_file, encoding='utf-8-sig')

                    if df.empty:
                        continue

                    # 標準化欄位名稱 (需要根據實際資料格式調整)
                    column_mapping = {
                        '交易日期': 'date',
                        '身份別': 'investor_type',
                        '期貨多方': 'futures_long',
                        '期貨空方': 'futures_short',
                        '期貨淨額': 'futures_net',
                        '選擇權多方': 'options_long',
                        '選擇權空方': 'options_short',
                        '選擇權淨額': 'options_net',
                        '總多方': 'total_long',
                        '總空方': 'total_short',
                        '總淨額': 'total_net'
                    }

                    df = df.rename(columns=column_mapping)

                    required_cols = ['date', 'investor_type', 'futures_long', 'futures_short', 'futures_net',
                                   'options_long', 'options_short', 'options_net', 'total_long', 'total_short', 'total_net']

                    existing_cols = [col for col in required_cols if col in df.columns]
                    df = df[existing_cols]

                    if not df.empty:
                        conn.execute("INSERT OR REPLACE INTO institutional_investors SELECT * FROM df")

                        total_imported += len(df)
                        self.logger.info(f"已匯入 {len(df)} 筆法人資料")

                except Exception as e:
                    self.logger.error(f"處理法人檔案失敗 {csv_file}: {e}")

            conn.close()

            self.logger.info(f"三大法人資料庫建置完成，共匯入 {total_imported} 筆資料")

        except Exception as e:
            self.logger.error(f"建置三大法人資料庫失敗: {e}")

    def build_all_databases(self):
        """建置所有資料庫"""
        self.logger.info("開始建置所有官方資料庫...")

        try:
            self.build_pcr_database()
            self.build_options_delta_database()
            self.build_futures_daily_database()
            self.build_options_daily_database()
            self.build_institutional_database()

            self.logger.info("所有官方資料庫建置完成")

            # 顯示統計資訊
            self.show_database_stats()

        except Exception as e:
            self.logger.error(f"建置資料庫失敗: {e}")

    def show_database_stats(self):
        """顯示資料庫統計資訊"""
        try:
            conn = duckdb.connect(str(self.db_path))

            tables = ['pcr_data', 'options_delta', 'futures_daily', 'options_daily', 'institutional_investors']

            print("\n=== 官方資料庫統計 ===")

            for table in tables:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    print(f"{table}: {count:,} 筆記錄")
                except:
                    print(f"{table}: 表格不存在或為空")

            # 顯示日期範圍
            print("\n=== 資料日期範圍 ===")
            for table in tables:
                try:
                    date_range = conn.execute(f"""
                        SELECT MIN(date) as start_date, MAX(date) as end_date, COUNT(DISTINCT date) as total_days
                        FROM {table}
                    """).fetchone()

                    if date_range[0]:
                        print(f"{table}: {date_range[0]} ~ {date_range[1]} ({date_range[2]} 個交易日)")
                except:
                    pass

            conn.close()

        except Exception as e:
            self.logger.error(f"顯示統計資訊失敗: {e}")


def main():
    """主程式"""
    print("=" * 70)
    print("  台灣期貨交易所官方資料資料庫建置工具")
    print("=" * 70)

    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    try:
        # 初始化建置器
        builder = TaifexOfficialDBBuilder(logger)

        # 建置所有資料庫
        builder.build_all_databases()

        print("\n" + "=" * 70)
        print("官方資料資料庫建置完成！")
        print("=" * 70)

    except Exception as e:
        logger.error(f"建置過程發生錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
