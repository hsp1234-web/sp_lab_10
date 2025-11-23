# -*- coding: utf-8 -*-
import os
import pandas as pd

def generate_report(bt, stats, ticker, output_dir):
    """
    Generate and save backtest reports.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Print Best Parameters
    print("\n[Report] Best Parameter Combination:")
    print(stats._strategy)

    # Print Risk Metrics
    equity_curve = stats['_equity_curve']
    monthly_returns = equity_curve['Equity'].resample('ME').last().pct_change()
    max_monthly_loss = monthly_returns.min()
    print("\n[Report] Risk Assessment (Optimized):")
    print(f"Max Monthly Loss: {max_monthly_loss:.2%}")

    # Save HTML Plot
    safe_ticker_name = ticker.replace(".", "_")
    plot_filename = os.path.join(output_dir, f'backtest_results_{safe_ticker_name}_optimized.html')
    
    # Note: open_browser=False prevents it from trying to pop up a window
    bt.plot(filename=plot_filename, open_browser=False)
    print(f"\n[Report] Detailed HTML report saved to: {plot_filename}")

    # Save Stats to Text File
    stats_filename = os.path.join(output_dir, f'stats_{safe_ticker_name}.txt')
    with open(stats_filename, 'w', encoding='utf-8') as f:
        f.write(str(stats))
    print(f"[Report] Statistics saved to: {stats_filename}")
