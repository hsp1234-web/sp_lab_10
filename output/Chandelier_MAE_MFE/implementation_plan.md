# MAE/MFE 分析與吊燈策略實作計畫

## 目標說明
利用現有的 DuckDB 資料庫 (`data/taifex.db`)，在 **TX (台指期)** 上實作 **吊燈停損 (Chandelier Stop)** 趨勢跟隨策略。
執行 **MAE (最大不利幅度)** 與 **MFE (最大有利幅度)** 分析，以優化停損/停利點並過濾交易。
使用 FinLab 風格的圖表視覺化分析結果。

## 需用戶審閱事項
> [!IMPORTANT]
> **資料表名稱差異**：現有資料庫中的資料表名稱為 `futures_data`，而非腳本中提供的 `futuresdata`。本計畫將使用 `futures_data`。

> [!WARNING]
> **外資數據缺失**：目前的 `futures_data` 資料表似乎不包含外資 (三大法人) 數據。若要實作「外資濾網」優化，我們需要先將此數據匯入 DuckDB。

> [!NOTE]
> **依賴套件**：此策略依賴 `pandas_ta` 進行 ATR 計算。需將此套件加入 `requirements.txt`。

## 預計變更

### 1. 依賴套件 (Dependencies)
#### [MODIFY] [requirements.txt](file:///c:/SP_lab_Projects/sp_lab_v9_1.1/lo2cin4bt-main/requirements.txt)
- 新增 `pandas_ta`

### 2. 策略實作 (Backtester)
建立一個新的指標模組來處理吊燈停損邏輯。

#### [NEW] [Chandelier_Indicator_backtester.py](file:///c:/SP_lab_Projects/sp_lab_v9_1.1/lo2cin4bt-main/backtester/Chandelier_Indicator_backtester.py)
- **類別**: `ChandelierIndicator`
- **參數**: `length` (預設 22), `multiplier` (預設 3.0)
- **邏輯**:
    - 計算 ATR(length)。
    - 計算滾動最高價(length) 與 最低價(length)。
    - `多單停損點 = 滾動最高價 - multiplier * ATR`
    - `空單停損點 = 滾動最低價 + multiplier * ATR`
    - 根據價格穿越這些水平產生 進場/出場 信號。

#### [MODIFY] [Indicators_backtester.py](file:///c:/SP_lab_Projects/sp_lab_v9_1.1/lo2cin4bt-main/backtester/Indicators_backtester.py)
- 在 `new_indicators` 映射中註冊 `ChandelierIndicator`。
- 新增別名映射 (例如: `CHANDELIER`)。

### 3. MAE/MFE 分析 (MetricsTracker)
建立一個專用的分析器，在回測結束 *後* 執行，計算幅度指標。

#### [NEW] [MAEMFE_Analyser_metricstracker.py](file:///c:/SP_lab_Projects/sp_lab_v9_1.1/lo2cin4bt-main/metricstracker/MAEMFE_Analyser_metricstracker.py)
- **類別**: `MAEMFEAnalyser`
- **輸入**: `trade_list` (DataFrame), `ohlcv_data` (DataFrame)
- **邏輯**:
    - 遍歷每一筆交易。
    - 切片取得該筆交易持有期間的 `ohlcv_data`。
    - 計算 `MAE`: 持有期間相對於進場價的最大回檔幅度。
    - 計算 `MFE`: 持有期間相對於進場價的最大獲利幅度。
    - 計算 `Edge Ratio` (優勢比率): 平均 MFE / 平均 MAE。
- **輸出**: 包含 MAE/MFE 欄位的增強版交易列表。

#### [MODIFY] [Base_metricstracker.py](file:///c:/SP_lab_Projects/sp_lab_v9_1.1/lo2cin4bt-main/metricstracker/Base_metricstracker.py)
- 新增選項/步驟以觸發 `MAEMFEAnalyser`。

### 4. 視覺化 (Plotter)
#### [NEW] [MAEMFE_plotter.py](file:///c:/SP_lab_Projects/sp_lab_v9_1.1/lo2cin4bt-main/plotter/MAEMFE_plotter.py)
- **函式**: `plot_mae_mfe(trades_df)`
- **圖表**:
    1. 報酬分布 (直方圖)
    2. Edge Ratio 時間序列
    3. MAE vs Return (散點圖)
    4. MFE vs MAE (散點圖)
    5. MDD vs GMFE
    6. 密度分布圖
- 依照用戶範例使用 `plotly.subplots`。

### 5. 資料載入器 (Data Loader) (可選更新)
#### [MODIFY] [duckdb_loader.py](file:///c:/SP_lab_Projects/sp_lab_v9_1.1/lo2cin4bt-main/dataloader/duckdb_loader.py)
- 確保能回傳 MAE/MFE 分析所需的原始 OHLCV 數據 (目前已支援)。
- (未來) 若有外資數據，新增載入支援。

## 驗證計畫

### 自動化測試
- 建立測試腳本 `tests/test_mae_mfe.py`：
    1. 模擬一小組交易與價格數據。
    2. 執行 `MAEMFEAnalyser`。
    3. 斷言 (Assert) MAE/MFE 數值計算正確。

### 手動驗證
- 在較短的日期範圍 (例如 2023-2024) 執行策略。
- 生成 MAE/MFE 報告。
- 比對視覺化輸出與預期的 FinLab 風格圖表。
