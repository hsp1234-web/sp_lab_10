# -*- coding: utf-8 -*-
"""
NY Fed 數據整合模塊 (NY Fed Integration Module)

整合紐約聯邦儲備銀行的一級交易商持有量數據到系統壓力指數中。

參考一級交易pro.ipynb中的實現，適配到我們的RORO策略框架。
"""

import pandas as pd
import numpy as np
import requests
import io
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import warnings

try:
    from .config_manager import ConfigManager
except ImportError:
    from config_manager import ConfigManager

logger = logging.getLogger(__name__)

class NYFedDataLoader:
    """
    NY Fed 一級交易商數據載入器

    從紐約聯邦儲備銀行下載和處理一級交易商的公債持有量數據。
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初始化 NY Fed 數據載入器

        Args:
            config_manager: 配置管理器實例
        """
        self.config = config_manager
        self.session = requests.Session()

        # 設置請求頭
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # 從配置中獲取URL和欄位設置
        self._load_config()

        logger.info("NYFedDataLoader 初始化完成")

    def _load_config(self):
        """從配置管理器載入 NY Fed 相關配置"""
        if self.config:
            ny_fed_config = self.config.get('ny_fed', {})

            # SBN URLs (Securities Bought Net?)
            self.sbn_urls = ny_fed_config.get('sbn_urls', [
                "https://www.newyorkfed.org/medialibrary/media/research/data_indicators/sbn.xlsx"
            ])

            # SBP URLs (Securities Bought Paid?)
            self.sbp2013_urls = ny_fed_config.get('sbp2013_urls', [
                "https://www.newyorkfed.org/medialibrary/media/research/data_indicators/sbp.xlsx",
                "https://www.newyorkfed.org/medialibrary/media/research/data_indicators/sbp2001.xlsx"
            ])

            # 加總欄位配置
            self.sbp2013_cols = ny_fed_config.get('sbp2013_cols_to_sum', [
                "PDPOSGSC-PDPOSGSC",
                "PDPOSGSC-PDPOSGSCT",
                "PDPOSGSC-PDPOSGSCF"
            ])

            self.sbp2001_cols = ny_fed_config.get('sbp2001_cols_to_sum', [
                "PDPOSGSC",
                "PDPOSGSCT",
                "PDPOSGSCF"
            ])
        else:
            # 默認配置
            self.sbn_urls = ["https://www.newyorkfed.org/medialibrary/media/research/data_indicators/sbn.xlsx"]
            self.sbp2013_urls = [
                "https://www.newyorkfed.org/medialibrary/media/research/data_indicators/sbp.xlsx",
                "https://www.newyorkfed.org/medialibrary/media/research/data_indicators/sbp2001.xlsx"
            ]
            self.sbp2013_cols = ["PDPOSGSC-PDPOSGSC", "PDPOSGSC-PDPOSGSCT", "PDPOSGSC-PDPOSGSCF"]
            self.sbp2001_cols = ["PDPOSGSC", "PDPOSGSCT", "PDPOSGSCF"]

    def fetch_ny_fed_data(self, start_date: str = None, end_date: str = None) -> pd.Series:
        """
        獲取 NY Fed 一級交易商持有量數據

        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            持有量時間序列 (百萬美元)
        """
        try:
            logger.info("開始獲取 NY Fed 一級交易商持有量數據")

            all_positions_data = []

            # 處理所有 URL
            all_urls = self.sbn_urls + self.sbp2013_urls
            processed_files = 0
            failed_files = []

            for url in all_urls:
                try:
                    series = self._process_single_file(url)
                    if series is not None and not series.empty:
                        all_positions_data.append(series)
                        processed_files += 1
                        logger.info(f"成功處理文件: {url.split('/')[-1]}")
                    else:
                        failed_files.append(url.split('/')[-1])

                except Exception as e:
                    logger.warning(f"處理文件失敗 {url.split('/')[-1]}: {str(e)}")
                    failed_files.append(url.split('/')[-1])

            if not all_positions_data:
                logger.error("未能獲取任何有效的 NY Fed 數據")
                return pd.Series(dtype='float64', name='ny_fed_positions')

            # 合併所有數據
            combined_positions = pd.concat(all_positions_data)

            # 按日期排序並處理重疊
            combined_positions = combined_positions.sort_index()
            final_series = combined_positions.groupby(level=0).last()  # 保留最新值

            # 清理數據
            final_series = final_series.dropna()
            final_series = final_series[final_series != 0]

            # 設置名稱
            final_series.name = 'Total_Primary_Dealer_Positions_Millions'

            # 日期過濾
            if start_date or end_date:
                if start_date:
                    start_dt = pd.to_datetime(start_date)
                    final_series = final_series[final_series.index >= start_dt]
                if end_date:
                    end_dt = pd.to_datetime(end_date)
                    final_series = final_series[final_series.index <= end_dt]

            logger.info(f"NY Fed 數據獲取完成，共 {len(final_series)} 筆有效數據")
            logger.info(f"成功處理 {processed_files} 個文件，失敗 {len(failed_files)} 個")

            return final_series

        except Exception as e:
            logger.error(f"NY Fed 數據獲取失敗: {str(e)}")
            return pd.Series(dtype='float64', name='ny_fed_positions')

    def _process_single_file(self, url: str) -> Optional[pd.Series]:
        """
        處理單個 NY Fed Excel 文件

        Args:
            url: 文件 URL

        Returns:
            處理後的數據序列
        """
        try:
            # 下載文件
            response = self.session.get(url, timeout=120)
            response.raise_for_status()

            excel_content = io.BytesIO(response.content)

            # 自動檢測表頭
            data_positions_long = self._parse_excel_with_auto_header(excel_content)

            if data_positions_long is None or data_positions_long.empty:
                return None

            # 轉換為寬格式
            data_positions_wide = self._convert_to_wide_format(data_positions_long)

            if data_positions_wide.empty:
                return None

            # 加總持有量
            daily_total = self._sum_positions(data_positions_wide, url)

            if daily_total is None or daily_total.empty:
                return None

            return daily_total

        except Exception as e:
            logger.error(f"處理文件失敗 {url}: {str(e)}")
            return None

    def _parse_excel_with_auto_header(self, excel_content: io.BytesIO) -> Optional[pd.DataFrame]:
        """
        自動檢測表頭並解析 Excel 文件

        Args:
            excel_content: Excel 文件內容

        Returns:
            解析後的長格式 DataFrame
        """
        possible_headers = [3, 4, 0]

        for header_row in possible_headers:
            try:
                excel_content.seek(0)  # 重置指針

                # 嘗試讀取樣本數據
                df_sample = pd.read_excel(excel_content, header=header_row, nrows=5, engine='openpyxl')

                # 查找必要的列
                cols_lower = [str(c).lower() for c in df_sample.columns]

                time_series_col = None
                value_col = None
                date_col = None

                # 查找 Time Series 列
                if 'time series' in cols_lower:
                    time_series_col = df_sample.columns[cols_lower.index('time series')]

                # 查找 Value 列
                if 'value (millions)' in cols_lower:
                    value_col = df_sample.columns[cols_lower.index('value (millions)')]
                elif 'value' in cols_lower:
                    value_col = df_sample.columns[cols_lower.index('value')]

                # 查找日期列
                if 'effective date' in cols_lower:
                    date_col = df_sample.columns[cols_lower.index('effective date')]
                elif len(df_sample.columns) > 0:
                    date_col = df_sample.columns[0]  # 假設第一列是日期

                # 如果找到必要列，則讀取完整數據
                if time_series_col and value_col and date_col:
                    excel_content.seek(0)
                    data_long = pd.read_excel(
                        excel_content,
                        header=header_row,
                        index_col=date_col,
                        parse_dates=True,
                        engine='openpyxl'
                    )

                    # 清理索引
                    if not isinstance(data_long.index, pd.DatetimeIndex):
                        data_long.index = pd.to_datetime(data_long.index, errors='coerce')
                        data_long.dropna(subset=[data_long.index.name], inplace=True)
                    data_long.index = data_long.index.normalize()

                    # 清理數值列
                    data_long[value_col] = pd.to_numeric(data_long[value_col], errors='coerce')
                    data_long.dropna(subset=[value_col], inplace=True)

                    if not data_long.empty:
                        logger.info(f"成功解析 Excel，表頭行: {header_row}, 數據行數: {len(data_long)}")
                        return data_long

            except Exception as e:
                logger.debug(f"嘗試表頭行 {header_row} 失敗: {str(e)}")
                continue

        logger.warning("無法自動檢測有效的 Excel 表頭")
        return None

    def _convert_to_wide_format(self, data_long: pd.DataFrame) -> pd.DataFrame:
        """
        將長格式數據轉換為寬格式

        Args:
            data_long: 長格式 DataFrame

        Returns:
            寬格式 DataFrame
        """
        try:
            # 找到列名
            cols_lower = [str(c).lower() for c in data_long.columns]
            time_series_col = None
            value_col = None

            if 'time series' in cols_lower:
                time_series_col = data_long.columns[cols_lower.index('time series')]

            if 'value (millions)' in cols_lower:
                value_col = data_long.columns[cols_lower.index('value (millions)')]
            elif 'value' in cols_lower:
                value_col = data_long.columns[cols_lower.index('value')]

            if not time_series_col or not value_col:
                logger.error("缺少必要的列")
                return pd.DataFrame()

            # 重置索引準備 pivot
            data_long = data_long.reset_index()

            # 處理重複項
            data_long = data_long.groupby(
                [data_long.columns[0], time_series_col]
            )[value_col].mean().reset_index()

            # Pivot
            data_wide = pd.pivot_table(
                data_long,
                index=data_long.columns[0],  # 日期列
                columns=time_series_col,
                values=value_col,
                aggfunc='mean'
            )

            logger.info(f"寬格式轉換完成: {len(data_wide)} 行 x {len(data_wide.columns)} 列")
            return data_wide

        except Exception as e:
            logger.error(f"寬格式轉換失敗: {str(e)}")
            return pd.DataFrame()

    def _sum_positions(self, data_wide: pd.DataFrame, url: str) -> Optional[pd.Series]:
        """
        加總持有量數據

        Args:
            data_wide: 寬格式數據
            url: 源 URL (用於確定加總規則)

        Returns:
            加總後的序列
        """
        try:
            # 確定加總欄位
            if 'SBN' in url:
                target_cols = [c for c in data_wide.columns if isinstance(c, str) and c.startswith('PDPOSGSC-')]
            elif 'SBP2013' in url:
                target_cols = self.sbp2013_cols
            elif 'SBP2001' in url:
                target_cols = self.sbp2001_cols
            else:
                target_cols = []

            if not target_cols:
                logger.warning(f"無加總規則適用於 URL: {url}")
                return None

            # 檢查實際存在的欄位
            cols_to_sum = [c for c in target_cols if c in data_wide.columns]

            if not cols_to_sum:
                logger.warning(f"未找到任何目標欄位: {target_cols}")
                return None

            if len(cols_to_sum) < len(target_cols):
                missing_cols = set(target_cols) - set(cols_to_sum)
                logger.warning(f"部分目標欄位未找到: {missing_cols}")

            # 確保數值類型
            for col in cols_to_sum:
                data_wide[col] = pd.to_numeric(data_wide[col], errors='coerce')

            # 加總
            daily_total = data_wide[cols_to_sum].sum(axis=1, skipna=True)

            # 清理
            daily_total = daily_total.dropna()
            daily_total = daily_total[daily_total != 0]

            if daily_total.empty:
                logger.warning("加總後無有效數據")
                return None

            logger.info(f"成功加總 {len(cols_to_sum)} 個欄位，獲得 {len(daily_total)} 筆有效數據")
            return daily_total

        except Exception as e:
            logger.error(f"加總失敗: {str(e)}")
            return None


