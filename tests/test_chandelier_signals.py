#!/usr/bin/env python3
"""
簡化版 Chandelier 策略測試 - 只測試信號生成
避開 Rich 編碼問題，直接測試風控邏輯
"""

import sys
import os
import pandas as pd
import numpy as np
import duckdb
from pathlib import Path
import logging

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'lo2cin4bt-main'))

def setup_logging():
    """設定簡單日誌"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('chandelier_test.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def load_test_data(logger):
    """載入測試數據"""
    logger.info("載入台指期測試數據...")

    con = duckdb.connect('data/taifex.db')

    # 載入 2022-2023 年的數據作為測試
    query = """
    SELECT
        strptime(Date, '%Y/%m/%d') as Time,
        Open, High, Low, Close, Volume
    FROM futures_data
    WHERE Symbol = 'TX'
    AND strptime(Date, '%Y/%m/%d') >= strptime('2022-01-01', '%Y-%m-%d')
    AND strptime(Date, '%Y/%m/%d') <= strptime('2023-12-31', '%Y-%m-%d')
    AND Open IS NOT NULL AND High IS NOT NULL AND Low IS NOT NULL AND Close IS NOT NULL
    ORDER BY strptime(Date, '%Y/%m/%d')
    """

    data = con.execute(query).fetchdf()
    con.close()

    logger.info(f"測試數據載入完成: {data.shape[0]} 行")
    logger.info(f"日期範圍: {data['Time'].min()} 到 {data['Time'].max()}")

    return data

def test_chandelier_signals(data, logger):
    """測試 Chandelier 策略信號生成"""
    from backtester.Chandelier_Indicator_backtester import ChandelierIndicator

    # 測試參數組合
    test_params = [
        {'length': 10, 'multiplier': 1.5, 'risk_per_trade': 0.01, 'stop_loss_atr_multiplier': 2.0, 'max_monthly_drawdown': 0.05},
        {'length': 14, 'multiplier': 2.0, 'risk_per_trade': 0.01, 'stop_loss_atr_multiplier': 2.0, 'max_monthly_drawdown': 0.05},
    ]

    results = []

    for i, params in enumerate(test_params):
        logger.info(f"測試參數組合 {i+1}: {params}")

        try:
            # 創建指標實例
            indicator = ChandelierIndicator(data, params, logger)

            # 生成信號
            signals = indicator.generate_signals()

            # 統計分析
            total_signals = np.sum(signals != 0)
            long_signals = np.sum(signals == 1)
            short_signals = np.sum(signals == -1)

            logger.info(f"總信號數: {total_signals}")
            logger.info(f"多頭進場: {long_signals}")
            logger.info(f"空頭進場: {short_signals}")

            # 簡單的模擬回測（不考慮交易成本）
            equity = 1000000.0
            position = 0
            entry_price = 0
            trades = []

            for j, signal in enumerate(signals):
                if signal == 1 and position == 0:  # 進場多頭
                    position = 1
                    entry_price = data.iloc[j]['Close']
                    trades.append({'type': 'entry', 'price': entry_price, 'date': data.iloc[j]['Time']})
                elif signal == -1 and position == 1:  # 出場多頭
                    exit_price = data.iloc[j]['Close']
                    pnl = exit_price - entry_price
                    equity += pnl
                    position = 0
                    trades.append({'type': 'exit', 'price': exit_price, 'pnl': pnl, 'date': data.iloc[j]['Time']})

            total_trades = len([t for t in trades if t['type'] == 'exit'])
            winning_trades = len([t for t in trades if t['type'] == 'exit' and t['pnl'] > 0])
            losing_trades = len([t for t in trades if t['type'] == 'exit' and t['pnl'] <= 0])

            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            total_pnl = sum([t['pnl'] for t in trades if t['type'] == 'exit'])
            final_equity = equity

            # 計算最大回撤
            peak = 1000000.0
            max_drawdown = 0
            current_equity = 1000000.0

            for trade in trades:
                if trade['type'] == 'exit':
                    current_equity += trade['pnl']
                    peak = max(peak, current_equity)
                    drawdown = (peak - current_equity) / peak
                    max_drawdown = max(max_drawdown, drawdown)

            result = {
                'params': params,
                'total_signals': total_signals,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'final_equity': final_equity,
                'max_drawdown': max_drawdown,
                'return_pct': (final_equity - 1000000.0) / 1000000.0
            }

            results.append(result)

            logger.info(f"勝率: {win_rate:.1%}")
            logger.info(f"總盈虧: ${total_pnl:,.0f}")
            logger.info(f"最終權益: ${final_equity:,.0f}")
            logger.info(f"最大回撤: {max_drawdown:.1%}")
            logger.info(f"總報酬率: {result['return_pct']:.1%}")
            logger.info("-" * 50)

        except Exception as e:
            logger.error(f"測試參數組合 {i+1} 失敗: {e}")
            continue

    return results

def save_results(results, logger):
    """保存測試結果"""
    output_dir = Path('output/experiment_results')
    output_dir.mkdir(parents=True, exist_ok=True)

    results_df = pd.DataFrame(results)
    output_file = output_dir / 'chandelier_risk_controlled_test_results.csv'
    results_df.to_csv(output_file, index=False, encoding='utf-8')

    logger.info(f"測試結果已保存到: {output_file}")

    # 打印總結報告
    print("\n" + "="*80)
    print("CHANDLIER 強化版策略測試報告")
    print("="*80)
    print(f"測試期間: 2022-01-01 到 2023-12-31")
    print(f"測試參數組合數: {len(results)}")
    print()

    for i, result in enumerate(results):
        print(f"參數組合 {i+1}:")
        print(f"  參數: Length={result['params']['length']}, Multiplier={result['params']['multiplier']}")
        print(f"  總交易次數: {result['total_trades']}")
        print(f"  勝率: {result['win_rate']:.1%}")
        print(f"  總報酬率: {result['return_pct']:.1%}")
        print(f"  最大回撤: {result['max_drawdown']:.1%}")
        print()

    # 最佳參數組合
    if results:
        best_result = max(results, key=lambda x: x['return_pct'])
        print("最佳參數組合:")
        print(f"  Length: {best_result['params']['length']}")
        print(f"  Multiplier: {best_result['params']['multiplier']}")
        print(f"  報酬率: {best_result['return_pct']:.1%}")
        print(f"  最大回撤: {best_result['max_drawdown']:.1%}")
        print(f"  勝率: {best_result['win_rate']:.1%}")

        # 風控檢查
        monthly_drawdown_limit = 0.05  # 5%
        if best_result['max_drawdown'] <= monthly_drawdown_limit:
            print("✓ 符合風控要求：最大回撤 ≤ 5%")
        else:
            print(f"✗ 超過風控限制：最大回撤 {best_result['max_drawdown']:.1%} > 5%")

    print("="*80)

def main():
    """主函數"""
    logger = setup_logging()
    logger.info("開始 Chandelier 強化版策略測試")

    try:
        # 載入測試數據
        data = load_test_data(logger)

        # 測試信號生成
        results = test_chandelier_signals(data, logger)

        # 保存結果
        save_results(results, logger)

        logger.info("Chandelier 策略測試完成")

    except Exception as e:
        logger.error(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
