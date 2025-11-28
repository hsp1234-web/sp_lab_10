import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt

print("=== 大跌後買進逆勢策略 - 簡化版本 ===")

# 1. 載入數據
conn = sqlite3.connect('data/taifex.db')
query = """
SELECT date, close
FROM futures
WHERE date >= '2000-01-01'
ORDER BY date
"""
df = pd.read_sql(query, conn)
conn.close()

df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')
df = df.sort_index()

print(f"數據範圍: {df.index.min()} 到 {df.index.max()}")
print(f"總交易日: {len(df)}")

# 計算報酬
df['returns'] = df['close'].pct_change()

# 2. 策略參數
ENTRY_THRESHOLD = -0.03  # 單日跌3%進場
EXIT_THRESHOLD = 0.02    # 漲2%出場
MAX_HOLD_DAYS = 20       # 最長持有20天

# 資金參數
TOTAL_CAPITAL = 1000000  # 100萬總資金
RISK_PER_TRADE = 0.02    # 單筆2%風險
MAX_TOTAL_RISK = 0.15    # 總風險15%

# 3. 訊號生成
df['entry_signal'] = df['returns'] <= ENTRY_THRESHOLD
df['exit_signal'] = df['returns'] >= EXIT_THRESHOLD

# 避免訊號過於頻繁 (進場後至少間隔10天)
df['can_entry'] = True
last_entry = None

for idx in df.index:
    if df.loc[idx, 'entry_signal']:
        if last_entry is None or (idx - last_entry).days >= 10:
            last_entry = idx
        else:
            df.loc[idx, 'can_entry'] = False
    else:
        df.loc[idx, 'can_entry'] = False

df['valid_entry'] = df['entry_signal'] & df['can_entry']

# 4. 模擬交易
trades = []
capital = TOTAL_CAPITAL
position = 0
entry_date = None
entry_price = 0

for idx, row in df.iterrows():
    # 進場
    if row['valid_entry'] and position == 0:
        entry_price = row['close']
        entry_date = idx

        # 計算部位大小 (基於風險控制)
        risk_amount = capital * RISK_PER_TRADE  # 2萬風險
        # 台指期每點價值約10萬，槓桿約10倍
        # 保守估計：每口保證金約10萬，承受跌幅約2%
        position_size = min(risk_amount / (entry_price * 0.02), 5)  # 最多5口

        position = position_size
        print(f"進場: {idx.date()} 價格:{entry_price:.0f} 部位:{position}口")

    # 出場條件
    elif position > 0:
        days_held = (idx - entry_date).days if entry_date else 0
        should_exit = (
            row['exit_signal'] or  # 獲利出場
            days_held >= MAX_HOLD_DAYS or  # 時間出場
            row['close'] <= entry_price * 0.95  # 停損5%
        )

        if should_exit:
            exit_price = row['close']
            # 每口台指期價值約10萬 * 點數變化
            pnl_per_contract = (exit_price - entry_price) * 100000
            total_pnl = pnl_per_contract * position

            capital += total_pnl

            trades.append({
                'entry_date': entry_date,
                'exit_date': idx,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'position': position,
                'pnl': total_pnl,
                'days_held': days_held
            })

            print(f"出場: {idx.date()} 價格:{exit_price:.0f} PnL:{total_pnl:,.0f} 總資金:{capital:,.0f}")
            position = 0
            entry_date = None

# 5. 績效分析
print(f"\n=== 績效分析 ({len(trades)}筆交易) ===")

