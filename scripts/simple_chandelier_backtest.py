#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版 Chandelier 回測腳本 - 直接執行回測邏輯
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
        logging.FileHandler('simple_backtest.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 添加 lo2cin4bt 到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'lo2cin4bt-main'))

def main():
    logger.info("開始簡化版 Chandelier 回測")
    
    try:
        import duckdb
        import pandas as pd
        import numpy as np
        
        # 讀取資料
        logger.info("載入台指期數據...")
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
        AND strptime(Date, '%Y/%m/%d') >= strptime('2018-01-01', '%Y-%m-%d')
        AND strptime(Date, '%Y/%m/%d') <= strptime('2024-12-31', '%Y-%m-%d')
        ORDER BY strptime(Date, '%Y/%m/%d')
        """
        
        data = con.execute(query).fetchdf()
        con.close()
        
        logger.info(f"資料形狀: {data.shape}")
        logger.info(f"資料日期範圍: {data['original_date'].min()} 到 {data['original_date'].max()}")
        
        # 重新命名欄位
        data = data.rename(columns={'Time': 'Time'})
        
        # 導入 Chandelier 指標
        from backtester.Chandelier_Indicator_backtester import ChandelierIndicator
        
        # 建立參數
        params = {
            'length': 14,
            'multiplier': 2.0,
            'risk_per_trade': 0.01,
            'stop_loss_atr_multiplier': 2.0,
            'max_monthly_drawdown': 0.05
        }
        
        logger.info(f"策略參數: {params}")
        
        # 執行指標計算
        chandelier = ChandelierIndicator(data, params, logger)
        signals = chandelier.generate_signals()
        
        logger.info(f"信號總數: {len(signals)}")
        logger.info(f"多頭進場信號: {np.sum(signals == 1)}")
        logger.info(f"空頭進場信號: {np.sum(signals == -1)}")
        logger.info(f"非零信號: {np.sum(signals != 0)}")
        
        # 儲存結果
        data['Signal'] = signals
        
        # 統計交易訊息
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
                # 進場空頭或出場多頭
                if current_position == 1:
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
                    current_position = -1
                    entry_price = row['Close']
                    entry_date = row['original_date']
                    trades.append({
                        'type': 'SHORT_ENTRY',
                        'date': entry_date,
                        'price': entry_price
                    })
                    logger.info(f"[{entry_date}] 空頭進場 @ {entry_price}")
        
        # 統計
        logger.info(f"\n===== 交易統計 =====")
        logger.info(f"總交易筆數: {len(trades)}")
        
        long_trades = [t for t in trades if 'entry_price' in t and 'pnl_pct' in t]
        if long_trades:
            avg_pnl = np.mean([t['pnl_pct'] for t in long_trades])
            win_rate = len([t for t in long_trades if t['pnl_pct'] > 0]) / len(long_trades) * 100
            logger.info(f"完整交易 (進出場): {len(long_trades)}")
            logger.info(f"平均 PnL: {avg_pnl:.2f}%")
            logger.info(f"勝率: {win_rate:.1f}%")
        
        # 導出結果到 CSV
        output_path = Path('output/chandelier_backtest_signals.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"信號已導出到: {output_path}")
        
        logger.info("\n[OK] 簡化版回測完成")
        
    except Exception as e:
        logger.error(f"[ERR] 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

