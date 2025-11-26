# -*- coding: utf-8 -*-
"""
此檔案用於存放所有客製化或組合的技術指標計算。
"""

import pandas as pd
import pandas_ta as ta

def add_supertrend(df: pd.DataFrame, length: int = 7, multiplier: float = 3.0) -> pd.DataFrame:
    """
    計算並新增超級趨勢指標 (SuperTrend) 到 DataFrame。

    Args:
        df (pd.DataFrame): 包含 'High', 'Low', 'Close' 的 K 線數據。
        length (int): ATR 計算的週期。
        multiplier (float): ATR 的乘數。

    Returns:
        pd.DataFrame: 附帶超級趨勢指標欄位的 DataFrame。
                      欄位包括: 'SUPERT' (趨勢值), 'SUPERTd' (趨勢方向), 'SUPERTl' (長倉趨勢線), 'SUPERTs' (短倉趨勢線)。
    """
    df.ta.supertrend(length=length, multiplier=multiplier, append=True)
    return df

def add_chandelier_exit(df: pd.DataFrame, atr_period: int = 22, atr_multiplier: float = 3.0) -> pd.DataFrame:
    """
    計算並新增錢德勒停損 (Chandelier Exit) 到 DataFrame。

    錢德勒停損分為多頭停損 (出場) 點和空頭停損 (出場) 點。
    - Long Stop: 過去 N 日的最高價 - ATR * M
    - Short Stop: 過去 N 日的最低價 + ATR * M

    Args:
        df (pd.DataFrame): 包含 'High', 'Low', 'Close' 的 K 線數據。
        atr_period (int): ATR 和最高/最低價的計算週期。
        atr_multiplier (float): ATR 的乘數。

    Returns:
        pd.DataFrame: 附帶 'ce_long' 和 'ce_short' 欄位的 DataFrame。
    """
    if 'ATR' not in df.columns:
        df.ta.atr(length=atr_period, append=True)

    # Backtesting.py 會自動處理欄位名稱，所以我們使用縮寫
    atr_col = f'ATRr_{atr_period}'
    df.ta.atr(length=atr_period, append=True, col_names=(atr_col,))

    highest_high = df['High'].rolling(window=atr_period).max()
    lowest_low = df['Low'].rolling(window=atr_period).min()

    df['ce_long'] = highest_high - df[atr_col] * atr_multiplier
    df['ce_short'] = lowest_low + df[atr_col] * atr_multiplier

    return df
