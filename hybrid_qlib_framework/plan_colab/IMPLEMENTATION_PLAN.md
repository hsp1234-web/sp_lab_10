# Hybrid Qlib Framework 實作計畫書

## 📋 專案概述

建立一個基於 **Qlib** 的量化交易系統，專門針對 **Google Colab** 環境優化，利用台指期/選擇權歷史資料（2017-2024）進行因子開發與回測驗證。

### 核心目標
- ✅ **低最大回撤 (Low MDD)**：風險控制優先
- ✅ **高夏普值 (High Sharpe)**：追求風險調整後報酬
- ✅ **真實數據驗證**：基於 `taifex.db` 真實歷史資料
- ✅ **Colab 友善**：針對 Colab 免費環境優化（GPU/TPU 加速）

---

## 🎯 使用者需求確認

> [!IMPORTANT]
> **關鍵決策：不使用 WSL，直接針對 Google Colab 環境開發**
> 
> - **原因**：後續將在 Colab 上執行，利用其免費 GPU/TPU 資源
> - **資料範圍**：2017-2024 年台指期/選擇權歷史資料
> - **資料來源**：
>   - `c:\SP_DOC\sp_lab_v10\data\taifex.db` (220 MB)
>   - `c:\SP_DOC\sp_lab_v10\data\taifex_options.db` (591 MB)
>   - `c:\SP_DOC\sp_lab_v10\hybrid_qlib_framework\data_export\taifex_daily.parquet`

---

## 📦 需要變更的檔案

### 🆕 新建檔案

#### [NEW] [colab_setup.ipynb](file:///c:/SP_DOC/sp_lab_v10/hybrid_qlib_framework/colab_setup.ipynb)
**用途**：Colab 環境初始化筆記本

**內容**：
- 安裝 Qlib、DuckDB、PyArrow 等依賴
- 從 Google Drive 掛載資料檔案
- 設定 Qlib 資料路徑
- 驗證環境是否正確設定

---

#### [NEW] [src/data_converter.py](file:///c:/SP_DOC/sp_lab_v10/hybrid_qlib_framework/src/data_converter.py)
**用途**：資料轉換模組

**功能**：
1. 從 SQLite (`taifex.db`) 讀取日線資料
2. 轉換為 Qlib Binary Format（高效讀取）
3. 使用 DuckDB Streaming 避免記憶體溢位
4. 支援增量更新（只轉換新資料）

**關鍵邏輯**：
```python
# 欄位映射
Symbol -> instrument  # 商品代碼
Date -> date          # 日期
Open/High/Low/Close -> $open/$high/$low/$close
Volume -> $volume
```

---

#### [NEW] [src/factor_lib.py](file:///c:/SP_DOC/sp_lab_v10/hybrid_qlib_framework/src/factor_lib.py)
**用途**：因子定義庫

**階段一：基準線因子（Alpha158）**
- 使用 Qlib 內建的 Alpha158 因子集
- 包含價格、成交量、技術指標等 158 個因子

**階段二：選擇權籌碼因子（自定義）**
- PCR (Put-Call Ratio)：買權/賣權比率
- IV Spread：隱含波動率價差
- OI Change：未平倉量變化
- 大額交易人部位分析

**因子表達式範例**：
```python
# PCR 因子
"PCR": "Ref($put_volume, 0) / Ref($call_volume, 0)"

# IV Spread 因子
"IV_SPREAD": "Ref($atm_iv, 0) - Ref($otm_iv, 0)"
```

---

#### [NEW] [src/model_runner.py](file:///c:/SP_DOC/sp_lab_v10/hybrid_qlib_framework/src/model_runner.py)
**用途**：模型訓練與回測引擎

**功能**：
1. 載入因子資料
2. 訓練 LightGBM 模型（初期）
3. 執行回測（Rolling Window）
4. 產出評估報告

**必須輸出的指標**：
- **IC / Rank IC**：因子有效性
- **Annualized Return**：年化報酬率
- **Max Drawdown**：最大回撤
- **Sharpe Ratio**：夏普值
- **Win Rate**：勝率

---

#### [NEW] [main.py](file:///c:/SP_DOC/sp_lab_v10/hybrid_qlib_framework/main.py)
**用途**：專案入口點（一鍵執行）

**流程**：
```
資料轉換 → 因子計算 → 模型訓練 → 回測驗證 → 報告產出
```

**命令列參數**：
```bash
python main.py --start-date 2017-01-01 --end-date 2024-12-31 --factors alpha158
```

---

#### [NEW] [configs/qlib_config.yaml](file:///c:/SP_DOC/sp_lab_v10/hybrid_qlib_framework/configs/qlib_config.yaml)
**用途**：Qlib 設定檔

**內容**：
- 資料路徑設定
- 回測參數（手續費、滑價）
- 模型超參數
- 因子選擇

---

#### [NEW] [upload_to_colab.py](file:///c:/SP_DOC/sp_lab_v10/hybrid_qlib_framework/upload_to_colab.py)
**用途**：資料上傳工具

**功能**：
- 將 `taifex.db` 和 `taifex_options.db` 壓縮
- 上傳至 Google Drive
- 產生 Colab 掛載程式碼

---

### 📝 修改檔案

#### [MODIFY] [DEVELOPMENT_PLAN.md](file:///c:/SP_DOC/sp_lab_v10/hybrid_qlib_framework/DEVELOPMENT_PLAN.md)

