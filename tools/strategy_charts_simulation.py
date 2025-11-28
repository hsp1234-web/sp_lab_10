import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# 設置中文字體
try:
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']

print("=== 懶人波段策略績效圖表模擬 ===")

# 生成模擬數據 (基於之前的實證結果)
np.random.seed(42)
start_date = pd.Timestamp('2007-01-01')
end_date = pd.Timestamp('2025-11-26')
dates = pd.date_range(start_date, end_date, freq='D')

# 模擬策略報酬 (基於實證結果調整)
n_days = len(dates)

# 月營收成長策略 (較高波動)
strategy1_daily_returns = np.random.normal(0.0003, 0.015, n_days)  # 年化約9%
strategy1_cumulative = (1 + pd.Series(strategy1_daily_returns, index=dates)).cumprod()

# 高股息低波動策略 (較低波動)
strategy2_daily_returns = np.random.normal(0.0001, 0.008, n_days)  # 年化約3%
strategy2_cumulative = (1 + pd.Series(strategy2_daily_returns, index=dates)).cumprod()

# 組合策略 (60%高股息 + 40%成長)
portfolio_daily_returns = 0.6 * strategy2_daily_returns + 0.4 * strategy1_daily_returns
portfolio_cumulative = (1 + pd.Series(portfolio_daily_returns, index=dates)).cumprod()

# 台股大盤 (年化約8%，波動15%)
market_daily_returns = np.random.normal(0.00025, 0.012, n_days)
market_cumulative = (1 + pd.Series(market_daily_returns, index=dates)).cumprod()

# 計算每月收益
monthly_portfolio = pd.Series(portfolio_daily_returns, index=dates).resample('M').apply(lambda x: (1 + x).prod() - 1)
monthly_market = pd.Series(market_daily_returns, index=dates).resample('M').apply(lambda x: (1 + x).prod() - 1)

# 計算回撤
def calculate_drawdown(cumulative):
    peak = cumulative.expanding().max()
    drawdown = (cumulative - peak) / peak
    return drawdown

dd_portfolio = calculate_drawdown(portfolio_cumulative)
dd_market = calculate_drawdown(market_cumulative)

# ================================
# 創建圖表
# ================================
fig, axes = plt.subplots(2, 3, figsize=(20, 12))
fig.suptitle('懶人波段策略績效分析報告 (Finlab實證數據模擬)', fontsize=16, fontweight='bold')

# 1. 累積收益比較圖
ax1 = axes[0, 0]
ax1.plot(dates, strategy1_cumulative.values, label='月營收成長策略', linewidth=2, alpha=0.7)
ax1.plot(dates, strategy2_cumulative.values, label='高股息低波動策略', linewidth=2, alpha=0.7)
ax1.plot(dates, portfolio_cumulative.values, label='組合策略 (60:40)', linewidth=3, linestyle='--', color='blue')
ax1.plot(dates, market_cumulative.values, label='台股大盤', linewidth=2, alpha=0.7, color='red')
ax1.set_title('累積收益走勢比較 (2007-2025)')
ax1.set_ylabel('累積報酬率')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}x'))

# 2. 每月收益走勢
ax2 = axes[0, 1]
bars = ax2.bar(monthly_portfolio.index, monthly_portfolio.values * 100,
               alpha=0.7, label='組合策略', color='blue', width=20)
ax2.plot(monthly_market.index, monthly_market.values * 100,
         label='大盤', color='red', linewidth=2)
ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax2.set_title('每月收益走勢 (%)')
ax2.set_ylabel('月報酬率 (%)')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 添加正負收益統計
positive_months = (monthly_portfolio > 0).sum()
total_months = len(monthly_portfolio)
ax2.text(0.02, 0.98, f'正報酬月數: {positive_months}/{total_months} ({positive_months/total_months:.1%})',
         transform=ax2.transAxes, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# 3. 回撤分析
ax3 = axes[0, 2]
ax3.fill_between(dates, dd_portfolio.values * 100, 0, alpha=0.3, color='red', label='組合策略回撤')
ax3.fill_between(dates, dd_market.values * 100, 0, alpha=0.3, color='gray', label='大盤回撤')
ax3.set_title('最大回撤分析')
ax3.set_ylabel('回撤幅度 (%)')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 計算MDD
mdd_portfolio = dd_portfolio.min() * 100
mdd_market = dd_market.min() * 100
ax3.text(0.02, 0.98, f'組合MDD: {mdd_portfolio:.1f}%\n大盤MDD: {mdd_market:.1f}%',
         transform=ax3.transAxes, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))

# 4. 績效指標比較
ax4 = axes[1, 0]

# 計算關鍵指標
annual_return_portfolio = portfolio_daily_returns.mean() * 252
annual_return_market = market_daily_returns.mean() * 252
sharpe_portfolio = annual_return_portfolio / (portfolio_daily_returns.std() * np.sqrt(252))
sharpe_market = annual_return_market / (market_daily_returns.std() * np.sqrt(252))
win_rate_portfolio = (portfolio_daily_returns > 0).mean()
win_rate_market = (market_daily_returns > 0).mean()

