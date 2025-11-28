#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雙均線策略完整回測腳本
"""
import sys
import os
import io
import json
import logging
from pathlib import Path

# 設置 UTF-8 輸出
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', line_buffering=True)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dual_ma_backtest.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 添加 lo2cin4bt 到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'lo2cin4bt-main'))

def run_dual_ma_backtest():
    """執行雙均線策略完整回測"""
    logger.info("開始執行雙均線策略完整回測")

    try:
        # 載入配置檔案
        config_path = project_root / 'config' / 'dual_ma_backtest_config.json'

        # 如果配置文件不存在，建立一個
        if not config_path.exists():
            logger.info("建立雙均線策略配置檔案")
            config = {
                "job_name": "dual_ma_trend_following_backtest",
                "mode": "incremental",
                "database_path": "records/dual_ma_backtest.db",
                "system": {
                    "max_workers": "auto",
                    "batch_size": 20
                },
                "predictors": [],
                "condition_pairs": [
                    {
                        "entry": ["DUAL_MA"],
                        "exit": ["DUAL_MA"]
                    }
                ],
                "indicator_params": {
                    "DUAL_MA_strategy_1": {
                        "fast_period": [20],
                        "slow_period": [60],
                        "volume_multiplier": [1.2],
                        "risk_per_trade": [0.01],
                        "stop_loss_atr_multiplier": [2.0],
                        "max_monthly_drawdown": [0.05]
                    }
                },
                "data": {
                    "source": "duckdb",
                    "db_path": "data/taifex.db",
                    "symbol": "TX",
                    "interval": "1d",
                    "start_date": "2018-01-01",
                    "end_date": "2024-12-31"
                },
                "trading": {
                    "initial_capital": 1000000,
                    "transaction_cost": 0.0004,
                    "slippage": 1,
                    "trade_delay": 0,
                    "trade_unit": 1
                }
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            logger.info(f"配置檔案已建立: {config_path}")
        else:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"載入配置檔案: {config_path}")

        logger.info(f"配置載入成功: {config['job_name']}")
        logger.info(f"數據範圍: {config['data']['start_date']} 到 {config['data']['end_date']}")

        # 載入數據
        logger.info("載入台指期數據...")
        import duckdb

        # 使用完整數據進行回測，但過濾異常值
        db_path = str(project_root / 'data' / 'taifex.db')
        logger.info(f"連接數據庫: {db_path}")

        con = duckdb.connect(db_path)

        query = f"""
        SELECT
            Date as original_date,
            strptime(Date, '%Y/%m/%d') as Time,
            Symbol,
            Open,
            High,
            Low,
            Close,
            Volume
        FROM futures_data
        WHERE Symbol = '{config['data']['symbol']}'
        AND strptime(Date, '%Y/%m/%d') >= strptime('{config['data']['start_date']}', '%Y-%m-%d')
        AND strptime(Date, '%Y/%m/%d') <= strptime('{config['data']['end_date']}', '%Y-%m-%d')
        AND Close IS NOT NULL AND Close > 100 AND Close < 30000  -- 過濾異常價格
        ORDER BY strptime(Date, '%Y/%m/%d')
        """

        data = con.execute(query).fetchdf()
        con.close()

        logger.info(f"數據載入完成，形狀: {data.shape}")
        logger.info(f"數據日期範圍: {data['original_date'].min()} 到 {data['original_date'].max()}")

        # 重新命名欄位
        data = data.rename(columns={'Time': 'Time'})
        logger.info(f"最終欄位: {list(data.columns)}")

        # 創建回測引擎
        logger.info("初始化回測引擎...")
        from backtester.IncrementalBacktestEngine import IncrementalBacktestEngine

        db_path = str(project_root / 'records' / 'dual_ma_backtest.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        engine = IncrementalBacktestEngine(data, config['data']['interval'], db_path)

        # 執行回測
        logger.info("開始執行回測...")
        engine.run_backtests(config, config['job_name'], resume=True)

        logger.info("雙均線策略回測執行完成！")

    except Exception as e:
        logger.error(f"回測執行失敗: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    run_dual_ma_backtest()

