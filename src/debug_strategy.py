#!/usr/bin/env python3
"""
除錯整合策略
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrated_strategy import IntegratedStrategy, create_default_config
import pandas as pd

def main():
    print("=== 整合策略除錯 ===")

    # 創建策略
    config = create_default_config()
    strategy = IntegratedStrategy(config)

    # 載入資料
    print("載入資料...")
    df = strategy.load_market_data('2022-01-01', '2022-12-31')
    df = strategy.calculate_technical_indicators(df)

    print("\n資料摘要:")
    print(f"資料長度: {len(df)}")
    print(f"日期範圍: {df.index.min()} 到 {df.index.max()}")

    print("\nPCR比率統計:")
    print(f"最小值: {df['pcr_ratio'].min():.2f}")
    print(f"最大值: {df['pcr_ratio'].max():.2f}")
    print(f"平均值: {df['pcr_ratio'].mean():.2f}")
    print(f"中位數: {df['pcr_ratio'].median():.2f}")

    print("\n趨勢方向分佈:")
    trend_counts = df['Trend_Direction'].value_counts()
    for direction, count in trend_counts.items():
        direction_name = {1: '多頭', -1: '空頭', 0: '無趨勢'}[direction]
        print(f"{direction_name}: {count} ({count/len(df)*100:.1f}%)")

    print("\n波動率統計:")
    print(f"最小值: {df['Volatility'].min():.2f}%")
    print(f"最大值: {df['Volatility'].max():.2f}%")
    print(f"平均值: {df['Volatility'].mean():.2f}%")

    # 檢查進場條件
    print("\n進場條件檢查:")    # 多頭進場條件
    bullish_condition = (
        (df['Trend_Direction'] == 1) &
        (df['pcr_ratio'] < config.pcr_threshold_bull) &
        (df['Close'] > df['MA20'])
    )
    bullish_signals = bullish_condition.sum()
    print(f"多頭進場條件滿足: {bullish_signals} 次")

    # 空頭進場條件
    bearish_condition = (
        (df['Trend_Direction'] == -1) &
        (df['pcr_ratio'] > config.pcr_threshold_bear) &
        (df['Close'] < df['MA20'])
    )
    bearish_signals = bearish_condition.sum()
    print(f"空頭進場條件滿足: {bearish_signals} 次")

    # 生成信號測試
    print("\n生成信號測試...")
    signals = strategy.generate_signals(df)
    signal_counts = pd.Series(signals).value_counts()
    print("信號統計:")
    for signal, count in signal_counts.items():
        signal_name = {1: '多頭進場', -1: '空頭進場/出場', 0: '無信號'}[signal]
        print(f"{signal_name}: {count}")

    print("\n策略統計:")
    stats = strategy.get_strategy_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
