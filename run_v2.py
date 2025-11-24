import sys
import os
import json
import argparse
import logging
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "lo2cin4bt-main"))

from backtester.IncrementalBacktestEngine import IncrementalBacktestEngine
from database.BacktestDB import BacktestDB
# from data_loader.DuckDBLoader import DuckDBLoader # 假設有這個 Loader

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("v2_backtest.log", encoding='utf-8')
        ]
    )

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_data(data_config):
    """
    載入回測數據
    這裡簡單實作，直接讀取 Parquet 或 CSV，或者連接 DuckDB
    """
    print(f"正在載入數據: {data_config}")
    # 暫時使用假數據生成，以便測試流程 (除非有真實數據路徑)
    # 實際專案中應調用 DataManager
    
    # 嘗試讀取 data/taifex.db (如果存在)
    db_path = data_config.get("db_path", "data/taifex.db")
    if os.path.exists(db_path):
        import duckdb
        conn = duckdb.connect(db_path)
        symbol = data_config.get("symbol", "TXF")
        start = data_config.get("start_date")
        end = data_config.get("end_date")
        
        query = f"""
            SELECT * FROM futures_1min 
            WHERE symbol = '{symbol}' 
            AND ts BETWEEN '{start}' AND '{end}'
            ORDER BY ts
        """
        try:
            df = conn.execute(query).df()
            # Rename columns to match engine expectations
            df = df.rename(columns={"ts": "Time", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
            conn.close()
    setup_logging()
    logger = logging.getLogger("V2_Runner")
    
    parser = argparse.ArgumentParser(description="V2 Incremental Backtest Runner")
    parser.add_argument("--config", type=str, default="config/backtest_config_template.json", help="Path to config file")
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        logger.error(f"Config file not found: {args.config}")
        return

    # 1. Load Config
    config = load_config(args.config)
    job_name = config.get("job_name", "default_job")
    db_path = config.get("database_path", "records/backtest_v2.db")
    
    logger.info(f"Job: {job_name}")
    logger.info(f"DB: {db_path}")
    
    # 2. Load Data
    data = load_data(config.get("data", {}))
    
    # 3. Initialize Engine
    engine = IncrementalBacktestEngine(
        data=data,
        frequency=config.get("data", {}).get("interval", "1m"),
        db_path=db_path
    )
    
    # 4. Run Backtest
    # 為了適配 VectorBacktestEngine 的 generate_parameter_combinations
    # 我們需要把 config 轉換成它期望的格式 (all_tasks)
    
    # 1. 構造 condition_pairs
    strategy_name = config["strategy"]["name"]
    condition_pairs = [
        {
            "entry": [strategy_name],
            "exit": [strategy_name]
        }
    ]
    
    # 2. 構造 indicator_params
    # 生成所有參數組合
    import itertools
    params_range = config["strategy"]["params_range"]
    keys = list(params_range.keys())
    values = list(params_range.values())
    combinations = list(itertools.product(*values))
    
    param_list = []
    for combo in combinations:
        param_dict = {"indicator_type": strategy_name}
        for k, v in zip(keys, combo):
            param_dict[k] = v
        param_list.append(param_dict)
        
    indicator_params = {
        f"{strategy_name}_strategy_1": param_list,
        f"{strategy_name}_strategy_1_exit": param_list # 假設出場參數與進場相同，或者根據策略邏輯調整
    }
    
    # 3. 構造 engine_config
    engine_config = {
        "condition_pairs": condition_pairs,
        "indicator_params": indicator_params,
        "predictors": ["Close"], # 默認預測因子
        "trading_params": config.get("trading", {})
    }
    
    logger.info(f"Generated {len(param_list)} parameter combinations.")
    
    try:
        engine.run_backtests(engine_config, job_id=job_name, resume=True)
    except Exception as e:
        logger.error(f"回測執行失敗: {e}", exc_info=True)

if __name__ == "__main__":
    main()
