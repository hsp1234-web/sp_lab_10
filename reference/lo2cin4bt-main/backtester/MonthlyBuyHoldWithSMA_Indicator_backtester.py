import pandas as pd
import numpy as np
from .Indicators_backtester import IndicatorsBacktester

class MonthlyBuyHoldWithSMAIndicator:
    """
    月度買入持有並結合 SMA 濾網的策略指標

    該策略在每個月的第一個交易日，當且僅當收盤價高於指定的 SMA 週期時買入，
    並在該月最後一個交易日賣出。
    """

    @staticmethod
    def calculate_signals(data: pd.DataFrame, params: object, **kwargs) -> pd.Series:
        """
        計算結合 SMA 濾網的月度買入和賣出信號。

        Args:
            data (pd.DataFrame): 包含 'Time' 和 'Close' 欄位的市場數據。
            params (object): 包含 `sma_period` 屬性的參數對象。

        Returns:
            pd.Series: 包含信號的 Series (1: 買入, -1: 賣出, 0: 無動作)。
        """
        sma_period = params.params.sma_period

        # 計算 SMA
        sma = data['Close'].rolling(window=sma_period).mean()

        # 確保 Time 欄位是 datetime 格式
        if not pd.api.types.is_datetime64_any_dtype(data['Time']):
            data['Time'] = pd.to_datetime(data['Time'])

        df = data.set_index('Time')

        signals = pd.Series(0, index=df.index)

        # 找到每個月的第一個和最後一個交易日
        month_series = pd.Series(df.index.month, index=df.index)
        buy_days_indexer = month_series != month_series.shift(1)
        sell_days_indexer = month_series != month_series.shift(-1)

        # 僅在月初符合 SMA 條件時，才將該月標記為「有效交易月」
        valid_month_entry_days = (df['Close'] > sma) & buy_days_indexer
        is_valid_month = valid_month_entry_days.groupby(df.index.to_period('M')).transform('any')

        # 只在有效交易月的首日買入
        signals[buy_days_indexer & is_valid_month] = 1
        # 只在有效交易月的末日賣出
        signals[sell_days_indexer & is_valid_month] = -1

        return signals.reset_index(drop=True)

    @staticmethod
    def vectorized_calculate_signals(tasks: list, signals_matrix: np.ndarray, data: pd.DataFrame):
        """
        向量化版本的信號計算，直接修改傳入的 signals_matrix。
        """
        # 1. 按 sma_period 分組任務
        sma_groups = {}
        for task_idx, indicator_idx, param in tasks:
            sma_period = param.params.sma_period
            if sma_period not in sma_groups:
                sma_groups[sma_period] = []
            sma_groups[sma_period].append((task_idx, indicator_idx, param))

        # 2. 預先計算通用的信號日期
        if not pd.api.types.is_datetime64_any_dtype(data['Time']):
            data['Time'] = pd.to_datetime(data['Time'])

        df = data.set_index('Time')
        month_series = pd.Series(df.index.month, index=df.index)
        buy_days_indexer = (month_series != month_series.shift(1)).values
        sell_days_indexer = (month_series != month_series.shift(-1)).values

        # 為了執行 groupby().transform('any') 的等效操作，我們需要月份的 ID
        month_group_ids, _ = pd.factorize(df.index.to_period('M'))

        # 3. 為每個 SMA 週期組計算信號
        for sma_period, group_tasks in sma_groups.items():
            # 計算 SMA
            sma = data['Close'].rolling(window=sma_period).mean().values

            # 識別出在月初滿足條件的「有效月份」
            valid_month_entry_days = (data['Close'].values > sma) & buy_days_indexer

            # 使用 NumPy 的方式實現 groupby().transform('any')
            # 首先，找出每個月份的起始索引
            _, month_start_indices = np.unique(month_group_ids, return_index=True)
            # 檢查每個月是否有任何一天是有效的進場日
            month_has_valid_entry = np.maximum.reduceat(valid_month_entry_days, month_start_indices)
            # 將這個布林值廣播回該月的所有天
            is_valid_month = month_has_valid_entry[month_group_ids]

            # 產生信號數組 (只在有效月份進行買賣)
            signal_values = np.zeros(len(data))
            signal_values[buy_days_indexer & is_valid_month] = 1
            signal_values[sell_days_indexer & is_valid_month] = -1

            # 將計算出的信號應用於該組的所有任務
            for task_idx, indicator_idx, param in group_tasks:
                signals_matrix[:, task_idx, indicator_idx] = signal_values
