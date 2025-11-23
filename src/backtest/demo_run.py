import sys
import os
import logging
import traceback

# Configure logging to BOTH file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('demo_run.log', mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # Add console output
    ]
)
logger = logging.getLogger("demo_run")

try:
    from pathlib import Path
    import pandas as pd

    # Add lo2cin4bt-main to sys.path
    project_root = Path(__file__).parent
    lo2cin4bt_path = project_root / "lo2cin4bt-main"
    sys.path.append(str(lo2cin4bt_path))

    # Import necessary modules from lo2cin4bt
    from dataloader.yfinance_loader import YahooFinanceLoader
    from autorunner.BacktestRunner_autorunner import BacktestRunnerAutorunner
except Exception as e:
    logger.error(f"Top-level Error: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

class DemoLoader(YahooFinanceLoader):
    """Subclass of YahooFinanceLoader to bypass interactive inputs."""
    
    def __init__(self, ticker="SPY", start_date="2017-01-01", end_date=None):
        super().__init__()
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        
    def _get_ticker(self) -> str:
        return self.ticker
        
    def _get_frequency(self) -> str:
        return "1d"
        
    def _get_date_range(self):
        from datetime import datetime
        end = self.end_date or datetime.now().strftime("%Y-%m-%d")
        return self.start_date, end
    
    # Override show methods to log instead of print
    def show_error(self, message: str) -> None:
        logger.error(message)
        
    def show_success(self, message: str) -> None:
        logger.info(message)
        
    def show_warning(self, message: str) -> None:
        logger.warning(message)
        
    def show_info(self, message: str) -> None:
        logger.info(message)

def main():
    logger.info("🚀 Starting Demo Run with lo2cin4bt...")
    
    try:
        # 1. Load Data
        logger.info("📥 Loading SPY data from 2017-01-01...")
        loader = DemoLoader(ticker="SPY", start_date="2017-01-01")
        data, frequency = loader.load()
        
        if data is None or data.empty:
            logger.error("❌ Failed to load data. Exiting.")
            return

        logger.info(f"✅ Data loaded: {len(data)} rows")
        
        # 2. Configure Backtest
        logger.info("⚙️ Configuring Backtest (Strategy: 20-day SMA Crossover)...")
        config = {
            "dataloader": {
                "source": "yfinance",
                "yfinance_config": {"symbol": "SPY"},
                "frequency": "1d",
                "predictor_config": {"predictor_path": "SPY_Demo"} 
            },
            "backtester": {
                "condition_pairs": [
                    {
                        "entry": ["MA1"], # Price > MA (Buy)
                        "exit": ["MA4"]   # Price < MA (Sell/Short)
                    }
                ],
                "indicator_params": {
                    "MA1_strategy_1": {
                        "ma_type": "SMA",
                        "ma_range": "20:20:1" 
                    },
                    "MA4_strategy_1": {
                        "ma_type": "SMA",
                        "ma_range": "20:20:1"
                    }
                },
                "trading_params": {
                    "initial_capital": 1000000,
                    "commission": 0.001,
                    "pyramiding": 1,
                    "mode": "Cash"
                },
                "selected_predictor": "Close"
            }
        }
        
        # 3. Run Backtest
        logger.info("🏃 Running Vectorized Backtest...")
        runner = BacktestRunnerAutorunner(logger=logger)
        results = runner.run_backtest(data, config)
        
        if results:
            logger.info("✅ Backtest Completed Successfully!")
            logger.info(f"📊 Results saved to records/backtester/")
            
            # Write summary to file
            with open("demo_summary.txt", "w", encoding="utf-8") as f:
                f.write("Backtest Summary\n")
                f.write("================\n")
                res_list = results.get("results", [])
                if res_list:
                    best_res = res_list[0]
                    f.write(f"Total Return: {best_res.get('total_return_pct', 0):.2f}%\n")
                    f.write(f"Win Rate: {best_res.get('win_rate', 0):.2f}%\n")
                    f.write(f"Trades: {best_res.get('total_trades', 0)}\n")
                    f.write(f"Sharpe Ratio: {best_res.get('sharpe_ratio', 0):.2f}\n")
                    f.write(f"Max Drawdown: {best_res.get('max_drawdown_pct', 0):.2f}%\n")
                else:
                    f.write("No results found in output.\n")
        else:
            logger.error("❌ Backtest Failed.")
            
    except Exception as e:
        logger.error(f"Exception in main: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
