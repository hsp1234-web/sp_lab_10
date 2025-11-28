# 🚀 動態 RORO 風險管理與跨資產配置策略 - AI 助手交接文件

**交接時間**: 2025年11月27日
**交接人**: 前任 AI 助手
**專案狀態**: 階段一完成，準備進入階段二

---

## 📋 專案總體概述

### 🎯 專案目標
設計、開發、回測並驗證一個動態調整的量化交易策略，實現：
- **最大回撤 (MDD) < 10%** - 硬性風險控制約束
- **長期穩定正報酬** - 可持續盈利能力
- **低 Beta (<1)** - 相對於台灣加權指數的風險控制
- **超額回報 (Alpha)** - 風險調整後的收益增強

### 🧠 核心策略理念
**動態風險開啟/關閉 (Risk-On/Risk-Off, RORO) 機制**：
- 結合市場寬度指標和系統壓力指數，動態調整資產配置
- 採用台灣加權股價指數期貨 (TXF) + 美國長天期公債 ETF (TLT) + 黃金 ETF (GLD) 的跨資產組合
- 強調「高容錯」：不依賴即時資料、低頻執行、耐心等待高勝算機會

### 📊 策略邏輯
```
RORO 信號生成 → 資產配置調整 → 風險控制驗證 → 執行決策
     ↓              ↓              ↓              ↓
  市場寬度指標    TXF/TLT/GLD    MDD < 10%      每日監測
  系統壓力指數    動態權重調整    停損機制      波段持有
```

---

## ✅ 已完成工作 (階段一：環境與數據管道搭建)

### 1. 專案基礎設施
- ✅ **專案目錄結構**：建立 `notebooks/`, `src/`, `config/`, `data/`, `results/`
- ✅ **Python 套件配置**：`src/__init__.py`
- ✅ **依賴管理**：更新 `requirements.txt` (pandas, yfinance, requests-cache, PyYAML 等)

### 2. 核心模組開發
- ✅ **`src/config_manager.py`**：
  - `ConfigManager` 類別實現
  - YAML 配置載入和管理
  - 巢狀鍵值支援 (`config.get('data.api_keys.fred')`)

- ✅ **`src/data_loader.py`**：
  - `DataLoader` 類別實現
  - L1 快取：requests-cache + SQLite
  - Yahoo Finance 數據載入 (`load_yahoo_finance_data`)
  - 專用資產載入 (`load_strategy_assets_data`) - TXF/TLT/GLD
  - L2 儲存：Parquet 格式保存 (`save_assets_to_parquet`/`load_assets_from_parquet`)
  - 數據清理和質量檢查

### 3. 主工作流程
- ✅ **`notebooks/Main_Strategy_Workflow.ipynb`**：
  - 環境設置與模組導入
  - 配置管理初始化
  - 數據載入測試
  - 開發日誌記錄系統

### 4. 功能驗證
- ✅ **數據管道測試**：Yahoo Finance API 連接正常
- ✅ **快取機制**：API 請求快取工作正常
- ✅ **數據格式**：Parquet 儲存/載入功能正常

---

## 🔄 當前狀態

### 📁 專案結構總覽
```
sp_lab_v10/
├── notebooks/Main_Strategy_Workflow.ipynb  # 主工作流程
├── src/
│   ├── __init__.py
│   ├── config_manager.py                  # 配置管理
│   ├── data_loader.py                     # 數據載入與快取
│   ├── integrated_strategy.py             # 現有策略
│   └── ...
├── config/                                # 配置文件目錄
├── data/                                  # 數據目錄
│   ├── raw_data/                         # 原始數據
│   ├── processed_data/                   # 處理後數據 (Parquet)
│   └── cache/                            # API 快取
├── results/                               # 結果輸出
└── requirements.txt                      # 依賴包
```

