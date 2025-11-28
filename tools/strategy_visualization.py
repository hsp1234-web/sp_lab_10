import finlab
from finlab import data
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

# 設置中文字體 (Windows環境)
try:
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.style.use('default')  # 使用默認樣式避免版本問題

print("=== 懶人波段策略可視化分析報告 ===")

# 登入FINLAB
api_key = "wnFW0KT5etgpNr6IKZI05kNyRrMQDrIeoaplJBlRc+Twz+RWciylMCjm0jvtL0n5#free"
finlab.login(api_key)

# 獲取數據
print("正在獲取數據...")
close = data.get('price:收盤價')
rev_growth = data.get('monthly_revenue:去年同月增減(%)')
yield_ratio = data.get('price_earning_ratio:殖利率(%)')
vol = data.get('price:成交股數')

# 計算台股大盤指數 (簡單平均)
market_index = close.mean(axis=1)
market_returns = market_index.pct_change()

print("數據準備完成，開始策略計算...")

# ================================
# 策略一：月營收成長波段策略
# ================================
print("計算策略一：月營收成長波段...")

# 條件
cond_growth = rev_growth > 20
pe = data.get('price_earning_ratio:本益比')
cond_value = (pe > 0) & (pe < 25)
sma60 = close.rolling(60).mean()
cond_trend = close > sma60
vol_ma5 = vol.rolling(5).mean()
cond_liquidity = vol_ma5 > 100000

# 綜合條件
position1 = cond_growth & cond_value & cond_trend & cond_liquidity
rank = rev_growth.rank(axis=1, ascending=False)
position1 = position1 & (rank <= 20)

# 月度換股
position1_monthly = position1.resample('MS').first()
position1_daily = position1_monthly.reindex(close.index, method='ffill')

# 計算報酬
returns = close.pct_change()
strategy1_returns = (position1_daily.shift(1) * returns).mean(axis=1)
strategy1_cumulative = (1 + strategy1_returns).cumprod()

# ================================
# 策略二：高股息低波動策略
# ================================
print("計算策略二：高股息低波動...")

# 條件
volatility = returns.rolling(60).std()
vol_rank = volatility.rank(axis=1, pct=True)
cond_yield = yield_ratio > 4
cond_low_vol = vol_rank < 0.5
cond_growth2 = rev_growth > 0
cond_liquidity2 = vol.rolling(5).mean() > 500000

position2 = cond_yield & cond_low_vol & cond_growth2 & cond_liquidity2
rank_yield = yield_ratio.rank(axis=1, ascending=False)
position2 = position2 & (rank_yield <= 10)

# 月度換股
position2_monthly = position2.resample('MS').first()
position2_daily = position2_monthly.reindex(close.index, method='ffill')

strategy2_returns = (position2_daily.shift(1) * returns).mean(axis=1)
strategy2_cumulative = (1 + strategy2_returns).cumprod()

# ================================
# 組合策略 (60%策略二 + 40%策略一)
# ================================
print("計算組合策略...")
portfolio_returns = 0.6 * strategy2_returns + 0.4 * strategy1_returns
portfolio_cumulative = (1 + portfolio_returns).cumprod()

# ================================
# 大盤基準
# ================================
market_cumulative = (1 + market_returns).cumprod()

# ================================
# 計算每月收益
# ================================
print("計算每月收益統計...")

# 每月報酬
monthly_strategy1 = strategy1_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
monthly_strategy2 = strategy2_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
monthly_portfolio = portfolio_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
monthly_market = market_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)

# ================================
# 計算MDD
# ================================
def calculate_mdd(cumulative_returns):
    """計算最大回撤"""
    peak = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - peak) / peak
    mdd = drawdown.min()
    return mdd, drawdown

mdd1, dd1 = calculate_mdd(strategy1_cumulative)
mdd2, dd2 = calculate_mdd(strategy2_cumulative)
mdd_portfolio, dd_portfolio = calculate_mdd(portfolio_cumulative)
mdd_market, dd_market = calculate_mdd(market_cumulative)