class NYFedPressureIndicator:
    """
    NY Fed 壓力指標

    將 NY Fed 一級交易商持有量數據轉換為壓力指標。
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初始化 NY Fed 壓力指標

        Args:
            config_manager: 配置管理器實例
        """
        self.config = config_manager
        self.data_loader = NYFedDataLoader(config_manager)

        logger.info("NYFedPressureIndicator 初始化完成")

    def calculate_ny_fed_pressure(self, start_date: str, end_date: str) -> pd.Series:
        """
        計算 NY Fed 壓力指標

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            壓力指標序列
        """
        try:
            logger.info("開始計算 NY Fed 壓力指標")

            # 獲取原始數據
            positions_data = self.data_loader.fetch_ny_fed_data(start_date, end_date)

            if positions_data.empty:
                logger.warning("無 NY Fed 數據，無法計算壓力指標")
                return pd.Series(dtype='float64', name='ny_fed_pressure')

            # 計算壓力指標
            pressure_indicator = self._calculate_pressure_from_positions(positions_data)

            logger.info(f"NY Fed 壓力指標計算完成，共 {len(pressure_indicator)} 筆數據")
            return pressure_indicator

        except Exception as e:
            logger.error(f"NY Fed 壓力指標計算失敗: {str(e)}")
            return pd.Series(dtype='float64', name='ny_fed_pressure')

    def _calculate_pressure_from_positions(self, positions_data: pd.Series) -> pd.Series:
        """
        從持有量數據計算壓力指標

        Args:
            positions_data: 持有量數據

        Returns:
            壓力指標序列
        """
        try:
            # 計算持有量變化
            positions_change = positions_data.pct_change(30)  # 30日變化率

            # 計算相對於歷史水平的偏離
            positions_ma = positions_data.rolling(252, min_periods=30).mean()  # 一年移動平均
            positions_std = positions_data.rolling(252, min_periods=30).std()  # 一年標準差

            positions_zscore = (positions_data - positions_ma) / positions_std

            # 綜合壓力指標
            # 高持有量通常表示市場寬鬆（低壓力），反之亦然
            pressure_indicator = -positions_zscore  # 負號使高持有量對應低壓力

            # 平滑處理
            pressure_indicator = pressure_indicator.rolling(5, min_periods=1).mean()

            pressure_indicator = pressure_indicator.fillna(0)
            pressure_indicator.name = 'ny_fed_pressure'

            return pressure_indicator

        except Exception as e:
            logger.error(f"從持有量計算壓力指標失敗: {str(e)}")
            return pd.Series(dtype='float64', name='ny_fed_pressure')


