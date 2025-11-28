#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試雙均線策略的基本功能
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_dual_ma.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 添加 lo2cin4bt 到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'lo2cin4bt-main'))

def test_dual_ma_basic():
    """測試雙均線策略基本功能"""
    logger.info("開始測試雙均線策略基本功能")

    try:
        import duckdb
        import pandas as pd
        import numpy as np

        # 載入最近 2 年數據進行測試
        logger.info("載入台指期數據 (最近2年)...")
        db_path = str(project_root / 'data' / 'taifex.db')
        con = duckdb.connect(db_path)

        query = """
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
        WHERE Symbol = 'TX'
        AND strptime(Date, '%Y/%m/%d') >= strptime('2023-01-01', '%Y-%m-%d')
        AND strptime(Date, '%Y/%m/%d') <= strptime('2024-12-31', '%Y-%m-%d')
        AND Close IS NOT NULL AND Close > 1000  -- 過濾異常數據
        ORDER BY strptime(Date, '%Y/%m/%d')
        """

        data = con.execute(query).fetchdf()
        con.close()

        logger.info(f"測試數據形狀: {data.shape}")
        logger.info(f"測試數據日期範圍: {data['original_date'].min()} 到 {data['original_date'].max()}")

        if len(data) < 100:
            logger.error("數據量不足，無法進行測試")
            return

        # 導入雙均線策略
        from backtester.Dual_MA_Strategy_backtester import DualMovingAverageStrategy

        # 設定策略參數
        params = {
            'fast_period': 20,
            'slow_period': 60,
            'volume_multiplier': 1.2,
            'risk_per_trade': 0.01,
            'stop_loss_atr_multiplier': 2.0,
            'max_monthly_drawdown': 0.05
        }

        logger.info(f"策略參數: {params}")

        # 建立策略實例
        dual_ma = DualMovingAverageStrategy(data, params, logger)

        # 生成信號
        signals = dual_ma.generate_signals()

        logger.info(f"信號總數: {len(signals)}")
        logger.info(f"多頭進場信號: {np.sum(signals == 1)}")
        logger.info(f"空頭進場信號: {np.sum(signals == -1)}")
        logger.info(f"非零信號: {np.sum(signals != 0)}")

        # 統計交易訊息
        data['Signal'] = signals

        # 簡單模擬交易
        trades = []
        current_position = 0
        entry_price = 0
        entry_date = None

        for idx, row in data.iterrows():
            if row['Signal'] == 1 and current_position <= 0:
                # 進場多頭
                current_position = 1
                entry_price = row['Close']
                entry_date = row['original_date']
                trades.append({
                    'type': 'LONG_ENTRY',
                    'date': entry_date,
                    'price': entry_price
                })
                logger.info(f"[{entry_date}] 多頭進場 @ {entry_price}")

            elif row['Signal'] == -1 and current_position >= 0:
                if current_position == 1:
                    # 出場多頭
                    exit_price = row['Close']
                    pnl = (exit_price - entry_price) / entry_price * 100
                    trades.append({
                        'type': 'LONG_EXIT',
                        'date': row['original_date'],
                        'price': exit_price,
                        'entry_date': entry_date,
                        'entry_price': entry_price,
                        'pnl_pct': pnl
                    })
                    logger.info(f"[{row['original_date']}] 多頭出場 @ {exit_price}, PnL: {pnl:.2f}%")
                    current_position = 0
                else:
                    # 進場空頭
                    current_position = -1
                    entry_price = row['Close']
                    entry_date = row['original_date']
                    trades.append({
                        'type': 'SHORT_ENTRY',
                        'date': entry_date,
                        'price': entry_price
                    })
                    logger.info(f"[{entry_date}] 空頭進場 @ {entry_price}")

        # 統計結果
        logger.info(f"\n===== 雙均線策略測試統計 =====")
        logger.info(f"總交易筆數: {len(trades)}")

        long_trades = [t for t in trades if 'entry_price' in t and 'pnl_pct' in t]
        if long_trades:
            avg_pnl = np.mean([t['pnl_pct'] for t in long_trades])
            win_rate = len([t for t in long_trades if t['pnl_pct'] > 0]) / len(long_trades) * 100
            logger.info(f"完整交易 (進出場對): {len(long_trades)}")
            logger.info(f"平均 PnL: {avg_pnl:.2f}%")
            logger.info(f"勝率: {win_rate:.1f}%")

            # 詳細交易記錄
            logger.info("\n詳細交易記錄:")
            for i, trade in enumerate(long_trades[:10]):  # 只顯示前10筆
                logger.info(f"{i+1}. {trade['entry_date']} -> {trade['date']}: {trade['pnl_pct']:.2f}%")

        # 導出測試結果
        output_path = Path('output/dual_ma_test_signals.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"測試信號已導出到: {output_path}")

        # 檢查均線計算
        logger.info("\n均線計算檢查:")
        sample_data = data.head(10)[['original_date', 'Close', 'Signal']].copy()
        if 'EMA_fast' in data.columns and 'EMA_slow' in data.columns:
            sample_data['EMA_20'] = data['EMA_fast'].head(10)
            sample_data['EMA_60'] = data['EMA_slow'].head(10)
        logger.info(sample_data.to_string())

        logger.info("\n[OK] 雙均線策略測試完成")

    except Exception as e:
        logger.error(f"[ERR] 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dual_ma_basic()

