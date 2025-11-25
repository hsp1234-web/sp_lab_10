# -*- coding: utf-8 -*-
"""
快速回饋核心回測腳本

這個腳本提供了一個由設定檔驅動的、非互動式的回測流程，
旨在快速驗證交易邏輯並獲得即時的績效回饋。

主要流程：
1. 讀取指定的 JSON 設定檔。
2. 從 yfinance.db 數據庫加載指定的市場數據。
3. 初始化增量回測引擎 (IncrementalBacktestEngine)。
4. 執行回測。
5. (未來) 在回測過程中即時輸出月度績效。
"""
import sys
import os
import json
import argparse
import logging
import duckdb
import pandas as pd
import itertools
import types
from pathlib import Path

# --- 路徑設定 ---
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "lo2cin4bt-main"))

from backtester.IncrementalBacktestEngine import IncrementalBacktestEngine

# --- 日誌設定 ---
def setup_logging(log_path):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding='utf-8')
        ]
    )

# --- 核心函式 ---
def load_config(config_path: Path) -> dict:
    """從 JSON 檔案載入設定。"""
    if not config_path.exists():
        raise FileNotFoundError(f"設定檔不存在：{config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_data_from_db(db_path: Path, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """從 DuckDB 載入市場數據。"""
    if not db_path.exists():
        raise FileNotFoundError(f"數據庫不存在：{db_path}")

    con = duckdb.connect(str(db_path))
    query = f"""
        SELECT * FROM ohlcv
        WHERE Symbol = ?
        AND Time BETWEEN ? AND ?
        ORDER BY Time
    """
    df = con.execute(query, [symbol, start_date, end_date]).df()
    con.close()

    df.rename(columns={'time': 'Time'}, inplace=True, errors='ignore')
    df['Time'] = pd.to_datetime(df['Time'])  # 確保時間欄位是 datetime 格式
    return df

def prepare_engine_config(config: dict) -> dict:
    """將我們的 JSON 設定轉換為引擎可接受的格式。"""
    strategy_name = config["strategy"]["name"]
    params_range = config["strategy"]["params_range"]

    # 1. 構造 condition_pairs (最終修正格式)
    # 引擎期望 entry/exit 的值是策略名稱的列表, e.g., ["MovingAverage"]
    condition_pairs = [{
        "entry": [strategy_name],
        "exit": [strategy_name]
    }]

    # 2. 構造 indicator_params
    keys = list(params_range.keys())
    values = list(params_range.values())

    param_list = []
    if not keys:
        # 處理無參數的策略
        param_dict = {
            "indicator_type": strategy_name,
            "params": {}
        }
        param_obj = json.loads(json.dumps(param_dict), object_hook=lambda d: types.SimpleNamespace(**d))
        param_list.append(param_obj)
    else:
        combinations = list(itertools.product(*values))
        for combo in combinations:
            # 框架的核心期望一個具有 .params 屬性的物件
            param_details = dict(zip(keys, combo))

            # 創建一個巢狀結構
            param_dict = {
                "indicator_type": strategy_name,
                "params": param_details
            }

            # 將字典遞歸地轉換為 SimpleNamespace 對象
            param_obj = json.loads(json.dumps(param_dict), object_hook=lambda d: types.SimpleNamespace(**d))
            param_list.append(param_obj)

    # 引擎會使用 condition_pairs 中的 "entry" 值 (e.g., "MovingAverage")
    # 來構造鍵 "MovingAverage_strategy_1"，並在此查找參數列表。
    indicator_params = {
        f"{strategy_name}_strategy_1": param_list
    }

    # 3. 構造最終的 engine_config
    engine_config = {
        "condition_pairs": condition_pairs,
        "indicator_params": indicator_params,
        "predictors": ["Close"],  # 默認使用收盤價
        "trading_params": config.get("trading", {})
    }

    return engine_config, len(param_list)

def main():
    parser = argparse.ArgumentParser(description="快速回饋回測腳本")
    parser.add_argument("--config", type=str, default="config/quick_feedback.json", help="回測設定檔的路徑")
    args = parser.parse_args()

    config_path = PROJECT_ROOT / args.config
    config = load_config(config_path)

    log_dir = PROJECT_ROOT / "output" / "logs"
    log_dir.mkdir(exist_ok=True)
    setup_logging(log_dir / "quick_feedback.log")
    logger = logging.getLogger("QuickFeedbackRunner")

    logger.info(f"--- 開始執行快速回饋回測任務 ---")
    logger.info(f"使用設定檔: {config_path}")

    data_config = config['data']
    db_path = PROJECT_ROOT / data_config['db_path']
    logger.info(f"正在從 {db_path} 載入 '{data_config['symbol']}' 的數據...")

    data = load_data_from_db(db_path, data_config['symbol'], data_config['start_date'], data_config['end_date'])

    if data.empty:
        logger.error("數據為空，無法進行回測。請檢查數據庫和設定。")
        return

    logger.info(f"成功載入 {len(data)} 筆數據。")

    engine_config_params = config['engine']
    db_output_path = str(PROJECT_ROOT / engine_config_params['db_output_path'])

    engine = IncrementalBacktestEngine(data=data, frequency=data_config['frequency'], db_path=db_output_path)

    logger.info(f"回測引擎已初始化。結果將儲存至: {db_output_path}")

    # 準備並執行回測
    engine_config, num_combos = prepare_engine_config(config)
    logger.info(f"已生成 {num_combos} 種參數組合，準備執行回測...")

    try:
        engine.run_backtests(
            config=engine_config,
            job_id=config['job_name'],
            resume=False  # 強制重新計算
        )
        logger.info("--- 回測執行成功 ---")
    except Exception as e:
        logger.error(f"回測執行失敗: {e}", exc_info=True)

    logger.info("--- 任務執行完畢 ---")

if __name__ == "__main__":
    main()
