import finlab
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

print("=== FINLAB 功能探索 ===")

# 檢查版本和可用功能
print(f"FinLab版本: {finlab.__version__}")

# 查看可用的模塊
print("\n可用的finlab模塊:")
finlab_modules = [attr for attr in dir(finlab) if not attr.startswith('_')]
for module in finlab_modules:
    print(f"  - {module}")

print("\n=== 數據獲取測試 ===")

# 測試數據獲取功能
try:
    # 獲取台積電數據
    tsmc = finlab.data.get('price:收盤價', '2330')
    print(f"台積電數據樣本數: {len(tsmc) if hasattr(tsmc, '__len__') else 'N/A'}")
    if hasattr(tsmc, 'head'):
        print("台積電最近5日數據:")
        print(tsmc.tail(5))
except Exception as e:
    print(f"數據獲取失敗: {e}")

# 測試技術指標
print("\n=== 技術指標測試 ===")
try:
    # 獲取台灣加權指數
    twii = finlab.data.get('price:收盤價', 'TAIEX')
    print(f"台灣加權指數數據樣本數: {len(twii) if hasattr(twii, '__len__') else 'N/A'}")

    if hasattr(twii, 'head') and len(twii) > 0:
        print("台灣加權指數最近5日數據:")
        print(twii.tail(5))

        # 計算簡單的技術指標
        sma_20 = twii.rolling(20).mean()
        sma_60 = twii.rolling(60).mean()
        print(f"\nSMA20最新值: {sma_20.iloc[-1] if len(sma_20) > 0 else 'N/A'}")
        print(f"SMA60最新值: {sma_60.iloc[-1] if len(sma_60) > 0 else 'N/A'}")

except Exception as e:
    print(f"技術指標測試失敗: {e}")

# 測試其他功能
print("\n=== 其他功能探索 ===")
try:
    # 查看有哪些數據類型可用
    print("嘗試獲取可用的數據列表...")
    # 這通常需要API金鑰
    available_data = finlab.data.get_available_data()
    print(f"可用數據類型數量: {len(available_data) if available_data else 0}")
    if available_data:
        print("前10個數據類型:")
        for i, data_type in enumerate(available_data[:10]):
            print(f"  {i+1}. {data_type}")

except Exception as e:
    print(f"其他功能測試失敗: {e}")

print("\n=== 總結 ===")
print("FINLAB提供了台灣股市的數據獲取和分析功能")
print("主要優勢:")
print("- 台灣市場專用數據")
print("- 內建技術指標")
print("- 數據可視化支持")
print("- 回測框架")

