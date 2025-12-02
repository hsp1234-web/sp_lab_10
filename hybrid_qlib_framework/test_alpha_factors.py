#!/usr/bin/env python3
"""
測試 Alpha 因子計算模組
"""

import pandas as pd
import numpy as np
from src.alpha_factors import AlphaFactorCalculator, create_alpha158_factors

def create_test_data():
    """創建測試數據"""
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    np.random.seed(42)

    # 創建 OHLCV 數據
    close_prices = 100 + np.random.randn(100).cumsum()

    data = pd.DataFrame({
        'open': close_prices + np.random.randn(100) * 0.5,
        'high': close_prices + abs(np.random.randn(100)) * 1.0,
        'low': close_prices - abs(np.random.randn(100)) * 1.0,
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)

    # 確保價格邏輯正確
    for i in range(len(data)):
        row = data.iloc[i]
        data.loc[data.index[i], 'high'] = max(row['high'], row['open'], row['close'])
        data.loc[data.index[i], 'low'] = min(row['low'], row['open'], row['close'])

    return data

def test_basic_functionality():
    """測試基本功能"""
    print("=== 測試基本功能 ===")

    # 創建測試數據
    data = create_test_data()
    print(f"測試數據形狀: {data.shape}")

    # 創建計算器
    calculator = AlphaFactorCalculator(data, window_sizes=[5, 10, 20])
    print("AlphaFactorCalculator 創建成功")

    # 測試各種類型因子
    factor_types = [
        ('趨勢因子', calculator.calculate_trend_factors),
        ('動量因子', calculator.calculate_momentum_factors),
        ('波動性因子', calculator.calculate_volatility_factors),
        ('成交量因子', calculator.calculate_volume_factors),
        ('技術指標因子', calculator.calculate_technical_factors)
    ]

    total_factors = 0
    for factor_name, calculate_func in factor_types:
        try:
            factors = calculate_func()
            print(f"{factor_name}: {len(factors)} 個因子")
            total_factors += len(factors)
        except Exception as e:
            print(f"{factor_name} 計算失敗: {e}")

    print(f"總計因子數: {total_factors}")

def test_alpha158():
    """測試 Alpha158 因子集"""
    print("\n=== 測試 Alpha158 因子集 ===")

    data = create_test_data()
    print(f"測試數據形狀: {data.shape}")

    try:
        alpha158_factors = create_alpha158_factors(data)
        print(f"Alpha158 因子形狀: {alpha158_factors.shape}")
        print("Alpha158 因子列表:")
        for i, col in enumerate(alpha158_factors.columns, 1):
            print("2d")

        # 顯示因子統計
        print(f"\n因子統計摘要:")
        print(alpha158_factors.describe().round(4))

    except Exception as e:
        print(f"Alpha158 計算失敗: {e}")
        import traceback
        traceback.print_exc()

def test_with_taifex_data():
    """測試使用台期貨數據"""
    print("\n=== 測試台期貨數據整合 ===")

    try:
        # 載入台期貨數據 (如果存在)
        taifex_path = "../data/taifex.db"
        import os
        if os.path.exists(taifex_path):
            import sqlite3
            conn = sqlite3.connect(taifex_path)

            # 獲取最近一個月的數據作為測試
            query = """
            SELECT date, open, high, low, close, volume
            FROM futures_data
            WHERE symbol = 'TX00'
            ORDER BY date DESC
            LIMIT 100
            """

            df = pd.read_sql_query(query, conn)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            print(f"台期貨數據形狀: {df.shape}")

            if len(df) > 20:  # 確保有足夠數據
                alpha_factors = create_alpha158_factors(df)
                print(f"台期貨 Alpha158 因子形狀: {alpha_factors.shape}")
            else:
                print("台期貨數據不足，跳過測試")

            conn.close()
        else:
            print(f"台期貨數據庫不存在: {taifex_path}")

    except Exception as e:
        print(f"台期貨數據測試失敗: {e}")

if __name__ == "__main__":
    print("開始測試 Alpha 因子計算模組")
    print("=" * 50)

    test_basic_functionality()
    test_alpha158()
    test_with_taifex_data()

    print("\n" + "=" * 50)
    print("測試完成")
