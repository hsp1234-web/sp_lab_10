# -*- coding: utf-8 -*-
"""
RORO 量化交易策略包

此包包含動態風險開啟/關閉 (Risk-On/Risk-Off, RORO) 策略的所有模塊。
"""

from .market_indicators import MarketWidthIndicator
from .pressure_index import SystemPressureIndex
from .roro_engine import ROROEngine, ROROState, RORODecision
from .roro_signal_generator import ROROSignalGenerator
from .signal_validator import SignalValidator
from .ny_fed_integration import NYFedDataLoader, NYFedPressureIndicator

__all__ = [
    'MarketWidthIndicator',
    'SystemPressureIndex',
    'ROROEngine',
    'ROROState',
    'RORODecision',
    'ROROSignalGenerator',
    'SignalValidator',
    'NYFedDataLoader',
    'NYFedPressureIndicator'
]

__version__ = "1.0.0"
