# 專案整理與 GitHub 上傳指南

## 📋 目前狀況

專案檔案較為混亂，需要整理後再上傳至 GitHub。

## 🎯 整理目標

1. ✅ 建立完整文檔（中文內容，英文檔名）
2. ✅ 設定 `.gitignore`（保留回測記錄，排除不必要檔案）
3. 🔄 整理專案結構（符合 AGENTS.md 規範）
4. 🔄 準備 GitHub 上傳

---

## 📁 建議的專案結構

```
sp_lab_v9_1.1/
├── docs/                    # 📚 文檔目錄
│   ├── backtest_project_documentation.md  # 完整專案文檔
│   └── logs/                # 開發日誌（按月份分類）
│       └── 2025-11/
│           └── 2025-11-24_03-00_wsl_setup_and_backtest.md
│
├── src/                     # 💻 核心程式碼
│   ├── demo_run.py          # 回測執行腳本
│   ├── full_analysis.py     # 完整分析腳本
│   └── check_columns.py     # 欄位檢查腳本
│
├── output/                  # 📊 輸出結果
│   ├── backtest_analysis.txt
│   └── column_check_result.txt
│
├── lo2cin4bt-main/          # 🔧 回測框架（保持原樣）
│   ├── dataloader/
│   ├── backtester/
│   ├── autorunner/
│   └── records/             # ⭐ 回測記錄（需上傳至 GitHub）
│       └── backtester/
│           └── *.parquet
│
├── .gitignore               # Git 忽略設定
├── README.md                # 專案簡介
├── AGENTS.md                # AI 協作指南
└── requirements.txt         # Python 依賴清單（待建立）
```

---

## 🔧 整理步驟

### 步驟 1: 建立目錄結構

```powershell
# 建立必要目錄
New-Item -ItemType Directory -Force -Path docs
New-Item -ItemType Directory -Force -Path docs\logs\2025-11
New-Item -ItemType Directory -Force -Path src
```

### 步驟 2: 移動檔案到正確位置

```powershell
# 移動腳本到 src/
Move-Item demo_run.py src\ -Force
Move-Item full_analysis.py src\ -Force
Move-Item check_columns.py src\ -Force
Move-Item quick_analysis.py src\ -Force
Move-Item analyze_results.py src\ -Force

# 移動文檔到 docs/
# (backtest_project_documentation.md 已在 artifacts 目錄，需要複製)
```

### 步驟 3: 建立 requirements.txt

```powershell
# 建立依賴清單
@"
numpy==1.26.4
pandas==2.3.3
yfinance==0.2.66
pyarrow==22.0.0
numba==0.62.1
llvmlite==0.45.1
plotly==6.5.0
dash==3.3.0
rich==14.2.0
beautifulsoup4==4.14.2
aiohttp==3.13.2
requests==2.32.5
"@ | Out-File -FilePath requirements.txt -Encoding utf8
```

### 步驟 4: 清理不必要的檔案

```powershell
# 刪除臨時檔案和測試檔案
Remove-Item test.txt -ErrorAction SilentlyContinue
Remove-Item test_py.txt -ErrorAction SilentlyContinue
Remove-Item pandas_test.txt -ErrorAction SilentlyContinue
Remove-Item demo_run.log -ErrorAction SilentlyContinue
Remove-Item setup_wsl.sh -ErrorAction SilentlyContinue
Remove-Item setup_wsl_venv.sh -ErrorAction SilentlyContinue
```

---

## 🚀 GitHub 上傳步驟

### 初始化 Git 倉庫

```powershell
# 1. 初始化 Git
git init

# 2. 加入所有檔案（.gitignore 會自動排除不必要的）
git add .

# 3. 查看將要提交的檔案
git status

# 4. 提交
git commit -m "Initial commit: lo2cin4bt backtest project"

# 5. 連接到 GitHub（替換成您的倉庫 URL）
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 6. 推送到 GitHub
git push -u origin main
```

---

## ✅ .gitignore 設定說明

已建立的 `.gitignore` 會：

**✅ 保留（上傳至 GitHub）：**
- 回測記錄：`lo2cin4bt-main/records/backtester/*.parquet`
- 分析結果：`output/*.txt`
- 核心程式碼：`src/*.py`
- 文檔：`docs/**/*.md`
- 設定檔：`README.md`, `AGENTS.md`, `requirements.txt`

**❌ 排除（不上傳）：**
- 虛擬環境：`.venv/`, `.venv_wsl/`
- Python 快取：`__pycache__/`, `*.pyc`
- IDE 設定：`.vscode/`, `.idea/`
- 臨時檔案：`*.log`, `*.tmp`, `*.bak`
- 大型數據檔：`*.csv`, `*.xlsx`（除非在 output/ 中）
- WSL 設定腳本：`setup_wsl*.sh`

---

## 📊 上傳後的檔案大小估算

| 類型 | 大小估算 |
|------|---------|
| Python 腳本 | < 100 KB |
| 文檔 (Markdown) | < 200 KB |
| 回測記錄 (Parquet) | ~30 MB |
| 分析結果 (TXT) | < 50 KB |
| **總計** | **~30 MB** |

**結論：** 檔案大小合理，適合上傳至 GitHub。

---

## 🎯 後續維護

### 每次回測後

```powershell
# 1. 執行回測
python src/demo_run.py

# 2. 分析結果
python src/full_analysis.py

# 3. 提交變更
git add lo2cin4bt-main/records/backtester/*.parquet
git add output/*.txt
git commit -m "Update backtest results: YYYY-MM-DD"
git push
```

### 建立新日誌

```powershell
# 使用工具建立
python utils/create_log.py

# 或手動建立
New-Item -Path "docs/logs/2025-11/2025-11-24_15-30_strategy_optimization.md"
```

---

## ⚠️ 注意事項

1. **不要上傳虛擬環境**：`.venv/` 和 `.venv_wsl/` 已在 `.gitignore` 中排除
2. **保留回測記錄**：Parquet 檔案雖然較大但很重要，已設定保留
3. **定期清理**：建議每月清理一次舊的回測記錄
4. **敏感資訊**：確保沒有 API 金鑰或密碼在程式碼中

---

**建立日期：** 2025-11-24  
**最後更新：** 2025-11-24
