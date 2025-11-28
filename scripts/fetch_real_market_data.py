# -*- coding: utf-8 -*-
"""
獲取真實市場數據驗證本金保護區間策略
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def fetch_taiwan_index_data():
    """獲取台灣指數數據"""
    print("=== 獲取台灣指數數據 ===")

    try:
        # 使用台灣加權指數作為台指期替代
        twii = yf.Ticker('^TWII')
        data = twii.history(period='5y')  # 5年數據

        # 清理數據
        data = data.dropna()
        data = data.reset_index()

        print(f"數據期間: {data['Date'].min()} 到 {data['Date'].max()}")
        print(f"數據筆數: {len(data)}")
        print("最新數據樣本:")
        print(data.tail())

        # 保存數據
        data.to_csv('data/twii_real_data.csv', index=False)
        print("台灣指數數據已保存至 data/twii_real_data.csv")

        return data

    except Exception as e:
        print(f"獲取台灣指數數據失敗: {e}")
        return None

def fetch_financial_sector_data():
    """獲取金融板塊數據"""
    print("\n=== 獲取金融板塊數據 ===")

    # 台灣主要金融股代碼
    financial_stocks = {
        '2881.TW': '富邦金',
        '2882.TW': '國泰金',
        '2886.TW': '兆豐金',
        '2890.TW': '永豐金',
        '2884.TW': '玉山金',
        '2891.TW': '中信金',
        '2883.TW': '開發金',
        '2892.TW': '第一金'
    }

    financial_data = {}

    try:
        for symbol, name in financial_stocks.items():
            print(f"獲取 {name} ({symbol}) 數據...")
            stock = yf.Ticker(symbol)
            data = stock.history(period='5y')
            data = data.dropna().reset_index()

            if len(data) > 0:
                financial_data[symbol] = data
                print(f"  ✓ {name}: {len(data)} 筆數據")
            else:
                print(f"  ✗ {name}: 無數據")

        # 保存綜合金融板塊指數
        if financial_data:
            # 簡單平均計算金融板塊指數
            base_symbol = list(financial_data.keys())[0]
            financial_index = financial_data[base_symbol][['Date']].copy()

            prices = []
            for symbol, data in financial_data.items():
                # 將價格標準化到相同基準
                price_series = data.set_index('Date')['Close']
                normalized_price = price_series / price_series.iloc[0]
                prices.append(normalized_price)

            # 計算平均值
            price_df = pd.DataFrame(prices).T
            financial_index['financial_index'] = price_df.mean(axis=1)

            financial_index.to_csv('data/financial_sector_index.csv', index=False)
            print("金融板塊指數已保存至 data/financial_sector_index.csv")

        return financial_data

    except Exception as e:
        print(f"獲取金融板塊數據失敗: {e}")
        return {}

def fetch_macro_data():
    """獲取宏觀經濟數據"""
    print("\n=== 獲取宏觀經濟數據 ===")

    try:
        # 獲取VIX恐慌指數
        vix = yf.Ticker('^VIX')
        vix_data = vix.history(period='5y')
        vix_data = vix_data.dropna().reset_index()
        vix_data.to_csv('data/vix_data.csv', index=False)
        print(f"VIX數據: {len(vix_data)} 筆")

        # 獲取美元指數 (美債相關)
        dxy = yf.Ticker('DX-Y.NYB')
        dxy_data = dxy.history(period='5y')
        dxy_data = dxy_data.dropna().reset_index()
        dxy_data.to_csv('data/dxy_data.csv', index=False)
        print(f"美元指數數據: {len(dxy_data)} 筆")

        return {
            'vix': vix_data,
            'dxy': dxy_data
        }

    except Exception as e:
        print(f"獲取宏觀數據失敗: {e}")
        return {}

def validate_strategy_assumptions():
    """驗證策略假設"""
    print("\n=== 驗證策略假設 ===")

    try:
        # 讀取台灣指數數據
        twii_data = pd.read_csv('data/twii_real_data.csv')
        twii_data['Date'] = pd.to_datetime(twii_data['Date'])
        twii_data = twii_data.sort_values('Date')

        print(f"台灣指數數據: {len(twii_data)} 筆記錄")
        print(f"數據期間: {twii_data['Date'].min()} 到 {twii_data['Date'].max()}")

        # 計算月度報酬
        twii_data['month'] = twii_data['Date'].dt.to_period('M')
        monthly_returns = []

        for month, group in twii_data.groupby('month'):
            if len(group) >= 5:  # 至少5個交易日
                start_price = group['Close'].iloc[0]
                end_price = group['Close'].iloc[-1]
                monthly_return = (end_price - start_price) / start_price

                monthly_returns.append({
                    'month': str(month),
                    'monthly_return': monthly_return,
                    'max_drawdown': calculate_monthly_mdd(group['Close'].values)
                })

        monthly_df = pd.DataFrame(monthly_returns)
        print(f"月度數據: {len(monthly_df)} 個月")

        # 驗證買進持有策略表現
        bh_stats = {
            'total_months': len(monthly_df),
            'positive_months': (monthly_df['monthly_return'] > 0).sum(),
            'positive_ratio': (monthly_df['monthly_return'] > 0).mean(),
            'avg_monthly_return': monthly_df['monthly_return'].mean(),
            'max_loss': monthly_df['monthly_return'].min(),
            'max_mdd': monthly_df['max_drawdown'].max()
        }

        print("買進持有策略表現:")
        print(".2%")
        print(".2%")
        print(".2%")
        print(".2%")
        print(".2%")

        # 保存月度數據
        monthly_df.to_csv('data/twii_monthly_returns.csv', index=False)

        return bh_stats

    except Exception as e:
        print(f"驗證策略假設失敗: {e}")
        return None

def calculate_monthly_mdd(price_array):
    """計算月度最大回撤"""
    if len(price_array) < 2:
        return 0.0

    peak = price_array[0]
    max_drawdown = 0.0

    for price in price_array:
        if price > peak:
            peak = price
        drawdown = (peak - price) / peak
        max_drawdown = max(max_drawdown, drawdown)

    return max_drawdown

def analyze_financial_leading_signals():
    """分析金融板塊領先信號"""
    print("\n=== 分析金融板塊領先信號 ===")

    try:
        # 讀取數據
        twii_data = pd.read_csv('data/twii_real_data.csv')
        twii_data['Date'] = pd.to_datetime(twii_data['Date'])

        financial_data = pd.read_csv('data/financial_sector_index.csv')
        financial_data['Date'] = pd.to_datetime(financial_data['Date'])

        # 合併數據
        merged_data = pd.merge(twii_data[['Date', 'Close']],
                             financial_data[['Date', 'financial_index']],
                             on='Date', how='inner')

        print(f"合併數據: {len(merged_data)} 筆記錄")

        # 計算相關性和領先性
        twii_returns = merged_data['Close'].pct_change()
        financial_returns = merged_data['financial_index'].pct_change()

        # 計算相關係數
        correlation = twii_returns.corr(financial_returns)
        print(f"台指與金融板塊相關係數: {correlation:.3f}")
        # 計算領先相關性
        lead_correlations = {}
        for lag in range(-10, 11):
            if lag < 0:
                corr = twii_returns.corr(financial_returns.shift(-lag))
            else:
                corr = twii_returns.corr(financial_returns.shift(lag))
            lead_correlations[lag] = corr

        best_lead = max(lead_correlations.items(), key=lambda x: abs(x[1]))
        print(f"最佳領先相關: 金融股領先 {best_lead[0]} 天, 相關係數: {best_lead[1]:.3f}")

        return {
            'correlation': correlation,
            'lead_analysis': lead_correlations,
            'best_lead': best_lead
        }

    except Exception as e:
        print(f"分析金融領先信號失敗: {e}")
        return None

def main():
    """主函數"""
    print("=== 本金保護區間策略真實數據驗證 ===")
    print("=" * 60)

    # 切換到專案根目錄
    os.chdir(Path(__file__).parent.parent)

    # 創建data目錄（如果不存在）
    os.makedirs('data', exist_ok=True)

    results = {}

    # 1. 獲取台灣指數數據
    twii_data = fetch_taiwan_index_data()
    results['twii_data'] = twii_data is not None

    # 2. 獲取金融板塊數據
    financial_data = fetch_financial_sector_data()
    results['financial_data'] = len(financial_data) > 0

    # 3. 獲取宏觀數據
    macro_data = fetch_macro_data()
    results['macro_data'] = len(macro_data) > 0

    # 4. 驗證策略假設
    bh_stats = validate_strategy_assumptions()
    results['bh_stats'] = bh_stats is not None

    # 5. 分析金融領先信號
    financial_analysis = analyze_financial_leading_signals()
    results['financial_analysis'] = financial_analysis is not None

    print("\n" + "=" * 60)
    print("數據獲取總結:")
    for name, success in results.items():
        status = "[成功]" if success else "[失敗]"
        print(f"  {name}: {status}")

    success_count = sum(results.values())
    print(f"\n總計: {success_count}/{len(results)} 項任務成功")

    if bh_stats:
        print("\n關鍵發現:")
        print(f"  • 買進持有策略正報酬比例: {bh_stats['positive_ratio']:.1%}")
        print(f"  • 平均月報酬: {bh_stats['avg_monthly_return']:.2%}")
        print(f"  • 最大月虧損: {bh_stats['max_loss']:.2%}")
        print(f"  • 月度最大回撤: {bh_stats['max_mdd']:.2%}")

if __name__ == "__main__":
    main()