if trades:
    trades_df = pd.DataFrame(trades)

    # 基本統計
    win_trades = trades_df[trades_df['pnl'] > 0]
    loss_trades = trades_df[trades_df['pnl'] < 0]

    print(f"勝率: {len(win_trades)}/{len(trades)} = {len(win_trades)/len(trades):.1%}")
    print(f"平均獲利: {win_trades['pnl'].mean():,.0f}" if len(win_trades) > 0 else "平均獲利: 0")
    print(f"平均虧損: {loss_trades['pnl'].mean():,.0f}" if len(loss_trades) > 0 else "平均虧損: 0")
    print(f"平均持有天數: {trades_df['days_held'].mean():.1f}天")

    # 年化報酬
    total_return = (capital - TOTAL_CAPITAL) / TOTAL_CAPITAL
    total_days = (df.index[-1] - df.index[0]).days
    annual_return = (1 + total_return) ** (365 / total_days) - 1

    print(f"總報酬: {total_return:.2%}")
    print(f"年化報酬: {annual_return:.2%}")

    # 資金曲線和回撤
    capital_curve = [TOTAL_CAPITAL]
    dates = [df.index[0]]

    for trade in trades:
        capital_curve.append(capital_curve[-1] + trade['pnl'])
        dates.append(trade['exit_date'])

    capital_series = pd.Series(capital_curve, index=dates)
    capital_series = capital_series.reindex(df.index, method='ffill')
    capital_series = capital_series.fillna(TOTAL_CAPITAL)

    # 計算回撤
    peak = capital_series.expanding().max()
    drawdown = (capital_series - peak) / peak
    max_dd = drawdown.min()

    print(f"最大回撤: {max_dd:.2%}")

    # 風險評估
    print(f"\n=== 風險評估 (您的資金: {TOTAL_CAPITAL:,.0f}台幣) ===")
    print(f"單筆最大損失: {TOTAL_CAPITAL * RISK_PER_TRADE:,.0f}台幣 ({RISK_PER_TRADE:.1%})")
    print(f"總資金最大損失: {TOTAL_CAPITAL * MAX_TOTAL_RISK:,.0f}台幣 ({MAX_TOTAL_RISK:.1%})")
    print(f"實際最大回撤: {abs(max_dd)*100:.1f}%")
    print(f"是否超過您的承受度 (15%): {'❌ 超過' if abs(max_dd) > MAX_TOTAL_RISK else '✅ 可接受'}")

    if abs(max_dd) > MAX_TOTAL_RISK:
        print("建議: 降低單筆風險比例或調整進場條件")

else:
    print("未產生任何交易")

# 6. 可視化
print("\n生成圖表...")
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('大跌後買進逆勢策略分析 (2000-2024)', fontsize=14)

# 1. 台指期走勢和進場點
axes[0,0].plot(df.index, df['close'], linewidth=1, alpha=0.7, color='blue', label='台指期')
if 'valid_entry' in df.columns:
    entry_points = df[df['valid_entry']]
    axes[0,0].scatter(entry_points.index, entry_points['close'],
                     color='red', marker='v', s=50, label='進場訊號')
axes[0,0].set_title('台指期走勢與進場訊號')
axes[0,0].set_ylabel('指數點位')
axes[0,0].legend()
axes[0,0].grid(True, alpha=0.3)

# 2. 資金曲線
if 'capital_series' in locals():
    axes[0,1].plot(capital_series.index, capital_series.values,
                  linewidth=2, color='green', label='策略資金')
    axes[0,1].axhline(y=TOTAL_CAPITAL, color='black', linestyle='--',
                     alpha=0.7, label='初始資金')
    axes[0,1].set_title('資金曲線變化')
    axes[0,1].set_ylabel('資金 (台幣)')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)

# 3. 回撤分析
if 'drawdown' in locals():
    axes[1,0].fill_between(drawdown.index, drawdown.values * 100, 0,
                          color='red', alpha=0.4, label='回撤幅度')
    axes[1,0].axhline(y=-15, color='orange', linestyle='--',
                     label='您的承受上限 (15%)')
    axes[1,0].set_title('策略回撤分析')
    axes[1,0].set_ylabel('回撤 (%)')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)

# 4. 月度報酬
if trades:
    trades_df['exit_month'] = trades_df['exit_date'].dt.to_period('M')
    monthly_pnl = trades_df.groupby('exit_month')['pnl'].sum()
    axes[1,1].bar(range(len(monthly_pnl)), monthly_pnl.values / 1000,
                  alpha=0.7, color='blue', label='月度損益')
    axes[1,1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
    axes[1,1].set_title('月度損益分佈 (千元)')
    axes[1,1].set_xlabel('月份')
    axes[1,1].set_ylabel('損益 (千元)')
    axes[1,1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('contrarian_strategy_simple.png', dpi=300, bbox_inches='tight')
print("圖表已保存: contrarian_strategy_simple.png")

# 7. 最終建議
print(f"\n=== 最終資金配置建議 ===")
print(f"總資金: {TOTAL_CAPITAL:,.0f} 台幣")
print(f"建議單筆風險: {RISK_PER_TRADE:.1%} ({TOTAL_CAPITAL * RISK_PER_TRADE:,.0f} 台幣)")
print(f"建議總風險上限: {MAX_TOTAL_RISK:.1%} ({TOTAL_CAPITAL * MAX_TOTAL_RISK:,.0f} 台幣)")

if 'max_dd' in locals():
    if abs(max_dd) <= MAX_TOTAL_RISK:
        print("✅ 此策略符合您的風險承受度")
    else:
        print("⚠️ 需要調整參數以降低回撤")

print(f"\n策略特點:")
print(f"- 交易頻率: 約每年 {len(trades)/ ((df.index[-1] - df.index[0]).days / 365):.1f} 次")
print(f"- 平均持有: {trades_df['days_held'].mean():.0f} 天" if trades else "- 無交易記錄")
print(f"- 適合資金: 30萬保證金 + 70萬現金的安全配置")