### 🔧 已安裝的關鍵依賴包
```python
pandas==2.3.3           # 數據處理
yfinance==0.2.66        # Yahoo Finance API
requests-cache==1.2.0   # API 快取
PyYAML==6.0.1           # 配置管理
pyarrow==22.0.0         # Parquet 格式
matplotlib==3.8.4       # 圖表
seaborn==0.13.2         # 統計圖表
```

---

## 🎯 階段二：指標與信號開發 (你的主要任務)

### 🎪 階段二總目標
實現 RORO 信號生成的核心邏輯：
1. **市場寬度指標計算** - 台灣股市內部健康度
2. **系統壓力指數整合** - 宏觀風險評估
3. **RORO 狀態判斷** - 動態風險等級分類
4. **信號生成測試** - 初步驗證邏輯

### 📈 具體研究方向

#### 1. **市場寬度指標開發**
**研究目標**：量化台灣股市的整體健康狀況和參與度

**核心指標**：
- **騰落線 (A/D Line)**：漲家數 vs 跌家數
- **漲跌家數比 (Advance-Decline Ratio)**
- **市場參與度 (Market Participation)**

**實現建議**：
```python
# 需要台灣股市成分股數據 (可能需要替代方案)
# 參考《市場寬度量化策略研究》
# 計算公式：A/D Line = (上漲家數 - 下跌家數) 的累計值
```

**挑戰**：台灣股市成分股 PIT (Point-in-Time) 數據難以獲取免費來源

#### 2. **系統壓力指數整合**
**研究目標**：整合多個宏觀指標形成綜合壓力評估

**核心輸入** (參考一級交易商壓力指數)：
- **SOFR 利率** - 短期融資成本
- **利差指標** - 各期限利差變化
- **一級交易商持倉部位** - 公債持有量變化
- **MOVE 指數** - 債券市場波動率
- **VIX 指數** - 股票市場恐慌指數
- **準備金比率** - 聯準會政策指標

**實現路徑**：
1. 數據獲取：FRED API (fredapi) + Yahoo Finance
2. 指標標準化：Z-score 或百分位數
3. 權重分配：經驗法則或統計優化
4. 綜合計算：加權平均或主成分分析

#### 3. **RORO 狀態分類**
**研究目標**：將連續指標轉換為離散的風險狀態

**狀態定義**：
- **強 Risk-On**：市場寬度健康 + 系統壓力低
- **弱 Risk-On**：市場寬度一般 + 系統壓力中等
- **中性**：市場寬度中性 + 系統壓力中等
- **弱 Risk-Off**：市場寬度轉弱 + 系統壓力升高
- **強 Risk-Off**：市場寬度惡化 + 系統壓力極高

**決策規則**：
- 使用閾值法或聚類分析
- 考慮歷史數據的統計分佈
- 加入滯後確認機制避免假訊號

#### 4. **信號驗證框架**
**研究目標**：建立初步的信號評估機制

**驗證方法**：
- **歷史回測**：在過去數據上測試 RORO 邏輯
- **訊號品質指標**：準確率、召回率、訊號頻率
- **經濟意義**：訊號是否與市場實際狀況一致
- **前瞻性測試**：在樣本外數據上的表現

---

## 🛠️ 技術實現細節

### 🔧 建議的實現順序

#### 階段二.1：市場寬度指標
1. **數據獲取**：
   ```python
   # 台灣加權指數成分股數據
   # 考慮使用替代指標或簡化版本
   tw_stocks = get_taiwan_stocks()  # 需要實現
   ```

2. **指標計算**：
   ```python
   # 實現 A/D Line 計算
   ad_line = calculate_ad_line(tw_stocks)
   ```

#### 階段二.2：系統壓力指數
1. **數據來源**：
   ```python
   from fredapi import Fred
   fred = Fred(api_key=config.get('api_keys.fred'))
   sofr = fred.get_series('SOFR')
   ```

2. **指數合成**：
   ```python
   # 實現壓力指數計算
   pressure_index = calculate_pressure_index([sofr, move, vix, ...])
   ```