**變更內容**：
- 更新「技術決策脈絡」章節，明確說明 **Colab 優先策略**
- 新增「Colab 環境需求」章節
- 更新「待執行任務」，調整為 Colab 工作流程

---

## 🔍 驗證計畫

### 自動化測試

#### 1. 資料轉換驗證
```bash
# 測試資料轉換是否正確
python -m pytest tests/test_data_converter.py -v
```

**驗證項目**：
- ✅ SQLite → Qlib Binary 轉換正確性
- ✅ 日期範圍完整性（2017-2024）
- ✅ 欄位映射正確性
- ✅ 資料筆數一致性

---

#### 2. 因子計算驗證
```bash
# 測試因子計算邏輯
python -m pytest tests/test_factor_lib.py -v
```

**驗證項目**：
- ✅ Alpha158 因子計算正確
- ✅ 自定義因子無 NaN/Inf
- ✅ 因子值範圍合理

---

#### 3. 回測引擎驗證
```bash
# 執行簡單回測
python main.py --start-date 2023-01-01 --end-date 2023-12-31 --factors alpha158
```

**驗證項目**：
- ✅ 回測流程完整執行
- ✅ 產出所有必要指標
- ✅ 無未來函數洩漏

---

### 手動驗證

#### 1. Colab 環境測試

> [!NOTE]
> **需要使用者協助**
> 
> 請使用者執行以下步驟：
> 
> 1. 開啟 Google Colab
> 2. 上傳 `colab_setup.ipynb`
> 3. 執行所有 Cell
> 4. 確認以下項目：
>    - ✅ Qlib 安裝成功
>    - ✅ 資料檔案成功掛載
>    - ✅ 能夠讀取 Qlib Binary 資料
>    - ✅ 能夠執行簡單回測

---

#### 2. 視覺化報告檢查

執行完整回測後，檢查產出的報告：

```bash
# 產生完整報告
python main.py --start-date 2017-01-01 --end-date 2024-12-31 --factors alpha158 --output-report
```

**檢查項目**：
- ✅ 累積報酬曲線圖
- ✅ 回撤曲線圖
- ✅ 因子 IC 熱力圖
- ✅ 月度報酬表
- ✅ 所有圖表都有繁體中文標籤

---

#### 3. 效能基準測試

**目標**：
- 資料轉換時間 < 5 分鐘
- 單次回測時間 < 10 分鐘（2017-2024）
- Colab 記憶體使用 < 12GB

**測試方法**：
```python
import time
start = time.time()
# 執行回測
print(f"執行時間: {time.time() - start:.2f} 秒")
```

---

## 🚀 實作順序

### 第一階段：基礎設施（預計 2-3 小時）
1. ✅ 建立目錄結構
2. ✅ 實作 `data_converter.py`
3. ✅ 實作 `upload_to_colab.py`
4. ✅ 建立 `colab_setup.ipynb`

### 第二階段：因子與模型（預計 3-4 小時）
5. ✅ 實作 `factor_lib.py`（Alpha158）
6. ✅ 實作 `model_runner.py`
7. ✅ 實作 `main.py`
8. ✅ 建立 `qlib_config.yaml`

### 第三階段：驗證與優化（預計 2-3 小時）
9. ✅ 執行本地測試
10. ✅ 上傳至 Colab 測試
11. ✅ 執行完整回測（2017-2024）
12. ✅ 產出評估報告

### 第四階段：選擇權因子擴充（預計 4-5 小時）
13. ✅ 整合 `taifex_options.db`
14. ✅ 開發 PCR、IV Spread 因子
15. ✅ 對比 Alpha158 vs 籌碼因子表現
16. ✅ 產出最終報告

---

## ⚠️ 風險點與應對方案

### 風險 1：Colab 記憶體不足
**應對**：
- 使用 DuckDB Streaming 分批處理
- 啟用 Colab Pro（如需要）
- 使用 Parquet 而非 CSV

### 風險 2：資料上傳至 Drive 過慢
**應對**：
- 先壓縮資料庫（ZIP）
- 使用增量上傳
- 考慮使用 Colab 本地上傳

### 風險 3：Qlib 在 Colab 相容性問題
**應對**：
- 使用 Docker 映像檔
- 固定 Qlib 版本（避免 API 變動）
- 準備降級方案

---

## 📊 預期成果

完成後將產出：

1. **完整的 Colab Notebook**：一鍵執行所有流程
2. **回測報告**（繁體中文）：
   - 2017-2024 年完整回測結果
   - Alpha158 基準線表現
   - 選擇權籌碼因子表現
   - 因子重要性分析
3. **可重複使用的框架**：
   - 模組化設計
   - 易於擴充新因子
   - 支援不同市場/商品

---

## 📝 後續優化方向

1. **模型升級**：LightGBM → LSTM/Transformer
2. **動態風控**：波動率濾網、動態停損
3. **多商品支援**：台股、美股、加密貨幣
4. **即時交易**：整合券商 API
5. **自動化報告**：每日/每週自動產出

---

## ✅ 檢查清單

- [x] 確認資料範圍（2017-2024）
- [x] 測試 Colab 環境
- [ ] 建立 Colab Notebook
- [ ] 實作資料轉換模組
- [ ] 實作因子庫（Alpha158）
- [ ] 實作回測引擎
- [ ] 執行本地測試
- [ ] 上傳至 Colab 測試
- [ ] 產出完整報告
- [ ] 開發選擇權因子
- [ ] 最終驗證

---

*本計畫書由 AI 助手生成，最後更新：2025-11-30*
