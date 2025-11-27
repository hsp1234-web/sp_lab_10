# 📋 SP Lab V10 量化交易專案交接文件

## 🎯 專案總覽

**專案名稱**: SP Lab V10 - 台灣期貨量化交易策略開發平台

**主要目標**: 開發並驗證台指期貨與選擇權的量化交易策略

**技術架構**: Python + DuckDB + lo2cin4bt 回測框架

---

## ✅ 已完成的核心工作

### 1. 資料基礎建設
| 資料來源 | 狀態 | 資料量 | 日期範圍 | 用途 |
|---------|-----|-------|---------|------|
| **台灣期貨交易所歷史資料** | ✅ 完整 | 1998-2024年 | 期貨+選擇權 | 回測用 |
| **台灣期貨交易所近期資料** | ✅ 部分完成 | PCR:22筆 | 最近30天 | 即時情緒指標 |
| **FinMind API** | ✅ 免費可用 | 56,995筆 | 2010-2025 | 補充資料源 |

### 2. 開發的策略框架
- ✅ **整合策略** (`src/integrated_strategy.py`) - 支援多資料源
- ✅ **Chandelier策略** - 已實作但參數需優化 (勝率 4.3%, 平均虧損 -77.76%)
- ✅ **雙均線策略** (`lo2cin4bt-main/backtester/Dual_MA_Strategy_backtester.py`) - 新實作 (勝率 9.9%, 平均虧損 -1.34%)
- ✅ **SMA策略** - 已實作並通過基本測試
- ✅ **月度買進持有策略** - 已實作並通過測試

### 3. 工具與腳本
- ✅ **資料下載器** - 台灣期貨交易所官方資料
- ✅ **資料庫建置工具** - 自動化資料匯入
- ✅ **回測引擎** - lo2cin4bt 框架整合
- ✅ **驗證腳本** - 資料品質檢查

---

## 🔄 下一步研究方向

### 優先順序 1: 策略優化與開發 (立即可開始)

#### A. 雙均線策略優化 ⭐ **當前重點**
**目前狀態**: 已實作並測試，勝率 9.9%，平均虧損 -1.34%
**優化方向**:
```python
# 參數優化測試
fast_periods = [10, 15, 20, 25]      # 快線週期
slow_periods = [40, 50, 60, 80]      # 慢線週期
volume_multipliers = [1.1, 1.2, 1.5, 2.0]  # 成交量放大倍數

# 策略改進
- 只做多頭趨勢 (移除空頭邏輯)
- 加入 RSI 過濾 (RSI > 50 進場)
- 優化停損邏輯
```

#### B. Chandelier 策略診斷
**目前問題**: 數據異常導致虛假虧損，勝率 4.3%，平均虧損 -77.76%
**建議行動**:
```python
# 數據清理
- 過濾 2018 年前的舊數據
- 移除異常價格記錄 (<100 或 >30000)
- 驗證數據完整性

# 參數重新測試
- 使用乾淨數據重新回測
- 比較不同參數組合表現
```

#### C. RSI + 布林帶策略實作
**策略邏輯**:
```python
# 進場: RSI(14) < 30 + 價格觸及布林帶下軌 + 前K收紅
# 出場: RSI(14) > 70 或 價格回到中軌 或 持有超過5天
```

#### C. RSI + 布林帶均值回歸策略
**策略邏輯**:
```python
# 進場: RSI(14) < 30 + 價格觸及布林帶下軌 + 前K收紅
# 出場: RSI(14) > 70 或 價格回到中軌 或 持有超過5天
```

### 優先順序 2: 資料來源擴展

#### A. 擴展台灣期貨交易所資料
目前只取得PCR資料，可進一步取得:
- 期貨每日行情 (futures_daily)
- 選擇權每日行情 (options_daily)
- 三大法人資料 (institutional_investors)

#### B. 整合更多市場指標
- Delta值計算 (Black-Scholes模型)
- 隱含波動率
- 市場恐懼指數

### 優先順序 3: 策略評估與組合

#### A. 建立策略比較框架
- 多策略同時回測
- 績效指標對比表格
- 視覺化分析

#### B. 投資組合優化
- 多策略動態配置
- 風險平價配置
- 月度正報酬機率優化

---

## 📚 可用的資源總覽

### 🎯 核心資料庫

#### 1. `data/taifex.db`
- **內容**: 台灣期貨交易所歷史期貨資料
- **資料量**: 涵蓋1998-2024年
- **用途**: 長期回測
- **查詢範例**:
```python
import duckdb
con = duckdb.connect('data/taifex.db')
df = con.execute("SELECT * FROM futures_data WHERE Symbol='TX'").df()
```