def main():
    """
    主函數 - 用於測試 NY Fed 數據整合
    """
    # 配置日誌
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 測試 NY Fed 數據載入
    try:
        from pathlib import Path
        from config_manager import ConfigManager

        config = ConfigManager(Path('config/roro_config.yaml'))
        ny_fed_loader = NYFedDataLoader(config)

        # 測試數據獲取
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        print(f"測試 NY Fed 數據獲取: {start_date} 到 {end_date}")

        positions_data = ny_fed_loader.fetch_ny_fed_data(start_date, end_date)

        if not positions_data.empty:
            print(f"成功獲取 {len(positions_data)} 筆 NY Fed 數據")
            print(f"數據範圍: {positions_data.index.min()} 到 {positions_data.index.max()}")
            print(f"最新值: {positions_data.iloc[-1]:.2f} 百萬美元")
            print(f"均值: {positions_data.mean():.2f} 百萬美元")
            print(f"標準差: {positions_data.std():.2f} 百萬美元")

            # 測試壓力指標計算
            pressure_indicator = NYFedPressureIndicator(config)
            pressure_data = pressure_indicator.calculate_ny_fed_pressure(start_date, end_date)

            if not pressure_data.empty:
                print(f"成功計算壓力指標，共 {len(pressure_data)} 筆數據")
                print(f"壓力指標最新值: {pressure_data.iloc[-1]:.4f}")
        else:
            print("NY Fed 數據獲取失敗")

    except Exception as e:
        print(f"測試失敗: {str(e)}")


if __name__ == "__main__":
    main()