#### 階段二.3：RORO 狀態機
1. **狀態定義**：
   ```python
   RORO_STATES = {
       'STRONG_RISK_ON': 1,
       'WEAK_RISK_ON': 0.5,
       'NEUTRAL': 0,
       'WEAK_RISK_OFF': -0.5,
       'STRONG_RISK_OFF': -1
   }
   ```

2. **狀態轉換邏輯**：
   ```python
   def determine_roro_state(width_score, pressure_score):
       # 實現狀態判斷邏輯
       pass
   ```

### 📊 數據來源建議

#### 主要數據來源：
1. **Yahoo Finance** (yfinance)：美股數據、台灣指數
2. **FRED API** (fredapi)：宏觀經濟數據
3. **台灣證券交易所**：台灣股市數據 (可能需要爬蟲)

#### 數據更新頻率：
- 每日收盤後更新
- 關鍵指標：日線級別
- 宏觀數據：按公布頻率

---

## ⚠️ 重要注意事項

### 🔴 關鍵風險點
1. **數據品質**：台灣股市成分股數據獲取困難
2. **訊號滯後**：宏觀指標通常有公布延遲
3. **過度優化**：避免在歷史數據上過度擬合
4. **市場變化**：策略邏輯需考慮市場結構變遷

### 💡 設計原則
1. **模組化**：繼續遵循現有的模組化架構
2. **可測試性**：每個功能都要有單元測試
3. **文檔化**：為每個函數添加詳細註釋
4. **版本控制**：使用 Git 管理所有變更

### 🎯 成功標準
1. **指標準確性**：RORO 狀態與市場實際狀況相關性 > 60%
2. **訊號頻率**：每日產生有效訊號 (非中性狀態) 的比例合理
3. **邏輯清晰**：代碼可讀性高，邏輯易於理解和修改

---

## 📚 參考資源

### 📖 關鍵研究文件 (已轉換為 .txt)
- `research/converted_texts/量化交易.txt` - 整體專案設計
- `research/converted_texts/運用流動性商品「配對」輔助判斷市場風險.txt` - 風險預警信號
- `research/converted_texts/9月小作文-債市、避險.txt` - 系統性風險分析
- `research/converted_texts/美國債券市場深度研究.txt` - 債券市場分析
- `research/converted_texts/美股估值系統設計研究.txt` - 估值框架

### 🔗 技術資源
- **yfinance 官方文檔**：Yahoo Finance API 用法
- **FRED API 文檔**：宏觀數據獲取
- **pandas-ta 庫**：技術分析指標計算
- **vectorbt 文檔**：回測框架 (階段三使用)

### 🎯 階段二成果期望
- **模組文件**：`src/market_indicators.py` (市場寬度指標)
- **模組文件**：`src/pressure_index.py` (系統壓力指數)
- **模組文件**：`src/roro_engine.py` (RORO 狀態機)
- **測試結果**：階段二指標和信號的初步驗證報告
- **文檔更新**：更新 `Main_Strategy_Workflow.ipynb` 加入階段二實現

---

## 🚀 建議的下一步行動

### 立即開始 (Day 1-2)
1. 探索台灣股市寬度指標的數據來源
2. 設定 FRED API 金鑰並測試數據獲取
3. 設計壓力指數的具體計算公式

### 第一週重點 (Day 3-7)
1. 實現市場寬度指標計算模組
2. 實現系統壓力指數整合模組
3. 建立 RORO 狀態判斷邏輯

### 第二週重點 (Day 8-14)
1. 整合所有指標形成完整信號生成流程
2. 進行歷史數據測試和參數調優
3. 生成階段二驗證報告

---

## 💬 聯絡與支援

如有任何技術問題或需要澄清的地方，請參考：
- `notebooks/Main_Strategy_Workflow.ipynb` - 主要工作流程
- `src/data_loader.py` - 數據處理範例
- `docs/logs/` - 開發日誌和歷史記錄

**記住**：這是一個「高容錯」策略，重點在於穩定性和風險控制，而非追求極致的收益最大化。保持耐心，逐步驗證每一個環節。

祝開發順利！🎯