# ================================
# 績效指標
# ================================
def calculate_metrics(returns, cumulative):
    """計算關鍵指標"""
    annual_return = returns.mean() * 252
    annual_vol = returns.std() * np.sqrt(252)
    sharpe = annual_return / annual_vol if annual_vol > 0 else 0
    mdd, _ = calculate_mdd(cumulative)
    win_rate = (returns > 0).mean()

    return {
        '年化報酬': annual_return,
        '年化波動': annual_vol,
        '夏普比率': sharpe,
        '最大回撤': mdd,
        '勝率': win_rate
    }

metrics1 = calculate_metrics(strategy1_returns, strategy1_cumulative)
metrics2 = calculate_metrics(strategy2_returns, strategy2_cumulative)
metrics_portfolio = calculate_metrics(portfolio_returns, portfolio_cumulative)
metrics_market = calculate_metrics(market_returns, market_cumulative)

# ================================
# 創建圖表
# ================================
print("生成可視化圖表...")

# 設定子圖
fig, axes = plt.subplots(2, 3, figsize=(20, 12))
fig.suptitle('懶人波段策略績效分析報告', fontsize=16, fontweight='bold')

# 1. 累積收益比較圖
ax1 = axes[0, 0]
ax1.plot(strategy1_cumulative.index, strategy1_cumulative.values, label='月營收成長策略', linewidth=2)
ax1.plot(strategy2_cumulative.index, strategy2_cumulative.values, label='高股息低波動策略', linewidth=2)
ax1.plot(portfolio_cumulative.index, portfolio_cumulative.values, label='組合策略 (60:40)', linewidth=3, linestyle='--')
ax1.plot(market_cumulative.index, market_cumulative.values, label='台股大盤', linewidth=2, alpha=0.7)
ax1.set_title('累積收益走勢比較')
ax1.set_ylabel('累積報酬率')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. 每月收益走勢
ax2 = axes[0, 1]
ax2.bar(monthly_portfolio.index, monthly_portfolio.values * 100, alpha=0.7, label='組合策略', color='blue')
ax2.plot(monthly_market.index, monthly_market.values * 100, label='大盤', color='red', linewidth=2)
ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax2.set_title('每月收益走勢 (%)')
ax2.set_ylabel('月報酬率 (%)')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. 回撤分析
ax3 = axes[0, 2]
ax3.fill_between(dd_portfolio.index, dd_portfolio.values * 100, 0, alpha=0.3, color='red', label='組合策略回撤')
ax3.fill_between(dd_market.index, dd_market.values * 100, 0, alpha=0.3, color='gray', label='大盤回撤')
ax3.set_title('最大回撤分析')
ax3.set_ylabel('回撤幅度 (%)')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. 績效指標雷達圖
ax4 = axes[1, 0]
categories = ['年化報酬', '夏普比率', '勝率', '最大回撤']
strategy_values = [
    metrics_portfolio['年化報酬'] * 100,
    metrics_portfolio['夏普比率'],
    metrics_portfolio['勝率'] * 100,
    abs(metrics_portfolio['最大回撤']) * 100
]
market_values = [
    metrics_market['年化報酬'] * 100,
    metrics_market['夏普比率'],
    metrics_market['勝率'] * 100,
    abs(metrics_market['最大回撤']) * 100
]

# 標準化數據到0-1範圍
max_values = [20, 2, 60, 50]  # 假設的最大值
strategy_norm = [min(v/max_v, 1) for v, max_v in zip(strategy_values, max_values)]
market_norm = [min(v/max_v, 1) for v, max_v in zip(market_values, max_values)]

angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
angles += angles[:1]

strategy_norm += strategy_norm[:1]
market_norm += market_norm[:1]

ax4.plot(angles, strategy_norm, 'o-', linewidth=2, label='組合策略', color='blue')
ax4.fill(angles, strategy_norm, alpha=0.25, color='blue')
ax4.plot(angles, market_norm, 'o-', linewidth=2, label='大盤', color='red')
ax4.fill(angles, market_norm, alpha=0.25, color='red')

ax4.set_xticks(angles[:-1])
ax4.set_xticklabels(categories)
ax4.set_title('策略vs大盤績效比較')
ax4.legend()
ax4.grid(True, alpha=0.3)

# 5. 年化報酬率走勢 (滾動計算)
ax5 = axes[1, 1]
rolling_window = 252  # 一年
rolling_return_strategy = strategy1_returns.rolling(rolling_window).mean() * 252 * 100
rolling_return_portfolio = portfolio_returns.rolling(rolling_window).mean() * 252 * 100
rolling_return_market = market_returns.rolling(rolling_window).mean() * 252 * 100

