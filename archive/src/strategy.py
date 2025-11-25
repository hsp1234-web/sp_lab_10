# -*- coding: utf-8 -*-
"""
此檔案用於定義核心的交易策略邏輯。
"""
import pandas as pd
import pandas_ta as ta
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover

# --- 輔助函式，確保指標回傳單一且正確的 pd.Series ---

def supertrend_direction(high, low, close, length: int, multiplier: float) -> pd.Series:
    """
    計算並只返回 Supertrend 的方向序列。
    增加對 None 值的穩健處理。
    """
    st = ta.supertrend(high=pd.Series(high), low=pd.Series(low), close=pd.Series(close), length=length, multiplier=multiplier)
    if st is None:
        return pd.Series(np.nan, index=pd.Series(close).index)
    return st[f'SUPERTd_{length}_{multiplier}']

def atr_series(high, low, close, length: int) -> pd.Series:
    """
    計算並返回 ATR 序列。
    增加對 None 值的穩健處理。
    """
    atr = ta.atr(high=pd.Series(high), low=pd.Series(low), close=pd.Series(close), length=length)
    if atr is None:
        return pd.Series(np.nan, index=pd.Series(close).index)
    return atr


class SupertrendBNFStrategy(Strategy):
    """
    結合超級趨勢 (Supertrend) 作為趨勢過濾器，
    並在價格大幅回調時 (BNF - Buy Near Fear) 進場的策略。
    使用錢德勒停損 (Chandelier Exit) 作為出場機制。
    """

    # --- 策略參數 ---
    st_length = 10
    st_multiplier = 3.0
    bnf_ma_period = 120
    bnf_entry_bias = -0.1
    ce_atr_period = 22
    ce_atr_multiplier = 3.0

    def init(self):
        """
        策略初始化，計算所有需要的技術指標。
        """
        # 為了方便在 lambda 函式中使用，先將資料賦值給局部變數
        high, low, close = self.data.High, self.data.Low, self.data.Close

        # 超級趨勢 Supertrend
        self.supertrend_dir = self.I(
            supertrend_direction,
            high, low, close,
            self.st_length, self.st_multiplier
        )

        # 乖離率 (BIAS)
        def calculate_bias(price_series, ma_period):
            ma = ta.sma(price_series, length=ma_period)
            return (price_series - ma) / ma

        self.bias = self.I(calculate_bias, pd.Series(close), self.bnf_ma_period)

        # 錢德勒停損 Chandelier Exit
        def calculate_chandelier_exit(high_series, low_series, close_series, atr_period, atr_multiplier):
            atr = atr_series(high_series, low_series, close_series, atr_period)
            highest_high = pd.Series(high_series).rolling(atr_period).max()
            return highest_high - atr * atr_multiplier

        self.chandelier_exit_long = self.I(
            calculate_chandelier_exit,
            pd.Series(high), pd.Series(low), pd.Series(close),
            self.ce_atr_period, self.ce_atr_multiplier
        )

    def next(self):
        """
        策略的主要邏輯，每個時間點 (K棒) 都會被呼叫。
        """
        # --- 進場條件 ---
        is_uptrend = self.supertrend_dir[-1] == 1
        is_fear_dip = self.bias[-1] < self.bnf_entry_bias

        if is_uptrend and is_fear_dip and not self.position:
            self.buy()

        # --- 出場條件 ---
        if self.position and self.data.Close[-1] < self.chandelier_exit_long[-1]:
            self.position.close()
