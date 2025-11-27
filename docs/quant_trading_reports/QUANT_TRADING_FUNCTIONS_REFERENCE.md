# 🔄 量化交易專案功能參考指南

## 📋 專案概述

這是一個完整的台灣期貨量化交易系統，整合了多種數據源、策略框架、風險管理系統和分析工具。專案涵蓋從數據獲取到策略執行的完整量化交易流程。

**專案代號**: SP Lab V10
**主要技術**: Python, DuckDB, Pandas, NumPy, Plotly
**數據來源**: 台指期, 選擇權, PCR比率, 法人數據, 宏觀指標

---

## 🗂️ 功能分類總覽

### 1. 📊 數據處理與管理
### 2. 📈 量化策略系統
### 3. 🔬 回測與分析框架
### 4. ⚠️ 風險管理系統
### 5. 📊 績效分析與可視化
### 6. 🛠️ 開發工具與腳本
### 7. 🧪 測試與驗證框架
### 8. 📚 文檔與報告系統

---

## 📊 1. 數據處理與管理功能

### 數據獲取與下載
| 功能名稱 | 檔案位置 | 功能描述 | 參數說明 |
|---------|---------|---------|---------|
| **台灣期貨官方數據下載器** | `scripts/taifex_official_downloader.py` | 下載PCR比率、選擇權數據、三大法人資料 | 日期範圍、數據類型 |
| **FinMind API整合** | `scripts/build_finmind_db.py` | 獲取免費金融數據API數據 | API金鑰、數據類型 |
| **台指期歷史數據建置** | `scripts/build_taifex_db.py` | 建立台指期歷史資料庫 | 數據源路徑、時間範圍 |
| **選擇權數據下載** | `scripts/download_taifex_options.py` | 下載選擇權歷史數據 | 到期日、履約價範圍 |

### 數據庫管理
| 功能名稱 | 檔案位置 | 功能描述 | 主要表格 |
|---------|---------|---------|----------|
| **DuckDB資料庫建置器** | `scripts/build_taifex_official_db.py` | 統一管理多來源金融數據 | pcr_data, options_delta, futures_daily |
| **數據庫驗證工具** | `scripts/verify_taifex_db.py` | 檢查數據完整性和品質 | 數據統計、異常檢測 |
| **數據遷移工具** | `scripts/manage_options_db.py` | 處理數據格式轉換和遷移 | 欄位映射、數據清理 |

### 數據處理與整合
| 功能名稱 | 檔案位置 | 功能描述 | 輸入/輸出 |
|---------|---------|---------|----------|
| **數據載入器** | `src/data_loader.py` | 統一數據載入接口 | 多格式數據 → 標準化DataFrame |
| **台指期數據整合** | `src/taifex_data_integration.py` | 整合多來源台指期數據 | 合併數據、去重處理 |
| **NY Fed數據整合** | `src/ny_fed_integration.py` | 整合宏觀經濟指標 | SOFR、VIX、FED數據 |

---

## 📈 2. 量化策略系統

### 核心策略框架
| 策略名稱 | 檔案位置 | 核心邏輯 | 適用場景 |
|---------|---------|---------|----------|
| **RORO動態風險管理策略** | `roro_strategy_optimized.py` | 熊市保護第一，動態調整倉位 | 全市場環境，特別適合波段操作 |
| **整合量化策略** | `src/integrated_strategy.py` | Chandelier趨勢 + PCR情緒 + 選擇權保護 | 多頭市場，注重風險控制 |
| **法人買賣超策略** | 腳本整合 | 三大法人動向跟隨 | 趨勢確認，保守投資 |
| **PCR比率策略** | 腳本整合 | 市場恐慌指標 | 反向操作，波段獲利 |

### 策略元件
| 元件名稱 | 檔案位置 | 功能描述 | 應用場景 |
|---------|---------|---------|----------|
| **市場指標計算器** | `src/market_indicators.py` | 計算技術指標和市場寬度指標 | 策略信號生成 |
| **系統壓力指數** | `src/pressure_index.py` | 計算市場壓力指數 | 風險評估 |
| **RORO引擎** | `src/roro_engine.py` | 動態風險開啟/關閉邏輯 | 倉位動態調整 |
| **信號生成器** | `src/roro_signal_generator.py` | 策略信號生成與驗證 | 交易決策 |

