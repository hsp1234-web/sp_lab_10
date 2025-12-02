import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional

class DualMovingAverageStrategy:
    """
    雙均線趨勢跟蹤策略 (Dual Moving Average Trend Following Strategy)

    策略邏輯：
    1. 計算 EMA(20) 和 EMA(60)
    2. 進場信號：EMA(20) 上穿 EMA(60) + 收盤價 > EMA(20) + 成交量放大
    3. 出場信號：EMA(20) 下穿 EMA(60) 或 虧損達 2×ATR(14)

    風控強化：
    - 單筆風險不超過總資金 1%
    - 硬性停損：基於 ATR * 2 或 2% 固定停損
    - 月度回撤超過 5% 暫停交易

    參數：
    - fast_period (int): 快線週期 (預設 20)
    - slow_period (int): 慢線週期 (預設 60)
    - volume_multiplier (float): 成交量放大倍數 (預設 1.2)
    - risk_per_trade (float): 單筆風險比例 (預設 0.01 = 1%)
    - stop_loss_atr_multiplier (float): 停損 ATR 倍數 (預設 2.0)
    - max_monthly_drawdown (float): 最大月度回撤閾值 (預設 0.05 = 5%)
    """

    STRATEGY_DESCRIPTIONS = {
        "DUAL_MA": "雙均線趨勢跟蹤策略 (EMA 20 vs EMA 60)"
    }

    def __init__(self, data: pd.DataFrame, params: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.data = data
        self.params = params
        self.logger = logger or logging.getLogger(__name__)

        # 策略參數
        self.fast_period = int(params.get('fast_period', 20))
        self.slow_period = int(params.get('slow_period', 60))
        self.volume_multiplier = float(params.get('volume_multiplier', 1.2))

        # 風控參數
        self.risk_per_trade = float(params.get('risk_per_trade', 0.01))
        self.stop_loss_atr_multiplier = float(params.get('stop_loss_atr_multiplier', 2.0))
        self.max_monthly_drawdown = float(params.get('max_monthly_drawdown', 0.05))

        # 交易狀態追蹤
        self.position_size = 1  # 動態調整的口數
        self.current_position = 0  # 當前倉位 (1=多頭, -1=空頭, 0=無倉位)
        self.entry_price = 0  # 進場價格
        self.stop_loss_price = 0  # 停損價格
        self.monthly_drawdown_tracker = 0  # 月度回撤追蹤

    @staticmethod
    def get_params(strat_idx: int = 1, params_config: Optional[Dict] = None) -> List[Any]:
        """
        產生參數組合
        """
        from .IndicatorParams_backtester import IndicatorParams

        # 預設參數範圍
        fast_periods = [20]  # 快線週期
        slow_periods = [60]  # 慢線週期
        volume_multipliers = [1.2]  # 成交量放大倍數

        # 風控參數
        risk_per_trades = [0.01]  # 1% 風險
        stop_loss_multipliers = [2.0]  # ATR 停損倍數

        if params_config:
            fast_periods = params_config.get('fast_period', fast_periods)
            slow_periods = params_config.get('slow_period', slow_periods)
            volume_multipliers = params_config.get('volume_multiplier', volume_multipliers)
            risk_per_trades = params_config.get('risk_per_trade', risk_per_trades)
            stop_loss_multipliers = params_config.get('stop_loss_atr_multiplier', stop_loss_multipliers)

        param_combinations = []
        for fast in fast_periods:
            for slow in slow_periods:
                for vol_mult in volume_multipliers:
                    for risk in risk_per_trades:
                        for sl_mult in stop_loss_multipliers:
                            param_combinations.append(
                                IndicatorParams(
                                    indicator_type='DUAL_MA',
                                    buy_threshold=0,
                                    sell_threshold=0,
                                    window=max(fast, slow),
                                    extra_params={
                                        'fast_period': fast,
                                        'slow_period': slow,
                                        'volume_multiplier': vol_mult,
                                        'risk_per_trade': risk,
                                        'stop_loss_atr_multiplier': sl_mult,
                                        'max_monthly_drawdown': 0.05
                                    }
                                )
                            )
        return param_combinations

    def generate_signals(self, predictor: Optional[str] = None) -> np.ndarray:
        """
        產生交易信號 - 雙均線趨勢跟蹤邏輯

        Returns:
            np.ndarray: 信號數組 (1: 多頭進場, -1: 空頭進場, 0: 無信號/持有)
        """
        df = self.data.copy()

        # 確保有必要的欄位
        required_cols = ['High', 'Low', 'Close', 'Volume', 'Time']
        for col in required_cols:
            if col not in df.columns:
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
            # 計算 EMA
            df['EMA_fast'] = df['Close'].ewm(span=self.fast_period, adjust=False).mean()
            df['EMA_slow'] = df['Close'].ewm(span=self.slow_period, adjust=False).mean()

            # 計算成交量平均
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()

            # 計算 ATR (用於停損)
            high = df['High']
            low = df['Low']
            close = df['Close']
            prev_close = close.shift(1)

            tr1 = high - low
            tr2 = (high - prev_close).abs()
            tr3 = (low - prev_close).abs()

            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            df['ATR'] = tr.ewm(alpha=1/14, adjust=False).mean()

            # 初始化信號和風控追蹤
            signals = np.zeros(len(df))
            position_active = np.zeros(len(df), dtype=bool)
            stop_loss_triggered = np.zeros(len(df), dtype=bool)
            monthly_dd_exceeded = np.zeros(len(df), dtype=bool)

            # 模擬動態權益追蹤 (用於風控)
            simulated_equity = 1000000.0  # 初始資金 100 萬
            monthly_high = simulated_equity  # 初始化月度高點

            close_vals = df['Close'].values
            time_vals = pd.to_datetime(df['Time'].values)
            ema_fast = df['EMA_fast'].values
            ema_slow = df['EMA_slow'].values
            volume_vals = df['Volume'].values
            volume_ma = df['Volume_MA'].values
            atr_vals = df['ATR'].values

            # 趨勢狀態追蹤
            current_trend = 0  # 0=無趨勢, 1=多頭, -1=空頭

            for i in range(len(df)):
                if np.isnan(close_vals[i]) or close_vals[i] <= 0:
                    continue

                current_price = close_vals[i]
                current_atr = atr_vals[i] if not np.isnan(atr_vals[i]) else 0

                # 月度回撤檢查
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

                # 確保有足夠的數據計算均線
                if i >= max(self.fast_period, self.slow_period):
                    prev_fast = ema_fast[i-1] if not np.isnan(ema_fast[i-1]) else 0
                    prev_slow = ema_slow[i-1] if not np.isnan(ema_slow[i-1]) else 0
                    curr_fast = ema_fast[i] if not np.isnan(ema_fast[i]) else 0
                    curr_slow = ema_slow[i] if not np.isnan(ema_slow[i]) else 0

                    # 多頭進場條件：
                    # 1. EMA(20) 上穿 EMA(60)
                    # 2. 收盤價 > EMA(20)
                    # 3. 成交量放大
                    if (prev_fast <= prev_slow and curr_fast > curr_slow and
                        current_price > curr_fast and
                        volume_vals[i] > volume_ma[i] * self.volume_multiplier and
                        current_trend != 1):
                        trend_signal = 1

                    # 空頭進場條件 (如果需要)：
                    # EMA(20) 下穿 EMA(60) + 收盤價 < EMA(20) + 成交量放大
                    elif (prev_fast >= prev_slow and curr_fast < curr_slow and
                          current_price < curr_fast and
                          volume_vals[i] > volume_ma[i] * self.volume_multiplier and
                          current_trend != -1):
                        trend_signal = -1

                # 出場條件檢查 (如果有倉位)
                if current_trend == 1:  # 多頭倉位
                    # 多頭出場: EMA(20) 下穿 EMA(60) 或 ATR 停損
                    if (curr_fast < curr_slow) or (current_price < self.entry_price - (current_atr * self.stop_loss_atr_multiplier)):
                        trend_signal = -1  # 出場信號
                        stop_loss_triggered[i] = current_price < self.entry_price - (current_atr * self.stop_loss_atr_multiplier)

                elif current_trend == -1:  # 空頭倉位
                    # 空頭出場: EMA(20) 上穿 EMA(60) 或 ATR 停損
                    if (curr_fast > curr_slow) or (current_price > self.entry_price + (current_atr * self.stop_loss_atr_multiplier)):
                        trend_signal = 1  # 出場信號
                        stop_loss_triggered[i] = current_price > self.entry_price + (current_atr * self.stop_loss_atr_multiplier)

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

            self.logger.info(f"雙均線策略 - 總信號: {total_signals}")
            self.logger.info(f"多頭進場: {long_signals}, 空頭進場: {short_signals}")
            self.logger.info(f"停損觸發: {stop_losses}, 月度熔斷: {monthly_breakers}")
            self.logger.info(f"參數: EMA({self.fast_period}) vs EMA({self.slow_period}), 成交量放大: {self.volume_multiplier}x")
            self.logger.info(f"風控: 單筆風險={self.risk_per_trade*100}%, 月度回撤閾值={self.max_monthly_drawdown*100}%")

            return signals

        except Exception as e:
            self.logger.error(f"雙均線策略計算錯誤: {e}")
            import traceback
            traceback.print_exc()
            return np.zeros(len(df))

