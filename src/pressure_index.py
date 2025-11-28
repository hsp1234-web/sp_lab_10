# -*- coding: utf-8 -*-
"""
系統壓力指數模塊 (System Pressure Index Module)

此模塊整合多個宏觀經濟指標，形成綜合的系統壓力評估。

核心輸入指標：
- SOFR 利率 (短期融資成本)
- 利差指標 (各期限利差變化)
- MOVE 指數 (債券市場波動率)
- VIX 指數 (股票市場恐慌指數)
- 準備金比率 (聯準會政策指標)
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import warnings

try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False
    warnings.warn("fredapi 未安裝，將使用 Yahoo Finance 作為備選數據源")

# 延遲導入 NY Fed 模塊（避免循環導入）
def _get_ny_fed_indicator():
    """延遲導入 NY Fed 指標"""
    try:
        from .ny_fed_integration import NYFedPressureIndicator
        return NYFedPressureIndicator
    except ImportError:
        return None

logger = logging.getLogger(__name__)

class SystemPressureIndex:
    """
    系統壓力指數計算類

    整合多個宏觀指標形成綜合壓力評估。
    """

    def __init__(self, fred_api_key: Optional[str] = None, config_manager=None):
        """
        初始化系統壓力指數計算器

        Args:
            fred_api_key: FRED API 金鑰
            config_manager: 配置管理器實例
        """
        self.config = config_manager
        self.fred_api_key = fred_api_key or self._get_fred_api_key()

        # FRED 數據系列代碼
        self.fred_series = {
            'SOFR': 'SOFR',  # 安全的隔夜融資利率
            'DFF': 'DFF',    # 聯邦基金利率
            'DGS1': 'DGS1',  # 1年期國債利率
            'DGS5': 'DGS5',  # 5年期國債利率
            'DGS10': 'DGS10', # 10年期國債利率
            'DGS30': 'DGS30', # 30年期國債利率
            'T10Y2Y': 'T10Y2Y',  # 10年-2年利差
            'T10Y3M': 'T10Y3M',  # 10年-3月利差
            'BAMLH0A0HYM2': 'BAMLH0A0HYM2',  # 高收益債券利差
            'IORR': 'IORRR',  # 準備金利率 (注意：IORR可能已停用，使用IORRR)
            'M2SL': 'M2SL',   # M2貨幣供應量
            'INDPRO': 'INDPRO',  # 工業生產指數
        }

        # Yahoo Finance 備選數據
        self.yahoo_tickers = {
            'VIX': '^VIX',     # CBOE波動率指數
            'MOVE': '^MOVE',   # ICE BofA MOVE指數 (如果可用)
            'TNX': '^TNX',     # 10年期國債殖利率
            'SPY': 'SPY',      # S&P 500 ETF
        }

        # 指標權重 (經驗法則)
        self.indicator_weights = {
            'SOFR': 0.12,      # 短期融資成本
            'spread_10y2y': 0.12,  # 期限利差
            'spread_10y3m': 0.12,  # 短期利差
            'VIX': 0.15,       # 市場恐慌指數
            'MOVE': 0.12,      # 債券波動率
            'high_yield_spread': 0.08,  # 高收益債券利差
            'industrial_production': 0.08,  # 經濟活動指標
            'ny_fed_pressure': 0.21,  # NY Fed 一級交易商壓力指標
        }

        # 初始化 FRED 客戶端
        self.fred_client = None
        if FRED_AVAILABLE and self.fred_api_key:
            try:
                self.fred_client = Fred(api_key=self.fred_api_key)
                logger.info("FRED API 客戶端初始化成功")
            except Exception as e:
                logger.warning(f"FRED API 初始化失敗: {str(e)}")

        logger.info("SystemPressureIndex 初始化完成")

    def _get_fred_api_key(self) -> Optional[str]:
        """從配置管理器獲取 FRED API 金鑰"""
        if self.config:
            return self.config.get('api_keys.fred')
        return None

    def fetch_fred_data(self, series_code: str, start_date: str, end_date: str) -> pd.Series:
        """
        從 FRED API 獲取數據

        Args:
            series_code: FRED 系列代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            數據序列
        """
        try:
            if not self.fred_client:
                logger.warning(f"無法獲取 {series_code}: FRED 客戶端未初始化")
                return pd.Series()

            data = self.fred_client.get_series(series_code, start_date, end_date)
            data = data.dropna()

            logger.info(f"成功獲取 FRED 數據: {series_code}, {len(data)} 個數據點")
            return data

        except Exception as e:
            logger.error(f"獲取 FRED 數據失敗 {series_code}: {str(e)}")
            return pd.Series()

    def fetch_yahoo_data(self, ticker: str, start_date: str, end_date: str) -> pd.Series:
        """
        從 Yahoo Finance 獲取數據

        Args:
            ticker: Yahoo Finance 代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            數據序列
        """
        try:
            data = yf.download(ticker, start=start_date, end=end_date)

            if data.empty:
                logger.warning(f"無法獲取 Yahoo 數據: {ticker}")
                return pd.Series()

            # 使用收盤價
            series = data['Close'].dropna()

            logger.info(f"成功獲取 Yahoo 數據: {ticker}, {len(series)} 個數據點")
            return series

        except Exception as e:
            logger.error(f"獲取 Yahoo 數據失敗 {ticker}: {str(e)}")
            return pd.Series()

    def calculate_sofr_pressure(self, sofr_data: pd.Series) -> pd.Series:
        """
        計算 SOFR 相關的壓力指標

        Args:
            sofr_data: SOFR 利率數據

        Returns:
            SOFR 壓力指標
        """
        try:
            if sofr_data.empty:
                return pd.Series()

            # SOFR 變化率
            sofr_change = sofr_data.pct_change(30)  # 30日變化率

            # SOFR 相對於歷史水平的偏離度
            sofr_ma = sofr_data.rolling(252, min_periods=30).mean()  # 一年移動平均
            sofr_std = sofr_data.rolling(252, min_periods=30).std()  # 一年標準差

            sofr_zscore = (sofr_data - sofr_ma) / sofr_std

            # 綜合壓力指標：變化率和偏離度的組合
            sofr_pressure = (sofr_change * 0.4 + sofr_zscore * 0.6).fillna(0)

            return sofr_pressure

        except Exception as e:
            logger.error(f"SOFR 壓力計算失敗: {str(e)}")
            return pd.Series()

    def calculate_yield_spread_pressure(self, yield_data: Dict[str, pd.Series]) -> pd.Series:
        """
        計算利差壓力指標

        Args:
            yield_data: 各期限殖利率數據字典

        Returns:
            利差壓力指標
        """
        try:
            spreads = {}

            # 計算關鍵利差
            if 'DGS10' in yield_data and 'DGS2' in yield_data:
                spreads['10y2y'] = yield_data['DGS10'] - yield_data.get('DGS2', yield_data['DGS10']*0.8)

            if 'DGS10' in yield_data and 'DGS3MO' in yield_data:
                spreads['10y3m'] = yield_data['DGS10'] - yield_data['DGS3MO']

            if not spreads:
                logger.warning("無足夠數據計算利差")
                return pd.Series()

            # 計算利差變化
            spread_changes = {}
            for name, spread in spreads.items():
                spread_changes[name] = spread.pct_change(30).fillna(0)

            # 綜合利差壓力 (等權重)
            combined_spread_change = pd.concat(spread_changes.values(), axis=1).mean(axis=1)

            # 標準化
            spread_pressure = (combined_spread_change - combined_spread_change.rolling(60).mean()) / combined_spread_change.rolling(60).std()
            spread_pressure = spread_pressure.fillna(0)

            return spread_pressure

        except Exception as e:
            logger.error(f"利差壓力計算失敗: {str(e)}")
            return pd.Series()

    def calculate_volatility_pressure(self, vix_data: pd.Series, move_data: Optional[pd.Series] = None) -> pd.Series:
        """
        計算波動率壓力指標

        Args:
            vix_data: VIX 數據
            move_data: MOVE 數據 (可選)

        Returns:
            波動率壓力指標
        """
        try:
            if vix_data.empty:
                return pd.Series()

            # VIX 標準化
            vix_ma = vix_data.rolling(60).mean()
            vix_std = vix_data.rolling(60).std()
            vix_zscore = (vix_data - vix_ma) / vix_std

            if move_data is not None and not move_data.empty:
                # MOVE 標準化
                move_ma = move_data.rolling(60).mean()
                move_std = move_data.rolling(60).std()
                move_zscore = (move_data - move_ma) / move_std

                # 綜合波動率壓力
                vol_pressure = (vix_zscore * 0.6 + move_zscore * 0.4).fillna(vix_zscore)
            else:
                vol_pressure = vix_zscore.fillna(0)

            return vol_pressure

        except Exception as e:
            logger.error(f"波動率壓力計算失敗: {str(e)}")
            return pd.Series()

    def calculate_economic_pressure(self, indicators: Dict[str, pd.Series]) -> pd.Series:
        """
        計算經濟活動壓力指標

        Args:
            indicators: 經濟指標數據字典

        Returns:
            經濟壓力指標
        """
        try:
            economic_scores = []

            # 工業生產指數變化
            if 'INDPRO' in indicators and not indicators['INDPRO'].empty:
                indpro_change = indicators['INDPRO'].pct_change(90)  # 90日變化率
                indpro_zscore = (indpro_change - indpro_change.rolling(252).mean()) / indpro_change.rolling(252).std()
                economic_scores.append(indpro_zscore * 0.5)

            # M2 貨幣供應量變化 (如果通脹壓力)
            if 'M2SL' in indicators and not indicators['M2SL'].empty:
                m2_change = indicators['M2SL'].pct_change(90)
                m2_zscore = (m2_change - m2_change.rolling(252).mean()) / m2_change.rolling(252).std()
                economic_scores.append(m2_zscore * 0.3)

            # 高收益債券利差 (如果可用)
            if 'BAMLH0A0HYM2' in indicators and not indicators['BAMLH0A0HYM2'].empty:
                hy_spread = indicators['BAMLH0A0HYM2']
                hy_zscore = (hy_spread - hy_spread.rolling(252).mean()) / hy_spread.rolling(252).std()
                economic_scores.append(hy_zscore * 0.2)

            if economic_scores:
                economic_pressure = pd.concat(economic_scores, axis=1).sum(axis=1)
                return economic_pressure.fillna(0)
            else:
                logger.warning("無經濟指標數據")
                return pd.Series()

        except Exception as e:
            logger.error(f"經濟壓力計算失敗: {str(e)}")
            return pd.Series()

    def calculate_composite_pressure_index(self, start_date: str, end_date: str) -> Dict[str, pd.Series]:
        """
        計算綜合系統壓力指數

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            包含各項壓力指標的字典
        """
        try:
            logger.info(f"開始計算系統壓力指數: {start_date} 到 {end_date}")

            pressure_indicators = {}

            # 1. 獲取所有基礎數據
            raw_data = {}

            # FRED 數據
            for name, series_code in self.fred_series.items():
                data = self.fetch_fred_data(series_code, start_date, end_date)
                if not data.empty:
                    raw_data[name] = data

            # Yahoo Finance 數據
            for name, ticker in self.yahoo_tickers.items():
                data = self.fetch_yahoo_data(ticker, start_date, end_date)
                if not data.empty:
                    raw_data[name] = data

            # 2. 計算各項壓力指標
            if 'SOFR' in raw_data:
                pressure_indicators['sofr_pressure'] = self.calculate_sofr_pressure(raw_data['SOFR'])

            # 利差壓力 (需要多個殖利率數據)
            yield_keys = [k for k in raw_data.keys() if k.startswith('DGS')]
            if len(yield_keys) >= 2:
                yield_data = {k: raw_data[k] for k in yield_keys}
                pressure_indicators['spread_pressure'] = self.calculate_yield_spread_pressure(yield_data)

            # 波動率壓力
            vix_data = raw_data.get('VIX')
            move_data = raw_data.get('MOVE')
            if vix_data is not None:
                pressure_indicators['volatility_pressure'] = self.calculate_volatility_pressure(vix_data, move_data)

            # 經濟壓力
            economic_indicators = {k: v for k, v in raw_data.items()
                                 if k in ['INDPRO', 'M2SL', 'BAMLH0A0HYM2']}
            if economic_indicators:
                pressure_indicators['economic_pressure'] = self.calculate_economic_pressure(economic_indicators)

            # NY Fed 一級交易商壓力指標
            ny_fed_indicator_class = _get_ny_fed_indicator()
            if ny_fed_indicator_class:
                try:
                    ny_fed_indicator = ny_fed_indicator_class(self.config)
                    ny_fed_pressure = ny_fed_indicator.calculate_ny_fed_pressure(start_date, end_date)
                    if not ny_fed_pressure.empty:
                        pressure_indicators['ny_fed_pressure'] = ny_fed_pressure
                        logger.info("成功整合 NY Fed 壓力指標")
                except Exception as e:
                    logger.warning(f"NY Fed 壓力指標計算失敗: {str(e)}")

            # 3. 計算綜合壓力指數
            if pressure_indicators:
                pressure_indicators['composite_pressure_index'] = self._combine_pressure_indicators(pressure_indicators)

            logger.info(f"成功計算 {len(pressure_indicators)} 項壓力指標")
            return pressure_indicators

        except Exception as e:
            logger.error(f"綜合壓力指數計算失敗: {str(e)}")
            return {}

    def _combine_pressure_indicators(self, indicators: Dict[str, pd.Series]) -> pd.Series:
        """
        組合各項壓力指標形成綜合指數

        Args:
            indicators: 各項壓力指標字典

        Returns:
            綜合壓力指數
        """
        try:
            # 對齊所有指標到共同的日期索引
            aligned_indicators = {}
            for name, series in indicators.items():
                if name != 'composite_pressure_index' and not series.empty:
                    aligned_indicators[name] = series

            if not aligned_indicators:
                return pd.Series()

            # 創建多索引 DataFrame 並前向填充缺失值
            combined_df = pd.DataFrame(aligned_indicators).fillna(method='ffill')

            # 使用權重計算綜合指數
            weights_used = {}
            weighted_sum = pd.Series(0, index=combined_df.index)

            for indicator_name, weight in self.indicator_weights.items():
                if indicator_name in combined_df.columns:
                    weights_used[indicator_name] = weight
                    weighted_sum += combined_df[indicator_name] * weight

            # 正規化權重
            total_weight = sum(weights_used.values())
            if total_weight > 0:
                composite_index = weighted_sum / total_weight
            else:
                composite_index = combined_df.mean(axis=1)

            logger.info(f"綜合壓力指數使用權重: {weights_used}")
            return composite_index

        except Exception as e:
            logger.error(f"壓力指標組合失敗: {str(e)}")
            return pd.Series()

    def get_pressure_status(self, pressure_index: pd.Series) -> pd.Series:
        """
        基於壓力指數判斷系統狀態

        Args:
            pressure_index: 壓力指數序列

        Returns:
            壓力狀態序列 (-1: 低壓力, 0: 中性, 1: 高壓力)
        """
        try:
            if pressure_index.empty:
                return pd.Series()

            # 使用分位數判斷狀態
            pressure_status = pd.cut(pressure_index,
                                   bins=[pressure_index.quantile(0.33),
                                         pressure_index.quantile(0.67)],
                                   labels=[-1, 0, 1],  # -1: 低壓力, 0: 中性, 1: 高壓力
                                   include_lowest=True)

            return pressure_status.astype(int)

        except Exception as e:
            logger.error(f"壓力狀態判斷失敗: {str(e)}")
            return pd.Series()


def main():
    """
    主函數 - 用於測試系統壓力指數計算
    """
    # 配置日誌
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 測試計算
    try:
        # 注意：需要有效的 FRED API 金鑰
        pressure_index = SystemPressureIndex()

        # 測試期間
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"測試系統壓力指數計算: {start_date} 到 {end_date}")

        # 計算壓力指數
        pressure_indicators = pressure_index.calculate_composite_pressure_index(start_date, end_date)

        if pressure_indicators:
            logger.info(f"成功計算以下壓力指標: {list(pressure_indicators.keys())}")

            # 顯示最新數據
            for name, series in pressure_indicators.items():
                if not series.empty:
                    latest_value = series.iloc[-1] if len(series) > 0 else 'N/A'
                    logger.info(f"{name}: {latest_value}")
        else:
            logger.warning("壓力指數計算失敗或無數據")

    except Exception as e:
        logger.error(f"測試失敗: {str(e)}")


if __name__ == "__main__":
    main()