### 選擇權策略 (開發中)
| 策略類型 | 開發狀態 | 核心邏輯 | 預期效益 |
|---------|---------|---------|----------|
| **保護性買權** | 計劃中 | PCR恐慌時期 + 買權保護 | 下跌保護，提升夏普比率 |
| **覆蓋性賣權** | 計劃中 | 多頭持有 + 賣權收入 | 穩定收益，降低波動 |
| **價差策略** | 計劃中 | 多空組合對沖 | 波動率交易，低成本對沖 |

---

## 🔬 3. 回測與分析框架

### 回測引擎
| 功能名稱 | 檔案位置 | 功能描述 | 輸出格式 |
|---------|---------|---------|----------|
| **Chandelier策略回測** | `scripts/run_chandelier_backtest.py` | ATR動態停損策略回測 | 信號CSV、績效JSON |
| **雙均線策略回測** | `scripts/run_dual_ma_backtest.py` | 移動平均交叉策略 | 交易記錄、統計分析 |
| **MAE/MFE分析器** | `output/Chandelier_MAE_MFE/` | 進出場時機最佳化分析 | HTML圖表、統計報告 |

### 策略比較與分析
| 功能名稱 | 檔案位置 | 功能描述 | 比較維度 |
|---------|---------|---------|----------|
| **綜合策略比較** | `scripts/comprehensive_strategy_comparison.py` | 多策略績效比較 | 收益、回撤、勝率、夏普比率 |
| **簡單策略比較** | `scripts/simple_strategy_comparison.py` | 基礎策略對比分析 | 月度績效、風險指標 |

### 回測結果分析
| 分析類型 | 輸出檔案 | 分析內容 | 可視化 |
|---------|---------|---------|--------|
| **績效統計** | `output/strategy_comparison_results.csv` | 月度收益、勝率、持有期 | ✅ |
| **風險分析** | `output/roro_vs_buyhold_comparison_*.json` | 最大回撤、波動率、VaR | ✅ |
| **交易記錄** | `output/chandelier_backtest_signals.csv` | 每筆交易詳情 | ✅ |

---

## ⚠️ 4. 風險管理系統

### 風險控制機制
| 機制名稱 | 實作位置 | 控制邏輯 | 觸發條件 |
|---------|---------|---------|----------|
| **單筆損失限制** | `roro_strategy_optimized.py` | 單筆最大虧損10% | 價格波動超過閾值 |
| **時間止損** | 所有策略 | 最大持有60天 | 持有時間超過限制 |
| **月度風險預算** | RORO策略 | 月度虧損控制5% | 月度累計損失觸發 |
| **熊市保護** | RORO引擎 | 強熊市自動減倉 | 市場狀態識別 |

### 風險評估工具
| 工具名稱 | 檔案位置 | 評估內容 | 報告格式 |
|---------|---------|---------|----------|
| **VaR計算** | 策略框架中 | 價值風險評估 | 數值指標 |
| **壓力測試** | 回測系統 | 極端市場條件測試 | 情境分析 |
| **相關性分析** | 分析腳本 | 策略間相關性 | 相關矩陣 |

---

## 📊 5. 績效分析與可視化

### 績效指標計算
| 指標名稱 | 計算位置 | 公式說明 | 解釋 |
|---------|---------|---------|------|
| **年化收益** | 所有回測 | (總收益/年數) | 年度化報酬率 |
| **夏普比率** | 策略比較 | (年化收益-無風險利率)/波動率 | 風險調整後收益 |
| **最大回撤** | 風險分析 | 最高點到最低點跌幅 | 最大虧損幅度 |
| **勝率** | 交易統計 | 盈利交易數/總交易數 | 交易成功率 |

### 可視化功能
| 圖表類型 | 檔案位置 | 應用場景 | 輸出格式 |
|---------|---------|---------|----------|
| **策略比較圖** | `output/roro_vs_buyhold_comparison_*.png` | 多策略績效對比 | PNG圖片 |
| **MAE/MFE分析圖** | `output/Chandelier_MAE_MFE/maemfe_charts.html` | 進出場時機分析 | 互動式HTML |
| **回測結果圖表** | 各回測腳本 | 收益曲線、回撤圖 | 多格式支援 |

