# sp_lab_v9_1.1 專案提交指南

## 📋 專案概述

此專案包含量化交易回測框架 `lo2cin4bt` 及相關工具。

### 目錄結構

```
sp_lab_v9_1.1/
├── data/                      # 大型資料檔案 (已排除,不上傳)
│   ├── taifex_extracted/
│   └── taifex.db (~300MB)
├── lo2cin4bt-main/            # 回測框架主程式
├── docs/                      # 文件目錄
│   ├── MEMORY_FIX_SUMMARY.md
│   ├── GITHUB_LARGE_FILES_SOLUTION.md
│   ├── DATA_SETUP.md
│   └── GIT_COMMIT_GUIDE.md
├── output/                    # 輸出結果
├── src/                       # 原始碼
├── scripts/                   # 腳本工具
└── tests/                     # 測試檔案
```

---

## ✅ 已完成的準備工作

### 1. 更新 .gitignore
已排除以下大型檔案:
- ✅ `data/` 目錄及所有子目錄
- ✅ `*.db`, `*.sqlite`, `*.duckdb` 資料庫檔案
- ✅ `*.csv`, `*.xlsx` (除了 output 中的分析結果)
- ✅ `*.parquet` (除了 output 中的分析結果)
- ✅ `*.zip`, `*.tar.gz` 等壓縮檔案

### 2. 文件整理
所有說明文件已移動到 `docs/` 目錄:
- `MEMORY_FIX_SUMMARY.md` - 記憶體優化修復總結
- `GITHUB_LARGE_FILES_SOLUTION.md` - GitHub 大檔案解決方案
- `DATA_SETUP.md` - 資料準備說明
- `GIT_COMMIT_GUIDE.md` - Git 提交指南

---

## 🚀 提交步驟

### 步驟 1: 初始化 Git (如果尚未初始化)

```powershell
cd c:\SP_lab_Projects\sp_lab_v9_1.1
git init
```

### 步驟 2: 檢查將要提交的檔案

```powershell
# 查看狀態
git status

# 確認沒有大檔案
git ls-files -z | xargs -0 du -h | sort -h | tail -20
```

### 步驟 3: 加入檔案

```powershell
# 加入所有檔案 (data/ 會被自動排除)
git add .

# 再次確認
git status
```

### 步驟 4: 提交

```powershell
git commit -m "初始提交: 量化交易回測框架

- 新增: lo2cin4bt 回測框架
- 新增: 記憶體優化修復
- 新增: Colab 遷移方案
- 新增: 完整文件與指南
- 排除: data 目錄 (大型資料檔案)

詳細說明請參考 docs/ 目錄"
```

### 步驟 5: 推送到 GitHub

```powershell
# 新增遠端 repository
git remote add origin https://github.com/YOUR_USERNAME/sp_lab_v9_1.1.git

# 推送
git push -u origin main
```

---

## ⚠️ 重要提醒

### 推送前最後檢查

```powershell
# 檢查是否有大於 50MB 的檔案
Get-ChildItem -Path . -Recurse -File | Where-Object { $_.Length -gt 50MB } | Select-Object FullName, @{Name="SizeMB";Expression={[math]::Round($_.Length/1MB,2)}}

# 確認 data 目錄被排除
git check-ignore -v data/
git check-ignore -v data/taifex.db
git check-ignore -v data/taifex_extracted/
```

**預期結果**: 所有 data 相關檔案都應該顯示被 `.gitignore` 排除

---

## 📊 預期的 Repository 大小

排除 `data/` 目錄後,repository 大小應該:
- ✅ < 100 MB (符合 GitHub 建議)
- ✅ 無單一檔案 > 100 MB
- ✅ 主要包含程式碼、文件、小型輸出結果

---

## 📚 資料分享方式

由於 `data/` 目錄未包含在 repository 中,請依照以下方式分享:

### 方法 1: Google Drive (推薦)

1. **壓縮資料**
   ```powershell
   Compress-Archive -Path data -DestinationPath taifex_data.zip
   ```

2. **上傳到 Google Drive**
   - 建立分享連結
   - 設定為「任何人皆可檢視」

3. **更新 docs/DATA_SETUP.md**
   - 填入 Google Drive 連結
   - 提供下載與設定說明

### 方法 2: Git LFS (如果需要版本控制)

參考 `docs/GITHUB_LARGE_FILES_SOLUTION.md` 中的 Git LFS 設定方式。

---

## 🔍 驗證清單

提交前請確認:
- [ ] `.gitignore` 已更新並排除 `data/`
- [ ] 所有文件已移動到 `docs/`
- [ ] 沒有大於 100MB 的檔案
- [ ] `data/` 目錄確實被排除
- [ ] 提交訊息清楚描述變更內容
- [ ] README.md 包含專案說明
- [ ] docs/DATA_SETUP.md 提供資料取得方式

---

## 📞 需要協助?

如果遇到問題,請參考:
- 📄 `docs/GITHUB_LARGE_FILES_SOLUTION.md` - 大檔案處理方案
- 📄 `docs/GIT_COMMIT_GUIDE.md` - 詳細提交指南
- 📄 `docs/DATA_SETUP.md` - 資料準備說明

---

**建立時間**: 2025-11-24
**專案版本**: v1.0
**Git Repository**: sp_lab_v9_1.1
