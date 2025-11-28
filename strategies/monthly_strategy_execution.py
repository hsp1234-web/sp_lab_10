import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 設置中文字體
try:
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']

print("=== 每月真實交易策略執行記錄 ===")

# 1. 載入真實數據
print("載入台灣指數真實數據...")
df = pd.read_csv('data/twii_real_data.csv')
df['Date'] = pd.to_datetime(df['Date'])
df = df.set_index('Date')
df = df.sort_index()

print(f"數據期間: {df.index.min()} 到 {df.index.max()}")
print(f"總交易日: {len(df)}")

# 計算技術指標
df['returns'] = df['Close'].pct_change()
df['ma20'] = df['Close'].rolling(20).mean()
df['ma60'] = df['Close'].rolling(60).mean()
df['volatility'] = df['returns'].rolling(20).std() * np.sqrt(252)

# 2. 策略參數設定
INITIAL_CAPITAL = 1000000  # 100萬總資金
DIVIDEND_ALLOCATION = 0.7  # 70% 高股息策略
MA_ALLOCATION = 0.2        # 20% 均線策略
CONTRARIAN_ALLOCATION = 0.1 # 10% 逆勢策略

DIVIDEND_TARGET_YIELD = 0.04  # 4%殖利率目標
MA_STOP_LOSS = 0.05           # 均線策略停損5%
CONTRARIAN_ENTRY = -0.03      # 逆勢進場跌幅3%

print("\n策略配置:")
print(f"總資金: {INITIAL_CAPITAL:,} 元")
print(f"高股息策略: {DIVIDEND_ALLOCATION:.0%} ({INITIAL_CAPITAL * DIVIDEND_ALLOCATION:,.0f} 元)")
print(f"均線策略: {MA_ALLOCATION:.0%} ({INITIAL_CAPITAL * MA_ALLOCATION:,.0f} 元)")
print(f"逆勢策略: {CONTRARIAN_ALLOCATION:.0%} ({INITIAL_CAPITAL * CONTRARIAN_ALLOCATION:,.0f} 元)")

# 3. 模擬策略執行
print("\n開始模擬每月交易...")

# 初始化部位和資金
dividend_position = DIVIDEND_ALLOCATION  # 高股息部位比例
ma_position = 0  # 均線策略部位 (0=空手, 1=持有多頭)
contrarian_position = 0  # 逆勢策略部位
ma_entry_price = 0  # 均線策略進場價格
contrarian_entry_price = 0  # 逆勢策略進場價格

capital = INITIAL_CAPITAL
monthly_records = []
yearly_records = []

current_year = df.index[0].year
year_start_capital = capital
year_trades = []