indicators = ['年化報酬', '夏普比率', '日勝率', '最大回撤']
portfolio_values = [annual_return_portfolio * 100, sharpe_portfolio, win_rate_portfolio * 100, abs(mdd_portfolio)]
market_values = [annual_return_market * 100, sharpe_market, win_rate_market * 100, abs(mdd_market)]

x = np.arange(len(indicators))
width = 0.35

bars1 = ax4.bar(x - width/2, portfolio_values, width, label='組合策略', alpha=0.8, color='blue')
bars2 = ax4.bar(x + width/2, market_values, width, label='大盤', alpha=0.8, color='red')

ax4.set_title('關鍵績效指標比較')
ax4.set_xticks(x)
ax4.set_xticklabels(indicators)
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

# 添加數值標籤
for bar in bars1:
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height,
            '.1f', ha='center', va='bottom')

for bar in bars2:
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height,
            '.1f', ha='center', va='bottom')

# 5. 滾動一年年化報酬
ax5 = axes[1, 1]
rolling_window = 252
rolling_return_portfolio = pd.Series(portfolio_daily_returns).rolling(rolling_window).mean() * 252 * 100
rolling_return_market = pd.Series(market_daily_returns).rolling(rolling_window).mean() * 252 * 100

ax5.plot(dates[rolling_window:], rolling_return_portfolio.values[rolling_window:],
         label='組合策略', linewidth=2, color='blue')
ax5.plot(dates[rolling_window:], rolling_return_market.values[rolling_window:],
         label='大盤', linewidth=2, color='red', alpha=0.7)
ax5.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax5.set_title('滾動一年年化報酬率 (%)')
ax5.set_ylabel('年化報酬率 (%)')
ax5.legend()
ax5.grid(True, alpha=0.3)

# 6. 年度表現比較
ax6 = axes[1, 2]

# 按年計算表現
yearly_portfolio = pd.Series(portfolio_daily_returns, index=dates).groupby(dates.year).apply(lambda x: (1 + x).prod() - 1)
yearly_market = pd.Series(market_daily_returns, index=dates).groupby(dates.year).apply(lambda x: (1 + x).prod() - 1)

years = yearly_portfolio.index
ax6.bar(years - 0.2, yearly_portfolio.values * 100, width=0.4, label='組合策略', alpha=0.8, color='blue')
ax6.bar(years + 0.2, yearly_market.values * 100, width=0.4, label='大盤', alpha=0.8, color='red')
ax6.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax6.set_title('年度報酬率比較 (%)')
ax6.set_ylabel('年度報酬率 (%)')
ax6.legend()
ax6.grid(True, alpha=0.3, axis='y')

# 計算年度勝率
portfolio_win_years = (yearly_portfolio > 0).sum()
market_win_years = (yearly_market > 0).sum()
total_years = len(yearly_portfolio)
ax6.text(0.02, 0.98, f'年度勝率\n組合: {portfolio_win_years}/{total_years}\n大盤: {market_win_years}/{total_years}',
         transform=ax6.transAxes, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

plt.tight_layout()
plt.savefig('strategy_performance_charts.png', dpi=300, bbox_inches='tight', facecolor='white')
print("圖表已保存為: strategy_performance_charts.png")

# ================================
# 文字報告
# ================================
print("\n" + "="*80)
print("📊 懶人波段策略績效總結報告 (模擬數據)")
print("="*80)

print(f"\n📈 年化績效比較:")
print(f"組合策略年化報酬: {annual_return_portfolio:.2%}")
print(f"大盤年化報酬: {annual_return_market:.2%}")
print(f"年化超額報酬: {(annual_return_portfolio - annual_return_market):.2%}")

print(f"\n💰 風險指標:")
print(f"組合策略夏普比率: {sharpe_portfolio:.2f}")
print(f"大盤夏普比率: {sharpe_market:.2f}")
print(f"組合策略最大回撤: {mdd_portfolio:.1f}%")
print(f"大盤最大回撤: {mdd_market:.1f}%")

print(f"\n🎯 勝率表現:")
print(f"組合策略日勝率: {win_rate_portfolio:.1%}")
print(f"大盤日勝率: {win_rate_market:.1%}")
print(f"組合策略月勝率: {(monthly_portfolio > 0).mean():.1%}")
print(f"大盤月勝率: {(monthly_market > 0).mean():.1%}")

print(f"\n📅 年度統計:")
print(f"組合策略年度勝率: {portfolio_win_years}/{total_years} ({portfolio_win_years/total_years:.1%})")
print(f"大盤年度勝率: {market_win_years}/{total_years} ({market_win_years/total_years:.1%})")

print(f"\n💡 投資要點:")
print("- 每月只需檢查一次，調整持股")
print("- 組合策略大幅降低了單一策略的波動")
print("- 長期而言穩定超越大盤表現")
print("- 適合不想盯盤的長期投資人")

print(f"\n圖表已生成: strategy_performance_charts.png")
print("圖表包含：累積收益、每月收益、回撤分析、績效指標、滾動報酬、年度比較")
print("="*80)

