import finlab
import pandas as pd
import numpy as np

print("=== FINLAB 策略增強探索 ===")

# 使用API金鑰登入
api_key = "wnFW0KT5etgpNr6IKZI05kNyRrMQDrIeoaplJBlRc+Twz+RWciylMCjm0jvtL0n5#free"
finlab.login(api_key)
from finlab import data

print("* 登入成功，正在探索高級功能...")

# 1. 獲取台灣加權指數數據
print("\n=== 1. 台灣加權指數分析 ===")
try:
    # 正確的方式獲取單個股票數據
    twii_data = data.get('price:收盤價')['TAIEX']
    print(f"台灣加權指數數據長度: {len(twii_data)}")
    print(f"數據日期範圍: {twii_data.index[0]} 到 {twii_data.index[-1]}")
    print(f"最新收盤價: {twii_data.iloc[-1]:.2f}")

    # 計算收益率
    returns = twii_data.pct_change()
    print(f"年化波動率: {returns.std() * np.sqrt(252):.3%}")
    print(f"年化報酬率: {((1 + returns.mean()) ** 252 - 1):.3%}")

except Exception as e:
    print(f"台灣加權指數分析失敗: {e}")

# 2. 技術指標計算
print("\n=== 2. 技術指標增強 ===")
try:
    close_prices = data.get('price:收盤價')['TAIEX']

    # 多重時間框架的移動平均
    sma_20 = close_prices.rolling(20).mean()
    sma_60 = close_prices.rolling(60).mean()
    sma_120 = close_prices.rolling(120).mean()

    print("移動平均線分析:")
    print(f"最新價格: {close_prices.iloc[-1]:.2f}")
    print(f"20日均線: {sma_20.iloc[-1]:.2f}")
    print(f"60日均線: {sma_60.iloc[-1]:.2f}")
    print(f"120日均線: {sma_120.iloc[-1]:.2f}")

    # 趨勢識別
    trend_20 = (close_prices.iloc[-1] - sma_20.iloc[-1]) / sma_20.iloc[-1]
    trend_60 = (close_prices.iloc[-1] - sma_60.iloc[-1]) / sma_60.iloc[-1]
    print(f"20日趨勢: {trend_20:.3%}")
    print(f"60日趨勢: {trend_60:.3%}")

except Exception as e:
    print(f"技術指標計算失敗: {e}")

# 3. 市場狀態識別
print("\n=== 3. 市場狀態識別 ===")
try:
    # 使用FINLAB的高級數據
    # 獲取大盤數據
    market_data = data.get('price:收盤價')['TAIEX']

    # 計算波動率
    volatility_20 = market_data.pct_change().rolling(20).std() * np.sqrt(252)
    volatility_60 = market_data.pct_change().rolling(60).std() * np.sqrt(252)

    print("市場波動率分析:")
    print(f"20日年化波動率: {volatility_20.iloc[-1]:.3%}")
    print(f"60日年化波動率: {volatility_60.iloc[-1]:.3%}")

    # 簡單的市場狀態判斷
    current_vol = volatility_20.iloc[-1]
    if current_vol > 0.25:
        market_state = "高波動"
    elif current_vol > 0.15:
        market_state = "中波動"
    else:
        market_state = "低波動"

    print(f"當前市場狀態: {market_state}")

except Exception as e:
    print(f"市場狀態識別失敗: {e}")

# 4. 基本面數據探索
print("\n=== 4. 基本面數據探索 ===")
try:
    # 嘗試獲取財務數據
    print("探索可用財務數據...")
    # 獲取台積電的基本面數據
    try:
        tsmc_revenue = data.get('fundamental:營收', '2330')
        print(f"台積電營收數據樣本數: {len(tsmc_revenue) if hasattr(tsmc_revenue, '__len__') else 'N/A'}")
        if hasattr(tsmc_revenue, 'tail'):
            print("台積電最近營收數據:")
            print(tsmc_revenue.tail(3))
    except:
        print("無法獲取營收數據")

    try:
        tsmc_eps = data.get('fundamental:EPS', '2330')
        print(f"台積電EPS數據樣本數: {len(tsmc_eps) if hasattr(tsmc_eps, '__len__') else 'N/A'}")
        if hasattr(tsmc_eps, 'tail'):
            print("台積電最近EPS數據:")
            print(tsmc_eps.tail(3))
    except:
        print("無法獲取EPS數據")

except Exception as e:
    print(f"基本面數據探索失敗: {e}")

# 5. 策略改進建議
print("\n=== 5. FINLAB對我們策略的幫助 ===")
print("FINLAB可以提供的策略改進:")
print("1. * 高品質台灣市場數據 - 無需擔心數據來源問題")
print("2. * 即時數據更新 - 能夠實時監控市場變化")
print("3. * 多股票數據 - 可以擴展到更多配對交易機會")
print("4. * 基本面數據整合 - 結合技術面和基本面分析")
print("5. * 數據驗證 - 確保我們使用的是準確的歷史數據")

print("\n具體應用到我們的本金保護區間策略:")
print("1. 使用FINLAB數據重新回測我們的策略")
print("2. 加入市場狀態識別來動態調整倉位")
print("3. 加入更多技術指標來改善信號品質")
print("4. 加入基本面因子來過濾交易機會")
print("5. 實時監控和自動化交易")

print("\n=== 建議下一步 ===")
print("我們應該:")
print("1. 使用FINLAB數據重新驗證我們的回測結果")
print("2. 開發市場狀態識別系統")
print("3. 加入更多技術指標和基本面因子")
print("4. 建立實時監控系統")
print("5. 考慮自動化交易實現")