#### 2. `data/taifex_options.db`
- **內容**: 台灣期貨交易所歷史選擇權資料
- **資料量**: 約308萬筆
- **用途**: 選擇權策略回測
- **查詢範例**:
```python
con = duckdb.connect('data/taifex_options.db')
df = con.execute("SELECT * FROM options_data WHERE Symbol='TXO'").df()
```

#### 3. `data/taifex_recent_data.db`
- **內容**: 近期官方資料（PCR等）
- **資料量**: PCR 22筆
- **用途**: 市場情緒分析
- **查詢範例**:
```python
con = duckdb.connect('data/taifex_recent_data.db')
df = con.execute("SELECT * FROM pcr_data").df()
```

#### 4. `data/finmind.db`
- **內容**: FinMind API 台指期資料
- **資料量**: 56,995筆
- **用途**: 補充即時資料
- **查詢範例**:
```python
con = duckdb.connect('data/finmind.db')
df = con.execute("SELECT * FROM ohlcv").df()
```

### 🛠️ 開發工具腳本

#### 資料處理相關
- `scripts/taifex_official_downloader.py` - 下載官方資料
- `scripts/build_taifex_recent_db.py` - 建置近期資料庫
- `scripts/build_finmind_db.py` - 建置FinMind資料庫

#### 策略測試相關
- `scripts/run_chandelier_backtest.py` - Chandelier策略回測
- `scripts/run_quick_feedback.py` - 快速回饋測試

#### 驗證工具
- `scripts/verify_taifex_db.py` - 資料庫驗證
- `scripts/check_options_db.py` - 選擇權資料庫檢查

### 🎯 策略框架

#### 1. `src/integrated_strategy.py`
- **功能**: 整合多資料源的策略框架
- **狀態**: 已完成基本實作
- **使用方式**:
```python
from src.integrated_strategy import IntegratedStrategy, create_default_config
strategy = IntegratedStrategy(create_default_config())
```

#### 2. `src/debug_strategy.py`
- **功能**: 策略除錯工具
- **用途**: 快速測試策略邏輯

#### 3. `lo2cin4bt-main/`
- **功能**: 專業回測引擎
- **狀態**: 已整合到專案
- **文檔**: `lo2cin4bt-main/README.md`

### 📊 設定與配置

#### 1. `config/` 目錄
- `backtest_config_template.json` - 回測配置範本
- `chandelier_backtest_config.json` - Chandelier策略配置
- `quick_feedback.json` - 快速回饋配置

#### 2. `output/` 目錄
- 所有回測結果和分析報告
- `Chandelier_MAE_MFE/` - Chandelier策略分析結果

### 📖 開發文檔

#### 1. 專案指南
- `AGENTS.md` - AI代理協作指南
- `README.md` - 專案總覽
- `QUANT_STRATEGY_DEVELOPMENT_PLAN.md` - 策略開發計畫

#### 2. 資料說明
- `data/README.md` - 資料庫使用指南

#### 3. 開發日誌
- `docs/logs/2025-11/` - 所有開發記錄
- 最新的綜合總結: `2025-11-27_03-30_comprehensive_progress_summary.md`

---

## 🚀 建議的下一步執行順序

### 階段一：立即可開始 (1-2小時) ⭐ **已更新**
1. **雙均線策略參數優化** - 測試不同EMA週期組合，提升勝率至30%+
2. **單向策略測試** - 只做多頭趨勢，簡化邏輯
3. **加入過濾條件** - RSI確認，減少假訊號

### 階段二：核心策略開發 (2-3天) ⭐ **已更新**
4. **RSI+布林帶策略實作** - 均值回歸邏輯，補充趨勢策略
5. **策略比較框架** - 雙均線 vs RSI布林帶 vs Chandelier
6. **參數網格搜索** - 自動化優化所有策略參數

### 階段三：進階功能 (1-2週)
7. **擴展資料來源** - 取得更多市場指標
8. **投資組合優化** - 多策略動態配置
9. **風險管理強化** - 停損停利優化

---

## ⚠️ 注意事項

### 技術限制
1. **Delta資料**: 台灣期貨交易所不提供直接下載，需自行計算
2. **即時資料**: 目前為每日更新，可考慮即時資料源
3. **運算效能**: 大型回測可能需要優化

### 開發建議
1. **從小開始**: 先修復現有策略，再開發新策略
2. **充分測試**: 每個策略都要通過完整的回測驗證
3. **記錄一切**: 按照`AGENTS.md`規範記錄所有開發過程
4. **成本控制**: 優先使用DeepSeek V3.1，複雜推理時使用R1

---

## 📞 聯絡與支援

如有任何問題，請參考：
- 📖 `docs/logs/` - 完整開發歷史
- 🔧 `AGENTS.md` - 開發規範
- 📊 `data/README.md` - 資料使用指南

**專案狀態**: 已實作雙均線策略，正進行策略優化階段！

---
*最後更新: 2025-11-27 03:50 CST*
