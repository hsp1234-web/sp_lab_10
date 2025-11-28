import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 設置中文字體
try:
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']

print("=== 台指期 + 遠月選擇權賣方價差策略 ===")

# 1. 載入台指數據
print("載入台指數據...")
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
df['rsi'] = 100 - (100 / (1 + df['returns'].rolling(14).mean() /
                          (-df['returns'].clip(upper=0).rolling(14).mean())))

# 2. 策略參數設定
INITIAL_CAPITAL = 1000000  # 100萬初始資金
FUTURES_MARGIN = 300000    # 30萬保證金
CASH_BUFFER = 700000       # 70萬現金緩衝

# 台指期槓桿參數 (假設10倍槓桿)
FUTURES_LEVERAGE = 10
CONTRACT_SIZE = 100000     # 台指期每點價值約10萬

# 選擇權參數
OPTION_PREMIUM_TARGET = 0.005  # 目標權利金收益0.5%
MAX_OPTION_LOSS = 0.02         # 最大選擇權損失2%
VOLATILITY_THRESHOLD = 0.25    # 波動率閾值25%

print("\n=== 策略參數 ===")
print(f"初始資金: {INITIAL_CAPITAL:,} 元")
print(f"期貨保證金: {FUTURES_MARGIN:,} 元")
print(f"現金緩衝: {CASH_BUFFER:,} 元")
print(f"期貨槓桿: {FUTURES_LEVERAGE}倍")
print(f"目標權利金: {OPTION_PREMIUM_TARGET:.1%}")
print(f"最大選擇權損失: {MAX_OPTION_LOSS:.1%}")

# 3. 核心策略邏輯
print("\n開始策略模擬...")

# 初始化變數
capital = INITIAL_CAPITAL
futures_position = 0  # 台指期部位 (正數=多頭, 負數=空頭)
option_position = 0   # 選擇權部位
total_pnl = []
capital_history = [INITIAL_CAPITAL]
dates_history = [df.index[0]]

