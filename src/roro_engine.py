# -*- coding: utf-8 -*-
"""
RORO 狀態引擎模塊 (Risk-On/Risk-Off Engine Module)

此模塊實現動態風險開啟/關閉 (Risk-On/Risk-Off, RORO) 機制，
整合市場寬度指標和系統壓力指數來判斷風險狀態。

RORO 狀態定義：
- 強 Risk-On：市場寬度健康 + 系統壓力低
- 弱 Risk-On：市場寬度一般 + 系統壓力中等
- 中性：市場寬度中性 + 系統壓力中等
- 弱 Risk-Off：市場寬度轉弱 + 系統壓力升高
- 強 Risk-Off：市場寬度惡化 + 系統壓力極高
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum

from .market_indicators import MarketWidthIndicator
from .pressure_index import SystemPressureIndex

logger = logging.getLogger(__name__)

class ROROState(Enum):
    """RORO 狀態枚舉"""
    STRONG_RISK_ON = 2    # 強風險開啟
    WEAK_RISK_ON = 1      # 弱風險開啟
    NEUTRAL = 0           # 中性
    WEAK_RISK_OFF = -1    # 弱風險關閉
    STRONG_RISK_OFF = -2  # 強風險關閉

class RORODecision(Enum):
    """RORO 決策枚舉"""
    FULL_RISK_ON = 1.0    # 完全風險開啟
    MODERATE_RISK_ON = 0.6  # 中等風險開啟
    NEUTRAL = 0.0         # 中性
    MODERATE_RISK_OFF = -0.6  # 中等風險關閉
    FULL_RISK_OFF = -1.0  # 完全風險關閉

class ROROEngine:
    """
    RORO 狀態引擎類

    整合市場寬度和系統壓力指標，動態判斷風險狀態並生成投資決策。
    """

    def __init__(self, config_manager=None):
        """
        初始化 RORO 引擎

        Args:
            config_manager: 配置管理器實例
        """
        self.config = config_manager

        # 初始化子模塊
        self.market_indicator = MarketWidthIndicator(config_manager)
        self.pressure_index = SystemPressureIndex(config_manager=config_manager)

        # RORO 狀態轉換閾值
        self.state_thresholds = {
            'market_width': {
                'strong_bullish': 1.0,    # 市場寬度強健康
                'weak_bullish': 0.3,      # 市場寬度一般健康
                'neutral': 0.0,           # 市場寬度中性
                'weak_bearish': -0.3,     # 市場寬度轉弱
                'strong_bearish': -1.0,   # 市場寬度惡化
            },
            'system_pressure': {
                'low_pressure': -0.5,     # 系統壓力低
                'moderate_pressure': 0.0, # 系統壓力中等
                'high_pressure': 0.5,     # 系統壓力高
                'extreme_pressure': 1.0,  # 系統壓力極高
            }
        }

        # 狀態轉換平滑參數
        self.transition_smoothing = 5  # 狀態轉換平滑天數
        self.confirmation_period = 3   # 狀態確認期間

        # 資產配置建議
        self.asset_allocation = {
            RORODecision.FULL_RISK_ON: {
                'TXF': 0.6,    # 台灣指數期貨
                'TLT': 0.3,    # 長天期美債 ETF
                'GLD': 0.1,    # 黃金 ETF
            },
            RORODecision.MODERATE_RISK_ON: {
                'TXF': 0.4,
                'TLT': 0.4,
                'GLD': 0.2,
            },
            RORODecision.NEUTRAL: {
                'TXF': 0.2,
                'TLT': 0.5,
                'GLD': 0.3,
            },
            RORODecision.MODERATE_RISK_OFF: {
                'TXF': 0.1,
                'TLT': 0.6,
                'GLD': 0.3,
            },
            RORODecision.FULL_RISK_OFF: {
                'TXF': 0.0,
                'TLT': 0.7,
                'GLD': 0.3,
            }
        }

        logger.info("ROROEngine 初始化完成")

    def determine_roro_state(self, market_width_score: Union[float, pd.Series],
                           system_pressure_score: Union[float, pd.Series]) -> Union[ROROState, pd.Series]:
        """
        基於市場寬度和系統壓力確定 RORO 狀態

        Args:
            market_width_score: 市場寬度評分
            system_pressure_score: 系統壓力評分

        Returns:
            RORO 狀態
        """
        try:
            # 處理單一數值輸入
            if isinstance(market_width_score, (int, float)) and isinstance(system_pressure_score, (int, float)):
                return self._determine_single_state(market_width_score, system_pressure_score)

            # 處理序列輸入
            elif isinstance(market_width_score, pd.Series) and isinstance(system_pressure_score, pd.Series):
                return self._determine_series_state(market_width_score, system_pressure_score)

            else:
                raise ValueError("市場寬度和系統壓力輸入類型不匹配")

        except Exception as e:
            logger.error(f"RORO 狀態判斷失敗: {str(e)}")
            return ROROState.NEUTRAL

    def _determine_single_state(self, market_width: float, pressure: float) -> ROROState:
        """
        確定單一時間點的 RORO 狀態

        Args:
            market_width: 市場寬度評分
            pressure: 系統壓力評分

        Returns:
            RORO 狀態
        """
        try:
            # 判斷市場寬度狀態
            if market_width >= self.state_thresholds['market_width']['strong_bullish']:
                width_state = 'strong_bullish'
            elif market_width >= self.state_thresholds['market_width']['weak_bullish']:
                width_state = 'weak_bullish'
            elif market_width >= self.state_thresholds['market_width']['weak_bearish']:
                width_state = 'neutral'
            elif market_width >= self.state_thresholds['market_width']['strong_bearish']:
                width_state = 'weak_bearish'
            else:
                width_state = 'strong_bearish'

            # 判斷系統壓力狀態
            if pressure <= self.state_thresholds['system_pressure']['low_pressure']:
                pressure_state = 'low'
            elif pressure <= self.state_thresholds['system_pressure']['moderate_pressure']:
                pressure_state = 'moderate'
            elif pressure <= self.state_thresholds['system_pressure']['high_pressure']:
                pressure_state = 'high'
            else:
                pressure_state = 'extreme'

            # 綜合判斷 RORO 狀態
            return self._combine_states_to_roro(width_state, pressure_state)

        except Exception as e:
            logger.error(f"單一狀態判斷失敗: {str(e)}")
            return ROROState.NEUTRAL

    def _determine_series_state(self, market_width_series: pd.Series,
                               pressure_series: pd.Series) -> pd.Series:
        """
        確定時間序列的 RORO 狀態

        Args:
            market_width_series: 市場寬度評分序列
            pressure_series: 系統壓力評分序列

        Returns:
            RORO 狀態序列
        """
        try:
            # 對齊序列
            combined_df = pd.DataFrame({
                'market_width': market_width_series,
                'pressure': pressure_series
            }).dropna()

            if combined_df.empty:
                logger.warning("無有效數據進行狀態判斷")
                return pd.Series()

            # 應用狀態判斷函數
            states = combined_df.apply(
                lambda row: self._determine_single_state(row['market_width'], row['pressure']),
                axis=1
            )

            # 轉換為數值序列
            state_values = states.apply(lambda x: x.value)

            # 應用狀態平滑和確認
            smoothed_states = self._smooth_state_transitions(state_values)

            return smoothed_states

        except Exception as e:
            logger.error(f"序列狀態判斷失敗: {str(e)}")
            return pd.Series()

    def _combine_states_to_roro(self, width_state: str, pressure_state: str) -> ROROState:
        """
        將市場寬度和壓力狀態組合為 RORO 狀態

        Args:
            width_state: 市場寬度狀態
            pressure_state: 壓力狀態

        Returns:
            RORO 狀態
        """
        # RORO 狀態決策矩陣
        decision_matrix = {
            ('strong_bullish', 'low'): ROROState.STRONG_RISK_ON,
            ('strong_bullish', 'moderate'): ROROState.STRONG_RISK_ON,
            ('strong_bullish', 'high'): ROROState.WEAK_RISK_ON,
            ('strong_bullish', 'extreme'): ROROState.NEUTRAL,

            ('weak_bullish', 'low'): ROROState.STRONG_RISK_ON,
            ('weak_bullish', 'moderate'): ROROState.WEAK_RISK_ON,
            ('weak_bullish', 'high'): ROROState.NEUTRAL,
            ('weak_bullish', 'extreme'): ROROState.WEAK_RISK_OFF,

            ('neutral', 'low'): ROROState.WEAK_RISK_ON,
            ('neutral', 'moderate'): ROROState.NEUTRAL,
            ('neutral', 'high'): ROROState.WEAK_RISK_OFF,
            ('neutral', 'extreme'): ROROState.STRONG_RISK_OFF,

            ('weak_bearish', 'low'): ROROState.NEUTRAL,
            ('weak_bearish', 'moderate'): ROROState.WEAK_RISK_OFF,
            ('weak_bearish', 'high'): ROROState.STRONG_RISK_OFF,
            ('weak_bearish', 'extreme'): ROROState.STRONG_RISK_OFF,

            ('strong_bearish', 'low'): ROROState.WEAK_RISK_OFF,
            ('strong_bearish', 'moderate'): ROROState.STRONG_RISK_OFF,
            ('strong_bearish', 'high'): ROROState.STRONG_RISK_OFF,
            ('strong_bearish', 'extreme'): ROROState.STRONG_RISK_OFF,
        }

        return decision_matrix.get((width_state, pressure_state), ROROState.NEUTRAL)

    def _smooth_state_transitions(self, state_series: pd.Series) -> pd.Series:
        """
        平滑狀態轉換，避免過度頻繁的狀態變化

        Args:
            state_series: 原始狀態序列

        Returns:
            平滑後的狀態序列
        """
        try:
            # 使用移動平均進行平滑
            smoothed = state_series.rolling(
                window=self.transition_smoothing,
                min_periods=1,
                center=True
            ).median()

            # 四捨五入到最接近的狀態值
            smoothed = smoothed.round()

            # 確保狀態值在有效範圍內
            smoothed = smoothed.clip(-2, 2)

            return smoothed.astype(int)

        except Exception as e:
            logger.error(f"狀態平滑失敗: {str(e)}")
            return state_series

    def generate_investment_decision(self, roro_state: Union[ROROState, pd.Series]) -> Union[RORODecision, pd.Series]:
        """
        基於 RORO 狀態生成投資決策

        Args:
            roro_state: RORO 狀態

        Returns:
            投資決策
        """
        try:
            if isinstance(roro_state, ROROState):
                return self._single_state_to_decision(roro_state)
            elif isinstance(roro_state, pd.Series):
                return roro_state.apply(self._single_state_to_decision)
            else:
                raise ValueError("無效的 RORO 狀態輸入")

        except Exception as e:
            logger.error(f"投資決策生成失敗: {str(e)}")
            return RORODecision.NEUTRAL

    def _single_state_to_decision(self, state: ROROState) -> RORODecision:
        """
        單一狀態轉換為投資決策

        Args:
            state: RORO 狀態

        Returns:
            投資決策
        """
        state_decision_map = {
            ROROState.STRONG_RISK_ON: RORODecision.FULL_RISK_ON,
            ROROState.WEAK_RISK_ON: RORODecision.MODERATE_RISK_ON,
            ROROState.NEUTRAL: RORODecision.NEUTRAL,
            ROROState.WEAK_RISK_OFF: RORODecision.MODERATE_RISK_OFF,
            ROROState.STRONG_RISK_OFF: RORODecision.FULL_RISK_OFF,
        }

        return state_decision_map.get(state, RORODecision.NEUTRAL)

    def get_asset_allocation(self, decision: Union[RORODecision, pd.Series]) -> Union[Dict[str, float], pd.DataFrame]:
        """
        獲取資產配置建議

        Args:
            decision: 投資決策

        Returns:
            資產配置字典或 DataFrame
        """
        try:
            if isinstance(decision, RORODecision):
                return self.asset_allocation.get(decision, self.asset_allocation[RORODecision.NEUTRAL])
            elif isinstance(decision, pd.Series):
                # 為序列中的每個決策獲取配置
                allocations = []
                for dec in decision:
                    if isinstance(dec, RORODecision):
                        alloc = self.asset_allocation.get(dec, self.asset_allocation[RORODecision.NEUTRAL])
                    else:
                        # 如果是數值，嘗試匹配
                        alloc = self._get_allocation_by_value(dec)
                    allocations.append(alloc)

                # 轉換為 DataFrame
                if allocations:
                    return pd.DataFrame(allocations, index=decision.index)
                else:
                    return pd.DataFrame()

            else:
                raise ValueError("無效的決策輸入")

        except Exception as e:
            logger.error(f"資產配置獲取失敗: {str(e)}")
            return self.asset_allocation[RORODecision.NEUTRAL]

    def _get_allocation_by_value(self, value: float) -> Dict[str, float]:
        """
        基於數值獲取資產配置

        Args:
            value: 決策數值

        Returns:
            資產配置字典
        """
        if value >= 0.8:
            return self.asset_allocation[RORODecision.FULL_RISK_ON]
        elif value >= 0.3:
            return self.asset_allocation[RORODecision.MODERATE_RISK_ON]
        elif value >= -0.3:
            return self.asset_allocation[RORODecision.NEUTRAL]
        elif value >= -0.8:
            return self.asset_allocation[RORODecision.MODERATE_RISK_OFF]
        else:
            return self.asset_allocation[RORODecision.FULL_RISK_OFF]

    def generate_roro_signals(self, start_date: str, end_date: str) -> Dict[str, pd.Series]:
        """
        生成完整的 RORO 信號流程

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            包含所有信號的字典
        """
        try:
            logger.info(f"開始生成 RORO 信號: {start_date} 到 {end_date}")

            signals = {}

            # 1. 計算市場寬度指標
            market_indicators = self.market_indicator.calculate_all_indicators(start_date, end_date)
            if market_indicators:
                signals.update(market_indicators)

            # 2. 計算系統壓力指數
            pressure_indicators = self.pressure_index.calculate_composite_pressure_index(start_date, end_date)
            if pressure_indicators:
                signals.update(pressure_indicators)

            # 3. 生成 RORO 狀態 (需要市場寬度和壓力指數)
            if 'market_width_score' in signals and 'composite_pressure_index' in signals:
                roro_states = self.determine_roro_state(
                    signals['market_width_score'],
                    signals['composite_pressure_index']
                )

                if isinstance(roro_states, pd.Series) and not roro_states.empty:
                    signals['roro_state'] = roro_states

                    # 4. 生成投資決策
                    decisions = self.generate_investment_decision(roro_states)
                    if isinstance(decisions, pd.Series) and not decisions.empty:
                        signals['investment_decision'] = decisions.apply(lambda x: x.value if hasattr(x, 'value') else x)

                        # 5. 生成資產配置
                        allocations = self.get_asset_allocation(decisions)
                        if isinstance(allocations, pd.DataFrame) and not allocations.empty:
                            # 將配置存儲為單獨的序列
                            for asset in ['TXF', 'TLT', 'GLD']:
                                if asset in allocations.columns:
                                    signals[f'allocation_{asset}'] = allocations[asset]

            logger.info(f"成功生成 {len(signals)} 項 RORO 信號")
            return signals

        except Exception as e:
            logger.error(f"RORO 信號生成失敗: {str(e)}")
            return {}

    def get_signal_summary(self, signals: Dict[str, pd.Series]) -> Dict[str, any]:
        """
        生成信號摘要統計

        Args:
            signals: 信號字典

        Returns:
            摘要統計字典
        """
        try:
            summary = {}

            if 'roro_state' in signals:
                state_counts = signals['roro_state'].value_counts().sort_index()
                summary['roro_state_distribution'] = state_counts.to_dict()

                # 計算狀態轉換頻率
                state_changes = signals['roro_state'].diff().abs()
                summary['state_transition_frequency'] = (state_changes > 0).sum()

            if 'investment_decision' in signals:
                decision_stats = signals['investment_decision'].describe()
                summary['decision_statistics'] = decision_stats.to_dict()

            # 信號品質指標
            if len(signals) > 0:
                summary['total_signals'] = len(signals)
                summary['date_range'] = {
                    'start': min([s.index.min() for s in signals.values() if not s.empty]),
                    'end': max([s.index.max() for s in signals.values() if not s.empty])
                }

            return summary

        except Exception as e:
            logger.error(f"信號摘要生成失敗: {str(e)}")
            return {}


def main():
    """
    主函數 - 用於測試 RORO 引擎
    """
    # 配置日誌
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 測試 RORO 引擎
    try:
        engine = ROROEngine()

        # 測試期間
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"測試 RORO 信號生成: {start_date} 到 {end_date}")

        # 生成 RORO 信號
        signals = engine.generate_roro_signals(start_date, end_date)

        if signals:
            logger.info(f"成功生成以下信號: {list(signals.keys())}")

            # 生成摘要
            summary = engine.get_signal_summary(signals)
            logger.info(f"信號摘要: {summary}")

            # 顯示最新信號
            for name, series in signals.items():
                if not series.empty and len(series) > 0:
                    latest_value = series.iloc[-1]
                    logger.info(f"{name}: {latest_value}")
        else:
            logger.warning("RORO 信號生成失敗")

    except Exception as e:
        logger.error(f"測試失敗: {str(e)}")


if __name__ == "__main__":
    main()



