import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime

# 設置中文字體
try:
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']

print("=== 大跌後買進逆勢策略設計 ===")

# 1. 數據載入和準備
print("載入台指期數據...")
conn = sqlite3.connect('data/taifex.db')

# 載入2000年以後的數據
query = """
SELECT date, close, high, low, volume
FROM futures
WHERE date >= '2000-01-01'
ORDER BY date
"""
df = pd.read_sql(query, conn)
conn.close()

# 數據清理
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')
df = df.sort_index()

print(f"數據範圍: {df.index.min()} 到 {df.index.max()}")
print(f"總交易日: {len(df)}")

# 計算日報酬率
df['returns'] = df['close'].pct_change()
df['log_returns'] = np.log(df['close'] / df['close'].shift(1))

# 2. 策略邏輯設計
print("\n=== 策略參數設定 ===")

# 逆勢策略參數
ENTRY_THRESHOLD = -0.03  # 單日跌幅超過3%進場
EXIT_THRESHOLD = 0.02    # 漲幅超過2%出場
HOLDING_DAYS_MAX = 30    # 最多持有30天
VOLATILITY_WINDOW = 20   # 波動率計算窗口

# 風險管理參數
TOTAL_CAPITAL = 1000000  # 總資金100萬台幣
RISK_PER_TRADE = 0.02    # 單筆交易風險2%
MAX_DRAWDOWN = 0.15      # 最大回撤15%

# 動態停損 (基於ATR)
ATR_PERIOD = 14
df['tr'] = np.maximum(df['high'] - df['low'],
                     np.maximum(abs(df['high'] - df['close'].shift(1)),
                               abs(df['low'] - df['close'].shift(1))))
df['atr'] = df['tr'].rolling(ATR_PERIOD).mean()
df['dynamic_stop'] = df['close'] - 2 * df['atr']  # 2倍ATR作為停損

# 3. 訊號生成
print("生成交易訊號...")

# 進場訊號：大跌日
df['entry_signal'] = df['returns'] <= ENTRY_THRESHOLD

# 出場訊號：獲利了結或停損
df['exit_signal'] = (
    (df['returns'] >= EXIT_THRESHOLD) |  # 獲利出場
    (df['close'] <= df['dynamic_stop'])   # 停損出場
)

# 確保訊號不會重疊（簡單版本：進場後30天內不進場）
df['days_since_entry'] = 0
last_entry_idx = None

for idx in df.index:
    if df.loc[idx, 'entry_signal'] and (last_entry_idx is None or (idx - last_entry_idx).days >= HOLDING_DAYS_MAX):
        last_entry_idx = idx
        df.loc[idx, 'valid_entry'] = True
    else:
        df.loc[idx, 'valid_entry'] = False

# 4. 回測模擬
print("執行回測模擬...")

trades = []
capital = TOTAL_CAPITAL
peak_capital = TOTAL_CAPITAL
current_position = 0
entry_price = 0
trade_dates = []

for idx, row in df.iterrows():
    # 進場邏輯
    if row['valid_entry'] and current_position == 0:
        # 計算進場金額 (使用槓桿)
        risk_amount = capital * RISK_PER_TRADE  # 2%風險
        # 台指期槓桿約10倍，假設保證金10%
        margin_required = row['close'] * 10  # 10口台指期
        position_size = min(risk_amount / (row['close'] * 0.1), margin_required)  # 保守估計

        entry_price = row['close']
        current_position = position_size
        trade_dates.append((idx, 'entry', entry_price, capital))

        print(f"進場: {idx.date()} 價格:{entry_price:.0f} 部位:{position_size:.0f}")

    # 出場邏輯
    elif current_position > 0 and (row['exit_signal'] or (idx - trade_dates[-1][0]).days >= HOLDING_DAYS_MAX):
        exit_price = row['close']
        pnl = (exit_price - entry_price) * (current_position / entry_price) * 100000  # 台指期每點10萬

        capital += pnl
        peak_capital = max(peak_capital, capital)

        trade_dates.append((idx, 'exit', exit_price, capital))
        trades.append({
            'entry_date': trade_dates[-2][0],
            'exit_date': idx,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'holding_days': (idx - trade_dates[-2][0]).days
        })

        current_position = 0
        print(f"出場: {idx.date()} 價格:{exit_price:.0f} PnL:{pnl:,.0f} 總資金:{capital:,.0f}")

