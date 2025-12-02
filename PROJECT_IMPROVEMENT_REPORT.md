# 專案改善報告 (Project Improvement Report)

> 產生日期：2025-12-02
> 專案：sp_lab_v10/zbo - 量化交易因子化框架

---

## 📋 執行摘要

本報告分析了專案目前的結構問題，並提供整合建議，以支援量化交易因子化的核心目標。

---

## ✅ 已完成項目

### 中文檔名重命名

| 原檔名 | 新檔名 | 內容摘要 |
|--------|--------|---------|
| `我先來討論一下...1b_4b_8b_270m.md` | `hierarchical_model_architecture.md` | 階層式模型分工策略 |
| `我們如果不使用預測...逐筆.md` | `tick_data_microstructure_analysis.md` | 逐筆交易微觀結構分析 |
| `那我們要走進設計資料庫...JSON失敗率.md` | `stepwise_ai_query_design.md` | 逐步AI查詢設計 |

---

## 📊 hybrid_qlib_framework 專案進度分析

### 🎯 專案目標

建立一個**因子驅動**的量化交易系統，使用 Qlib 框架進行因子計算與回測，支援：
- 低記憶體環境（WSL < 600MB）
- 本地開發 + Colab 完整回測

### ✅ 已完成模組

| 模組 | 檔案 | 完成度 | 說明 |
|------|------|--------|------|
| **開發計劃** | `DEVELOPMENT_PLAN.md` | ✅ 100% | 完整的開發藍圖 |
| **本地開發指南** | `LOCAL_DEVELOPMENT_GUIDE.md` | ✅ 100% | WSL 環境設定指南 |
| **CLI 主程式** | `main.py` | ✅ 90% | 支援 prepare-data, convert, backtest |
| **資料轉換器** | `src/data_converter.py` | ✅ 85% | DuckDB streaming + Qlib 格式轉換 |
| **Alpha 因子計算** | `src/alpha_factors.py` | ✅ 95% | Alpha158/360 因子 + 評估器 |
| **資料檢查** | `check_data.py` | ✅ 100% | 資料庫結構驗證 |
| **測試程式** | `test_alpha_factors.py` | ✅ 100% | 因子計算單元測試 |
| **設定檔** | `configs/qlib_example_config.yaml` | ✅ 100% | Qlib 範例設定 |

### ⏳ 待完成模組

| 模組 | 優先級 | 預估時間 | 說明 |
|------|--------|---------|------|
| **回測引擎** | 🔴 高 | 3-4 小時 | `src/model_runner.py` |
| **完整整合測試** | 🔴 高 | 1-2 小時 | Colab 端對端測試 |
| **資料準備腳本** | 🟡 中 | 1 小時 | 從 taifex.db 提取測試資料 |
| **績效報告產生** | 🟡 中 | 2 小時 | IC/Sharpe/MDD 報告 |

---

## 🔍 現況問題分析

### 目錄結構問題

```
sp_lab_v10/zbo/
├── 🔴 scripts/ + data_scripts/    → 功能重疊，需合併
├── 🔴 tools/ + utils/              → 功能重疊，需合併
├── 🟡 strategies/ 檔案分散         → 需按策略類型分類
├── 🟡 plan/ + docs/                → 可考慮合併
├── 🟢 hybrid_qlib_framework/       → 獨立完整框架 ✅
├── 🟢 src/                         → 核心程式碼 ✅
└── 🔴 archive/src/ 舊版程式碼      → 需評估清理
```

### 詳細問題列表

| 問題類別 | 說明 | 嚴重程度 |
|---------|------|---------|
| **目錄重複** | `scripts/` vs `data_scripts/`、`tools/` vs `utils/` 功能重疊 | ⭐⭐⭐⭐ |
| **檔案散落** | `Ollama整理資料v1.ipynb` 在根目錄 | ⭐⭐⭐ |
| **研究文件重複** | `drive-download-*/` 和 `research/converted_texts_archive/` 重複 | ⭐⭐⭐ |
| **舊版程式碼** | `archive/src/` 包含大量舊版檔案需檢視 | ⭐⭐⭐ |
| **重複檔案** | `config/AGENTS.md` 與根目錄重複 | ⭐⭐ |
| **外部資料夾重複** | `lo2cin4bt-main` 和 `reference/lo2cin4bt-main` | ⭐⭐ |

---

## 🔧 整合建議

### 方案 A：以 hybrid_qlib_framework 為核心整合（推薦）

