# -*- coding: utf-8 -*-
from backtesting import Backtest
import sys

def run_backtest(data, strategy_class, cash, commission, optimize=False, optimize_params=None):
    """
    Initialize and run the backtest.
    """
    print("[Backtest] Initializing backtest engine...")
    bt = Backtest(data, strategy_class, cash=cash, commission=commission)

    if optimize and optimize_params:
        print("[Backtest] Starting optimization (this may take a while)...")
        # Ensure output is flushed so user sees the message immediately
        sys.stdout.flush() 
        
        try:
            stats = bt.optimize(**optimize_params)
            print("[Backtest] Optimization completed.")
            return bt, stats
        except Exception as e:
            print(f"[Backtest] Error during optimization: {e}")
            return bt, None
    else:
        print("[Backtest] Running single backtest...")
        stats = bt.run()
        print("[Backtest] Execution completed.")
        return bt, stats
