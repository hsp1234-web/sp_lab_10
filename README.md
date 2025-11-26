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

## 💾 數據庫

### 期貨資料
本專案已整合 **DuckDB**，包含 1998-2024 年完整的台指期貨數據。

- **數據位置**：`data/taifex.db`
- **使用說明**：請參閱 [資料使用手冊](data/README.md)
- **功能**：
    - 支援高效查詢 27 年歷史數據
    - 已整合至 `lo2cin4bt` 框架 (選單選項 5)

### 選擇權資料庫 (New)
本專案已建立選擇權資料庫，包含 2001-2024 年完整的選擇權交易行情資料。

- **資料庫位置**：`data/taifex_options.db`
- **資料筆數**：約 3,080 萬筆
- **下載腳本**：`scripts/download_taifex_options.py` (下載原始 ZIP 檔案)
- **建置腳本**：`scripts/build_taifex_options_db.py` (匯入資料庫，含進度條)
- **使用說明**：請參閱 [資料使用手冊](data/README.md)
- **功能**：
    - 自動下載所有年份的選擇權年度資料 (ZIP 格式)
    - 自動建置 DuckDB 資料庫，支援高效查詢
    - 包含進度條顯示，處理過程清晰可見
    - 支援查詢所有選擇權商品 (TXO, TXO 等)

## 📁 專案結構

```
sp_lab_v10/
├── data/                           # 數據庫與說明
│   ├── taifex.db                   # DuckDB 期貨資料庫
│   ├── taifex_options.db           # DuckDB 選擇權資料庫
│   ├── taifex_options_raw/          # 選擇權原始資料 (ZIP)
│   └── README.md                   # 資料使用說明
├── lo2cin4bt-main/                 # 回測框架
├── scripts/                        # 工具腳本
│   ├── build_taifex_db.py          # 期貨資料庫建置腳本
│   ├── download_taifex_options.py  # 選擇權資料下載腳本
│   ├── build_taifex_options_db.py  # 選擇權資料庫建置腳本
│   └── check_options_db.py         # 選擇權資料庫檢查腳本
│   ├── verify_taifex_db.py         # 資料庫驗證腳本
│   └── run_quick_feedback.py       # 快速回測腳本
├── output/                         # 分析結果
├── config/                         # 設定檔
└── README.md                       # 本文檔
```

## 📚 完整文檔

詳細文檔請參閱：[專案文檔](docs/backtest_project_documentation.md)

## 🎯 下一步

- [x] 整合 DuckDB 台指期數據
- [x] 建立選擇權資料下載功能
- [x] 建立選擇權資料庫 (DuckDB)
- [ ] 整合選擇權資料到回測框架
- [ ] 測試不同均線參數（10日、50日）
- [ ] 加入 RSI、MACD 指標
- [ ] 實作止損止盈機制
- [ ] 多標的回測（QQQ、^TWII）

## 👥 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

MIT License

---

**最後更新：** 2025-11-26
