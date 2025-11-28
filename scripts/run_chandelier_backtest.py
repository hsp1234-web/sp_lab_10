#!/usr/bin/env python3
"""
Chandelier 策略回測執行腳本
執行強化版 Chandelier 策略，包含風控模組
"""

import sys
import os
import json
import logging
from pathlib import Path
import io

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'lo2cin4bt-main'))

def setup_logging():
    """設定日誌"""
    # 禁用 Rich 的 emoji 使用簡單格式
    import os
    os.environ['RICH_NO_EMOJI'] = '1'

    # 將 sys.stdout 重定向到一個支援 UTF-8 的 TextIOWrapper
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', line_buffering=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('chandelier_backtest.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_chandelier_backtest():
    """執行 Chandelier 策略回測"""
    logger = setup_logging()
    logger.info("開始執行 Chandelier 策略回測")

    try:
        # 直接使用 IncrementalBacktestEngine
        from backtester.IncrementalBacktestEngine import IncrementalBacktestEngine

        # 載入配置檔案
        config_path = project_root / 'config' / 'chandelier_backtest_config.json'
        logger.info(f"載入配置檔案: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        logger.info(f"配置載入成功: {config['job_name']}")
        logger.info(f"數據範圍: {config['data']['start_date']} 到 {config['data']['end_date']}")

        # 創建數據庫路徑
        db_path = str(project_root / 'records' / 'chandelier_backtest.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 載入數據
        logger.info("載入台指期數據...")
        import duckdb

        # 直接使用 DuckDB 載入數據
        db_path = str(project_root / 'data' / 'taifex.db')
        logger.info(f"連接數據庫: {db_path}")

        con = duckdb.connect(db_path)

        # 載入台指期數據 - 轉換日期格式
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
        AND Open IS NOT NULL
        AND High IS NOT NULL
        AND Low IS NOT NULL
        AND Close IS NOT NULL
        ORDER BY strptime(Date, '%Y/%m/%d')
        """

        data = con.execute(query).fetchdf()
        con.close()

        logger.info(f"數據載入完成，形狀: {data.shape}")
        logger.info(f"數據日期範圍: {data['original_date'].min()} 到 {data['original_date'].max()}")

        # 重新命名欄位以符合框架期望
        column_mapping = {
            'Time': 'Time',
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume'
        }

        data = data.rename(columns=column_mapping)
        logger.info(f"欄位重新命名完成")
        logger.info(f"最終欄位: {list(data.columns)}")

        # 創建回測引擎
        logger.info("初始化回測引擎...")
        engine = IncrementalBacktestEngine(data, config['data']['interval'], db_path)

        # 執行回測
        logger.info("開始執行回測...")
        engine.run_backtests(config, config['job_name'], resume=True) # 將 resume 設為 True

        logger.info("回測執行完成！")

    except Exception as e:
        logger.error(f"回測執行失敗: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    run_chandelier_backtest()
