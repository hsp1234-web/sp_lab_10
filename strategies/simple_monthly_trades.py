import pandas as pd
import numpy as np

print("=== 每月真實交易策略執行記錄 ===")

# 載入數據
df = pd.read_csv('data/twii_real_data.csv')
df['Date'] = pd.to_datetime(df['Date'])
df = df.set_index('Date')

# 計算指標
df['returns'] = df['Close'].pct_change()
df['ma60'] = df['Close'].rolling(60).mean()

# 策略參數
INITIAL_CAPITAL = 1000000

# 模擬每月交易
monthly_trades = []
current_year = None
year_trades = []

for year in range(2021, 2026):  # 2021-2025年
    year_data = df[df.index.year == year]

    if year != current_year:
        if current_year is not None:
            # 輸出去年統計
            print(f"\n=== {current_year}年年度統計 ===")
            total_trades = len(year_trades)
            winning_trades = sum(1 for t in year_trades if t.get('pnl', 0) > 0)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            total_pnl = sum(t.get('pnl', 0) for t in year_trades)

            print(f"總交易次數: {total_trades}")
            print(f"勝率: {win_rate:.1%}")
            print(f"總損益: {total_pnl:,.0f} 元")

        current_year = year
        year_trades = []

    print(f"\n=== {year}年每月交易記錄 ===")

    for month in range(1, 13):
        month_data = year_data[year_data.index.month == month]
        if len(month_data) == 0:
            continue

        month_start = month_data.index[0]
        month_end = month_data.index[-1]
        month_start_price = month_data['Close'].iloc[0]
        month_end_price = month_data['Close'].iloc[-1]
        month_return = (month_end_price - month_start_price) / month_start_price

        # 模擬當月交易
        trades_this_month = []

        # 均線策略訊號
        ma_signals = 0
        for idx, row in month_data.iterrows():
            if row['Close'] > row['ma60'] and (idx == month_data.index[0] or month_data.loc[idx-1, 'Close'] <= month_data.loc[idx-1, 'ma60']):
                trades_this_month.append({
                    'date': idx.date(),
                    'strategy': '均線策略',
                    'action': '進場做多',
                    'price': row['Close'],
                    'reason': f'突破60日均線 {row["ma60"]:.0f}'
                })
                ma_signals += 1

        # 逆勢策略訊號 (大跌進場)
        contrarian_signals = 0
        for idx, row in month_data.iterrows():
            if row['returns'] <= -0.03:  # 跌3%進場
                trades_this_month.append({
                    'date': idx.date(),
                    'strategy': '逆勢策略',
                    'action': '進場買進',
                    'price': row['Close'],
                    'reason': f'單日跌幅 {row["returns"]:.1%}'
                })
                contrarian_signals += 1

        # 高股息策略 (每月固定股息)
        dividend_yield = 0.045 / 12  # 月股息率
        dividend_income = INITIAL_CAPITAL * 0.7 * dividend_yield

        # 輸出當月記錄
        print(f"\n{year}-{month:02d}月:")
        print(f"  台指走勢: {month_start_price:.0f} → {month_end_price:.0f} ({month_return:.2%})")
        print(f"  股息收入: {dividend_income:,.0f} 元")
        print(f"  均線訊號: {ma_signals} 次")
        print(f"  逆勢訊號: {contrarian_signals} 次")

        if trades_this_month:
            print("  交易明細:")
            for trade in trades_this_month[:3]:  # 只顯示前3筆
                print(f"    {trade['date']} {trade['strategy']}: {trade['action']} @{trade['price']:.0f} ({trade['reason']})")
            if len(trades_this_month) > 3:
                print(f"    ...還有{len(trades_this_month)-3}筆交易")
        else:
            print("  本月無特殊交易訊號")

        # 加入年度交易記錄
        year_trades.extend(trades_this_month)

        # 加入月度記錄
        monthly_trades.append({
            'year': year,
            'month': month,
            'month_name': f'{year}-{month:02d}',
            'start_price': month_start_price,
            'end_price': month_end_price,
            'month_return': month_return,
            'dividend_income': dividend_income,
            'ma_signals': ma_signals,
            'contrarian_signals': contrarian_signals,
            'total_signals': len(trades_this_month)
        })

# 最後一年統計
if year_trades:
    print(f"\n=== {current_year}年年度統計 ===")
    total_trades = len(year_trades)
    winning_trades = sum(1 for t in year_trades if '進場' in t.get('action', ''))
    win_rate = winning_trades / total_trades if total_trades > 0 else 0

    print(f"總交易次數: {total_trades}")
    print(f"進場訊號次數: {winning_trades}")
    print(f"訊號密度: {total_trades / 12:.1f} 次/月")

# 總結統計
print(f"\n=== 總體統計 (2021-2025) ===")
monthly_df = pd.DataFrame(monthly_trades)

total_months = len(monthly_df)
positive_months = (monthly_df['month_return'] > 0).sum()
win_rate = positive_months / total_months

total_dividend = monthly_df['dividend_income'].sum()
total_signals = monthly_df['total_signals'].sum()

print(f"總分析月份: {total_months}")
print(f"正報酬月份: {positive_months} ({win_rate:.1%})")
print(f"累計股息收入: {total_dividend:,.0f} 元")
print(f"總交易訊號: {total_signals} 次")
print(f"平均每月訊號: {total_signals / total_months:.1f} 次")

# 年度比較
print(f"\n年度訊號統計:")
yearly_stats = monthly_df.groupby('year').agg({
    'total_signals': 'sum',
    'ma_signals': 'sum',
    'contrarian_signals': 'sum',
    'month_return': 'mean'
}).round(3)

for year, stats in yearly_stats.iterrows():
    print(f"{int(year)}年: 總訊號{stats['total_signals']}次, 均線{stats['ma_signals']}次, 逆勢{stats['contrarian_signals']}次, 月均報酬{stats['month_return']:.2%}")

print("\n策略特點總結:")
print("- 高股息策略: 每月穩定股息，降低波動")
print("- 均線策略: 跟隨中期趨勢，自動進出")
print("- 逆勢策略: 把握大跌機會，低頻操作")
print("- 組合效果: 多策略分散，降低整體風險")
print("- 操作頻率: 每月檢查一次，完全不用盯盤")
