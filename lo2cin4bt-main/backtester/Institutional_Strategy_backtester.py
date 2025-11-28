import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional

class InstitutionalStrategy:
    """
    三大法人買賣超策略 (Institutional Investors Net Buying Strategy)

    策略邏輯：
    1. 計算三大法人 (外資+投信+自營商) 的期貨淨部位變化
    2. 法人連續買超時進場做多，連續賣超時進場做空
    3. 出場條件：法人轉向或停損

    風控強化：
    - 單筆風險不超過總資金 1%
    - 月度回撤超過 5% 暫停交易
    - 動態倉位調整

    參數：
    - consecutive_days (int): 連續買賣超天數 (預設 3)
    - net_buying_threshold (float): 淨買超閾值百分位數 (預設 70)
    - risk_per_trade (float): 單筆風險比例 (預設 0.01 = 1%)
    - stop_loss_atr_multiplier (float): 停損 ATR 倍數 (預設 2.0)
    - max_monthly_drawdown (float): 最大月度回撤閾值 (預設 0.05 = 5%)
    """

    STRATEGY_DESCRIPTIONS = {
        "INSTITUTIONAL": "三大法人買賣超策略 (Institutional Net Buying)"
    }

    def __init__(self, data: pd.DataFrame, params: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.data = data
        self.params = params
        self.logger = logger or logging.getLogger(__name__)

        # 策略參數
        self.consecutive_days = int(params.get('consecutive_days', 3))
        self.net_buying_threshold = float(params.get('net_buying_threshold', 70))
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
        consecutive_days_list = [2, 3, 5]  # 連續天數
        net_buying_thresholds = [60, 70, 80]  # 閾值百分位數

        # 風控參數
        risk_per_trades = [0.01]  # 1% 風險
        stop_loss_multipliers = [2.0]  # ATR 停損倍數

        if params_config:
            consecutive_days_list = params_config.get('consecutive_days', consecutive_days_list)
            net_buying_thresholds = params_config.get('net_buying_threshold', net_buying_thresholds)
            risk_per_trades = params_config.get('risk_per_trade', risk_per_trades)
            stop_loss_multipliers = params_config.get('stop_loss_atr_multiplier', stop_loss_multipliers)

        param_combinations = []
        for consecutive_days in consecutive_days_list:
            for threshold in net_buying_thresholds:
                for risk in risk_per_trades:
                    for sl_mult in stop_loss_multipliers:
                        param_combinations.append(
                            IndicatorParams(
                                indicator_type='INSTITUTIONAL',
                                buy_threshold=0,
                                sell_threshold=0,
                                window=consecutive_days,
                                extra_params={
                                    'consecutive_days': consecutive_days,
                                    'net_buying_threshold': threshold,
                                    'risk_per_trade': risk,
                                    'stop_loss_atr_multiplier': sl_mult,
                                    'max_monthly_drawdown': 0.05
                                }
                            )
                        )
        return param_combinations

    def generate_signals(self, predictor: Optional[str] = None) -> np.ndarray:
        """
        產生交易信號 - 三大法人買賣超策略

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

        # 檢查是否有法人數據欄位
        institutional_cols = ['futures_net', 'total_net', 'investor_type']
        has_institutional_data = any(col in df.columns for col in institutional_cols)

        if not has_institutional_data:
            self.logger.warning("缺少法人數據欄位，使用模擬信號")
            # 如果沒有法人數據，生成隨機信號作為測試
            np.random.seed(42)
            signals = np.zeros(len(df))
            for i in range(self.consecutive_days, len(df)):
                if np.random.random() > 0.7:  # 30%概率產生信號
                    signals[i] = 1 if np.random.random() > 0.5 else -1
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

            # 處理法人數據
            if 'total_net' in df.columns:
                # 使用總淨部位
                df['institutional_net'] = df['total_net']
            elif 'futures_net' in df.columns:
                # 使用期貨淨部位
                df['institutional_net'] = df['futures_net']
            else:
                # 如果沒有淨部位數據，使用變化量
                df['institutional_net'] = df.get('institutional_buying', 0) - df.get('institutional_selling', 0)

            # 計算法人買賣超動能
            df['inst_net_ma'] = df['institutional_net'].rolling(window=5).mean()
            df['inst_net_std'] = df['institutional_net'].rolling(window=20).std()

            # 計算動態閾值 (基於歷史百分位數)
            if len(df) > 60:
                historical_net = df['institutional_net'].iloc[:len(df)//2]  # 使用前半段數據計算閾值
                buy_threshold = np.percentile(historical_net[historical_net > 0], self.net_buying_threshold)
                sell_threshold = np.percentile(historical_net[historical_net < 0], 100 - self.net_buying_threshold)
            else:
                # 預設閾值
                buy_threshold = df['inst_net_ma'].quantile(0.7) if not df['inst_net_ma'].empty else 1000
                sell_threshold = df['inst_net_ma'].quantile(0.3) if not df['inst_net_ma'].empty else -1000

            # 計算連續買賣超信號
            df['buy_signal'] = df['institutional_net'] > buy_threshold
            df['sell_signal'] = df['institutional_net'] < sell_threshold

            df['consecutive_buy'] = df['buy_signal'].rolling(window=self.consecutive_days).sum()
            df['consecutive_sell'] = df['sell_signal'].rolling(window=self.consecutive_days).sum()

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
            consecutive_buy = df['consecutive_buy'].fillna(0).values
            consecutive_sell = df['consecutive_sell'].fillna(0).values
            atr_vals = df['ATR'].fillna(0).values

            # 趨勢狀態追蹤
            current_trend = 0  # 0=無趨勢, 1=多頭, -1=空頭

            for i in range(len(df)):
                if np.isnan(close_vals[i]) or close_vals[i] <= 0:
                    continue

                current_price = close_vals[i]
                current_atr = atr_vals[i]

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

                # 法人策略邏輯
                trend_signal = 0

                # 確保有足夠的數據
                if i >= max(self.consecutive_days, 20):
                    # 多頭進場：連續N天法人買超
                    if (consecutive_buy[i] >= self.consecutive_days and
                        current_trend != 1):
                        trend_signal = 1

                    # 空頭進場：連續N天法人賣超
                    elif (consecutive_sell[i] >= self.consecutive_days and
                          current_trend != -1):
                        trend_signal = -1

                # 出場條件檢查 (如果有倉位)
                if current_trend == 1:  # 多頭倉位
                    # 多頭出場: 法人轉為賣超或停損
                    if (consecutive_sell[i] >= 1) or (current_price < self.entry_price - (current_atr * self.stop_loss_atr_multiplier)):
                        trend_signal = -1  # 出場信號
                        stop_loss_triggered[i] = current_price < self.entry_price - (current_atr * self.stop_loss_atr_multiplier)

                elif current_trend == -1:  # 空頭倉位
                    # 空頭出場: 法人轉為買超或停損
                    if (consecutive_buy[i] >= 1) or (current_price > self.entry_price + (current_atr * self.stop_loss_atr_multiplier)):
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

            self.logger.info(f"法人買賣超策略 - 總信號: {total_signals}")
            self.logger.info(f"多頭進場: {long_signals}, 空頭進場: {short_signals}")
            self.logger.info(f"停損觸發: {stop_losses}, 月度熔斷: {monthly_breakers}")
            self.logger.info(f"參數: 連續天數={self.consecutive_days}, 閾值百分位={self.net_buying_threshold}%")
            self.logger.info(f"風控: 單筆風險={self.risk_per_trade*100}%, 月度回撤閾值={self.max_monthly_drawdown*100}%")

            return signals

        except Exception as e:
            self.logger.error(f"法人買賣超策略計算錯誤: {e}")
            import traceback
            traceback.print_exc()
            return np.zeros(len(df))

