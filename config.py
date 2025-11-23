# -*- coding: utf-8 -*-
"""
Centralized configuration for the project.
"""

# Backtest Parameters
TICKER = '0050.TW'
START_DATE = '2010-01-01'
END_DATE = '2023-12-31'
INITIAL_CASH = 1_000_000
COMMISSION_RATE = .001425  # Taiwan stock commission rate

# Optimization Parameters
OPTIMIZATION_PARAMS = {
    'bnf_ma_period': range(60, 181, 20),
    'bnf_entry_bias': [x / 100.0 for x in range(-10, -2, 1)],
    'maximize': 'Sharpe Ratio'
}

# Output Paths
OUTPUT_DIR = 'output/generated'

# Execution Settings
TIMEOUT_SECONDS = 60  # 1 minute timeout as requested