```
sp_lab_v10/zbo/
├── hybrid_qlib_framework/     # 🎯 主要因子化框架
│   ├── src/                   # 核心模組
│   │   ├── alpha_factors.py   # Alpha 因子計算
│   │   ├── data_converter.py  # 資料轉換
│   │   └── model_runner.py    # 回測引擎（待開發）
│   ├── scripts/               # 輔助腳本
│   ├── tests/                 # 測試程式
│   └── configs/               # 設定檔
│
├── src/                       # 現有策略模組（維持）
│   ├── integrated_strategy.py
│   ├── roro_engine.py
│   └── taifex_data_integration.py
│
├── scripts/                   # 合併後的工具腳本
│   ├── data/                  # 資料處理（合併 data_scripts/）
│   ├── backtest/              # 回測相關
│   ├── check/                 # 驗證腳本
│   └── maintenance/           # 維護腳本
│
├── utils/                     # 合併後的工具函數（合併 tools/）
│   ├── visualization/
│   └── data/
│
├── strategies/                # 策略分類整理
│   ├── finlab/
│   ├── taifex/
│   ├── roro/
│   └── contrarian/
│
└── docs/                      # 文件整合
    ├── logs/
    ├── plans/                 # 從 plan/ 移入
    └── guides/
```

**優點：**
- 以因子化框架為核心，結構清晰
- 現有程式碼可逐步遷移
- 避免功能重複

**缺點：**
- 需要較多時間整合
- 可能影響現有程式碼

### 方案 B：維持雙軌並行

維持 `hybrid_qlib_framework/` 獨立，同時整理其他目錄：

| 優點 | 缺點 |
|------|------|
| hybrid_qlib_framework 保持獨立完整 | 部分功能重複 |
| 現有程式碼不受影響 | 需維護兩套程式碼 |
| 可逐步遷移 | 長期維護成本較高 |

---

## 🚀 建議執行順序

### 階段 1：基礎清理（30 分鐘）

```
✅ 已完成：
   → 中文檔名改英文

⏳ 待執行：
   → 刪除 temp/ 目錄
   → 刪除 config/AGENTS.md（重複）
   → 移動 Ollama整理資料v1.ipynb 到 notebooks/
```

### 階段 2：完成 hybrid_qlib_framework（3-4 小時）

```
優先任務：
   → 開發 src/model_runner.py（回測引擎）
   → 實作 scripts/prepare_test_data.py
   → 完成 Colab 整合測試
```

### 階段 3：目錄整合（1-2 小時）

```
執行任務：
   → 合併 scripts/ + data_scripts/
   → 合併 tools/ + utils/
   → 整理 strategies/ 分類
```

### 階段 4：舊版清理（1 小時）

```
評估任務：
   → 檢視 archive/src/ 是否需保留
   → 刪除 reference/lo2cin4bt-main（重複）
   → 評估 drive-download-*/ 是否需保留
```

---

## 📁 建議的最終專案結構

```
sp_lab_v10/zbo/
├── 📄 AGENTS.md                    # AI 協作指南
├── 📄 README.md                    # 專案說明
├── 📄 PROJECT_IMPROVEMENT_REPORT.md # 本報告
├── 📄 main.py                      # 主程式入口
│
├── 📁 hybrid_qlib_framework/       # 因子化框架（核心）
│   ├── src/
│   ├── scripts/
│   ├── tests/
│   ├── configs/
│   └── docs/
│
├── 📁 src/                         # 策略核心程式碼
│   ├── integrated_strategy.py
│   ├── roro_engine.py
│   └── taifex_data_integration.py
│
├── 📁 strategies/                  # 策略模組（需分類）
│   ├── finlab/
│   ├── taifex/
│   ├── roro/
│   └── contrarian/
│
├── 📁 scripts/                     # 工具腳本（需合併 data_scripts/）
│   ├── backtest/
│   ├── data/
│   ├── check/
│   └── maintenance/
│
├── 📁 utils/                       # 通用工具（需合併 tools/）
│   ├── visualization/
│   └── data/
│
├── 📁 config/                      # 設定檔
│
├── 📁 data/                        # 資料目錄
│
├── 📁 notebooks/                   # Jupyter 筆記本
│
├── 📁 docs/                        # 文件
│   ├── logs/
│   ├── plans/
│   └── guides/
│
├── 📁 research/                    # 研究資料
│
├── 📁 tests/                       # 測試程式
│
├── 📁 output/                      # 產出目錄
│
├── 📁 archive/                     # 封存目錄
│
├── 📁 colab_env/                   # Colab 環境
│
└── 📁 lo2cin4bt-main/              # 外部參考
```

---

## ❓ 待確認事項

1. **`hybrid_qlib_framework` 優先級**：是否優先完成這個框架？
2. **整合方案選擇**：選擇方案 A（全面整合）還是方案 B（雙軌並行）？
3. **舊版程式碼**：`archive/src/` 是否可以刪除？
4. **研究文件**：`drive-download-*/` 原始 docx 是否需保留？

---

## 📝 變更日誌

| 日期 | 變更內容 |
|------|---------|
| 2025-12-02 | 初版報告產生 |
| 2025-12-02 | 完成 plan/ 目錄中文檔名重命名 |
| 2025-12-02 | 更新 README.md 和 AGENTS.md |
| 2025-12-02 | 創建開發日誌記錄變更 |

---

*本報告由 AI 助手產生，供專案整理參考使用。*