### 報告生成
| 報告類型 | 生成位置 | 包含內容 | 更新頻率 |
|---------|---------|---------|----------|
| **策略績效報告** | 回測完成時 | 收益、風險、交易統計 | 每次回測 |
| **比較分析報告** | 比較腳本 | 多策略對比 | 定期分析 |
| **風險評估報告** | 風險分析 | VaR、壓力測試 | 月度評估 |

---

## 🛠️ 6. 開發工具與腳本

### 數據處理工具
| 工具名稱 | 檔案位置 | 主要功能 | 使用場景 |
|---------|---------|---------|----------|
| **編碼轉換器** | `utils/convert_encoding.py` | UTF-8編碼處理 | 文檔處理 |
| **日誌建立器** | `utils/create_log.py` | 結構化日誌生成 | 開發記錄 |
| **文檔轉換器** | `scripts/docx_to_txt_converter.py` | DOCX轉TXT | 研究資料處理 |

### 系統維護工具
| 工具名稱 | 檔案位置 | 主要功能 | 檢查項目 |
|---------|---------|---------|----------|
| **系統資源監控** | `scripts/check_system_resources.py` | CPU、記憶體、磁碟監控 | 效能優化 |
| **數據品質檢查** | `scripts/check_data_quality.py` | 數據完整性驗證 | 數據清理 |
| **資料庫檢查** | `scripts/check_db.py` | 資料庫連接和查詢測試 | 系統診斷 |

### 自動化腳本
| 腳本類型 | 主要腳本 | 功能描述 | 執行頻率 |
|---------|---------|---------|----------|
| **數據更新** | `scripts/taifex_official_update.py` | 自動更新最新數據 | 每日/每周 |
| **回測執行** | 多個run_*.py腳本 | 批量執行策略回測 | 按需求 |
| **報告生成** | 分析腳本 | 自動生成績效報告 | 回測完成後 |

---

## 🧪 7. 測試與驗證框架

### 單元測試
| 測試類型 | 檔案位置 | 測試內容 | 覆蓋範圍 |
|---------|---------|---------|----------|
| **數據載入測試** | `tests/test_data_loader.py` | 數據載入功能驗證 | 多格式支援 |
| **策略信號測試** | `tests/test_chandelier_signals.py` | 技術指標計算正確性 | 信號生成邏輯 |
| **API整合測試** | `tests/test_api.py` | 外部API連接和數據獲取 | FinMind, FRED |
| **雙均線策略測試** | `tests/test_dual_ma_strategy.py` | 均線交叉策略邏輯 | 買賣信號 |

### 整合測試
| 測試名稱 | 檔案位置 | 測試流程 | 驗證項目 |
|---------|---------|---------|----------|
| **DuckDB載入器測試** | `tests/test_duckdb_loader.py` | 資料庫查詢和數據處理 | 性能和正確性 |
| **FinMind API測試** | `tests/test_finmind.py` | 免費金融數據API功能 | 數據品質和完整性 |
| **NY Fed整合測試** | `tests/test_ny_fed_integration.py` | 宏觀經濟數據整合 | 數據同步 |

### 驗證工具
| 工具名稱 | 檔案位置 | 驗證內容 | 應用場景 |
|---------|---------|---------|----------|
| **POC驗證器** | `scripts/verify_poc.py` | 概念驗證結果確認 | 新功能測試 |
| **數據驗證器** | `scripts/verify_v2.py` | 數據處理結果驗證 | ETL流程檢查 |

---

## 📚 8. 文檔與報告系統

### 專案文檔
| 文檔類型 | 檔案位置 | 主要內容 | 更新頻率 |
|---------|---------|---------|----------|
| **專案總覽** | `PROJECT_STRUCTURE_ORGANIZATION.md` | 架構說明和使用指南 | 結構變更時 |
| **策略指南** | `RORO_STRATEGY_GUIDE.md` | RORO策略詳細說明 | 策略更新時 |
| **開發計劃** | `QUANT_STRATEGY_DEVELOPMENT_PLAN.md` | 未來開發路線圖 | 季度檢討 |

