#!/usr/bin/env python3
"""
測試因子評估工具的功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import numpy as np
from alpha_factors import AlphaFactorCalculator, FactorEvaluator, create_alpha158_factors

def main():
    print("=== 測試因子評估工具 ===\n")

    # 創建示例數據
    dates = pd.date_range('2020-01-01', periods=300, freq='D')
    np.random.seed(42)

    sample_data = pd.DataFrame({
        'open': 100 + np.random.randn(300).cumsum(),
        'high': 105 + np.random.randn(300).cumsum(),
        'low': 95 + np.random.randn(300).cumsum(),
        'close': 100 + np.random.randn(300).cumsum(),
        'volume': np.random.randint(1000, 10000, 300)
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

    print("1. 創建因子...")
    # 創建因子
    calculator = AlphaFactorCalculator(sample_data)
    factors_df = calculator.calculate_all_factors()

    print(f"   因子數量: {factors_df.shape[1]}")
    print(f"   數據期間: {factors_df.index[0]} 到 {factors_df.index[-1]}")

    # 計算報酬
    returns = sample_data['close'].pct_change()

    print("\n2. 創建因子評估器...")
    # 創建因子評估器
    evaluator = FactorEvaluator(factors_df, returns)

    print("3. 測試 IC 計算...")
    # 測試 IC 計算
    if factors_df.shape[1] > 0:
        first_factor = factors_df.columns[0]
        ic_stats = evaluator.calculate_ic(first_factor, forward_period=1)
        print(f"   因子 '{first_factor}' 的 IC 統計:")
        for key, value in ic_stats.items():
            if isinstance(value, (int, float)) and not np.isnan(value):
                print(".4f"            else:
                print(f"      {key}: {value}")

        print("\n4. 測試 IC 矩陣...")
        # 測試 IC 矩陣
        ic_matrix = evaluator.calculate_ic_matrix(forward_period=1)
        print("   前 5 個因子的 IC 值:")
        print(ic_matrix.head()[['ic', 'ic_abs', 't_stat']].round(4))

        print("\n5. 測試分組分析...")
        # 測試分組分析
        quantile_df = evaluator.quantile_analysis(first_factor, n_quantiles=5)
        print(f"   因子 '{first_factor}' 的分組報酬:")
        print(quantile_df[['quantile', 'mean_return', 'count']].round(6))

        if 'q5_minus_q1' in quantile_df.columns:
            q5_q1_diff = quantile_df['q5_minus_q1'].iloc[0]
            print(".6f"
        print("\n6. 測試因子總結報告...")
        # 測試因子總結
        summary_df = evaluator.get_factor_summary(forward_period=1)
        print("   因子總結 (前 5 個):")
        print(summary_df.head()[['factor', 'ic', 'ic_abs', 'q5_minus_q1']].round(4))

    print("\n7. 測試修復後的 Alpha158 因子選擇...")
    # 測試修復後的 Alpha158
    alpha158 = create_alpha158_factors(sample_data)
    print(f"   Alpha158 因子形狀: {alpha158.shape}")
    print(f"   選取的因子數量: {alpha158.shape[1]}")
    if alpha158.shape[1] > 0:
        print("   前 5 個 Alpha158 因子:")
        for i, col in enumerate(alpha158.columns[:5]):
            print(f"     {i+1}. {col}")

    print("\n✅ 所有測試完成！")

if __name__ == "__main__":
    main()