# 5. 績效分析
print("
=== 績效分析 ===")

if trades:
    trades_df = pd.DataFrame(trades)
    print(f"總交易次數: {len(trades)}")
    print(f"勝率: {(trades_df['pnl'] > 0).mean():.1%}")
    print(f"平均持有天數: {trades_df['holding_days'].mean():.1f}天")
    print(f"平均單筆獲利: {trades_df['pnl'].mean():,.0f}")

    # 年化報酬計算
    total_days = (df.index[-1] - df.index[0]).days
    total_return = (capital - TOTAL_CAPITAL) / TOTAL_CAPITAL
    annual_return = (1 + total_return) ** (365 / total_days) - 1
    print(f"總報酬: {total_return:.2%}")
    print(f"年化報酬: {annual_return:.2%}")

    # 最大回撤
    capital_series = pd.Series([TOTAL_CAPITAL], index=[df.index[0]])
    for trade in trades:
        capital_series[trade['exit_date']] = trade['exit_date'] column from trades_df

    capital_series = capital_series.sort_index()
    capital_series = capital_series.reindex(df.index, method='ffill')
    capital_series.iloc[0] = TOTAL_CAPITAL
    capital_series = capital_series.fillna(method='ffill')

    peak = capital_series.expanding().max()
    drawdown = (capital_series - peak) / peak
    max_dd = drawdown.min()

    print(f"最大回撤: {max_dd:.2%}")

    # 夏普比率
    daily_returns = capital_series.pct_change().dropna()
    sharpe = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() > 0 else 0
    print(f"夏普比率: {sharpe:.2f}")

else:
    print("沒有產生交易訊號")

# 6. 可視化
print("\n生成績效圖表...")

fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('大跌後買進逆勢策略績效分析 (2000-2024)', fontsize=16)

# 1. 台指期走勢圖
axes[0,0].plot(df.index, df['close'], linewidth=1, alpha=0.7, color='blue')
axes[0,0].set_title('台指期走勢 (2000-2024)')
axes[0,0].set_ylabel('指數點位')
axes[0,0].grid(True, alpha=0.3)

# 標記進場點
if 'valid_entry' in df.columns:
    entry_points = df[df['valid_entry']]
    axes[0,0].scatter(entry_points.index, entry_points['close'],
                      color='red', marker='^', s=50, label='進場訊號')
    axes[0,0].legend()

# 2. 資金曲線
if 'capital_series' in locals():
    axes[0,1].plot(capital_series.index, capital_series.values, linewidth=2, color='green')
    axes[0,1].axhline(y=TOTAL_CAPITAL, color='black', linestyle='--', alpha=0.5, label='初始資金')
    axes[0,1].set_title('資金曲線變化')
    axes[0,1].set_ylabel('資金金額 (台幣)')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)

# 3. 回撤圖
if 'drawdown' in locals():
    axes[1,0].fill_between(drawdown.index, drawdown.values * 100, 0,
                          color='red', alpha=0.3, label='回撤幅度')
    axes[1,0].set_title('策略回撤分析')
    axes[1,0].set_ylabel('回撤 (%)')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)

# 4. 月度報酬分佈
if trades:
    monthly_pnl = trades_df.groupby(trades_df['exit_date'].dt.to_period('M'))['pnl'].sum()
    axes[1,1].bar(range(len(monthly_pnl)), monthly_pnl.values / 1000,  # 轉換為千元
                  alpha=0.7, color='blue', label='月度PnL')
    axes[1,1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
    axes[1,1].set_title('月度損益分佈 (千元)')
    axes[1,1].set_xlabel('月份序列')
    axes[1,1].set_ylabel('損益 (千元)')
    axes[1,1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('contrarian_strategy_analysis.png', dpi=300, bbox_inches='tight')
print("圖表已保存為: contrarian_strategy_analysis.png")

# 7. 風險評估和資金配置建議
print("\n=== 資金配置分析 ===")
print(f"總資金: {TOTAL_CAPITAL:,.0f} 台幣")
print(f"保證金: {30:,.0f} 萬台幣 ({30/TOTAL_CAPITAL:.1%})")
print(f"現金: {70:,.0f} 萬台幣 ({70/TOTAL_CAPITAL:.1%})")

if 'max_dd' in locals():
    print(f"策略最大回撤: {max_dd:.1%}")
    print(f"相對於您的承受度 ({MAX_DRAWDOWN:.1%}): {'✓ 可接受' if abs(max_dd) <= MAX_DRAWDOWN else '✗ 超過承受度'}")

print(f"\n單筆交易最大風險: {RISK_PER_TRADE:.1%} = {TOTAL_CAPITAL * RISK_PER_TRADE:,.0f} 台幣")
print(f"總部位最大風險: {MAX_DRAWDOWN:.1%} = {TOTAL_CAPITAL * MAX_DRAWDOWN:,.0f} 台幣")

print("
=== 策略調整建議 ===")
print("1. 進場門檻: 單日跌幅3% (可調整為2-4%)")
print("2. 出場條件: 2%漲幅或2倍ATR停損")
print("3. 持有上限: 30天 (避免長期持有)")
print("4. 交易頻率: 每年5-15次 (視市場波動而定)")

if trades:
    win_rate = (trades_df['pnl'] > 0).mean()
    print(f"\n目前勝率: {win_rate:.1%}")
    if win_rate < 0.6:
        print("建議: 調整進場條件，降低進場門檻或增加技術確認")
    else:
        print("勝率表現良好，可考慮維持現有參數")

print(f"\n圖表已生成: contrarian_strategy_analysis.png")
print("包含: 台指期走勢、資金曲線、回撤分析、月度損益分佈")