# 模擬交易
for i in range(60, len(df)):  # 從第60天開始（確保有足夠歷史數據）
    current_date = df.index[i]
    current_price = df.iloc[i]['Close']
    current_vol = df.iloc[i]['volatility']

    # 檢查是否接近結算日 (每月最後5個交易日)
    days_to_month_end = (current_date + pd.offsets.MonthEnd(1) - current_date).days
    near_settlement = days_to_month_end <= 5

    # 決定台指期部位 (趨勢跟隨)
    ma20 = df.iloc[i]['ma20']
    ma60 = df.iloc[i]['ma60']

    # 簡單趨勢策略
    if current_price > ma20 and ma20 > ma60:  # 多頭趨勢
        target_position = 1  # 多頭
    elif current_price < ma20 and ma20 < ma60:  # 空頭趨勢
        target_position = -1  # 空頭
    else:
        target_position = 0  # 觀望

    # 波動率過高時減少部位
    if current_vol > VOLATILITY_THRESHOLD:
        target_position *= 0.5

    # 調整台指期部位
    if futures_position != target_position:
        # 計算部位大小 (基於保證金限制)
        max_contracts = int(FUTURES_MARGIN / (current_price / FUTURES_LEVERAGE))

        if target_position == 1:  # 多頭
            new_position = min(max_contracts, 3)  # 最多3口
        elif target_position == -1:  # 空頭
            new_position = max(-max_contracts, -3)  # 最多3口
        else:
            new_position = 0

        futures_position = new_position

    # 選擇權增益策略 (在結算日前使用遠月選擇權)
    if near_settlement and current_vol < VOLATILITY_THRESHOLD and futures_position != 0:
        # 計算選擇權賣方價差的權利金收益
        # 假設賣出價外1個標準差的選擇權，權利金約為當前價格的0.3-0.5%
        implied_vol = current_vol
        strike_distance = current_price * implied_vol  # 1個標準差的距離

        # 遠月選擇權權利金較高 (假設遠月權利金是近月的1.5倍)
        option_premium = current_price * 0.004 * 1.5  # 遠月權利金約0.4%

        # 決定是否進場 (權利金 > 目標收益)
        if option_premium > current_price * OPTION_PREMIUM_TARGET:
            # 賣出價差部位 (簡化模擬：假設有50%勝率，平均獲利0.3%)
            option_risk = current_price * MAX_OPTION_LOSS
            option_reward = option_premium

            # 凱利公式計算部位大小
            win_rate = 0.6  # 假設勝率60%
            risk_reward_ratio = option_risk / option_reward if option_reward > 0 else 10

            kelly_fraction = (win_rate - (1-win_rate)/risk_reward_ratio) if risk_reward_ratio > 0 else 0
            kelly_fraction = max(0, min(kelly_fraction, 0.5))  # 限制在50%以內

            option_position = kelly_fraction * 0.1  # 保守使用10%的資金
        else:
            option_position = 0
    else:
        option_position = 0

    # 計算每日損益
    futures_pnl = 0
    option_pnl = 0

    # 台指期損益計算
    if futures_position != 0:
        price_change = df.iloc[i]['Close'] - df.iloc[i-1]['Close']
        futures_pnl = futures_position * price_change * CONTRACT_SIZE

    # 選擇權損益計算 (簡化模擬)
    if option_position > 0:
        # 隨機模擬選擇權結果 (60%勝率，平均獲利0.3%，最大損失2%)
        if np.random.random() < 0.6:  # 60%勝率
            option_pnl = option_position * capital * 0.003  # 0.3%收益
        else:
            option_pnl = -option_position * capital * MAX_OPTION_LOSS  # 最大損失

    # 更新資金
    daily_pnl = futures_pnl + option_pnl
    capital += daily_pnl

    # 記錄歷史
    total_pnl.append(daily_pnl)
    capital_history.append(capital)
    dates_history.append(current_date)

    # 每100天輸出一次進度
    if i % 100 == 0:
        print(f"處理到 {current_date.date()}: 資金 {capital:,.0f}, 部位 {futures_position}")

# 4. 績效分析
print("\n=== 策略績效分析 ===")

# 計算關鍵指標
capital_series = pd.Series(capital_history, index=dates_history)
capital_series = capital_series[~capital_series.index.duplicated(keep='last')]

total_return = (capital - INITIAL_CAPITAL) / INITIAL_CAPITAL
annual_return = (1 + total_return) ** (365 / len(df)) - 1

# 最大回撤
peak = capital_series.expanding().max()
drawdown = (capital_series - peak) / peak
max_dd = drawdown.min()

# 勝率和波動率
daily_returns = capital_series.pct_change().dropna()
win_rate = (daily_returns > 0).mean()
volatility = daily_returns.std() * np.sqrt(252)
sharpe_ratio = annual_return / volatility if volatility > 0 else 0

print(f"總報酬率: {total_return:.2%}")
print(f"年化報酬率: {annual_return:.2%}")
print(f"最大回撤: {max_dd:.2%}")
print(f"日勝率: {win_rate:.1%}")
print(f"年化波動率: {volatility:.2%}")
print(f"夏普比率: {sharpe_ratio:.2f}")
print(f"最終資金: {capital:,.0f} 元")
print(f"總交易日: {len(daily_returns)}")

# 月度統計
monthly_returns = daily_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
monthly_win_rate = (monthly_returns > 0).mean()
print(f"月勝率: {monthly_win_rate:.1%}")
print(f"平均月報酬: {monthly_returns.mean():.2%}")

# 5. 可視化
print("\n生成策略圖表...")

fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('台指期 + 遠月選擇權賣方價差策略績效分析', fontsize=16)

