#!/usr/bin/env python3
"""
測試 alpha_factors.py 模組的因子計算功能
"""

import pandas as pd
import numpy as np
from src.alpha_factors import AlphaFactorCalculator

def main():
    # 創建範例數據
    dates = pd.date_range('2020-01-01', periods=200, freq='D')
    np.random.seed(42)

    sample_data = pd.DataFrame({
        'open': 100 + np.random.randn(200).cumsum(),
        'high': 105 + np.random.randn(200).cumsum(),
        'low': 95 + np.random.randn(200).cumsum(),
        'close': 100 + np.random.randn(200).cumsum(),
        'volume': np.random.randint(1000, 10000, 200)
    }, index=dates)

    # 修正 OHLC 邏輯
    for i in range(len(sample_data)):
        sample_data.loc[sample_data.index[i], 'high'] = max(
            sample_data.loc[sample_data.index[i], ['open', 'close']].max(),
            sample_data.loc[sample_data.index[i], 'high']
        )
        sample_data.loc[sample_data.index[i], 'low'] = min(
            sample_data.loc[sample_data.index[i], ['open', 'close']].min(),
            sample_data.loc[sample_data.index[i], 'low']
        )

    # 計算因子
    print("開始計算 Alpha 因子...")
    calculator = AlphaFactorCalculator(sample_data)
    factors_df = calculator.calculate_all_factors()

    print(f'\n因子數量：{factors_df.shape[1]}')
    print(f'資料期間：{factors_df.index[0]} 到 {factors_df.index[-1]}')
    print()
    print('因子分類統計：')
    print('趨勢因子 (trend_*)：', len([col for col in factors_df.columns if col.startswith('trend_')]))
    print('動量因子 (momentum_*)：', len([col for col in factors_df.columns if col.startswith('momentum_')]))
    print('波動性因子 (volatility_*)：', len([col for col in factors_df.columns if col.startswith('volatility_')]))
    print('成交量因子 (volume_*)：', len([col for col in factors_df.columns if col.startswith('volume_')]))
    print('技術指標因子 (technical_*)：', len([col for col in factors_df.columns if col.startswith('technical_')]))
    print('相關性因子 (correlation_*)：', len([col for col in factors_df.columns if col.startswith('correlation_')]))

    # 顯示前幾個因子名稱
    print(f'\n前 10 個因子名稱：')
    for i, col in enumerate(factors_df.columns[:10]):
        print(f'  {i+1}. {col}')

    # 顯示最後一個因子的統計
    last_factor = factors_df.columns[-1]
    print(f'\n最後一個因子 ({last_factor}) 的統計：')
    print(f'  均值：{factors_df[last_factor].mean():.6f}')
    print(f'  標準差：{factors_df[last_factor].std():.6f}')
    print(f'  最小值：{factors_df[last_factor].min():.6f}')
    print(f'  最大值：{factors_df[last_factor].max():.6f}')
    print(f'  非空值數量：{factors_df[last_factor].count()}')

if __name__ == "__main__":
    main()
