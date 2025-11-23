# lo2cin4bt 回測專案

[![Python Version](https://img.shields.io/badge/python-3.11.9-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📊 專案簡介

使用 `lo2cin4bt` 框架進行 SPY（S&P 500 ETF）技術分析策略回測。

**當前策略：** 20 日簡單移動平均線（SMA）交叉策略

## 🚀 快速開始

```powershell
# 安裝依賴
pip install numpy==1.26.4 pandas yfinance pyarrow numba llvmlite

# 執行回測
python demo_run.py

# 查看分析
python full_analysis.py
```

## 📈 回測績效

| 指標 | 數值 |
|------|------|
| 總報酬率 | 50.55% |
| 年化報酬率 | 4.71% |
| 最大回撤 | 40.09% |
| 勝率 | 42.31% |
| 盈虧比 | 2.72:1 |

**回測期間：** 2017-01-03 至 2025-11-21 (8.88 年)

## 📁 專案結構

```
sp_lab_v9_1.1/
├── lo2cin4bt-main/          # 回測框架
├── output/                  # 分析結果
├── demo_run.py              # 回測腳本
├── full_analysis.py         # 分析腳本
└── README.md                # 本文檔
```

## 📚 完整文檔

詳細文檔請參閱：[專案文檔](docs/backtest_project_documentation.md)

## 🎯 下一步

- [ ] 測試不同均線參數（10日、50日）
- [ ] 加入 RSI、MACD 指標
- [ ] 實作止損止盈機制
- [ ] 多標的回測（QQQ、^TWII）

## 👥 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

MIT License

---

**最後更新：** 2025-11-24
