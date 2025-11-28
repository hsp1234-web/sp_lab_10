# -*- coding: utf-8 -*-
"""
市場寬度指標模塊 (Market Indicators Module)

此模塊實現台灣股市的市場寬度指標計算，用於評估市場整體健康狀況。

核心指標：
- 騰落線 (Advance-Decline Line)
- 漲跌家數比 (Advance-Decline Ratio)
- 市場參與度 (Market Participation)

由於台灣股市成分股數據獲取困難，此版本使用簡化的實現方法。
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import warnings

logger = logging.getLogger(__name__)

class MarketWidthIndicator:
    """
    台灣股市市場寬度指標計算類

    實現簡化的市場寬度指標，基於台灣加權指數和相關數據。
    """

    def __init__(self, config_manager=None):
        """
        初始化市場寬度指標計算器

        Args:
            config_manager: 配置管理器實例
        """
        self.config = config_manager
        self.taiwan_market_tickers = {
            'main_index': '^TWII',  # 台灣加權指數
            'large_cap': ['2330.TW', '2454.TW', '2317.TW', '2412.TW', '2382.TW'],  # 台積電等大型權值股
            'small_cap': ['9945.TW', '1434.TW', '1707.TW']  # 部分小型股作為補充
        }

        # 指標計算參數
        self.ad_line_window = 20  # A/D Line 計算窗口
        self.participation_threshold = 0.7  # 市場參與度閾值

        logger.info("MarketWidthIndicator 初始化完成")

    def calculate_ad_line_simple(self, price_data: pd.DataFrame,
                               window: int = 20) -> pd.Series:
        """
        計算簡化的騰落線 (Advance-Decline Line)

        由於無法獲取完整的漲跌家數數據，使用價格變動的正負數量作為替代。

        Args:
            price_data: 價格數據 DataFrame
            window: 計算窗口期

        Returns:
            A/D Line 序列
        """
        try:
            # 計算每日漲跌
            daily_returns = price_data.pct_change()

            # 正漲天數減去負跌天數
            ad_values = (daily_returns > 0).sum(axis=1) - (daily_returns < 0).sum(axis=1)

            # 累計計算 A/D Line
            ad_line = ad_values.rolling(window=window, min_periods=1).sum()

            logger.info(f"成功計算 A/D Line，使用 {len(price_data.columns)} 個股票")
            return ad_line

        except Exception as e:
            logger.error(f"A/D Line 計算失敗: {str(e)}")
            return pd.Series()

    def calculate_ad_ratio(self, price_data: pd.DataFrame,
                          window: int = 20) -> pd.Series:
        """
        計算漲跌家數比 (Advance-Decline Ratio)

        Args:
            price_data: 價格數據 DataFrame
            window: 計算窗口期

        Returns:
            A/D Ratio 序列
        """
        try:
            daily_returns = price_data.pct_change()

            # 計算漲跌家數
            advances = (daily_returns > 0).sum(axis=1)
            declines = (daily_returns < 0).sum(axis=1)

            # 避免除零錯誤
            declines = declines.replace(0, 0.1)

            # 計算漲跌比
            ad_ratio = advances / declines

            # 移動平均平滑
            ad_ratio_smooth = ad_ratio.rolling(window=window, min_periods=1).mean()

            logger.info("成功計算 A/D Ratio")
            return ad_ratio_smooth

        except Exception as e:
            logger.error(f"A/D Ratio 計算失敗: {str(e)}")
            return pd.Series()

    def calculate_market_participation(self, price_data: pd.DataFrame,
                                     volume_data: Optional[pd.DataFrame] = None,
                                     window: int = 20) -> pd.Series:
        """
        計算市場參與度 (Market Participation)

        衡量市場中有多少股票在積極參與交易。

        Args:
            price_data: 價格數據 DataFrame
            volume_data: 成交量數據 DataFrame (可選)
            window: 計算窗口期

        Returns:
            市場參與度序列
        """
        try:
            # 計算每日價格變動幅度
            daily_range = (price_data.max(axis=1) - price_data.min(axis=1)) / price_data.mean(axis=1)

            # 計算參與度：有價格變動的股票比例
            participation = (price_data.notna().sum(axis=1) / len(price_data.columns))

            # 如果有成交量數據，加入成交量權重
            if volume_data is not None:
                volume_participation = (volume_data > volume_data.quantile(0.1, axis=1).min()).sum(axis=1) / len(volume_data.columns)
                participation = (participation + volume_participation) / 2

            # 移動平均平滑
            participation_smooth = participation.rolling(window=window, min_periods=1).mean()

            logger.info("成功計算市場參與度")
            return participation_smooth

        except Exception as e:
            logger.error(f"市場參與度計算失敗: {str(e)}")
            return pd.Series()

    def fetch_taiwan_market_data(self, start_date: str, end_date: str) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
        """
        獲取台灣股市數據

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            (價格數據, 成交量數據) 元組
        """
        try:
            logger.info(f"開始獲取台灣股市數據: {start_date} 到 {end_date}")

            all_tickers = (self.taiwan_market_tickers['large_cap'] +
                          self.taiwan_market_tickers['small_cap'] +
                          [self.taiwan_market_tickers['main_index']])

            price_data = []
            volume_data = []

            # 分批獲取數據避免API限制
            batch_size = 5
            for i in range(0, len(all_tickers), batch_size):
                batch_tickers = all_tickers[i:i+batch_size]
                logger.info(f"處理股票批次: {batch_tickers}")

                try:
                    data = yf.download(batch_tickers, start=start_date, end=end_date,
                                     group_by='ticker', threads=True)

                    # 處理數據結構
                    if len(batch_tickers) == 1:
                        # 單一股票
                        ticker = batch_tickers[0]
                        if not data.empty:
                            price_data.append(data[['Close']].rename(columns={'Close': ticker}))
                            volume_data.append(data[['Volume']].rename(columns={'Volume': f"{ticker}_vol"}))
                    else:
                        # 多股票
                        for ticker in batch_tickers:
                            if ticker in data.columns.get_level_values(0):
                                ticker_data = data[ticker]
                                if not ticker_data.empty:
                                    price_data.append(ticker_data[['Close']].rename(columns={'Close': ticker}))
                                    volume_data.append(ticker_data[['Volume']].rename(columns={'Volume': f"{ticker}_vol"}))

                    # 添加延遲避免API限制
                    import time
                    time.sleep(1)

                except Exception as e:
                    logger.warning(f"獲取批次數據失敗 {batch_tickers}: {str(e)}")
                    continue

            # 合併所有數據
            if price_data:
                combined_prices = pd.concat(price_data, axis=1, join='outer')
                combined_prices = combined_prices.sort_index()

                combined_volumes = None
                if volume_data:
                    combined_volumes = pd.concat(volume_data, axis=1, join='outer')
                    combined_volumes = combined_volumes.sort_index()

                logger.info(f"成功獲取 {len(combined_prices.columns)} 個股票的數據")
                return combined_prices, combined_volumes
            else:
                logger.error("未能獲取任何台灣股市數據")
                return pd.DataFrame(), None

        except Exception as e:
            logger.error(f"獲取台灣股市數據失敗: {str(e)}")
            return pd.DataFrame(), None

    def calculate_all_indicators(self, start_date: str, end_date: str) -> Dict[str, pd.Series]:
        """
        計算所有市場寬度指標

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            包含所有指標的字典
        """
        try:
            logger.info("開始計算所有市場寬度指標")

            # 獲取數據
            price_data, volume_data = self.fetch_taiwan_market_data(start_date, end_date)

            if price_data.empty:
                logger.error("無有效數據，無法計算指標")
                return {}

            # 計算各項指標
            indicators = {}

            # A/D Line
            ad_line = self.calculate_ad_line_simple(price_data, self.ad_line_window)
            if not ad_line.empty:
                indicators['ad_line'] = ad_line

            # A/D Ratio
            ad_ratio = self.calculate_ad_ratio(price_data, self.ad_line_window)
            if not ad_ratio.empty:
                indicators['ad_ratio'] = ad_ratio

            # 市場參與度
            participation = self.calculate_market_participation(price_data, volume_data, self.ad_line_window)
            if not participation.empty:
                indicators['participation'] = participation

            # 計算綜合市場寬度評分
            if len(indicators) >= 2:
                indicators['market_width_score'] = self._calculate_composite_score(indicators)

            logger.info(f"成功計算 {len(indicators)} 項市場寬度指標")
            return indicators

        except Exception as e:
            logger.error(f"市場寬度指標計算失敗: {str(e)}")
            return {}

    def _calculate_composite_score(self, indicators: Dict[str, pd.Series]) -> pd.Series:
        """
        計算綜合市場寬度評分

        Args:
            indicators: 各項指標字典

        Returns:
            綜合評分序列
        """
        try:
            # 標準化各項指標
            normalized_indicators = {}

            for name, series in indicators.items():
                if name != 'market_width_score':
                    # Z-score 標準化
                    normalized = (series - series.rolling(20, min_periods=1).mean()) / series.rolling(20, min_periods=1).std()
                    normalized_indicators[name] = normalized.fillna(0)

            # 計算綜合評分 (等權重)
            composite_score = pd.concat(normalized_indicators.values(), axis=1).mean(axis=1)

            return composite_score

        except Exception as e:
            logger.error(f"綜合評分計算失敗: {str(e)}")
            return pd.Series()

    def get_market_health_status(self, indicators: Dict[str, pd.Series]) -> pd.Series:
        """
        基於指標判斷市場健康狀態

        Args:
            indicators: 指標字典

        Returns:
            市場健康狀態序列 (-1: 惡化, 0: 中性, 1: 健康)
        """
        try:
            if 'market_width_score' not in indicators:
                logger.warning("無市場寬度評分，無法判斷健康狀態")
                return pd.Series()

            score = indicators['market_width_score']

            # 基於評分判斷狀態
            status = pd.cut(score,
                          bins=[-np.inf, -1, 1, np.inf],
                          labels=[-1, 0, 1])  # -1: 惡化, 0: 中性, 1: 健康

            return status.astype(int)

        except Exception as e:
            logger.error(f"市場健康狀態判斷失敗: {str(e)}")
            return pd.Series()


def main():
    """
    主函數 - 用於測試市場寬度指標計算
    """
    # 配置日誌
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 測試計算
    try:
        indicator = MarketWidthIndicator()

        # 測試期間
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"測試市場寬度指標計算: {start_date} 到 {end_date}")

        # 計算指標
        indicators = indicator.calculate_all_indicators(start_date, end_date)

        if indicators:
            logger.info(f"成功計算以下指標: {list(indicators.keys())}")

            # 顯示最新數據
            for name, series in indicators.items():
                if not series.empty:
                    latest_value = series.iloc[-1]
                    logger.info(f"{name}: {latest_value:.4f}")
        else:
            logger.error("指標計算失敗")

    except Exception as e:
        logger.error(f"測試失敗: {str(e)}")


if __name__ == "__main__":
    main()



