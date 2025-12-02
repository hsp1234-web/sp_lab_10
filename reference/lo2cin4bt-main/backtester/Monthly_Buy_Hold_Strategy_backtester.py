import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional

class Monthly_Buy_Hold_Strategy:
    """
    月度買進持有策略 (Monthly Buy and Hold Strategy)

    策略邏輯：
    1. 每月第一個交易日買進
    2. 月底最後一個交易日賣出
    3. 模擬每月定期的買進持有行為

    參數：
    - entry_day (int): 進場日 (預設 1 = 每月1日)
    - exit_day (int): 出場日 (預設 -1 = 月末最後一日)
    """

    STRATEGY_DESCRIPTIONS = {
        "MONTHLY_BUY_HOLD": "月度買進持有策略 (Monthly Buy & Hold)"
    }

    def __init__(self, data: pd.DataFrame, params: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.data = data
        self.params = params
        self.logger = logger or logging.getLogger(__name__)

        # 策略參數
        self.entry_day = int(params.get('entry_day', 1))
        self.exit_day = int(params.get('exit_day', -1))  # -1表示月末

    @staticmethod
    def get_params(strat_idx: int = 1, params_config: Optional[Dict] = None) -> List[Any]:
        """
        產生參數組合
        """
        from .IndicatorParams_backtester import IndicatorParams

        # 預設參數範圍
        entry_days = [1, 5]  # 進場日
        exit_days = [-1]  # 出場日 (-1=月末)

        if params_config:
            entry_days = params_config.get('entry_day', entry_days)
            exit_days = params_config.get('exit_day', exit_days)

        param_combinations = []
        for entry_day in entry_days:
            for exit_day in exit_days:
                param_combinations.append(
                    IndicatorParams(
                        indicator_type='MONTHLY_BUY_HOLD',
                        buy_threshold=0,
                        sell_threshold=0,
                        window=30,  # 月度窗口
                        extra_params={
                            'entry_day': entry_day,
                            'exit_day': exit_day
                        }
                    )
                )
        return param_combinations

    def generate_signals(self, predictor: Optional[str] = None) -> np.ndarray:
        """
        產生交易信號 - 月度買進持有策略

        Returns:
            np.ndarray: 信號數組 (1: 多頭進場, -1: 空頭進場/出場, 0: 持有)
        """
        df = self.data.copy()

        # 確保有必要的欄位
        required_cols = ['Time']
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
            # 轉換時間欄位
            df['date'] = pd.to_datetime(df['Time'])
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
            df['day'] = df['date'].dt.day

            # 計算每月第一個和最後一個交易日
            monthly_first_days = df.groupby(['year', 'month'])['day'].min().reset_index()
            monthly_first_days['first_trading_day'] = monthly_first_days.apply(
                lambda row: df[(df['year'] == row['year']) &
                              (df['month'] == row['month']) &
                              (df['day'] >= row['day'])].index[0], axis=1
            )

            monthly_last_days = df.groupby(['year', 'month'])['day'].max().reset_index()
            monthly_last_days['last_trading_day'] = monthly_last_days.apply(
                lambda row: df[(df['year'] == row['year']) &
                              (df['month'] == row['month']) &
                              (df['day'] <= row['day'])].index[-1], axis=1
            )

            # 初始化信號
            signals = np.zeros(len(df))

            # 生成月度買進持有信號
            current_position = 0
            for idx, row in df.iterrows():
                year_month = (row['year'], row['month'])

                # 檢查是否為進場日
                first_day_idx = monthly_first_days[
                    (monthly_first_days['year'] == row['year']) &
                    (monthly_first_days['month'] == row['month'])
                ]['first_trading_day']

                if not first_day_idx.empty:
                    entry_idx = first_day_idx.values[0]
                    if idx == entry_idx and current_position == 0:
                        signals[idx] = 1  # 買進
                        current_position = 1

                # 檢查是否為出場日
                last_day_idx = monthly_last_days[
                    (monthly_last_days['year'] == row['year']) &
                    (monthly_last_days['month'] == row['month'])
                ]['last_trading_day']

                if not last_day_idx.empty:
                    exit_idx = last_day_idx.values[0]
                    if idx == exit_idx and current_position == 1:
                        signals[idx] = -1  # 賣出
                        current_position = 0

            self.logger.info(f"月度買進持有策略 - 總信號: {np.sum(signals != 0)}")
            self.logger.info(f"買進信號: {np.sum(signals == 1)}, 賣出信號: {np.sum(signals == -1)}")
            self.logger.info(f"參數: 進場日={self.entry_day}, 出場日={self.exit_day}")

            return signals

        except Exception as e:
            self.logger.error(f"月度買進持有策略計算錯誤: {e}")
            import traceback
            traceback.print_exc()
            return np.zeros(len(df))

