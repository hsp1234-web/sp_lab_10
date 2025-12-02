"""
自定義 Alpha 因子計算模組

實現 Alpha158 和 Alpha360 因子集的計算
支援台期貨數據的因子計算

作者：AI Assistant
日期：2025-12-01
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
import logging
from scipy import stats

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlphaFactorCalculator:
    """
    Alpha 因子計算器

    實現常見的技術因子計算，包括：
    - 趨勢因子 (trend)
    - 動量因子 (momentum)
    - 波動性因子 (volatility)
    - 成交量因子 (volume)
    - 相關性因子 (correlation)
    - 技術指標 (technical indicators)
    """

    def __init__(self, data: pd.DataFrame, window_sizes: Optional[List[int]] = None):
        """
        初始化因子計算器

        Args:
            data: OHLCV 數據框
            window_sizes: 計算窗口大小列表，默認 [5, 10, 20, 30, 60]
        """
        self.data = data.copy()
        self.window_sizes = window_sizes or [5, 10, 20, 30, 60]

        # 確保必要的欄位存在
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in self.data.columns]
        if missing_cols:
            raise ValueError(f"缺少必要的欄位: {missing_cols}")

        # 計算中間數據
        self._precompute_data()

        logger.info(f"AlphaFactorCalculator 初始化完成，數據形狀: {self.data.shape}")

    def _precompute_data(self):
        """預計算常用的數據"""
        # 收益率
        self.data['returns'] = self.data['close'].pct_change()

        # 對數收益率
        self.data['log_returns'] = np.log(self.data['close'] / self.data['close'].shift(1))

        # 價格變化
        self.data['price_change'] = self.data['close'] - self.data['open']
        self.data['high_low_diff'] = self.data['high'] - self.data['low']

        # 成交量變化
        self.data['volume_change'] = self.data['volume'].pct_change()

    def calculate_trend_factors(self) -> Dict[str, pd.Series]:
        """
        計算趨勢因子

        Returns:
            趨勢因子字典
        """
        factors = {}

        for window in self.window_sizes:
            # 價格趨勢
            factors[f'trend_price_{window}d'] = (
                self.data['close'] / self.data['close'].shift(window) - 1
            )

            # 移動平均趨勢
            ma_short = self.data['close'].rolling(window=window//2).mean()
            ma_long = self.data['close'].rolling(window=window).mean()
            factors[f'trend_ma_{window}d'] = (ma_short / ma_long - 1)

            # 線性回歸斜率趨勢
            factors[f'trend_slope_{window}d'] = self._calculate_slope(
                self.data['close'], window
            )

        return factors

    def calculate_momentum_factors(self) -> Dict[str, pd.Series]:
        """
        計算動量因子

        Returns:
            動量因子字典
        """
        factors = {}

        for window in self.window_sizes:
            # 簡單動量
            factors[f'momentum_simple_{window}d'] = (
                self.data['close'] / self.data['close'].shift(window) - 1
            )

            # 指數加權動量
            ewm = self.data['close'].ewm(span=window).mean()
            factors[f'momentum_ewm_{window}d'] = (
                self.data['close'] / ewm.shift(1) - 1
            )

            # RSI 動量
            factors[f'momentum_rsi_{window}d'] = self._calculate_rsi(window)

            # Williams %R
            factors[f'momentum_williams_{window}d'] = self._calculate_williams_r(window)

        return factors

    def calculate_volatility_factors(self) -> Dict[str, pd.Series]:
        """
        計算波動性因子

        Returns:
            波動性因子字典
        """
        factors = {}

        for window in self.window_sizes:
            # 歷史波動性 (收益率標準差)
            factors[f'volatility_returns_{window}d'] = (
                self.data['returns'].rolling(window=window).std()
            )

            # 價格波動性 (價格範圍)
            price_range = (self.data['high'] - self.data['low']) / self.data['close']
            factors[f'volatility_price_{window}d'] = price_range.rolling(window=window).std()

            # ATR (平均真實波動範圍)
            factors[f'volatility_atr_{window}d'] = self._calculate_atr(window)

            # 帕金森波動性
            factors[f'volatility_parkinson_{window}d'] = self._calculate_parkinson_volatility(window)

        return factors

    def calculate_volume_factors(self) -> Dict[str, pd.Series]:
        """
        計算成交量因子

        Returns:
            成交量因子字典
        """
        factors = {}

        for window in self.window_sizes:
            # 成交量趨勢
            factors[f'volume_trend_{window}d'] = (
                self.data['volume'] / self.data['volume'].shift(window) - 1
            )

            # 成交量比率 (相對於價格變化)
            price_change_abs = abs(self.data['returns'])
            factors[f'volume_price_ratio_{window}d'] = (
                self.data['volume'] / price_change_abs.rolling(window=window).mean()
            )

            # OBV (能量潮指標)
            factors[f'volume_obv_{window}d'] = self._calculate_obv(window)

            # 成交量波動性
            factors[f'volume_volatility_{window}d'] = (
                self.data['volume_change'].rolling(window=window).std()
            )

        return factors

    def calculate_technical_factors(self) -> Dict[str, pd.Series]:
        """
        計算技術指標因子

        Returns:
            技術指標因子字典
        """
        factors = {}

        for window in self.window_sizes:
            # MACD
            macd, signal, hist = self._calculate_macd(window)
            factors[f'technical_macd_{window}d'] = macd
            factors[f'technical_macd_signal_{window}d'] = signal
            factors[f'technical_macd_hist_{window}d'] = hist

            # Bollinger Bands
            upper, middle, lower = self._calculate_bollinger_bands(window)
            factors[f'technical_bb_upper_{window}d'] = upper
            factors[f'technical_bb_middle_{window}d'] = middle
            factors[f'technical_bb_lower_{window}d'] = lower
            factors[f'technical_bb_width_{window}d'] = (upper - lower) / middle

            # KDJ 指標
            k, d, j = self._calculate_kdj(window)
            factors[f'technical_kdj_k_{window}d'] = k
            factors[f'technical_kdj_d_{window}d'] = d
            factors[f'technical_kdj_j_{window}d'] = j

        return factors

    def calculate_correlation_factors(self, other_assets: Optional[Dict[str, pd.Series]] = None) -> Dict[str, pd.Series]:
        """
        計算相關性因子

        Args:
            other_assets: 其他資產的價格序列字典

        Returns:
            相關性因子字典
        """
        factors = {}

        for window in self.window_sizes:
            # 自相關性
            factors[f'correlation_autocorr_{window}d'] = (
                self.data['returns'].rolling(window=window).corr(
                    self.data['returns'].shift(1)
                )
            )

            # 如果有其他資產，計算交叉相關性
            if other_assets:
                for asset_name, asset_prices in other_assets.items():
                    asset_returns = asset_prices.pct_change()
                    corr = self.data['returns'].rolling(window=window).corr(asset_returns)
                    factors[f'correlation_{asset_name}_{window}d'] = corr

        return factors

    def calculate_all_factors(self, other_assets: Optional[Dict[str, pd.Series]] = None) -> pd.DataFrame:
        """
        計算所有因子

        Args:
            other_assets: 其他資產的價格序列字典

        Returns:
            包含所有因子的數據框
        """
        logger.info("開始計算所有 Alpha 因子...")

        all_factors = {}

        # 計算各種類型的因子
        factor_groups = [
            self.calculate_trend_factors,
            self.calculate_momentum_factors,
            self.calculate_volatility_factors,
            self.calculate_volume_factors,
            self.calculate_technical_factors,
            lambda: self.calculate_correlation_factors(other_assets)
        ]

        for calculate_func in factor_groups:
            try:
                factors = calculate_func()
                all_factors.update(factors)
                logger.info(f"計算完成 {len(factors)} 個因子")
            except Exception as e:
                logger.warning(f"因子計算失敗: {e}")

        # 合併因子到數據框
        factors_df = pd.DataFrame(all_factors, index=self.data.index)

        # 清理數據 (移除 NaN 和無限值)
        factors_df = factors_df.replace([np.inf, -np.inf], np.nan)
        factors_df = factors_df.dropna(axis=1, how='all')  # 移除全為 NaN 的欄位

        logger.info(f"Alpha 因子計算完成，共 {factors_df.shape[1]} 個因子")

        return factors_df

    # 私有方法：具體指標計算實現
    def _calculate_slope(self, series: pd.Series, window: int) -> pd.Series:
        """計算線性回歸斜率"""
        def slope_func(y):
            if len(y) < window:
                return np.nan
            x = np.arange(len(y))
            slope = np.polyfit(x, y, 1)[0]
            return slope

        return series.rolling(window=window).apply(slope_func, raw=False)

    def _calculate_rsi(self, window: int) -> pd.Series:
        """計算 RSI 指標"""
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_williams_r(self, window: int) -> pd.Series:
        """計算 Williams %R 指標"""
        highest_high = self.data['high'].rolling(window=window).max()
        lowest_low = self.data['low'].rolling(window=window).min()
        williams_r = -100 * (highest_high - self.data['close']) / (highest_high - lowest_low)
        return williams_r

    def _calculate_atr(self, window: int) -> pd.Series:
        """計算 ATR (平均真實波動範圍)"""
        high_low = self.data['high'] - self.data['low']
        high_close = np.abs(self.data['high'] - self.data['close'].shift(1))
        low_close = np.abs(self.data['low'] - self.data['close'].shift(1))

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=window).mean()
        return atr

    def _calculate_parkinson_volatility(self, window: int) -> pd.Series:
        """計算帕金森波動性"""
        log_hl = np.log(self.data['high'] / self.data['low'])
        parkinson = log_hl.rolling(window=window).std() / np.sqrt(4 * np.log(2))
        return parkinson

    def _calculate_obv(self, window: int) -> pd.Series:
        """計算 OBV (能量潮指標)"""
        obv = pd.Series(index=self.data.index, dtype=float)
        obv.iloc[0] = self.data['volume'].iloc[0]

        for i in range(1, len(self.data)):
            if self.data['close'].iloc[i] > self.data['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + self.data['volume'].iloc[i]
            elif self.data['close'].iloc[i] < self.data['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - self.data['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]

        return obv

    def _calculate_macd(self, window: int) -> tuple:
        """計算 MACD 指標"""
        fast_period = window // 3
        slow_period = window
        signal_period = window // 6

        fast_ema = self.data['close'].ewm(span=fast_period).mean()
        slow_ema = self.data['close'].ewm(span=slow_period).mean()
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=signal_period).mean()
        hist = macd - signal

        return macd, signal, hist

    def _calculate_bollinger_bands(self, window: int) -> tuple:
        """計算布林帶"""
        middle = self.data['close'].rolling(window=window).mean()
        std = self.data['close'].rolling(window=window).std()
        upper = middle + 2 * std
        lower = middle - 2 * std

        return upper, middle, lower

    def _calculate_kdj(self, window: int) -> tuple:
        """計算 KDJ 指標"""
        highest_high = self.data['high'].rolling(window=window).max()
        lowest_low = self.data['low'].rolling(window=window).min()

        rsv = 100 * (self.data['close'] - lowest_low) / (highest_high - lowest_low)
        k = rsv.ewm(com=2).mean()
        d = k.ewm(com=2).mean()
        j = 3 * k - 2 * d

        return k, d, j


def create_alpha158_factors(data: pd.DataFrame,
                          other_assets: Optional[Dict[str, pd.Series]] = None) -> pd.DataFrame:
    """
    創建 Alpha158 因子集

    這是簡化的 Alpha158 實現，包含最核心的因子

    Args:
        data: OHLCV 數據
        other_assets: 其他資產價格數據

    Returns:
        Alpha158 因子數據框
    """
    calculator = AlphaFactorCalculator(data)
    factors = calculator.calculate_all_factors(other_assets)

    # 動態選擇可用的 Alpha158 核心因子
    # 根據實際產生的因子名稱進行匹配
    alpha158_patterns = [
        # 趨勢因子 - 匹配 trend_*_20d 或 trend_*_30d
        [col for col in factors.columns if col.startswith('trend_') and ('_20d' in col or '_30d' in col)],
        # 動量因子 - 匹配 momentum_*_20d 或 momentum_*_30d, 以及 RSI 等
        [col for col in factors.columns if col.startswith('momentum_') and ('_20d' in col or '_30d' in col or '_14d' in col)],
        # 波動性因子 - 匹配 volatility_*_20d 或 volatility_*_30d
        [col for col in factors.columns if col.startswith('volatility_') and ('_20d' in col or '_30d' in col or '_14d' in col)],
        # 成交量因子 - 匹配 volume_*_20d 或 volume_*_30d
        [col for col in factors.columns if col.startswith('volume_') and ('_20d' in col or '_30d' in col)],
        # 技術指標因子 - 匹配 technical_*_20d, technical_*_30d 或特定指標
        [col for col in factors.columns if col.startswith('technical_') and ('_20d' in col or '_30d' in col or '_26d' in col or '_14d' in col)]
    ]

    # 從每個類別選擇最多 2-3 個因子
    selected_factors = []
    for pattern_list in alpha158_patterns:
        selected_factors.extend(pattern_list[:3])  # 每個類別最多選 3 個

    # 如果沒有匹配到足夠因子，使用備用策略：選擇所有因子
    if len(selected_factors) < 10:
        logger.warning("Alpha158 因子匹配不足，使用所有可用因子")
        selected_factors = list(factors.columns)

    # 確保因子存在
    available_factors = [f for f in selected_factors if f in factors.columns]
    result_factors = factors[available_factors].copy()

    logger.info(f"Alpha158 因子創建完成，共 {result_factors.shape[1]} 個因子")
    logger.info(f"選取的因子: {available_factors[:5]}..." if len(available_factors) > 5 else f"選取的因子: {available_factors}")

    return result_factors


def create_alpha360_factors(data: pd.DataFrame,
                          other_assets: Optional[Dict[str, pd.Series]] = None) -> pd.DataFrame:
    """
    創建 Alpha360 因子集

    擴展版的因子集，包含更多樣化的因子

    Args:
        data: OHLCV 數據
        other_assets: 其他資產價格數據

    Returns:
        Alpha360 因子數據框
    """
    calculator = AlphaFactorCalculator(data)
    factors = calculator.calculate_all_factors(other_assets)

    # Alpha360 包含所有可用因子
    logger.info(f"Alpha360 因子創建完成，共 {factors.shape[1]} 個因子")

    return factors


class FactorEvaluator:
    """
    因子評估工具

    提供因子評估相關功能，包括：
    - IC (Information Coefficient) 計算
    - 分組報酬分析
    - 因子穩定性分析
    - 因子相關性分析
    """

    def __init__(self, factors: pd.DataFrame, returns: pd.Series, forward_periods: Optional[List[int]] = None):
        """
        初始化因子評估器

        Args:
            factors: 因子數據框 (index=日期, columns=因子名稱)
            returns: 報酬序列 (index=日期)
            forward_periods: 向前看幾期的報酬，默認 [1, 5, 10, 20]
        """
        self.factors = factors.copy()
        self.returns = returns.copy()
        self.forward_periods = forward_periods or [1, 5, 10, 20]

        # 計算向前報酬
        self.forward_returns = {}
        for period in self.forward_periods:
            self.forward_returns[period] = self.returns.shift(-period)

        logger.info(f"FactorEvaluator 初始化完成，因子數量: {self.factors.shape[1]}")

    def calculate_ic(self, factor_name: str, forward_period: int = 1,
                    method: str = 'spearman') -> Dict[str, float]:
        """
        計算單個因子的 IC 值

        Args:
            factor_name: 因子名稱
            forward_period: 向前報酬期數
            method: 相關係數方法 ('spearman' 或 'pearson')

        Returns:
            IC 統計結果字典
        """
        if factor_name not in self.factors.columns:
            raise ValueError(f"因子 '{factor_name}' 不存在")

        if forward_period not in self.forward_returns:
            raise ValueError(f"向前期數 {forward_period} 不在預設範圍內")

        factor_values = self.factors[factor_name]
        future_returns = self.forward_returns[forward_period]

        # 移除 NaN 值
        valid_data = pd.concat([factor_values, future_returns], axis=1).dropna()
        if len(valid_data) < 30:  # 至少需要 30 個樣本
            return {
                'ic': np.nan,
                'ic_abs': np.nan,
                't_stat': np.nan,
                'p_value': np.nan,
                'sample_size': len(valid_data)
            }

        if method == 'spearman':
            ic, p_value = stats.spearmanr(valid_data.iloc[:, 0], valid_data.iloc[:, 1])
        elif method == 'pearson':
            ic, p_value = stats.pearsonr(valid_data.iloc[:, 0], valid_data.iloc[:, 1])
        else:
            raise ValueError("method 必須是 'spearman' 或 'pearson'")

        t_stat = ic * np.sqrt(len(valid_data) - 2) / np.sqrt(1 - ic**2)

        return {
            'ic': ic,
            'ic_abs': abs(ic),
            't_stat': t_stat,
            'p_value': p_value,
            'sample_size': len(valid_data)
        }

    def calculate_ic_matrix(self, forward_period: int = 1,
                           method: str = 'spearman') -> pd.DataFrame:
        """
        計算所有因子的 IC 值

        Args:
            forward_period: 向前報酬期數
            method: 相關係數方法

        Returns:
            IC 統計結果數據框
        """
        results = []

        for factor_name in self.factors.columns:
            ic_stats = self.calculate_ic(factor_name, forward_period, method)
            ic_stats['factor'] = factor_name
            results.append(ic_stats)

        ic_df = pd.DataFrame(results)
        ic_df = ic_df.set_index('factor')

        # 按 IC 絕對值排序
        ic_df = ic_df.sort_values('ic_abs', ascending=False)

        return ic_df

    def quantile_analysis(self, factor_name: str, n_quantiles: int = 5,
                         forward_period: int = 1) -> pd.DataFrame:
        """
        分組報酬分析

        Args:
            factor_name: 因子名稱
            n_quantiles: 分組數量
            forward_period: 向前報酬期數

        Returns:
            分組報酬統計數據框
        """
        if factor_name not in self.factors.columns:
            raise ValueError(f"因子 '{factor_name}' 不存在")

        factor_values = self.factors[factor_name]
        future_returns = self.forward_returns[forward_period]

        # 合併數據並移除 NaN
        combined_data = pd.concat([factor_values, future_returns], axis=1).dropna()
        combined_data.columns = ['factor', 'return']

        if len(combined_data) < n_quantiles * 10:  # 確保每組有足夠樣本
            logger.warning(f"樣本數量不足: {len(combined_data)}")

        # 按因子值分組
        combined_data['quantile'] = pd.qcut(combined_data['factor'], n_quantiles,
                                          labels=[f'Q{i+1}' for i in range(n_quantiles)],
                                          duplicates='drop')

        # 計算每組的統計
        quantile_stats = []
        for quantile in combined_data['quantile'].unique():
            group_data = combined_data[combined_data['quantile'] == quantile]
            stats_dict = {
                'quantile': quantile,
                'mean_return': group_data['return'].mean(),
                'std_return': group_data['return'].std(),
                'count': len(group_data),
                'sharpe_ratio': group_data['return'].mean() / group_data['return'].std() if group_data['return'].std() > 0 else np.nan
            }
            quantile_stats.append(stats_dict)

        result_df = pd.DataFrame(quantile_stats)

        # 計算 Q5-Q1 差異
        if len(result_df) >= 2:
            q1_return = result_df[result_df['quantile'] == 'Q1']['mean_return'].iloc[0]
            q5_return = result_df[result_df['quantile'] == 'Q5']['mean_return'].iloc[0]
            result_df['q5_minus_q1'] = q5_return - q1_return

        return result_df

    def factor_correlation_matrix(self, method: str = 'spearman') -> pd.DataFrame:
        """
        計算因子間相關性矩陣

        Args:
            method: 相關係數方法

        Returns:
            相關性矩陣
        """
        if method == 'spearman':
            corr_matrix = self.factors.corr(method='spearman')
        elif method == 'pearson':
            corr_matrix = self.factors.corr(method='pearson')
        else:
            raise ValueError("method 必須是 'spearman' 或 'pearson'")

        return corr_matrix

    def factor_stability_analysis(self, factor_name: str, window: int = 60) -> pd.Series:
        """
        分析因子的時間穩定性 (滾動 IC)

        Args:
            factor_name: 因子名稱
            window: 滾動窗口大小

        Returns:
            滾動 IC 序列
        """
        if factor_name not in self.factors.columns:
            raise ValueError(f"因子 '{factor_name}' 不存在")

        rolling_ic = []

        for i in range(window, len(self.factors)):
            factor_window = self.factors[factor_name].iloc[i-window:i]
            return_window = self.returns.iloc[i-window:i]

            valid_data = pd.concat([factor_window, return_window], axis=1).dropna()
            if len(valid_data) > 10:
                ic, _ = stats.spearmanr(valid_data.iloc[:, 0], valid_data.iloc[:, 1])
                rolling_ic.append(ic)
            else:
                rolling_ic.append(np.nan)

        return pd.Series(rolling_ic, index=self.factors.index[window:])

    def get_factor_summary(self, forward_period: int = 1) -> pd.DataFrame:
        """
        生成因子總結報告

        Args:
            forward_period: 向前報酬期數

        Returns:
            因子總結數據框
        """
        ic_matrix = self.calculate_ic_matrix(forward_period)

        summary_data = []

        for factor_name in ic_matrix.index:
            # 分組分析
            quantile_df = self.quantile_analysis(factor_name, forward_period=forward_period)

            # 穩定性分析
            stability = self.factor_stability_analysis(factor_name)
            stability_mean = stability.mean()
            stability_std = stability.std()

            summary_dict = {
                'factor': factor_name,
                'ic': ic_matrix.loc[factor_name, 'ic'],
                'ic_abs': ic_matrix.loc[factor_name, 'ic_abs'],
                'ic_t_stat': ic_matrix.loc[factor_name, 't_stat'],
                'ic_p_value': ic_matrix.loc[factor_name, 'p_value'],
                'q5_minus_q1': quantile_df['q5_minus_q1'].iloc[0] if 'q5_minus_q1' in quantile_df.columns else np.nan,
                'stability_mean': stability_mean,
                'stability_std': stability_std,
                'stability_score': stability_mean / stability_std if stability_std > 0 else np.nan
            }

            summary_data.append(summary_dict)

        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('ic_abs', ascending=False)

        return summary_df


# 使用示例
if __name__ == "__main__":
    # 創建示例數據
    dates = pd.date_range('2020-01-01', periods=200, freq='D')
    np.random.seed(42)

    sample_data = pd.DataFrame({
        'open': 100 + np.random.randn(200).cumsum(),
        'high': 105 + np.random.randn(200).cumsum(),
        'low': 95 + np.random.randn(200).cumsum(),
        'close': 100 + np.random.randn(200).cumsum(),
        'volume': np.random.randint(1000, 10000, 200)
    }, index=dates)

    # 修正 OHLC 邏輯
    for i in range(len(sample_data)):
        sample_data.loc[sample_data.index[i], 'high'] = max(
            sample_data.loc[sample_data.index[i], ['open', 'close']].max(),
            sample_data.loc[sample_data.index[i], 'high']
        )
        sample_data.loc[sample_data.index[i], 'low'] = min(
            sample_data.loc[sample_data.index[i], ['open', 'close']].min(),
            sample_data.loc[sample_data.index[i], 'low']
        )

    # 創建因子
    calculator = AlphaFactorCalculator(sample_data)
    factors_df = calculator.calculate_all_factors()

    # 計算報酬
    returns = sample_data['close'].pct_change()

    # 創建因子評估器
    evaluator = FactorEvaluator(factors_df, returns)

    # 測試 IC 計算
    print("=== IC 計算測試 ===")
    if factors_df.shape[1] > 0:
        first_factor = factors_df.columns[0]
        ic_stats = evaluator.calculate_ic(first_factor, forward_period=1)
        print(f"因子 '{first_factor}' 的 IC 統計:")
        for key, value in ic_stats.items():
            print(f"  {key}: {value:.4f}" if isinstance(value, (int, float)) and not np.isnan(value) else f"  {key}: {value}")

        # 測試 IC 矩陣
        print(f"\n=== IC 矩陣 (前 5 個因子) ===")
        ic_matrix = evaluator.calculate_ic_matrix(forward_period=1)
        print(ic_matrix.head())

        # 測試分組分析
        print(f"\n=== 分組分析: {first_factor} ===")
        quantile_df = evaluator.quantile_analysis(first_factor, n_quantiles=5)
        print(quantile_df)

        print("
因子評估工具測試完成！"
    else:
        print("沒有可用的因子進行測試")

    # 創建 Alpha158 因子
    alpha158 = create_alpha158_factors(sample_data)
    print(f"\nAlpha158 因子形狀: {alpha158.shape}")
    print("Alpha158 因子名稱:")
    print(alpha158.columns.tolist()[:5])  # 只顯示前 5 個