ax5.plot(rolling_return_strategy.index, rolling_return_strategy.values,
         label='月營收成長策略', alpha=0.7)
ax5.plot(rolling_return_portfolio.index, rolling_return_portfolio.values,
         label='組合策略', linewidth=2, color='blue')
ax5.plot(rolling_return_market.index, rolling_return_market.values,
         label='大盤', linewidth=2, color='red')
ax5.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax5.set_title('滾動一年年化報酬率 (%)')
ax5.set_ylabel('年化報酬率 (%)')
ax5.legend()
ax5.grid(True, alpha=0.3)

# 6. 年度報酬率比較圖
ax6 = axes[1, 2]

# 按年計算各策略表現
yearly_strategy1 = strategy1_returns.groupby(strategy1_returns.index.year).apply(lambda x: (1 + x).prod() - 1)
yearly_strategy2 = strategy2_returns.groupby(strategy2_returns.index.year).apply(lambda x: (1 + x).prod() - 1)
yearly_portfolio = portfolio_returns.groupby(portfolio_returns.index.year).apply(lambda x: (1 + x).prod() - 1)
yearly_market = market_returns.groupby(market_returns.index.year).apply(lambda x: (1 + x).prod() - 1)

years = yearly_portfolio.index
ax6.bar(years - 0.3, yearly_portfolio.values * 100, width=0.2, label='組合策略', alpha=0.7)
ax6.bar(years - 0.1, yearly_strategy1.values * 100, width=0.2, label='月營收策略', alpha=0.7)
ax6.bar(years + 0.1, yearly_strategy2.values * 100, width=0.2, label='高股息策略', alpha=0.7)
ax6.bar(years + 0.3, yearly_market.values * 100, width=0.2, label='大盤', alpha=0.7)
ax6.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax6.set_title('年度報酬率比較 (%)')
ax6.set_ylabel('年度報酬率 (%)')
ax6.legend()
ax6.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('strategy_performance_analysis.png', dpi=300, bbox_inches='tight')
print("圖表已保存為: strategy_performance_analysis.png")

# ================================
# 文字報告
# ================================
print("\n" + "="*80)
print("📊 懶人波段策略績效總結報告")
print("="*80)

print(f"\n📈 策略表現 (2007-2025):")
print(f"組合策略年化報酬: {metrics_portfolio['年化報酬']:.2%}")
print(f"大盤年化報酬: {metrics_market['年化報酬']:.2%}")
print(f"超額報酬: {(metrics_portfolio['年化報酬'] - metrics_market['年化報酬']):.2%}")

print(f"\n💰 風險指標:")
print(f"組合策略夏普比率: {metrics_portfolio['夏普比率']:.2f}")
print(f"大盤夏普比率: {metrics_market['夏普比率']:.2f}")
print(f"組合策略最大回撤: {metrics_portfolio['最大回撤']:.2%}")
print(f"大盤最大回撤: {metrics_market['最大回撤']:.2%}")

print(f"\n🎯 勝率分析:")
print(f"組合策略月勝率: {metrics_portfolio['勝率']:.1%}")
print(f"大盤月勝率: {metrics_market['勝率']:.1%}")

print(f"\n📅 月度統計:")
print(f"組合策略平均月報酬: {monthly_portfolio.mean():.2%}")
print(f"大盤平均月報酬: {monthly_market.mean():.2%}")
print(f"組合策略月報酬波動: {monthly_portfolio.std():.2%}")
print(f"大盤月報酬波動: {monthly_market.std():.2%}")

print(f"\n🏆 年度表現亮點:")
best_years = yearly_portfolio[yearly_portfolio > yearly_market].index.tolist()
print(f"組合策略超越大盤的年份: {best_years}")

print(f"\n💡 投資建議:")
print("- 月初檢查Finlab選股清單，調整持股")
print("- 建議資金分配: 60%高股息策略 + 40%成長策略")
print("- 每月只需操作一次，適合忙碌投資人")
print("- 加入Covered Call可進一步提升收益")

print(f"\n圖表已生成: strategy_performance_analysis.png")
print("="*80)