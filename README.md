# SP Lab v10 - 量化交易研究平台

[![Python Version](https://img.shields.io/badge/python-3.11.9-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📊 專案簡介

**SP Lab v10** 是一個整合性的量化交易研究平台，專注於台灣期貨與選擇權市場的量化策略開發。平台整合了多個子專案，提供了從數據獲取、因子計算、策略回測到績效分析的完整量化交易研究流程。

### 🎯 核心功能

- **Alpha 因子計算**：自定義技術指標與統計因子計算
- **Qlib 量化框架整合**：基於微軟 Qlib 的標準化回測流程
- **台期貨數據處理**：完整的台灣期貨、選擇權數據庫管理
- **因子評估系統**：IC 計算、分組回報分析、因子穩定性測試
- **多策略框架**：支援技術分析、統計套利等多種策略類型

## 🚀 快速開始

### 本地開發環境設置

```bash
# 1. 安裝 Python 依賴
pip install -r requirements.txt

# 2. 初始化數據庫
python scripts/build_taifex_db.py

# 3. 執行因子測試
cd hybrid_qlib_framework
python test_factor_evaluation.py
```

### Google Colab 開發環境

```python
# 在 Colab 中克隆並設置
!git clone https://github.com/your-repo/sp_lab_v10.git
!cd sp_lab_v10/hybrid_qlib_framework
!pip install -r requirements.txt
```

## 📁 專案結構總覽

```
sp_lab_v10/
├── 📁 hybrid_qlib_framework/        # 🧠 Alpha 因子計算與 Qlib 整合
│   ├── src/                         # 因子計算核心代碼
│   ├── tests/                       # 因子測試
│   └── docs/                        # 因子計算文檔
├── 📁 src/                          # 🔧 主專案核心代碼
│   ├── integrated_strategy.py       # 整合策略
│   └── taifex_data_integration.py   # 台期貨數據整合
├── 📁 scripts/                      # 🛠️ 工具腳本
│   ├── build_taifex_db.py           # 期貨資料庫建置
│   ├── download_taifex_options.py   # 選擇權資料下載
│   └── verify_taifex_db.py          # 資料庫驗證
├── 📁 data/                         # 💾 數據管理
│   ├── taifex.db                    # 台指期貨數據庫
│   ├── taifex_options.db            # 選擇權數據庫
│   ├── raw/                         # 原始數據
│   └── processed/                   # 處理後數據
├── 📁 output/                       # 📊 輸出結果
│   ├── results/                     # 回測結果
│   ├── logs/                        # 執行日誌
│   └── archive/                     # 歷史檔案
├── 📁 docs/                         # 📚 文檔系統
│   ├── logs/                        # 開發日誌
│   ├── quant_trading_reports/       # 量化報告
│   └── README.md                    # 文檔說明
├── 📁 notebooks/                    # 📓 Jupyter 筆記本
├── 📁 research/                     # 🔬 研究資料
├── 📁 config/                       # ⚙️ 設定檔案
├── 📁 tests/                        # ✅ 測試套件
├── 📁 utils/                        # 🔧 工具函數
├── 📁 strategies/                   # 📈 策略實現
├── 📁 reference/                    # 📖 參考專案
│   └── lo2cin4bt-main/              # 回測框架參考
├── AGENTS.md                        # 🤖 AI 代理指南
└── README.md                        # 📖 本文件
```

## 🔍 各資料夾功能說明

### 🧠 `hybrid_qlib_framework/` - Alpha 因子計算引擎

專門處理量化因子計算的子專案，整合微軟 Qlib 框架。

**主要功能：**
- 自定義 Alpha 因子計算（趨勢、動量、波動性、成交量等）
- 因子評估系統（IC 計算、分組回報分析）
- Qlib 回測框架整合
- 台期貨市場因子優化

**快速開始：**
```bash
cd hybrid_qlib_framework
python test_factor_evaluation.py  # 測試因子功能
```

### 🔧 `src/` - 主專案核心代碼

平台的核心業務邏輯實現。

- `integrated_strategy.py`：整合多種交易策略
- `taifex_data_integration.py`：台期貨數據整合處理

### 🛠️ `scripts/` - 工具腳本

各種實用工具腳本的集合。

**核心腳本：**
- `build_taifex_db.py`：建置台指期貨數據庫
- `download_taifex_options.py`：下載選擇權數據
- `build_taifex_options_db.py`：建置選擇權數據庫

### 💾 `data/` - 數據管理中心

統一的數據存儲和管理系統。

**數據庫內容：**
- `taifex.db`：台指期貨數據（1998-2024）
- `taifex_options.db`：選擇權數據（2001-2024，約3千萬筆）
- `raw/`：原始數據存儲
- `processed/`：處理後的數據

### 📊 `output/` - 輸出結果管理

所有自動生成的結果統一存放。

- `results/`：回測結果、績效報表
- `logs/`：系統執行日誌
- `archive/`：歷史檔案備份

### 📚 `docs/` - 文檔系統

完整的專案文檔和開發記錄。

- `logs/`：結構化開發日誌（按月份分類）
- `quant_trading_reports/`：量化交易研究報告
- 各項功能的使用說明

### 📖 `reference/` - 參考專案

存放參考用的外部專案和框架。

- `lo2cin4bt-main/`：量化回測框架參考實現

## 💾 數據庫說明

### 台指期貨數據庫 (`taifex.db`)

- **數據範圍**：1998-2024 年完整台指期貨行情
- **數據類型**：日線、分鐘線、Tick 數據
- **功能特色**：高效查詢、高壓縮存儲

### 選擇權數據庫 (`taifex_options.db`)

- **數據範圍**：2001-2024 年選擇權交易數據
- **數據規模**：約 3,080 萬筆交易記錄
- **覆蓋商品**：TXO、TXO 等全系列選擇權
- **功能特色**：自動化下載、批量處理、進度顯示

## 🛠️ 開發指南

### AI 代理協作指南

請參閱 [`AGENTS.md`](AGENTS.md) 了解：
- 專案結構規範
- 編碼標準
- 開發工作流程
- 日誌維護系統

### 環境需求

- **Python**: 3.11.9+
- **主要依賴**: pandas, numpy, qlib, scipy
- **推薦環境**: Google Colab (12GB+ RAM) 或本地開發 (16GB+ RAM)

## 🎯 當前功能狀態

### ✅ 已完成功能

- [x] **Alpha 因子計算系統** - 100+ 個技術指標與統計因子
- [x] **因子評估系統** - IC 計算、分組回報分析、因子穩定性測試
- [x] **Qlib 框架整合** - 標準化回測流程
- [x] **台期貨數據庫** - 完整台指期貨與選擇權數據
- [x] **數據處理工具** - 自動化數據下載與處理

### 🚧 開發中功能

- [ ] **多策略整合** - 技術分析與統計套利策略結合
- [ ] **機器學習預測** - LightGBM、LSTM 等模型應用
- [ ] **風險管理系統** - 動態止損、倉位管理
- [ ] **實時交易接口** - 期貨API整合

### 📋 計劃中功能

- [ ] **選擇權策略開發** - 基於選擇權數據的量化策略
- [ ] **多資產配置** - 台股、期貨、選擇權的組合優化
- [ ] **強化學習應用** - RL 在交易策略中的應用
- [ ] **高頻交易框架** - Tick 級別的交易策略

## 👥 貢獻指南

歡迎參與專案開發！請遵循以下步驟：

1. 查看 [`AGENTS.md`](AGENTS.md) 的開發規範
2. 在 Issues 中提出功能建議或回報問題
3. Fork 專案並建立功能分支
4. 提交 Pull Request 並通過代碼審查

## 📄 授權

MIT License - 詳見 [LICENSE](LICENSE) 文件

---

**專案維護者**：AI Assistant
**最後更新**：2025-12-01

**開發環境建議**：由於本地記憶體限制，強烈建議在 Google Colab 環境中進行開發和測試。
