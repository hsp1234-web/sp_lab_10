import finlab
import pandas as pd
import numpy as np

print("=== FINLAB配對交易調試 ===")

# 登入FINLAB
api_key = "wnFW0KT5etgpNr6IKZI05kNyRrMQDrIeoaplJBlRc+Twz+RWciylMCjm0jvtL0n5#free"
finlab.login(api_key)
from finlab import data

print("* 登入成功")

# 獲取數據
price_data = data.get('price:收盤價')
print(f"數據形狀: {price_data.shape}")

# 選擇一部分股票進行測試（避免計算過於耗時）
test_stocks = price_data.columns[:100].tolist()  # 前100支股票
test_data = price_data[test_stocks]

print(f"測試股票數量: {len(test_stocks)}")
print(f"測試數據形狀: {test_data.shape}")

# 計算相關係數
print("\n=== 計算相關係數 ===")
returns = test_data.pct_change().dropna()
print(f"報酬數據形狀: {returns.shape}")

correlation_matrix = returns.corr()
print(f"相關係數矩陣形狀: {correlation_matrix.shape}")

# 查看相關係數分佈
correlations = []
for i in range(len(test_stocks)):
    for j in range(i+1, len(test_stocks)):
        corr = correlation_matrix.iloc[i, j]
        if not np.isnan(corr):
            correlations.append(corr)

print(f"相關係數樣本數: {len(correlations)}")
print(f"平均相關係數: {np.mean(correlations):.3f}")
print(f"相關係數標準差: {np.std(correlations):.3f}")
print(f"最大相關係數: {np.max(correlations):.3f}")
print(f"最小相關係數: {np.min(correlations):.3f}")

# 統計高相關配對
high_corr_pairs = [(i, j) for i in range(len(test_stocks)) for j in range(i+1, len(test_stocks))
                   if correlation_matrix.iloc[i, j] > 0.7]
print(f"相關係數>0.7的配對數: {len(high_corr_pairs)}")

# 測試單一配對的Z分數計算
print("\n=== 測試Z分數計算 ===")
if len(high_corr_pairs) > 0:
    i, j = high_corr_pairs[0]  # 第一個高相關配對
    stock1, stock2 = test_stocks[i], test_stocks[j]
    corr = correlation_matrix.iloc[i, j]

    print(f"測試配對: {stock1} vs {stock2}, 相關係數: {corr:.3f}")

    # 計算價差
    spread = test_data[stock1] - test_data[stock2]
    print(f"價差長度: {len(spread)}")
    print(f"價差均值: {spread.mean():.2f}")
    print(f"價差標準差: {spread.std():.2f}")

    # 計算Z分數
    spread_mean = spread.rolling(60).mean()
    spread_std = spread.rolling(60).std()
    z_score = (spread - spread_mean) / spread_std

    print(f"Z分數長度: {len(z_score.dropna())}")
    print(f"當前Z分數: {z_score.iloc[-1]:.3f}")
    print(f"Z分數絕對值: {abs(z_score.iloc[-1]):.3f}")

    # 檢查進場條件
    z_entry_threshold = 2.0
    if abs(z_score.iloc[-1]) > z_entry_threshold:
        print(f"✓ 滿足進場條件 (Z > {z_entry_threshold})")
    else:
        print(f"✗ 不滿足進場條件 (Z <= {z_entry_threshold})")
else:
    print("沒有找到相關係數>0.7的配對")

# 分析為什麼沒有配對
print("\n=== 問題診斷 ===")
print("可能原因:")
print("1. 相關係數門檻過高 (0.7)")
print("2. Z分數進場門檻過高 (2.0)")
print("3. 數據時間窗口不足")
print("4. 股票波動性差異大")

# 降低門檻重新測試
print("\n=== 降低門檻測試 ===")
min_corr = 0.5  # 降低相關係數門檻
z_entry = 1.5   # 降低Z分數門檻

relaxed_pairs = []
for i in range(len(test_stocks)):
    for j in range(i+1, len(test_stocks)):
        stock1, stock2 = test_stocks[i], test_stocks[j]
        corr = correlation_matrix.iloc[i, j]

        if corr > min_corr:
            spread = test_data[stock1] - test_data[stock2]
            spread_mean = spread.rolling(60).mean()
            spread_std = spread.rolling(60).std()
            z_score = (spread - spread_mean) / spread_std

            current_z = z_score.iloc[-1]
            if abs(current_z) > z_entry:
                relaxed_pairs.append({
                    'stock1': stock1,
                    'stock2': stock2,
                    'correlation': corr,
                    'z_score': current_z
                })

print(f"放寬條件後找到 {len(relaxed_pairs)} 個配對")

if len(relaxed_pairs) > 0:
    print("前3個配對:")
    for pair in relaxed_pairs[:3]:
        print(f"  {pair['stock1']} vs {pair['stock2']}: corr={pair['correlation']:.3f}, z={pair['z_score']:.2f}")

print("\n=== 結論 ===")
print("FINLAB數據可用，但配對交易參數需要調整:")
print("- 台灣股市相關性可能較低，建議降低相關係數門檻")
print("- Z分數進場門檻可以適度降低")
print("- 可以考慮加入更多技術指標過濾")
print("- 建議使用更長的歷史數據窗口")

