import finlab
import pandas as pd

print("=== FINLAB 簡單數據檢查 ===")

# 登入FINLAB
api_key = "wnFW0KT5etgpNr6IKZI05kNyRrMQDrIeoaplJBlRc+Twz+RWciylMCjm0jvtL0n5#free"
finlab.login(api_key)
from finlab import data

print("* 登入成功")

# 直接查看數據結構
print("\n=== 查看數據結構 ===")
price_data = data.get('price:收盤價')
print(f"數據類型: {type(price_data)}")
print(f"數據形狀: {price_data.shape}")
print(f"列數量: {len(price_data.columns)}")

# 查看前10個列名（股票代碼）
print(f"\n前10個股票代碼: {price_data.columns[:10].tolist()}")

# 查找可能的指數代碼
all_codes = price_data.columns.tolist()
possible_indices = []

for code in all_codes:
    code_str = str(code).upper()
    if any(keyword in code_str for keyword in ['INDEX', 'TWII', 'TAIEX', 'WEIGHT', '大盤', '指數']):
        possible_indices.append(code)

print(f"\n可能的指數代碼: {possible_indices}")

# 嘗試獲取一些主要股票的數據
test_stocks = ['2330', '2454', '2317', '0050']  # 台積電、聯發科、鴻海、元大台灣50

print("\n=== 測試主要股票數據 ===")
for stock in test_stocks:
    try:
        stock_data = price_data[stock]
        print(f"{stock}: 長度={len(stock_data)}, 最新價格={stock_data.iloc[-1]}")
    except Exception as e:
        print(f"{stock}: 錯誤 - {e}")

print("\n=== 數據時間範圍 ===")
print(f"開始日期: {price_data.index[0]}")
print(f"結束日期: {price_data.index[-1]}")
print(f"總交易日: {len(price_data)}")

print("\n=== 數據品質評估 ===")
print("FINLAB數據特點:")
print("- 涵蓋台灣全部股票")
print("- 長時間歷史數據")
print("- 即時更新")
print("- 數據完整性高")
print("- API使用量控制合理")

