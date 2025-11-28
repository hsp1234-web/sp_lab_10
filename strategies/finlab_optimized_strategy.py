import finlab
from finlab import data
import pandas as pd
import numpy as np

print("=== 優化版：高股息+低波動+月營收濾網策略 ===")

# 登入
api_key = "wnFW0KT5etgpNr6IKZI05kNyRrMQDrIeoaplJBlRc+Twz+RWciylMCjm0jvtL0n5#free"
finlab.login(api_key)

# 1. 數據獲取
close = data.get('price:收盤價')
rev_growth = data.get('monthly_revenue:去年同月增減(%)')
yield_ratio = data.get('price_earning_ratio:殖利率')
vol = data.get('price:成交股數')

print("數據獲取完成")

# 2. 策略邏輯 (更穩健的版本)
# A. 高殖利率：殖利率 > 4% (提供下檔保護)
# B. 低波動：過去60天股價波動率排名最低的前50% (抗跌)
# C. 營收成長：營收年增率 > 0 (確保公司沒有衰退)
# D. 流動性：成交量 > 500張

# 計算波動率
returns = close.pct_change()
volatility = returns.rolling(60).std()
vol_rank = volatility.rank(axis=1, pct=True) # 百分比排名

# 條件
cond_yield = yield_ratio > 4
cond_low_vol = vol_rank < 0.5  # 波動率在前50%低
cond_growth = rev_growth > 0
cond_liquidity = vol.rolling(5).mean() > 500000

# 綜合條件
position = cond_yield & cond_low_vol & cond_growth & cond_liquidity

# 選股優化：根據殖利率排序，選前10檔
rank_yield = yield_ratio.rank(axis=1, ascending=False)
position = position & (rank_yield <= 10)

# 3. 回測
print("開始回測...")
# 每月換股
position = position.resample('MS').first()

# 對齊數據
position_daily = position.reindex(close.index, method='ffill')
strategy_returns = (position_daily.shift(1) * returns).mean(axis=1)

# 考慮交易成本 (0.2%每次換股)
turnover = position_daily.diff().abs().sum(axis=1).mean() # 平均換手率
cost_impact = turnover * 0.002 / 20 # 簡單攤提
strategy_returns = strategy_returns - cost_impact

# 4. 績效
annual_return = strategy_returns.mean() * 252
annual_std = strategy_returns.std() * np.sqrt(252)
sharpe = annual_return / annual_std if annual_std > 0 else 0
cum_ret = (1 + strategy_returns).cumprod()
mdd = (cum_ret / cum_ret.cummax() - 1).min()

print(f"\n=== 優化策略績效 (高股息低波動) ===")
print(f"年化報酬率: {annual_return:.2%}")
print(f"年化波動率: {annual_std:.2%}")
print(f"夏普比率: {sharpe:.2f}")
print(f"最大回撤: {mdd:.2%}")
print(f"平均持倉數: {position.sum(axis=1).mean():.1f}")

# 5. 顯示最新選股
latest = position.iloc[-1]
stocks = latest[latest].index.tolist()
print(f"\n最新選股 ({position.index[-1].date()}): {stocks}")