# 按月處理
for month_start in pd.date_range(start=df.index[0], end=df.index[-1], freq='MS'):
    month_end = (month_start + pd.offsets.MonthEnd(1))
    if month_end > df.index[-1]:
        month_end = df.index[-1]

    # 獲取當月數據
    month_data = df.loc[month_start:month_end]
    if len(month_data) == 0:
        continue

    month_returns = []
    month_trades = []
    month_dividend_yield = 0.045  # 假設平均4.5%殖利率 (真實數據中沒有殖利率，用假設值)

    # 處理每一天
    for idx, row in month_data.iterrows():
        daily_return = row['returns']
        current_price = row['Close']
        ma60 = row['ma60'] if not np.isnan(row['ma60']) else current_price

        # 高股息策略：穩定持有，獲得股息
        dividend_daily_return = daily_return * dividend_position + (month_dividend_yield / 252) * dividend_position

        # 均線策略
        ma_daily_return = 0
        if ma_position > 0:
            # 持有中，檢查停損
            if current_price <= ma_entry_price * (1 - MA_STOP_LOSS):
                # 停損出場
                ma_position = 0
                month_trades.append({
                    'date': idx,
                    'strategy': '均線策略',
                    'action': '停損出場',
                    'price': current_price,
                    'reason': f'跌破停損線 {ma_entry_price * (1 - MA_STOP_LOSS):.0f}'
                })
            else:
                ma_daily_return = daily_return * ma_position * MA_ALLOCATION
        else:
            # 空手，檢查進場條件
            if current_price > ma60 and not np.isnan(ma60):
                ma_position = 1
                ma_entry_price = current_price
                month_trades.append({
                    'date': idx,
                    'strategy': '均線策略',
                    'action': '進場',
                    'price': current_price,
                    'reason': f'突破60日均線 {ma60:.0f}'
                })

        # 逆勢策略
        contrarian_daily_return = 0
        if contrarian_position > 0:
            # 持有中，檢查出場條件 (漲2%或持有超過10天)
            days_held = (idx - pd.Timestamp(contrarian_entry_date)).days if 'contrarian_entry_date' in locals() else 0
            if (current_price >= contrarian_entry_price * 1.02) or days_held > 10:
                contrarian_position = 0
                month_trades.append({
                    'date': idx,
                    'strategy': '逆勢策略',
                    'action': '出場',
                    'price': current_price,
                    'pnl': (current_price - contrarian_entry_price) * CONTRARIAN_ALLOCATION * 100000 / current_price,
                    'reason': f'漲幅達標或超持'
                })
            else:
                contrarian_daily_return = daily_return * contrarian_position * CONTRARIAN_ALLOCATION
        else:
            # 空手，檢查進場條件 (大跌3%)
            if daily_return <= CONTRARIAN_ENTRY:
                contrarian_position = 1
                contrarian_entry_price = current_price
                contrarian_entry_date = idx
                month_trades.append({
                    'date': idx,
                    'strategy': '逆勢策略',
                    'action': '進場',
                    'price': current_price,
                    'reason': f'單日跌幅 {daily_return:.1%}'
                })

        # 計算總日收益
        total_daily_return = dividend_daily_return + ma_daily_return + contrarian_daily_return
        capital *= (1 + total_daily_return)
        month_returns.append(total_daily_return)

    # 月度統計
    if month_returns:
        month_total_return = (1 + np.sum(month_returns)) - 1
        month_sharpe = np.mean(month_returns) / np.std(month_returns) * np.sqrt(252) if np.std(month_returns) > 0 else 0

        monthly_record = {
            'year': month_start.year,
            'month': month_start.month,
            'month_name': month_start.strftime('%Y-%m'),
            'start_price': month_data['Close'].iloc[0],
            'end_price': month_data['Close'].iloc[-1],
            'month_return': month_total_return,
            'capital_end': capital,
            'trades': month_trades,
            'dividend_yield': month_dividend_yield * 100,
            'ma_signals': len([t for t in month_trades if t['strategy'] == '均線策略']),
            'contrarian_signals': len([t for t in month_trades if t['strategy'] == '逆勢策略'])
        }

        monthly_records.append(monthly_record)

        # 年份統計
        if month_start.year != current_year:
            # 計算去年統計
            year_return = (capital - year_start_capital) / year_start_capital
            yearly_records.append({
                'year': current_year,
                'start_capital': year_start_capital,
                'end_capital': capital,
                'year_return': year_return,
                'total_trades': len(year_trades)
            })

            # 重置年統計
            current_year = month_start.year
            year_start_capital = capital
            year_trades = []

        year_trades.extend(month_trades)

    print(f"處理完成: {month_start.strftime('%Y-%m')} - 資金: {capital:,.0f}")

# 最後一年統計
if year_trades:
    year_return = (capital - year_start_capital) / year_start_capital
    yearly_records.append({
        'year': current_year,
        'start_capital': year_start_capital,
        'end_capital': capital,
        'year_return': year_return,
        'total_trades': len(year_trades)
    })

