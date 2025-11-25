# SPY 市場月度持有策略回測報告

這份報告總結了在 SPY 市場上，執行基礎的「月度持有」策略（無 SMA 濾網）的回測績效。

## 績效摘要

| params                                                                                                                          |   total_return |   sharpe_ratio |   max_drawdown |   trade_count |
|:--------------------------------------------------------------------------------------------------------------------------------|---------------:|---------------:|---------------:|--------------:|
| {"entry": {"indicator_type": "MonthlyBuyAndHold", "params": {}}, "exit": {"indicator_type": "MonthlyBuyAndHold", "params": {}}} |    0.000428403 |       0.576265 |   -0.000125071 |           179 |

## 實驗設定

```json
{
  "job_name": "SPY_Monthly_BuyAndHold_Baseline",
  "data": {
    "db_path": "data/yfinance.db",
    "symbol": "SPY",
    "start_date": "2010-01-01",
    "end_date": "2024-12-31",
    "frequency": "1d"
  },
  "engine": {
    "db_output_path": "output/results/quick_feedback.db"
  },
  "strategy": {
    "name": "MonthlyBuyAndHold",
    "params_range": {}
  },
  "trading": {
    "initial_capital": 1000000,
    "trade_unit": 1,
    "transaction_cost": 0.0005,
    "slippage": 0.0005
  }
}
```
