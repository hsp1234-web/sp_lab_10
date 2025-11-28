# Colab 環境部署指南

這個資料夾 (`colab_env`) 包含了在 Google Colab 上執行 AI 交易系統所需的核心腳本與設定。

## 📂 資料夾結構

```
colab_env/
├── scripts/               # 數據收集與資料庫建置腳本
│   ├── taifex_official_update.py
│   ├── build_finmind_db.py
│   └── ...
├── requirements.txt       # Colab 環境依賴套件
└── main_colab.ipynb       # (建議建立) Colab 主程式 Notebook
```

## 🚀 如何在 Colab 使用

1. **上傳資料夾**: 將整個 `colab_env` 資料夾上傳至您的 Google Drive (例如: `/content/drive/MyDrive/ai_trading/`).
2. **掛載 Drive**:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   %cd /content/drive/MyDrive/ai_trading/colab_env
   ```
3. **安裝依賴**:
   ```python
   !pip install -r requirements.txt
   ```
4. **執行數據更新**:
   ```python
   # 更新期交所數據
   !python scripts/taifex_official_update.py
   
   # 更新 FinMind 數據
   !python scripts/build_finmind_db.py
   ```

## ☁️ Colab vs GCP 選擇建議

| 特性 | Google Colab | Google Cloud Platform (GCP) |
| :--- | :--- | :--- |
| **核心優勢** | **免費 GPU (T4)**、互動式開發、快速切換硬體 | **24/7 自動化**、穩定性高、可擴展 |
| **硬體彈性** | ⭐⭐⭐⭐⭐ (一鍵切換 T4/A100/TPU) | ⭐⭐⭐ (需設定 VM 規格，A100 很貴) |
| **成本** | **免費** (或 Pro $10/月) | **付費** (VM + Storage 流量費) |
| **適用階段** | **MVP 開發、回測、模型訓練** | **實盤交易、全自動化部署** |

**結論**: 
目前階段強烈建議使用 **Colab**。
1. **省錢**: 免費 GPU 對於跑本地 LLM (Ollama/Gemma) 至關重要。
2. **彈性**: 您提到的「隨時調整硬體規格」，Colab 是最方便的 (選單切換即可)。
3. **遷移**: 等策略穩定獲利後，再將這些腳本搬到 GCP VM 即可 (Python 腳本是通用的)。