# 4. 輸出每月交易記錄
print("
=== 每月交易記錄 ===")
monthly_df = pd.DataFrame(monthly_records)

for record in monthly_records[-12:]:  # 最近12個月
    print(f"\n{record['month_name']}:")
    print(f"  台指走勢: {record['start_price']:.0f} → {record['end_price']:.0f}")
    print(f"  月報酬: {record['month_return']:.2%}")
    print(f"  資金餘額: {record['capital_end']:,.0f}")
    print(f"  股息收益率: {record['dividend_yield']:.1f}%")

    if record['trades']:
        print("  交易記錄:")
        for trade in record['trades']:
            print(f"    {trade['date'].date()} {trade['strategy']}: {trade['action']} @{trade['price']:.0f} ({trade['reason']})")
    else:
        print("  無交易記錄")

# 5. 年份統計
print("
=== 年份統計 ===")
yearly_df = pd.DataFrame(yearly_records)

for record in yearly_records:
    print(f"\n{record['year']}年:")
    print(f"  起始資金: {record['start_capital']:,.0f}")
    print(f"  結束資金: {record['end_capital']:,.0f}")
    print(f"  年報酬: {record['year_return']:.2%}")
    print(f"  總交易次數: {record['total_trades']}")

# 6. 可視化
print("\n生成可視化圖表...")

fig, axes = plt.subplots(3, 2, figsize=(15, 12))
fig.suptitle('每月真實交易策略執行分析', fontsize=16)

# 1. 月度報酬走勢
if monthly_records:
    months = [r['month_name'] for r in monthly_records]
    returns = [r['month_return'] * 100 for r in monthly_records]

    axes[0,0].bar(range(len(months)), returns, alpha=0.7, color='blue')
    axes[0,0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
    axes[0,0].set_title('月度報酬走勢 (%)')
    axes[0,0].set_ylabel('月報酬 (%)')
    axes[0,0].set_xticks(range(0, len(months), 6))  # 每6個月標記
    axes[0,0].set_xticklabels([months[i] for i in range(0, len(months), 6)], rotation=45)

# 2. 累積資金曲線
capital_history = [INITIAL_CAPITAL]
for record in monthly_records:
    capital_history.append(record['capital_end'])

axes[0,1].plot(capital_history, linewidth=2, color='green')
axes[0,1].axhline(y=INITIAL_CAPITAL, color='black', linestyle='--', alpha=0.7)
axes[0,1].set_title('累積資金曲線')
axes[0,1].set_ylabel('資金 (元)')
axes[0,1].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

# 3. 年化報酬比較
if yearly_records:
    years = [str(r['year']) for r in yearly_records]
    year_returns = [r['year_return'] * 100 for r in yearly_records]

    axes[1,0].bar(years, year_returns, alpha=0.7, color='orange')
    axes[1,0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
    axes[1,0].set_title('年度報酬比較 (%)')
    axes[1,0].set_ylabel('年報酬 (%)')

# 4. 每月交易次數統計
ma_signals = [r['ma_signals'] for r in monthly_records]
contrarian_signals = [r['contrarian_signals'] for r in monthly_records]

x = range(len(monthly_records))
axes[1,1].bar(x, ma_signals, alpha=0.7, label='均線策略', color='blue')
axes[1,1].bar(x, contrarian_signals, alpha=0.7, label='逆勢策略', color='red', bottom=ma_signals)
axes[1,1].set_title('每月交易訊號統計')
axes[1,1].set_ylabel('訊號次數')
axes[1,1].legend()
axes[1,1].set_xticks(range(0, len(monthly_records), 6))
axes[1,1].set_xticklabels([monthly_records[i]['month_name'] for i in range(0, len(monthly_records), 6)], rotation=45)

# 5. 與台指比較
if monthly_records:
    twii_monthly_returns = []
    for record in monthly_records:
        month_data = df.loc[record['month_name']]
        if len(month_data) > 1:
            month_return = (month_data['Close'].iloc[-1] - month_data['Close'].iloc[0]) / month_data['Close'].iloc[0]
            twii_monthly_returns.append(month_return * 100)
        else:
            twii_monthly_returns.append(0)

    strategy_returns_pct = [r['month_return'] * 100 for r in monthly_records]

    axes[2,0].plot(strategy_returns_pct, label='策略組合', linewidth=2, color='blue')
    axes[2,0].plot(twii_monthly_returns, label='台指指數', linewidth=2, color='red', alpha=0.7)
    axes[2,0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
    axes[2,0].set_title('策略vs台指月度報酬比較 (%)')
    axes[2,0].set_ylabel('月報酬 (%)')
    axes[2,0].legend()

# 6. 勝率分析
if monthly_records:
    strategy_win_rate = sum(1 for r in monthly_records if r['month_return'] > 0) / len(monthly_records)

    labels = ['勝月', '敗月']
    sizes = [strategy_win_rate, 1 - strategy_win_rate]
    colors = ['green', 'red']

    axes[2,1].pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    axes[2,1].set_title(f'月度勝率統計 (總共{len(monthly_records)}個月)')

plt.tight_layout()
plt.savefig('monthly_strategy_execution.png', dpi=300, bbox_inches='tight')
print("圖表已保存: monthly_strategy_execution.png")

# 7. 最終統計
print("
=== 最終統計摘要 ===")
print(f"總投資期間: {len(monthly_records)} 個月")
print(f"最終資金: {capital:,.0f} 元")
print(f"總報酬: {(capital - INITIAL_CAPITAL) / INITIAL_CAPITAL:.2%}")
print(f"年化報酬: {((capital / INITIAL_CAPITAL) ** (12 / len(monthly_records)) - 1):.2%}")
print(f"月勝率: {sum(1 for r in monthly_records if r['month_return'] > 0) / len(monthly_records):.1%}")

max_dd = 0
peak = INITIAL_CAPITAL
for record in monthly_records:
    if record['capital_end'] > peak:
        peak = record['capital_end']
    dd = (peak - record['capital_end']) / peak
    max_dd = max(max_dd, dd)

print(f"最大回撤: {max_dd:.2%}")

print("
策略配置回顧:"print(f"• 高股息策略 (70%): 提供穩定股息收入")
print(f"• 均線策略 (20%): 跟隨趨勢，自動停損")
print(f"• 逆勢策略 (10%): 把握大跌機會")
print(f"• 每月調整: 檢查均線位置和殖利率")

print("
成功關鍵:"print("• 每月固定檢視，及時調整")
print("• 嚴格遵守停損原則")
print("• 多策略組合分散風險")
print("• 資金管理控制在安全範圍內")