### 量化交易報告系統
| 報告分類 | 目錄位置 | 包含內容 | 管理規範 |
|---------|---------|---------|----------|
| **策略報告** | `docs/quant_trading_reports/strategy_reports/` | 策略設計、參數說明 | 策略變更時更新 |
| **回測報告** | `docs/quant_trading_reports/backtest_reports/` | 回測結果、績效分析 | 每次回測生成 |
| **風險報告** | `docs/quant_trading_reports/risk_reports/` | 風險評估、VaR分析 | 月度更新 |
| **績效報告** | `docs/quant_trading_reports/performance_reports/` | 收益分析、歸因分析 | 季度/年度 |

### 開發日誌系統
| 日誌類型 | 存放位置 | 記錄內容 | 命名規範 |
|---------|---------|---------|----------|
| **開發日誌** | `docs/logs/YYYY-MM/` | 功能開發、問題解決 | `YYYY-MM-DD_HH-MM_brief-description.md` |
| **測試日誌** | `output/logs/backtest_logs/` | 回測過程和結果 | 自動生成 |
| **系統日誌** | `output/logs/` | 系統運行狀態 | 運行時生成 |

---

## 🚀 快速入門指南

### 新使用者
1. **閱讀總覽**: 先看 `PROJECT_STRUCTURE_ORGANIZATION.md`
2. **了解架構**: 查看 `docs/quant_trading_reports/README.md`
3. **運行範例**: 執行 `scripts/simple_strategy_comparison.py`
4. **查看結果**: 檢查 `output/strategy_comparison_results.csv`

### 開發者入門
1. **環境設定**: 確認Python 3.11+, 安裝requirements.txt
2. **數據準備**: 運行 `scripts/build_taifex_db.py`
3. **策略開發**: 參考 `src/integrated_strategy.py`
4. **測試驗證**: 使用 `tests/` 下的測試腳本

### 常用命令
```bash
# 數據更新
python scripts/taifex_official_downloader.py

# 策略回測
python scripts/run_chandelier_backtest.py

# 策略比較
python scripts/comprehensive_strategy_comparison.py

# 結果查看
python scripts/view_results.py
```

---

## 📞 技術支援

### 問題分類
- **數據問題**: 檢查 `data/README.md` 和相關建置腳本
- **策略問題**: 參考策略說明文檔和測試案例
- **技術問題**: 查看開發日誌和錯誤處理機制
- **性能問題**: 使用系統資源監控工具診斷

### 聯絡方式
- **文檔中心**: `docs/` 目錄
- **問題排查**: `docs/logs/` 開發記錄
- **功能說明**: `docs/quant_trading_reports/`

---

*最後更新: 2025年11月27日 | 版本: SP Lab V10.1 | 作者: AI Assistant*

---

**附錄: 關鍵檔案路徑總覽**

```
專案根目錄/
├── src/                          # 核心策略程式碼
│   ├── integrated_strategy.py     # 整合量化策略 ⭐⭐⭐
│   ├── roro_strategy_optimized.py # RORO優化策略 ⭐⭐⭐
│   └── market_indicators.py       # 市場指標計算 ⭐⭐
├── scripts/                       # 工具腳本
│   ├── run_chandelier_backtest.py # Chandelier回測 ⭐⭐
│   ├── comprehensive_strategy_comparison.py # 策略比較 ⭐⭐
│   └── taifex_official_downloader.py # 數據下載 ⭐⭐
├── data/                          # 數據檔案
│   ├── taifex.db                  # 台指期歷史數據 ⭐⭐⭐
│   ├── taifex_options.db          # 選擇權數據 ⭐⭐⭐
│   └── taifex_official.db         # 官方數據 ⭐⭐
├── output/                        # 分析結果
│   ├── strategy_comparison_results.csv # 策略比較 ⭐⭐⭐
│   └── Chandelier_MAE_MFE/       # MAE/MFE分析 ⭐⭐
├── docs/                          # 文檔系統
│   ├── quant_trading_reports/     # 量化交易報告 ⭐⭐⭐
│   └── logs/                      # 開發日誌 ⭐⭐
└── tests/                         # 測試框架 ⭐⭐
```

**圖例**: ⭐⭐⭐ = 核心功能 | ⭐⭐ = 重要功能 | ⭐ = 輔助功能


