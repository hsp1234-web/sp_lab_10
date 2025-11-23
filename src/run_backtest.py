# -*- coding: utf-8 -*-
"""
Main entry point for the modular backtesting system.
"""
import warnings
import pandas as pd
import sys
import time
import os
# Add project root to sys.path to allow importing config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from src.data_loader import load_and_process_data
from src.strategy_engine import get_strategy_class
from src.backtest_engine import run_backtest
from src.reporting import generate_report

# --- Global Settings ---
warnings.filterwarnings('ignore', category=FutureWarning)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

def run_backtest_process():
    """
    The core backtest logic to be run.
    """
    print("=== Starting Modular Backtest System ===")
    sys.stdout.flush()
    try:
        # 1. Load Data
        data = load_and_process_data(config.TICKER, config.START_DATE, config.END_DATE)
        if data.empty:
            print("Exiting due to missing data.")
            return

        # 2. Select Strategy
        StrategyClass = get_strategy_class('SupertrendBNF')

        # 3. Run Backtest & Optimization
        bt, stats = run_backtest(
            data,
            StrategyClass,
            cash=config.INITIAL_CASH,
            commission=config.COMMISSION_RATE,
            optimize=True,
            optimize_params=config.OPTIMIZATION_PARAMS
        )

        if stats is None:
            print("Backtest failed.")
            return

        # 4. Generate Report
        generate_report(bt, stats, config.TICKER, config.OUTPUT_DIR)
        print("=== Process Completed Successfully ===")
        sys.stdout.flush()
    except Exception as e:
        print(f"An error occurred during backtest execution: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()

def main():
    """
    Main entry point that runs the backtest directly.
    """
    print("Starting backtest (no timeout, will run until completion)...")
    start_time = time.time()
    run_backtest_process()
    elapsed = time.time() - start_time
    print(f"\nBacktest finished in {elapsed:.2f} seconds.")
    sys.stdout.flush()

if __name__ == '__main__':
    main()
