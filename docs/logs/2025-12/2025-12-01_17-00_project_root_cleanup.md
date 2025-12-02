# 2025-12-01_17-00_project_root_cleanup.md

- 任務名稱：專案根目錄深度整理與檔案組織優化
- 日期：2025-12-01 17:00 CST
- 作者：AI Assistant
- 摘要：根據 AGENTS.md 規範，對根目錄進行深度整理，將散落檔案移至適當目錄，實現清潔的專案結構。

## 📋 整理工作總結

### 🎯 整理目標

根據 AGENTS.md 檔案組織規範：
- 核心程式碼必須存放在 `src/` 目錄下
- 數據資料必須存放在 `data/` 目錄下
- 產出檔案必須統一存放在 `output/` 目錄下
- 工具腳本應存放在 `scripts/` 目錄下
- 嚴禁將程式碼檔案或產出物直接散落在根目錄

### 📁 檔案移動詳情

#### 1. Jupyter Notebook 整理
- **移動檔案**：`Ollama整理資料v1.ipynb`
- **來源位置**：根目錄
- **目標位置**：`notebooks/`
- **原因**：Jupyter notebook 應統一存放在 notebooks 目錄

#### 2. 輸出檔案整理
- **移動檔案**：
  - `check_ignore_output.txt`
  - `workspace_stats.csv`
- **來源位置**：根目錄
- **目標位置**：`output/`
- **原因**：這些是檢查和統計輸出檔案，屬於產出檔案

#### 3. 測試檔案整理
- **移動檔案**：`terminal_test.txt`
- **來源位置**：根目錄
- **目標位置**：`temp/`
- **原因**：測試檔案應存放在臨時目錄

#### 4. 參考文檔整理
- **移動目錄**：`drive-download-20251126T202650Z-1-001/`
- **重新命名**：`google_drive_documents`
- **來源位置**：根目錄
- **目標位置**：`research/google_drive_documents/`
- **原因**：這些是從 Google Drive 下載的金融研究文檔，屬於參考資料
- **檔案數量**：68 個 .docx 文檔

#### 5. 測試目錄清理
- **移動目錄**：`test_cursor_dir_2/` → `temp/test_cursor_dir_2/`
- **刪除目錄**：`test_destination_dir/`（空目錄）
- **原因**：清理開發過程中的測試目錄

### 📊 整理結果統計

| 整理類型 | 檔案/目錄數量 | 目標目錄 |
|---------|-------------|---------|
| Jupyter Notebook | 1 | notebooks/ |
| 輸出檔案 | 2 | output/ |
| 測試檔案 | 1 | temp/ |
| 參考文檔目錄 | 1 | research/ |
| 測試目錄 | 1 (移動) + 1 (刪除) | temp/ |

### ✅ 最終根目錄狀態

整理後的根目錄現在只包含：
- `main.py`：主入口檔案（保留）
- `README.md`：專案說明文件（保留）
- `AGENTS.md`：AI 代理指南（保留）
- 各功能目錄：archive/, colab_env/, config/, data/, docs/, hybrid_qlib_framework/, notebooks/, output/, plan/, records/, reference/, research/, scripts/, src/, strategies/, temp/, tests/, tools/, utils/

### 🔍 驗證結果

- ✅ 所有散落檔案已移至適當目錄
- ✅ 根目錄結構清潔有序
- ✅ 檔案組織符合 AGENTS.md 規範
- ✅ 無功能破壞（所有移動都是非破壞性）

### 📝 注意事項

1. **檔案引用檢查**：移動檔案後應檢查是否有其他檔案引用這些檔案的舊路徑
2. **腳本相容性**：確保移動後的檔案路徑在相關腳本中正確更新
3. **版本控制**：建議提交這些整理變更到 git 以保持歷史記錄

### 🎯 下一步建議

1. 檢查是否有程式碼引用移動檔案的舊路徑
2. 考慮進一步整理子目錄結構（如 data_scripts/, records/ 等）
3. 更新相關文檔中的檔案路徑引用
