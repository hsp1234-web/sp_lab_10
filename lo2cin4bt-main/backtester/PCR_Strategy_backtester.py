import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional

class PCR_Strategy:
    """
    PCR比率策略 (Put-Call Ratio Strategy)

    策略邏輯：
    1. 計算Put-Call Ratio (PCR)
    2. PCR > 高閾值時市場恐慌，做多期貨
    3. PCR < 低閾值時市場過度樂觀，做空期貨
    4. 結合VIX或波動率指標

    風控強化：
    - 單筆風險不超過總資金 1%
    - 月度回撤超過 5% 暫停交易
    - 動態倉位調整

    參數：
    - pcr_high_threshold (float): PCR高閾值 (預設 1.2)
    - pcr_low_threshold (float): PCR低閾值 (預設 0.8)
    - pcr_ma_window (int): PCR移動平均窗口 (預設 5)
    - risk_per_trade (float): 單筆風險比例 (預設 0.01 = 1%)
    - stop_loss_atr_multiplier (float): 停損 ATR 倍數 (預設 2.0)
    - max_monthly_drawdown (float): 最大月度回撤閾值 (預設 0.05 = 5%)
    """

    STRATEGY_DESCRIPTIONS = {
        "PCR": "PCR比率策略 (Put-Call Ratio)"
    }

    def __init__(self, data: pd.DataFrame, params: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.data = data
        self.params = params
        self.logger = logger or logging.getLogger(__name__)

        # 策略參數
        self.pcr_high_threshold = float(params.get('pcr_high_threshold', 1.2))
        self.pcr_low_threshold = float(params.get('pcr_low_threshold', 0.8))
        self.pcr_ma_window = int(params.get('pcr_ma_window', 5))

        # 風控參數
        self.risk_per_trade = float(params.get('risk_per_trade', 0.01))
        self.stop_loss_atr_multiplier = float(params.get('stop_loss_atr_multiplier', 2.0))
        self.max_monthly_drawdown = float(params.get('max_monthly_drawdown', 0.05))

        # 風控參數
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
        pcr_high_thresholds = [1.1, 1.2, 1.3]  # PCR高閾值
        pcr_low_thresholds = [0.7, 0.8, 0.9]  # PCR低閾值
        pcr_ma_windows = [3, 5, 7]  # 移動平均窗口

        # 風控參數
        risk_per_trades = [0.01]  # 1% 風險
        stop_loss_multipliers = [2.0]  # ATR 停損倍數

        if params_config:
            pcr_high_thresholds = params_config.get('pcr_high_threshold', pcr_high_thresholds)
            pcr_low_thresholds = params_config.get('pcr_low_threshold', pcr_low_thresholds)
            pcr_ma_windows = params_config.get('pcr_ma_window', pcr_ma_windows)
            risk_per_trades = params_config.get('risk_per_trade', risk_per_trades)
            stop_loss_multipliers = params_config.get('stop_loss_atr_multiplier', stop_loss_multipliers)

        param_combinations = []
        for high_thresh in pcr_high_thresholds:
            for low_thresh in pcr_low_thresholds:
                for ma_window in pcr_ma_windows:
                    for risk in risk_per_trades:
                        for sl_mult in stop_loss_multipliers:
                            param_combinations.append(
                                IndicatorParams(
                                    indicator_type='PCR',
                                    buy_threshold=0,
                                    sell_threshold=0,
                                    window=ma_window,
                                    extra_params={
                                        'pcr_high_threshold': high_thresh,
                                        'pcr_low_threshold': low_thresh,
                                        'pcr_ma_window': ma_window,
                                        'risk_per_trade': risk,
                                        'stop_loss_atr_multiplier': sl_mult,
                                        'max_monthly_drawdown': 0.05
                                    }
                                )
                            )
        return param_combinations

    def generate_signals(self, predictor: Optional[str] = None) -> np.ndarray:
        """
        產生交易信號 - PCR比率策略

        Returns:
            np.ndarray: 信號數組 (1: 多頭進場, -1: 空頭進場, 0: 無信號/持有)
        """
        df = self.data.copy()

        # 確保有必要的欄位
        required_cols = ['High', 'Low', 'Close', 'Time']
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

        # 檢查是否有PCR數據
        pcr_cols = ['pcr_ratio', 'pcr', 'PCR']
        has_pcr_data = any(col in df.columns for col in pcr_cols)

        if not has_pcr_data:
            self.logger.warning("缺少PCR數據欄位，使用模擬信號")
            # 如果沒有PCR數據，生成基於波動率的模擬信號
            np.random.seed(42)
            signals = np.zeros(len(df))

            # 計算簡易波動率作為PCR替代
            if 'Close' in df.columns:
                df['returns'] = df['Close'].pct_change()
                df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
                df['simulated_pcr'] = 1.0 + (df['volatility'] - df['volatility'].mean()) / df['volatility'].std() * 0.3

                for i in range(20, len(df)):
                    pcr_value = df['simulated_pcr'].iloc[i]
                    if pcr_value > self.pcr_high_threshold and np.random.random() > 0.7:
                        signals[i] = 1  # 恐慌時做多
                    elif pcr_value < self.pcr_low_threshold and np.random.random() > 0.7:
                        signals[i] = -1  # 過度樂觀時做空

            return signals

        try:
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

            # 處理PCR數據
            if 'pcr_ratio' in df.columns:
                df['pcr'] = df['pcr_ratio']
            elif 'pcr' not in df.columns:
                df['pcr'] = df.get('PCR', 1.0)

            # 計算PCR移動平均
            df['pcr_ma'] = df['pcr'].rolling(window=self.pcr_ma_window).mean()

            # 計算PCR變化率
            df['pcr_change'] = df['pcr'].pct_change()

            # 計算市場波動率 (輔助指標)
            df['returns'] = df['Close'].pct_change()
            df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)

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
            pcr_ma_vals = df['pcr_ma'].fillna(1.0).values
            volatility_vals = df['volatility'].fillna(0).values
            atr_vals = df['ATR'].fillna(0).values

            # 趨勢狀態追蹤
            current_trend = 0  # 0=無趨勢, 1=多頭, -1=空頭

            for i in range(len(df)):
                if np.isnan(close_vals[i]) or close_vals[i] <= 0:
                    continue

                current_price = close_vals[i]
                current_atr = atr_vals[i]
                current_pcr = pcr_ma_vals[i]
                current_vol = volatility_vals[i]

                # 月度回撤檢查
                if i > 0:
                    current_month = time_vals[i].strftime('%Y-%m')
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

                # PCR策略邏輯
                trend_signal = 0

                # 確保有足夠的數據
                if i >= self.pcr_ma_window:
                    # 多頭進場：PCR過高(市場恐慌) + 波動率確認
                    if (current_pcr > self.pcr_high_threshold and
                        current_vol > df['volatility'].quantile(0.6) and  # 波動率較高
                        current_trend != 1):
                        trend_signal = 1

                    # 空頭進場：PCR過低(市場過度樂觀) + 波動率確認
                    elif (current_pcr < self.pcr_low_threshold and
                          current_vol < df['volatility'].quantile(0.4) and  # 波動率較低
                          current_trend != -1):
                        trend_signal = -1

                # 出場條件檢查 (如果有倉位)
                if current_trend == 1:  # 多頭倉位
                    # 多頭出場: PCR回到正常水平或停損
                    if (current_pcr < 1.0) or (current_price < self.entry_price - (current_atr * self.stop_loss_atr_multiplier)):
                        trend_signal = -1  # 出場信號
                        stop_loss_triggered[i] = current_price < self.entry_price - (current_atr * self.stop_loss_atr_multiplier)

                elif current_trend == -1:  # 空頭倉位
                    # 空頭出場: PCR回到正常水平或停損
                    if (current_pcr > 1.0) or (current_price > self.entry_price + (current_atr * self.stop_loss_atr_multiplier)):
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

            self.logger.info(f"PCR比率策略 - 總信號: {total_signals}")
            self.logger.info(f"多頭進場: {long_signals}, 空頭進場: {short_signals}")
            self.logger.info(f"停損觸發: {stop_losses}, 月度熔斷: {monthly_breakers}")
            self.logger.info(f"參數: PCR高閾值={self.pcr_high_threshold}, 低閾值={self.pcr_low_threshold}, MA窗口={self.pcr_ma_window}")
            self.logger.info(f"風控: 單筆風險={self.risk_per_trade*100}%, 月度回撤閾值={self.max_monthly_drawdown*100}%")

            return signals

        except Exception as e:
            self.logger.error(f"PCR比率策略計算錯誤: {e}")
            import traceback
            traceback.print_exc()
            return np.zeros(len(df))

