# 根目錄檔案整理計畫

## 📋 當前根目錄檔案清單

### 🗂️ 目錄 (13個)
- `.git/` - Git 版本控制
- `.venv/`, `.venv_lo2cin4bt/`, `.venv_std/`, `.venv_wsl/` - 虛擬環境（4個）
- `__pycache__/` - Python 快取
- `docs/` - 文檔
- `lo2cin4bt-main/` - 回測框架
- `notebooks/` - Jupyter notebooks
- `output/` - 輸出結果
- `src/` - 原始碼
- `tests/` - 測試
- `utils/` - 工具

### 📄 檔案 (16個)
- `.gitignore` - Git 忽略設定 ✅
- `AGENTS.md` - AI 協作指南 ✅
- `README.md` - 專案簡介 ✅
- `requirements.txt` - 依賴清單 ✅
- `config.py` - 設定檔
- `main.py` - 主程式
- `version.txt` - 版本資訊
- `demo_run.py` - 回測腳本 ⚠️ 應移至 src/
- `demo_run.log` - 日誌檔 ⚠️ 應刪除或移至 output/
- `demo_summary.txt` - 摘要 ⚠️ 應移至 output/
- `analyze_results.py` - 分析腳本 ⚠️ 應移至 src/
- `check_columns.py` - 檢查腳本 ⚠️ 應移至 src/
- `full_analysis.py` - 完整分析 ⚠️ 應移至 src/
- `quick_analysis.py` - 快速分析 ⚠️ 應移至 src/
- `setup_wsl.sh` - WSL 設定 ⚠️ 應刪除或移至 scripts/
- `setup_wsl_venv.sh` - WSL 虛擬環境 ⚠️ 應刪除或移至 scripts/

---

## 🎯 整理目標

**根目錄應該只保留：**
- 設定檔：`.gitignore`, `AGENTS.md`, `README.md`, `requirements.txt`
- 主程式：`main.py`, `config.py`
- 版本資訊：`version.txt`
- 目錄：`src/`, `docs/`, `output/`, `lo2cin4bt-main/`, `tests/`, `utils/`

**需要移動或刪除：**
- Python 腳本 → `src/`
- 日誌檔案 → `output/logs/` 或刪除
- WSL 設定腳本 → `scripts/` 或刪除
- 虛擬環境 → 保留一個即可，其他刪除

---

## 📁 建議的新資料夾結構

```
sp_lab_v9_1.1/
├── .git/                    # Git 版本控制
├── .venv/                   # 虛擬環境（只保留一個）
│
├── src/                     # 💻 原始碼
│   ├── backtest/            # 回測相關腳本
│   │   ├── demo_run.py
│   │   ├── full_analysis.py
│   │   ├── quick_analysis.py
│   │   ├── check_columns.py
│   │   └── analyze_results.py
│   └── (其他現有檔案)
│
├── scripts/                 # 🔧 工具腳本（新建）
│   ├── setup_wsl.sh
│   └── setup_wsl_venv.sh
│
├── output/                  # 📊 輸出結果
│   ├── logs/                # 日誌檔案
│   │   └── demo_run.log
│   ├── summaries/           # 摘要檔案
│   │   └── demo_summary.txt
│   ├── backtest_analysis.txt
│   └── column_check_result.txt
│
├── docs/                    # 📚 文檔
├── lo2cin4bt-main/          # 🔧 回測框架
├── tests/                   # 🧪 測試
├── utils/                   # 🛠️ 工具
│
├── .gitignore               # Git 設定
├── AGENTS.md                # AI 協作指南
├── README.md                # 專案簡介
├── requirements.txt         # 依賴清單
├── config.py                # 設定檔
├── main.py                  # 主程式
└── version.txt              # 版本資訊
```

---

## 🚀 執行步驟

### 步驟 1: 建立新目錄

```powershell
# 建立 scripts 目錄
New-Item -ItemType Directory -Force -Path scripts

# 建立 output 子目錄
New-Item -ItemType Directory -Force -Path output\logs
New-Item -ItemType Directory -Force -Path output\summaries

# 建立 src 子目錄
New-Item -ItemType Directory -Force -Path src\backtest
```

### 步驟 2: 移動檔案

```powershell
# 移動回測腳本到 src/backtest/
Move-Item demo_run.py src\backtest\ -Force
Move-Item full_analysis.py src\backtest\ -Force
Move-Item quick_analysis.py src\backtest\ -Force
Move-Item check_columns.py src\backtest\ -Force
Move-Item analyze_results.py src\backtest\ -Force

# 移動 WSL 設定腳本到 scripts/
Move-Item setup_wsl.sh scripts\ -Force
Move-Item setup_wsl_venv.sh scripts\ -Force

# 移動日誌和摘要到 output/
Move-Item demo_run.log output\logs\ -Force -ErrorAction SilentlyContinue
Move-Item demo_summary.txt output\summaries\ -Force -ErrorAction SilentlyContinue
```

### 步驟 3: 清理虛擬環境（保留一個）

```powershell
# 刪除多餘的虛擬環境（保留 .venv）
Remove-Item -Recurse -Force .venv_lo2cin4bt -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .venv_std -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .venv_wsl -ErrorAction SilentlyContinue

# 刪除 Python 快取
Remove-Item -Recurse -Force __pycache__ -ErrorAction SilentlyContinue
```

### 步驟 4: 更新 .gitignore

```powershell
# .gitignore 已經設定好，會自動排除虛擬環境和快取
```

### 步驟 5: 驗證整理結果

```powershell
# 查看根目錄檔案
Get-ChildItem -Name

# 應該只看到：
# .git, .gitignore, .venv, AGENTS.md, README.md, config.py, 
# docs, lo2cin4bt-main, main.py, notebooks, output, 
# requirements.txt, scripts, src, tests, utils, version.txt
```

---

## ✅ 整理後的優點

1. **根目錄整潔**：只保留設定檔和主程式
2. **分類清晰**：
   - 回測腳本 → `src/backtest/`
   - 工具腳本 → `scripts/`
   - 輸出結果 → `output/`（含子分類）
3. **符合規範**：遵循 AGENTS.md 的目錄結構要求
4. **易於維護**：檔案分類明確，容易找到

---

## 🔄 後續使用

### 執行回測

```powershell
# 新路徑
python src\backtest\demo_run.py
```

### 分析結果

```powershell
python src\backtest\full_analysis.py
```

### WSL 設定

```powershell
wsl bash scripts/setup_wsl.sh
```

---

**建立日期：** 2025-11-24  
**狀態：** 待執行
