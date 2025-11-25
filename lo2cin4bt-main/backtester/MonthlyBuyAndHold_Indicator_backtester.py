import pandas as pd
import numpy as np

class MonthlyBuyAndHoldIndicator:
    """
    月度買入並持有策略指標

    該策略在每個月的第一個交易日買入，並在最後一個交易日賣出。
    """

    @staticmethod
    def calculate_signals(data: pd.DataFrame, **kwargs) -> pd.Series:
        """
        計算月度買入和賣出信號。

        Args:
            data (pd.DataFrame): 包含 'Time' 欄位的市場數據。

        Returns:
            pd.Series: 包含信號的 Series (1: 買入, -1: 賣出, 0: 無動作)。
        """
        # 確保 Time 欄位是 datetime 格式
        if not pd.api.types.is_datetime64_any_dtype(data['Time']):
            data['Time'] = pd.to_datetime(data['Time'])

        # 將 Time 設為索引以方便操作
        df = data.set_index('Time')

        # 創建一個全為 0 的信號 Series
        signals = pd.Series(0, index=df.index)

        # 找到每個月的第一天 (買入信號)
        # 條件：當前月份與前一個月份不同
        month_series = pd.Series(df.index.month, index=df.index)
        buy_signals = month_series != month_series.shift(1)
        signals[buy_signals] = 1

        # 找到每個月的最後一天 (賣出信號)
        # 條件：當前月份與後一個月份不同
        sell_signals = month_series != month_series.shift(-1)
        signals[sell_signals] = -1

        # 重設索引以匹配原始 DataFrame 格式
        signals = signals.reset_index(drop=True)

        return signals

    @staticmethod
    def vectorized_calculate_signals(tasks: list, signals_matrix: np.ndarray, data: pd.DataFrame):
        """
        向量化版本的信號計算，直接修改傳入的 signals_matrix。
        """
        # 由於此策略不依賴參數，所有任務的信號都相同。
        # 我們只需計算一次，然後應用於所有相關任務。

        # 確保 Time 欄位是 datetime 格式
        if not pd.api.types.is_datetime64_any_dtype(data['Time']):
            data['Time'] = pd.to_datetime(data['Time'])

        df = data.set_index('Time')

        # 計算買入信號
        month_series = pd.Series(df.index.month, index=df.index)
        buy_signals = month_series != month_series.shift(1)

        # 計算賣出信號
        sell_signals = month_series != month_series.shift(-1)

        # 將信號轉換為 +1 / -1
        signal_values = np.zeros(len(data))
        signal_values[buy_signals] = 1
        signal_values[sell_signals] = -1

        # 將計算出的信號應用於所有相關的任務
        for task_idx, indicator_idx, param in tasks:
            signals_matrix[:, task_idx, indicator_idx] = signal_values
