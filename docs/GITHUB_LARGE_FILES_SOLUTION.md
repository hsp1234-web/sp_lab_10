# GitHub 大檔案上傳解決方案

## ⚠️ GitHub 檔案大小限制

### 限制說明
- **單檔上限**: 100 MB (警告)
- **單檔硬限制**: 100 MB (無法推送)
- **Repository 建議大小**: < 1 GB
- **Repository 硬限制**: 5 GB

### 您的問題
- CSV 檔案和 data 資料夾超過 300MB
- 直接上傳會被 GitHub 拒絕

---

## ✅ 解決方案

### 方案 1: 使用 .gitignore 排除大檔案 (推薦)

#### 優點
- ✅ 最簡單,無需額外工具
- ✅ 保持 repository 輕量
- ✅ 適合資料檔案(可重新生成或另外儲存)

#### 實作步驟

**1. 更新 .gitignore**

已經為您準備好更新的 `.gitignore`,包含:
```gitignore
# 大型資料檔案
data/
*.db
*.csv
*.parquet

# 回測結果
records/**/*.parquet
records/**/*.csv
```

**2. 建立資料下載說明**

在 `README.md` 中說明如何取得資料:
```markdown
## 資料準備

由於資料檔案過大,未包含在 repository 中。請依照以下步驟準備:

1. 下載 DuckDB 資料庫: [連結]
2. 放置於 `data/taifex.db`
3. 或執行資料載入腳本: `python scripts/download_data.py`
```

**3. 提供資料下載方式**
- Google Drive 分享連結
- OneDrive 分享連結
- 或提供資料來源與載入腳本

---

### 方案 2: 使用 Git LFS (Large File Storage)

#### 優點
- ✅ 可以版本控制大檔案
- ✅ GitHub 官方支援
- ✅ 適合需要追蹤資料變更的情況

#### 缺點
- ⚠️ 免費額度有限 (1GB 儲存 + 1GB 頻寬/月)
- ⚠️ 超過需付費 ($5/月 for 50GB)
- ⚠️ 需要額外安裝 Git LFS

#### 實作步驟

**1. 安裝 Git LFS**
```powershell
# 使用 Chocolatey
choco install git-lfs

# 或下載安裝: https://git-lfs.github.com/
```

**2. 初始化 Git LFS**
```powershell
cd c:\SP_lab_Projects\sp_lab_v9_1.1\lo2cin4bt-main
git lfs install
```

**3. 追蹤大檔案**
```powershell
# 追蹤所有 .db 檔案
git lfs track "*.db"

# 追蹤 data 目錄下的所有檔案
git lfs track "data/**"

# 追蹤大型 CSV
git lfs track "*.csv"
```

**4. 提交 .gitattributes**
```powershell
git add .gitattributes
git commit -m "設定 Git LFS 追蹤大檔案"
```

**5. 正常提交**
```powershell
git add data/
git commit -m "新增資料檔案 (使用 Git LFS)"
git push
```

---

### 方案 3: 分離資料 Repository

#### 優點
- ✅ 程式碼與資料分離
- ✅ 更好的版本控制
- ✅ 可以獨立管理權限

#### 實作步驟

**1. 建立兩個 Repository**
- `lo2cin4bt` (程式碼)
- `lo2cin4bt-data` (資料)

**2. 在程式碼 repo 中說明**
```markdown
## 資料準備

資料儲存在獨立的 repository:
https://github.com/your-username/lo2cin4bt-data

請 clone 資料 repo 到 `data/` 目錄:
\`\`\`bash
git clone https://github.com/your-username/lo2cin4bt-data.git data
\`\`\`
```

**3. 使用 Git Submodule (進階)**
```powershell
# 在程式碼 repo 中加入資料 repo 作為 submodule
git submodule add https://github.com/your-username/lo2cin4bt-data.git data
```

---

### 方案 4: 使用外部儲存服務

#### 適用情況
- 資料非常大 (> 5GB)
- 不需要版本控制資料
- 需要分享給非技術人員

#### 服務選擇

| 服務 | 免費額度 | 優點 | 缺點 |
|------|---------|------|------|
| Google Drive | 15GB | 易用,分享方便 | 需要 Google 帳號 |
| OneDrive | 5GB | 整合 Windows | 較慢 |
| Dropbox | 2GB | 穩定 | 額度小 |
| Mega | 20GB | 額度大 | 較少人用 |

#### 實作步驟

**1. 上傳資料到雲端**
- 壓縮 `data/` 目錄: `taifex_data.zip`
- 上傳到 Google Drive
- 設定分享連結

**2. 在 README 中提供下載連結**
```markdown
## 資料下載

1. 下載資料: [Google Drive 連結](https://drive.google.com/...)
2. 解壓縮到專案根目錄
3. 確認 `data/taifex.db` 存在
```

**3. (可選) 建立下載腳本**
```python
# scripts/download_data.py
import gdown

# Google Drive 檔案 ID
file_id = "YOUR_FILE_ID"
output = "data/taifex_data.zip"

# 下載
gdown.download(id=file_id, output=output, quiet=False)

# 解壓縮
import zipfile
with zipfile.ZipFile(output, 'r') as zip_ref:
    zip_ref.extractall('data/')
```

---

## 🎯 建議方案

### 針對您的情況

**如果資料可以重新生成或從其他來源取得**:
→ **方案 1: 使用 .gitignore** (最簡單)

**如果資料需要版本控制且 < 1GB**:
→ **方案 2: Git LFS**

**如果資料很大 (> 1GB) 且需要分享**:
→ **方案 4: Google Drive + 下載腳本**

**如果資料和程式碼需要獨立管理**:
→ **方案 3: 分離 Repository**

---

## 📝 立即行動步驟

### 步驟 1: 更新 .gitignore

我已經為您準備好更新的 `.gitignore`,請檢視並確認。

### 步驟 2: 檢查目前的大檔案

```powershell
# 檢查超過 50MB 的檔案
Get-ChildItem -Path . -Recurse -File | Where-Object { $_.Length -gt 50MB } | Select-Object FullName, @{Name="SizeMB";Expression={[math]::Round($_.Length/1MB,2)}}
```

### 步驟 3: 決定處理方式

根據檔案類型決定:
- **資料庫檔案 (.db)**: 排除或使用 Git LFS
- **CSV 檔案**: 排除或壓縮後上傳到雲端
- **Parquet 檔案**: 排除 (這些是回測結果,可重新生成)

### 步驟 4: 建立資料說明文件

我會為您建立 `DATA_SETUP.md`,說明如何取得資料。

---

## ⚠️ 注意事項

### 如果已經提交大檔案

如果您已經 commit 了大檔案,需要從歷史記錄中移除:

```powershell
# 使用 BFG Repo-Cleaner (推薦)
# 1. 下載 BFG: https://rtyley.github.io/bfg-repo-cleaner/
# 2. 移除大於 100MB 的檔案
java -jar bfg.jar --strip-blobs-bigger-than 100M lo2cin4bt-main

# 或使用 git filter-branch (較慢)
git filter-branch --tree-filter 'rm -rf data/' HEAD
```

### 推送前檢查

```powershell
# 檢查即將推送的檔案大小
git ls-files -z | xargs -0 du -h | sort -h | tail -20
```

---

**建立時間**: 2025-11-24
**適用專案**: lo2cin4bt
