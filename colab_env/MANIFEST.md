# Colab 專用部署包 (Colab Deployment Package)

這個資料夾彙整了所有 **AI 交易系統 MVP** 所需的關鍵程式碼與計畫文件，方便直接上傳至 Google Colab 使用。

## 📂 檔案清單 (File List)

### 1. 核心計畫文件 (Plans)
*   `AI_Trading_Implementation_Plan.md`: 完整的系統實施計畫。
*   `Colab_MVP_Implementation.md`: Colab 執行細節。
*   `Free_MVP_Action_Plan.md`: 免費資源操作指南。
*   `Level1_Trading_Pro.ipynb`: **(原 一級交易pro.ipynb)** 核心交易策略 Notebook (已更名)。

### 2. 腳本資料夾 (scripts/)
所有 Python 執行腳本都位於 `scripts/` 目錄下：
*   `data_loader.py`: 整合型數據載入器。
*   `create_db.py`: 資料庫建置腳本。
*   `taifex_official_update.py`: 期交所每日更新腳本。
*   `taifex_official_downloader.py`: 期交所進階數據下載。
*   `download_taifex_options.py`: 選擇權歷史下載。
*   `build_*.py`: 各種資料庫建置工具 (FinMind, Yfinance, Taifex)。

## 🚀 使用說明

1.  將此 `colab_env` 資料夾整個上傳至 Google Drive。
2.  在 Colab 中開啟 `Level1_Trading_Pro.ipynb`。
3.  掛載 Drive 後，即可呼叫 `scripts/` 內的工具進行數據更新。
