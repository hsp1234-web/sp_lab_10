# 台指期市場月度持有策略 (帶SMA濾網) 回測報告

這份報告總結了在台指期 (TX) 市場上，執行帶有 SMA 濾網的「月度持有」策略的回測績效。

## 績效摘要

| params                                                                                                                                                                    |   total_return |   sharpe_ratio |   max_drawdown |   trade_count |
|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------:|---------------:|---------------:|--------------:|
| {"entry": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 100}}, "exit": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 100}}} |    -0.00946752 |      0.0191212 |     -0.0242481 |           179 |
| {"entry": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 100}}, "exit": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 150}}} |    -0.00946752 |      0.0191212 |     -0.0242481 |           179 |
| {"entry": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 100}}, "exit": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 200}}} |    -0.00946752 |      0.0191212 |     -0.0242481 |           179 |
| {"entry": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 150}}, "exit": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 100}}} |    -0.00946752 |      0.0191212 |     -0.0242481 |           179 |
| {"entry": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 150}}, "exit": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 150}}} |    -0.00946752 |      0.0191212 |     -0.0242481 |           179 |
| {"entry": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 150}}, "exit": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 200}}} |    -0.00946752 |      0.0191212 |     -0.0242481 |           179 |
| {"entry": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 200}}, "exit": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 100}}} |    -0.00952198 |      0.0191156 |     -0.0242494 |           178 |
| {"entry": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 200}}, "exit": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 150}}} |    -0.00952198 |      0.0191156 |     -0.0242494 |           178 |
| {"entry": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 200}}, "exit": {"indicator_type": "MonthlyBuyHoldWithSMA", "params": {"sma_period": 200}}} |    -0.00952198 |      0.0191156 |     -0.0242494 |           178 |

## 實驗設定

```json
{
  "job_name": "TAIFEX_Monthly_BuyHold_With_SMA_Filter_Test",
  "data": {
    "db_path": "data/finmind.db",
    "symbol": "TX",
    "start_date": "2010-01-01",
    "end_date": "2024-12-31",
    "frequency": "1d"
  },
  "engine": {
    "db_output_path": "output/results/quick_feedback.db"
  },
  "strategy": {
    "name": "MonthlyBuyHoldWithSMA",
    "params_range": {
      "sma_period": [100, 150, 200]
    }
  },
  "trading": {
    "initial_capital": 1000000,
    "trade_unit": 1,
    "transaction_cost": 0.0005,
    "slippage": 0.0005
  }
}
```
