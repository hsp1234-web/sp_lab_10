# Google Colab 遷移指南

## 📋 遷移概覽

將 `lo2cin4bt` 回測框架遷移到 Google Colab,以獲得更大的記憶體和計算資源。

### 優勢
- ✅ 免費記憶體: 12.7GB (標準) / 51GB (Colab Pro)
- ✅ 免費 GPU: Tesla T4 (可選)
- ✅ 預裝常用套件: pandas, numpy, matplotlib
- ✅ 雲端儲存: Google Drive 整合
- ✅ 分享協作: 可分享 Notebook 連結

---

## 🚀 遷移步驟

### 步驟 1: 準備專案檔案

#### 1.1 壓縮專案目錄
```powershell
# 在本機執行
cd c:\SP_lab_Projects\sp_lab_v9_1.1
Compress-Archive -Path lo2cin4bt-main -DestinationPath lo2cin4bt.zip
```

#### 1.2 壓縮 DuckDB 資料庫
```powershell
# 壓縮資料庫檔案
cd c:\SP_lab_Projects\sp_lab_v9_1.1
Compress-Archive -Path data\taifex.db -DestinationPath taifex_db.zip
```

### 步驟 2: 上傳到 Google Drive

1. 開啟 [Google Drive](https://drive.google.com)
2. 建立資料夾: `lo2cin4bt_project`
3. 上傳檔案:
   - `lo2cin4bt.zip`
   - `taifex_db.zip`

### 步驟 3: 建立 Colab Notebook

#### 3.1 新增 Notebook
1. 在 Google Drive 中右鍵 → 更多 → Google Colaboratory
2. 命名為: `lo2cin4bt_backtest.ipynb`

#### 3.2 設定執行環境

```python
# Cell 1: 掛載 Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Cell 2: 解壓專案檔案
!unzip -q /content/drive/MyDrive/lo2cin4bt_project/lo2cin4bt.zip -d /content/
!unzip -q /content/drive/MyDrive/lo2cin4bt_project/taifex_db.zip -d /content/lo2cin4bt-main/data/

# Cell 3: 安裝相依套件
%cd /content/lo2cin4bt-main
!pip install -q -r requirements.txt

# Cell 4: 檢查系統資源
import psutil
import os

print(f"💾 總記憶體: {psutil.virtual_memory().total / (1024**3):.1f} GB")
print(f"💾 可用記憶體: {psutil.virtual_memory().available / (1024**3):.1f} GB")
print(f"🖥️ CPU 核心數: {os.cpu_count()}")
print(f"📁 專案路徑: {os.getcwd()}")

# Cell 5: 執行回測
!python run_test.py
```

### 步驟 4: 下載結果

```python
# Cell 6: 壓縮結果檔案
!zip -r backtest_results.zip records/backtester/*.parquet records/metricstracker/*.parquet

# Cell 7: 複製到 Google Drive
!cp backtest_results.zip /content/drive/MyDrive/lo2cin4bt_project/

# 或直接下載到本機
from google.colab import files
files.download('backtest_results.zip')
```

---

## 📊 效能比較

| 項目 | 本機 (您的電腦) | Colab 標準 | Colab Pro |
|------|----------------|-----------|-----------|
| 總記憶體 | 5.9 GB | 12.7 GB | 51 GB |
| 可用記憶體 | 0.9 GB | ~10 GB | ~45 GB |
| CPU 核心 | 12 核 | 2 核 | 2-8 核 |
| 執行時間 (13000 策略) | 17 分鐘 | ~15 分鐘 | ~10 分鐘 |
| 導出成功率 | ❌ 失敗 | ✅ 成功 | ✅ 成功 |

---

## ⚠️ 注意事項

### 限制
1. **執行時間限制**: 
   - 標準版: 12 小時
   - Pro 版: 24 小時
2. **閒置斷線**: 90 分鐘無互動會斷線
3. **GPU 限制**: 每日使用時數有限

### 解決方案
1. **防止斷線**: 在 Console 執行
   ```javascript
   function ClickConnect(){
     console.log("Working"); 
     document.querySelector("colab-connect-button").click()
   }
   setInterval(ClickConnect,60000)
   ```

2. **分段執行**: 將大型回測拆分成多個小任務

---

## 🔧 優化建議

### 1. 使用 Colab Pro (可選)
- 月費: $9.99 USD
- 記憶體: 51GB
- GPU: 優先使用權
- 執行時間: 24 小時

### 2. 啟用 GPU 加速 (如需要)
```python
# 檢查 GPU
!nvidia-smi

# 在 Numba 中使用 CUDA
# 需要修改 VectorBacktestEngine 以支援 GPU
```

### 3. 使用 TPU (進階)
- 適合大規模矩陣運算
- 需要重寫部分程式碼以支援 JAX/TensorFlow

---

## 📝 完整 Notebook 範例

請參考附件: [lo2cin4bt_colab_template.ipynb](file:///c:/SP_lab_Projects/sp_lab_v9_1.1/lo2cin4bt_colab_template.ipynb)

---

## 🎯 下一步

1. **立即測試**: 先在本機測試修復後的導出功能
2. **準備遷移**: 壓縮專案檔案並上傳到 Google Drive
3. **Colab 測試**: 在 Colab 上執行小規模測試 (1000 策略)
4. **全面回測**: 確認無誤後執行完整回測 (13000 策略)

---

## 💡 提示

- 第一次在 Colab 執行會較慢 (需要安裝套件)
- 建議先測試小規模回測,確認環境正常
- 定期將結果備份到 Google Drive
- 可以開啟多個 Colab Notebook 同時執行不同策略