# 1. 資金曲線
axes[0,0].plot(capital_series.index, capital_series.values, linewidth=2, color='blue', label='策略資金')
axes[0,0].axhline(y=INITIAL_CAPITAL, color='black', linestyle='--', alpha=0.7, label='初始資金')
axes[0,0].set_title('資金曲線變化')
axes[0,0].set_ylabel('資金 (元)')
axes[0,0].legend()
axes[0,0].grid(True, alpha=0.3)
axes[0,0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

# 2. 回撤分析
axes[0,1].fill_between(drawdown.index, drawdown.values * 100, 0,
                      color='red', alpha=0.4, label='回撤幅度')
axes[0,1].axhline(y=-15, color='orange', linestyle='--', label='15%風險線')
axes[0,1].set_title('策略回撤分析')
axes[0,1].set_ylabel('回撤 (%)')
axes[0,1].legend()
axes[0,1].grid(True, alpha=0.3)

# 3. 台指趨勢與策略訊號
ax3 = axes[1,0]
ax3.plot(df.index, df['Close'], linewidth=1, alpha=0.7, color='gray', label='台指指數')
ax3.plot(df.index, df['ma20'], linewidth=1, color='blue', label='20日均線')
ax3.plot(df.index, df['ma60'], linewidth=1, color='red', label='60日均線')
ax3.set_title('台指趨勢與策略基礎')
ax3.set_ylabel('指數點位')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. 月度報酬分佈
monthly_data = monthly_returns.reset_index()
monthly_data['year'] = monthly_data['Date'].dt.year
yearly_avg = monthly_data.groupby('year')[0].mean()

axes[1,1].bar(range(len(yearly_avg)), yearly_avg.values * 100,
              alpha=0.7, color='green', label='年度平均月報酬')
axes[1,1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
axes[1,1].set_title('年度平均月報酬')
axes[1,1].set_xlabel('年份')
axes[1,1].set_ylabel('月報酬率 (%)')
axes[1,1].set_xticks(range(len(yearly_avg)))
axes[1,1].set_xticklabels(yearly_avg.index.astype(int))
axes[1,1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('taifex_options_strategy_analysis.png', dpi=300, bbox_inches='tight', facecolor='white')
print("圖表已保存: taifex_options_strategy_analysis.png")

# 6. 策略總結
print("\n" + "="*60)
print("💰 台指期 + 遠月選擇權策略總結")
print("="*60)

print(f"\n📊 績效指標:")
print(f"• 年化報酬率: {annual_return:.1%}")
print(f"• 最大回撤: {max_dd:.1%}")
print(f"• 夏普比率: {sharpe_ratio:.2f}")
print(f"• 月勝率: {monthly_win_rate:.1%}")

print(f"\n💡 策略特點:")
print("• 核心部位: 台指期趨勢跟隨 (動態調整多空)")
print("• 增益部位: 遠月選擇權賣方價差 (結算日前進場)")
print("• 風險控制: 波動率過高時自動減倉")
print("• 資金配置: 30萬保證金 + 70萬現金緩衝")

print(f"\n🎯 適合場景:")
print("• 月結算日前5個交易日")
print("• 市場波動率 < 25%")
print("• 台指處於明確趨勢")
print("• 遠月選擇權權利金充足")

print(f"\n⚠️ 風險提醒:")
print("• 選擇權有時間價值衰減風險")
print("• 結算日前波動可能放大")
print("• 遠月合約流動性較差")
print("• 建議先用小額資金測試")

print(f"\n💵 資金使用效率:")
total_trading_days = len([p for p in total_pnl if p != 0])
avg_daily_pnl = np.mean([p for p in total_pnl if p != 0]) if total_pnl else 0
print(f"• 平均每日損益: {avg_daily_pnl:,.0f} 元")
print(f"• 有部位交易日: {total_trading_days} 天")
print(f"• 資金使用率: {total_trading_days/len(df):.1%}")

print(f"\n🚀 改進建議:")
print("1. 優化選擇權進場時機 (結合隱含波動率)")
print("2. 增加選擇權Delta對沖機制")
print("3. 測試不同到期月的權利金效率")
print("4. 加入機器學習預測趨勢轉折點")

print("="*60)

