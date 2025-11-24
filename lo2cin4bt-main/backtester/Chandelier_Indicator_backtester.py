import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional

class ChandelierIndicator:
    """
    吊燈停損指標 (Chandelier Stop Indicator)
    
    策略邏輯：
    1. 計算 ATR (Average True Range)。
    2. 計算 N 週期內的最高價 (High) 和最低價 (Low)。
    3. 多頭停損點 (Long Stop) = N 週期最高價 - Multiplier * ATR
    4. 空頭停損點 (Short Stop) = N 週期最低價 + Multiplier * ATR
    5. 進場信號：收盤價突破前一期 High Rolling Max (趨勢轉多)
    6. 出場信號：收盤價跌破 Long Stop (多單出場) 或 突破 Short Stop (空單出場)
    
    參數：
    - length (int): 計算 ATR 和 Rolling Max/Min 的週期 (預設 22)
    - multiplier (float): ATR 的倍數 (預設 3.0)
    """
    
    STRATEGY_DESCRIPTIONS = {
        "CHANDELIER": "吊燈停損策略 (Trend Following)"
    }

    def __init__(self, data: pd.DataFrame, params: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.data = data
        self.params = params
        self.logger = logger or logging.getLogger(__name__)
        
        # 參數提取
        self.length = int(params.get('length', 22))
        self.multiplier = float(params.get('multiplier', 3.0))

    @staticmethod
    def get_params(strat_idx: int = 1, params_config: Optional[Dict] = None) -> List[Any]:
        """
        產生參數組合
        """
        from .IndicatorParams_backtester import IndicatorParams
        
        # 預設參數範圍
        lengths = [22]
        multipliers = [3.0]
        
        if params_config:
            lengths = params_config.get('length', lengths)
            multipliers = params_config.get('multiplier', multipliers)
            
        param_combinations = []
        for length in lengths:
            for mult in multipliers:
                param_combinations.append(
                    IndicatorParams(
                        indicator_type='CHANDELIER',
                        buy_threshold=0, # 不使用
                        sell_threshold=0, # 不使用
                        window=length,
                        extra_params={'length': length, 'multiplier': mult}
                    )
                )
        return param_combinations

    def generate_signals(self, predictor: Optional[str] = None) -> np.ndarray:
        """
        產生交易信號
        Returns:
            np.ndarray: 信號數組 (1: 多頭進場, -1: 空頭進場, 0: 無信號/持有)
        """
        df = self.data.copy()
        
        # 確保有必要的欄位
        required_cols = ['High', 'Low', 'Close']
        for col in required_cols:
            if col not in df.columns:
                # 嘗試匹配大小寫
                found = False
                for c in df.columns:
                    if c.lower() == col.lower():
                        df[col] = df[c]
                        found = True
                        break
                if not found:
                    self.logger.error(f"缺少必要欄位: {col}")
                    return np.zeros(len(df))

        try:
            # 手動計算 ATR
            high = df['High']
            low = df['Low']
            close = df['Close']
            prev_close = close.shift(1)
            
            tr1 = high - low
            tr2 = (high - prev_close).abs()
            tr3 = (low - prev_close).abs()
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            # 使用 RMA (Wilder's Smoothing) 計算 ATR，或者簡單 SMA/EMA
            # pandas_ta 預設可能是 RMA
            # 這裡使用簡單的 rolling mean 作為近似，或者實現 RMA
            # RMA: alpha = 1/length
            df['ATR'] = tr.ewm(alpha=1/self.length, adjust=False).mean()
            
            # 計算 Rolling Max High / Min Low
            df['High_Roll'] = df['High'].rolling(self.length).max()
            df['Low_Roll'] = df['Low'].rolling(self.length).min()
            
            # 計算 Chandelier Stops
            df['Chandelier_Long'] = df['High_Roll'] - self.multiplier * df['ATR']
            df['Chandelier_Short'] = df['Low_Roll'] + self.multiplier * df['ATR']
            
            # 產生趨勢信號
            
            # 初始化信號
            signals = np.zeros(len(df))
            
            close_vals = df['Close'].values
            high_roll = df['High_Roll'].values
            chan_long = df['Chandelier_Long'].values
            
            # 實作向量化邏輯 (Shift 1)
            prev_high_roll = np.roll(high_roll, 1)
            prev_chan_long = np.roll(chan_long, 1)
            
            # 處理邊界
            prev_high_roll[0] = np.inf
            prev_chan_long[0] = -np.inf
            
            # 簡單趨勢判斷
            trend_series = pd.Series(0, index=df.index)
            
            # 條件 1: Close > Prev High Roll -> Trend = 1
            cond_up = close_vals > prev_high_roll
            
            # 條件 2: Close < Prev Chandelier Long -> Trend = -1
            cond_down = close_vals < prev_chan_long
            
            # 結合
            temp_trend = pd.Series(np.nan, index=df.index)
            temp_trend[cond_up] = 1
            temp_trend[cond_down] = -1
            
            # Debug info
            self.logger.info(f"Cond Up count: {np.sum(cond_up)}")
            self.logger.info(f"Cond Down count: {np.sum(cond_down)}")
            
            # 填補 NaN (保持前一狀態)
            trend_series = temp_trend.ffill().fillna(0)
            
            # 計算信號 (Diff)
            signals_series = trend_series.diff().fillna(0)
            
            # 轉換為 numpy array
            signals = signals_series.values
            
            self.logger.info(f"Signals generated: {np.sum(signals != 0)}")
            
            return signals

        except Exception as e:
            self.logger.error(f"Chandelier Indicator 計算錯誤: {e}")
            import traceback
            traceback.print_exc()
            return np.zeros(len(df))
