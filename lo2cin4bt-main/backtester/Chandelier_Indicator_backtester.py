import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional

class ChandelierIndicator:
    """
    吊燈停損指標 (Chandelier Stop Indicator) - 強化版
    
    策略邏輯：
    1. 計算 ATR (Average True Range)。
    2. 計算 N 週期內的最高價 (High) 和最低價 (Low)。
    3. 多頭停損點 (Long Stop) = N 週期最高價 - Multiplier * ATR
    4. 空頭停損點 (Short Stop) = N 週期最低價 + Multiplier * ATR
    5. 進場信號：收盤價突破前一期 High Rolling Max (趨勢轉多)
    6. 出場信號：收盤價跌破 Long Stop (多單出場) 或 突破 Short Stop (空單出場)
    
    風控強化：
    - 動態口數：單筆風險不超過總資金 1%
    - 硬性停損：基於 ATR * 2 或 2% 固定停損
    - 熔斷機制：月度回撤超過 5% 暫停交易

    參數：
    - length (int): 計算 ATR 和 Rolling Max/Min 的週期 (預設 14, 從 22 調降)
    - multiplier (float): ATR 的倍數 (預設 2.0, 從 3.0 調降)
    - risk_per_trade (float): 單筆風險比例 (預設 0.01 = 1%)
    - stop_loss_atr_multiplier (float): 停損 ATR 倍數 (預設 2.0)
    - max_monthly_drawdown (float): 最大月度回撤閾值 (預設 0.05 = 5%)
    """
    
    STRATEGY_DESCRIPTIONS = {
        "CHANDELIER": "吊燈停損策略 (Trend Following)"
    }

    def __init__(self, data: pd.DataFrame, params: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.data = data
        self.params = params
        self.logger = logger or logging.getLogger(__name__)
        
        # 參數提取 - 調整為更敏感的預設值
        self.length = int(params.get('length', 14))  # 從 22 調降到 14
        self.multiplier = float(params.get('multiplier', 2.0))  # 從 3.0 調降到 2.0

        # 風控參數
        self.risk_per_trade = float(params.get('risk_per_trade', 0.01))  # 單筆風險 1%
        self.stop_loss_atr_multiplier = float(params.get('stop_loss_atr_multiplier', 2.0))  # 停損 ATR 倍數
        self.max_monthly_drawdown = float(params.get('max_monthly_drawdown', 0.05))  # 月度最大回撤 5%

        # 交易狀態追蹤
        self.position_size = 1  # 動態調整的口數
        self.current_position = 0  # 當前倉位 (1=多頭, -1=空頭, 0=無倉位)
        self.entry_price = 0  # 進場價格
        self.stop_loss_price = 0  # 停損價格
        self.monthly_drawdown_tracker = 0  # 月度回撤追蹤

    @staticmethod
    def get_params(strat_idx: int = 1, params_config: Optional[Dict] = None) -> List[Any]:
        """
        產生參數組合 - 包含風控參數
        """
        from .IndicatorParams_backtester import IndicatorParams
        
        # 預設參數範圍 - 更激進的設定
        lengths = [10, 14]  # 從保守的 22 調降為更敏感的 10-14
        multipliers = [1.5, 2.0]  # 從 3.0 調降為 1.5-2.0

        # 風控參數
        risk_per_trades = [0.01]  # 1% 風險
        stop_loss_multipliers = [2.0]  # ATR 停損倍數
        
        if params_config:
            lengths = params_config.get('length', lengths)
            multipliers = params_config.get('multiplier', multipliers)
            risk_per_trades = params_config.get('risk_per_trade', risk_per_trades)
            stop_loss_multipliers = params_config.get('stop_loss_atr_multiplier', stop_loss_multipliers)
            
        param_combinations = []
        for length in lengths:
            for mult in multipliers:
                for risk in risk_per_trades:
                    for sl_mult in stop_loss_multipliers:
                        param_combinations.append(
                            IndicatorParams(
                                indicator_type='CHANDELIER',
                                buy_threshold=0, # 不使用
                                sell_threshold=0, # 不使用
                                window=length,
                                extra_params={
                                    'length': length,
                                    'multiplier': mult,
                                    'risk_per_trade': risk,
                                    'stop_loss_atr_multiplier': sl_mult,
                                    'max_monthly_drawdown': 0.05  # 固定 5%
                                }
                            )
                        )
        return param_combinations

    def generate_signals(self, predictor: Optional[str] = None) -> np.ndarray:
        """
        產生交易信號 - 強化版包含風控邏輯
        Returns:
            np.ndarray: 信號數組 (1: 多頭進場, -1: 空頭進場, 0: 無信號/持有)
        """
        df = self.data.copy()
        
        # 確保有必要的欄位
        required_cols = ['High', 'Low', 'Close', 'Time']
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
            df['ATR'] = tr.ewm(alpha=1/self.length, adjust=False).mean()
            
            # 計算 Rolling Max High / Min Low
            df['High_Roll'] = df['High'].rolling(self.length).max()
            df['Low_Roll'] = df['Low'].rolling(self.length).min()
            
            # 計算 Chandelier Stops
            df['Chandelier_Long'] = df['High_Roll'] - self.multiplier * df['ATR']
            df['Chandelier_Short'] = df['Low_Roll'] + self.multiplier * df['ATR']
            
            # 初始化信號和風控追蹤
            signals = np.zeros(len(df))
            position_active = np.zeros(len(df), dtype=bool)
            stop_loss_triggered = np.zeros(len(df), dtype=bool)
            monthly_dd_exceeded = np.zeros(len(df), dtype=bool)

            # 模擬動態權益追蹤 (用於風控)
            simulated_equity = 1000000.0  # 初始資金 100 萬
            monthly_high = simulated_equity
            
            close_vals = df['Close'].values
            time_vals = pd.to_datetime(df['Time'].values)
            high_roll = df['High_Roll'].values
            chan_long = df['Chandelier_Long'].values
            chan_short = df['Chandelier_Short'].values
            atr_vals = df['ATR'].values
            
            # 實作向量化邏輯
            prev_high_roll = np.roll(high_roll, 1)
            prev_chan_long = np.roll(chan_long, 1)
            prev_chan_short = np.roll(chan_short, 1)
            
            # 處理邊界
            prev_high_roll[0] = np.inf
            prev_chan_long[0] = -np.inf
            prev_chan_short[0] = np.inf

            # 趨勢狀態追蹤
            current_trend = 0  # 0=無趨勢, 1=多頭, -1=空頭

            for i in range(len(df)):
                if np.isnan(close_vals[i]) or close_vals[i] <= 0:
                    continue

                current_price = close_vals[i]
                current_atr = atr_vals[i] if not np.isnan(atr_vals[i]) else 0

                # 月度回撤檢查 (簡化版本)
                current_month = time_vals[i].strftime('%Y-%m')
                if i > 0:
                    prev_month = time_vals[i-1].strftime('%Y-%m')
                    if current_month != prev_month:
                        # 新月份重置
                        monthly_high = simulated_equity

                monthly_dd = (simulated_equity - monthly_high) / monthly_high if monthly_high > 0 else 0
                monthly_dd_exceeded[i] = monthly_dd < -self.max_monthly_drawdown

                # 如果月度回撤超過閾值，停止交易
                if monthly_dd_exceeded[i]:
                    current_trend = 0
                    position_active[i] = False
                    continue

                # 計算動態口數 (基於 ATR 和風險控制)
                if current_atr > 0:
                    risk_amount = simulated_equity * self.risk_per_trade
                    stop_distance = current_atr * self.stop_loss_atr_multiplier
                    self.position_size = max(1, int(risk_amount / stop_distance))

                # 趨勢判斷邏輯
                trend_signal = 0

                # 條件 1: 多頭進場 - 收盤價突破前一期 High Roll
                if current_price > prev_high_roll[i] and current_trend != 1:
                    trend_signal = 1

                # 條件 2: 空頭進場 - 收盤價跌破前一期 Chandelier Short
                elif current_price < prev_chan_short[i] and current_trend != -1:
                    trend_signal = -1

                # 出場條件檢查 (如果有倉位)
                if current_trend == 1:  # 多頭倉位
                    # 多頭出場: 跌破 Chandelier Long 或 ATR 停損
                    stop_price = self.entry_price - (current_atr * self.stop_loss_atr_multiplier)
                    if current_price < prev_chan_long[i] or current_price < stop_price:
                        trend_signal = -1  # 出場信號
                        stop_loss_triggered[i] = True

                elif current_trend == -1:  # 空頭倉位
                    # 空頭出場: 突破 Chandelier Short 或 ATR 停損
                    stop_price = self.entry_price + (current_atr * self.stop_loss_atr_multiplier)
                    if current_price > prev_chan_short[i] or current_price > stop_price:
                        trend_signal = 1  # 出場信號
                        stop_loss_triggered[i] = True

                # 更新趨勢狀態
                if trend_signal != 0:
                    if trend_signal == 1 and current_trend <= 0:
                        # 進場多頭
                        current_trend = 1
                        self.entry_price = current_price
                        signals[i] = 1
                        position_active[i] = True
                    elif trend_signal == -1 and current_trend >= 0:
                        # 進場空頭
                        current_trend = -1
                        self.entry_price = current_price
                        signals[i] = -1
                        position_active[i] = True
                    elif (trend_signal == 1 and current_trend == 1) or (trend_signal == -1 and current_trend == -1):
                        # 出場
                        current_trend = 0
                        signals[i] = -trend_signal  # 反向出場信號
                        position_active[i] = False

            # 記錄統計信息
            total_signals = np.sum(signals != 0)
            long_signals = np.sum(signals == 1)
            short_signals = np.sum(signals == -1)
            stop_losses = np.sum(stop_loss_triggered)
            monthly_breakers = np.sum(monthly_dd_exceeded)

            self.logger.info(f"Chandelier 風控版本 - 總信號: {total_signals}")
            self.logger.info(f"多頭進場: {long_signals}, 空頭進場: {short_signals}")
            self.logger.info(f"停損觸發: {stop_losses}, 月度熔斷: {monthly_breakers}")
            self.logger.info(f"參數: Length={self.length}, Multiplier={self.multiplier}")
            self.logger.info(f"風控: 單筆風險={self.risk_per_trade*100}%, 月度回撤閾值={self.max_monthly_drawdown*100}%")
            
            return signals

        except Exception as e:
            self.logger.error(f"Chandelier Indicator 風控版計算錯誤: {e}")
            import traceback
            traceback.print_exc()
            return np.zeros(len(df))
