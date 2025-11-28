# AI Agent 量化交易系統 - 實施計劃

## 專案目標

建立一個 **AI 驅動的智能交易系統**，模擬專業交易者的決策流程：
- 每天分析市場、新聞、風險
- AI 自主決策是否交易及倉位分配
- 目標績效：月虧損 < 5%、季度盈利、年化接近 SPY

---

## 系統架構

### 核心流程

```mermaid
graph TD
    A[每日市場開盤前] --> B[數據收集層]
    B --> C[AI 分析引擎]
    C --> D[決策執行層]
    D --> E[風險管理層]
    E --> F[回測驗證]
    
    B --> B1[ETF 價格數據]
    B --> B2[新聞情緒]
    B --> B3[市場指標]
    B --> B4[技術指標]
    
    C --> C1[市場狀態判斷]
    C --> C2[個股評分]
    C --> C3[風險評估]
    
    D --> D1[交易決策]
    D --> D2[倉位分配]
    
    E --> E1[最大回撤控制]
    E --> E2[倉位上限]
```

### 資料庫設計 (Database Schema)

為了提升小模型 (如 Gemma-4b) 的輸出穩定性，我們採用 **「群組化提問 (Grouped Questions)」** 策略，將多個相關問題合併為單次 AI 交互，並以結構化方式存儲。

#### 1. `market_data_daily` - 基礎行情表
```sql
CREATE TABLE market_data_daily (
    date DATE,
    symbol TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    
    -- 技術指標 (預先計算)
    sma_20 REAL,
    sma_60 REAL,
    rsi_14 REAL,
    
    PRIMARY KEY (date, symbol)
);
```

#### 2. `chip_data_daily` - 籌碼數據表 (FinMind)
```sql
CREATE TABLE chip_data_daily (
    date DATE,
    symbol TEXT,
    
    -- 三大法人買賣超
    foreign_net_buy INTEGER,  -- 外資
    trust_net_buy INTEGER,    -- 投信
    dealer_net_buy INTEGER,   -- 自營商
    
    -- 融資融券
    margin_balance INTEGER,   -- 融資餘額
    short_balance INTEGER,    -- 融券餘額
    
    PRIMARY KEY (date, symbol)
);
```

#### 3. `ai_analysis_log` - AI 分析日誌 (寬表設計)
此表存儲 AI 對各面向的解讀結果。我們不要求 AI 輸出複雜 JSON，而是輸出 `Signal|Reasoning` 格式的字串，再由程式解析存入。

```sql
CREATE TABLE ai_analysis_log (
    date DATE,
    symbol TEXT,
    
    -- [群組 1] 籌碼面解讀
    -- Prompt: "分析外資與投信動向..." -> Output: "Bullish|外資投信同步買超"
    chip_signal TEXT,      
    chip_reasoning TEXT,   
    
    -- [群組 2] 技術面解讀
    -- Prompt: "分析均線與RSI..." -> Output: "Neutral|均線糾結但RSI背離"
    tech_signal TEXT,      
    tech_reasoning TEXT,   
    
    -- [群組 3] 最終決策
    -- Prompt: "綜合以上分析..." -> Output: "BUY|0.8|0.2" (Action|Confidence|Position)
    final_action TEXT,     -- BUY / SELL / HOLD
    confidence REAL,       -- 0.0 - 1.0
    position_pct REAL,     -- 建議倉位 (0.0 - 1.0)
    
    model_used TEXT,       -- 使用的模型 (e.g., gemma:4b)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (date, symbol)
);
```

#### 4. `portfolio_history` - 投資組合歷史
```sql
CREATE TABLE portfolio_history (
    date DATE PRIMARY KEY,
    total_value REAL,
    cash REAL,
    daily_return REAL,
    max_drawdown REAL,
    
    -- 持倉明細 (JSON 格式存儲，方便擴展)
    positions JSON  -- e.g., {"2330.TW": {"shares": 1000, "cost": 500}}
);
```

---

## 實施階段

### 📍 階段一：數據基礎建設 (Data Infrastructure)

基於免費資源限制，我們採取 **「混合數據源策略 (Hybrid Data Strategy)」**：

#### 1. 數據源與更新頻率表

| 數據類型 | 來源 | 頻率 | 免費版限制/對策 | 用途 |
| :--- | :--- | :--- | :--- | :--- |
| **籌碼面** (三大法人/融資券) | **FinMind** | 每日 (盤後) | 300次/小時。我們只抓關注名單 (Watchlist)，每日一次，完全足夠。 | 判斷主力動向、散戶情緒 |
| **基本面** (營收/財報) | **FinMind** | 每月/每季 | 頻率低，無限制問題。 | 過濾績優股、長線保護短線 |
| **微觀結構** (5秒委託統計) | **FinMind** | 每日 (盤後) | 若在免費名單內，這是**關鍵數據**。可用於分析掛單虛實與短線壓力。 | 替代逐筆交易，分析盤中籌碼 |
| **價格數據** (1分K/日K) | **Yahoo Finance** | 每日/即時 | 無硬性限制。 | 計算技術指標、回測價格 |
| **選擇權/期貨** (逐筆/日報) | **TAIFEX (期交所)** | 每日 (爬蟲) | 需撰寫 Python 腳本自動下載期交所每日結算 CSV/ZIP。 | 選擇權策略回測、大額交易人分析 |

#### 2. 數據收集流程 (Pipeline) - 整合現有模組

我們將直接調用專案中已存在的成熟腳本，避免重複造輪子：

1.  **每日收盤後 (15:30+)**:
    *   啟動 `data_collector.py` (作為主控腳本)。
    *   **Step 1 (FinMind)**: 呼叫 `scripts/build_finmind_db.py` (需微調以支援 Watchlist 每日更新)。
    *   **Step 2 (Yfinance)**: 呼叫 `scripts/build_yfinance_db.py` 更新價格數據。
    *   **Step 3 (TAIFEX)**: 
        *   **期貨/選擇權**: 直接執行 `scripts/taifex_official_update.py` (下載最近 30 天官方資料)。
        *   **PCR/Delta**: 執行 `scripts/taifex_official_downloader.py`。
        *   **資料庫整合**: 執行 `scripts/build_taifex_recent_db.py` 將新下載的 CSV 匯入 `data/taifex_recent_data.db`。

2.  **資料庫存儲優化**:
    *   **FinMind/YF**: 存入 `trading_system.db` (SQLite)。
    *   **TAIFEX**: 繼續沿用現有的 DuckDB 架構 (`data/taifex_recent_data.db`)，因為 DuckDB 對於處理大量逐筆/選擇權數據效能更佳。我們只需在 Python 中透過 `duckdb` 套件讀取所需特徵即可。

#### 3. 產出物 (修正後)
*   `data_collector.py`: **(新增)** 整合型主控腳本，負責依序呼叫上述現有腳本。
*   `scripts/build_finmind_db.py`: **(修改)** 增加每日增量更新功能。
*   `scripts/build_yfinance_db.py`: **(修改)** 增加每日增量更新功能。
*   `etf_database.db`: **(移除)** 改用現有的 `trading_system.db` (SQLite) 與 `data/*.db` (DuckDB) 混合架構。

---

### 📍 階段二：AI 決策引擎 (2-3 週)

#### 核心功能

**1. 市場狀態判斷 (Market Regime Detection)**
```python
def analyze_market_state(date):
    """
    AI 分析當前市場狀態
    輸入：當日市場數據
    輸出：Bull/Bear/Sideways + 信心度
    """
    prompt = f"""
    分析以下市場數據，判斷當前市場狀態：
    
    - SPY 近 5 日報酬: {spy_returns}
    - VIX 水平: {vix}
    - 成交量變化: {volume_change}
    
    請回答：
    1. 市場狀態 (多頭/空頭/震盪)
    2. 信心度 (0-1)
    3. 主要理由 (30 字內)
    """
    
    # 使用 Gemini API 或 Ollama
    return ai_model.generate(prompt)
```

**2. 個股評分系統**
```python
def score_etf(symbol, date):
    """
    對單一 ETF 進行評分
    輸入：股票代碼、日期
    輸出：評分 (0-100)、建議動作
    """
    # 收集多維度數據
    price_data = get_price_data(symbol, days=30)
    news_sentiment = get_news_sentiment(symbol, date)
    technical_indicators = calculate_indicators(price_data)
    
    prompt = f"""
    評估 {symbol} 的投資價值：
    
    技術面：
    - 趨勢: {technical_indicators['trend']}
    - RSI: {technical_indicators['rsi']}
    - MACD: {technical_indicators['macd']}
    
    基本面/消息面：
    - 新聞數量: {news_sentiment['count']}
    - 正面情緒: {news_sentiment['positive']}%
    - 負面情緒: {news_sentiment['negative']}%
    
    請給出：
    1. 綜合評分 (0-100)
    2. 建議動作 (買入/賣出/持有)
    3. 建議倉位百分比
    4. 推理過程
    """
    
    return ai_model.generate(prompt)
```

**3. 風險評估**
```python
def assess_risk(portfolio, market_state):
    """
    評估當前風險水平
    """
    prompt = f"""
    評估投資組合風險：
    
    市場狀態: {market_state}
    當前倉位: {portfolio.positions}
    近 30 日最大回撤: {portfolio.max_drawdown}
    
    請評估：
    1. 風險等級 (低/中/高)
    2. 是否需要減倉
    3. 風險控制建議
    """
    
    return ai_model.generate(prompt)
```

#### 任務清單
- [ ] 開發 AI 提示詞模板
- [ ] 整合 Gemini 1.5 Flash API
- [ ] 建立決策邏輯流程
- [ ] 測試 AI 回應穩定性

---

### 📍 階段三：回測框架 (2 週)

#### 回測引擎設計

```python
class AITradingBacktest:
    def __init__(self, start_date, end_date, initial_capital=100000):
        self.start_date = start_date
        self.end_date = end_date
        self.capital = initial_capital
        self.portfolio = Portfolio()
        
    def run(self):
        """執行回測"""
        for date in self.trading_dates:
            # 1. 收集當日數據
            market_data = self.get_market_data(date)
            
            # 2. AI 分析市場
            market_state = self.ai_analyze_market(market_data)
            
            # 3. AI 評估每個 ETF
            decisions = {}
            for symbol in self.universe:
                score = self.ai_score_etf(symbol, date)
                decisions[symbol] = score
            
            # 4. 風險控制
            risk_check = self.assess_risk(self.portfolio, market_state)
            if risk_check['level'] == 'HIGH':
                # 啟動防守模式
                self.reduce_positions()
            
            # 5. 執行交易
            self.execute_trades(decisions, date)
            
            # 6. 記錄結果
            self.record_portfolio(date)
            
        # 生成績效報告
        return self.generate_report()
```

#### 任務清單
- [ ] 開發回測引擎
- [ ] 實現倉位管理邏輯
- [ ] 加入風險控制機制
- [ ] 產出績效報告模組

---

### 📍 階段四：優化與標準化 (2-3 週)

#### 1. 策略優化
- 測試不同 AI 提示詞版本
- 調整風險參數
- 優化倉位分配演算法

#### 2. 績效監控
建立儀表板追蹤：
- 月度報酬率
- 最大回撤
- 勝率
- Sharpe Ratio
- AI 決策準確度

#### 3. 教育材料準備
- 系統操作手冊
- AI 決策邏輯解析
- 回測報告範例
- 風險管理指南

---

## 技術選擇建議

### AI 模型選擇

| 方案 | 優點 | 缺點 | 成本 |
|------|------|------|------|
| **Gemini 1.5 Flash** | 便宜、快速、API 穩定 | 需要網路 | $0.075/1M tokens |
| **Ollama (本地)** | 免費、隱私 | 較慢、需要 GPU | 免費 |
| **Claude 3.5 Sonnet** | 推理能力強 | 較貴 | $3/1M tokens |

> **推薦**：先用 Gemini 1.5 Flash 開發，成本低且效能好

### 數據源

| 數據類型 | 推薦來源 | 成本 |
|---------|---------|------|
| ETF 價格 | yfinance | 免費 |
| 新聞 | NewsAPI | 免費額度 100 次/日 |
| 市場情緒 | FinBrain, Reddit API | 部分免費 |
| 基本面 | Alpha Vantage | 免費額度 25 次/日 |

---

## 風險管理規則

### 硬性規則（不可違反）
1. **單月最大虧損 5%** → 觸發停止交易
2. **單日最大虧損 2%** → 當日不再開新倉
3. **單一 ETF 最大倉位 20%** → 分散風險
4. **現金保留底線 10%** → 保持流動性

### AI 建議（可調整）
- 動態調整倉位比例
- 市場恐慌時減倉
- 高波動時降低槓桿

---

## 預期績效目標

### 保守估計（可實現）
- **年化報酬**: 8-12%
- **Sharpe Ratio**: 0.8-1.2
- **最大回撤**: < 15%
- **月度勝率**: 60-70%

### 與您的目標對比
| 指標 | 您的期望 | 系統預期 | 評估 |
|------|---------|----------|------|
| 月虧損 | < 5% | ✅ 可達成 | 透過風控 |
| 季度盈利 | 100% | ⚠️ 70-80% | 需要容忍偶爾虧損季度 |
| 年化報酬 | ≈ SPY (10-12%) | ✅ 可達成 | 需要一年以上數據驗證 |

---

## 成本估算

### 數據成本（月）
- NewsAPI Pro: $0-49/月
- Alpha Vantage: $0-50/月

### AI API 成本（月）
- Gemini 1.5 Flash: 估計 $5-20/月
  - 每天 20 次決策 × 30 天 = 600 次
  - 每次約 1000 tokens
  - 總計: 600K tokens ≈ $0.045

### 總成本：$10-100/月（可控）

---

## 下一步行動

### 立即可做
1. ✅ 討論並確認系統架構
2. ✅ 選擇要交易的 ETF 清單（建議 10-20 個）
3. ✅ 決定 AI 模型（Gemini vs Ollama）

### 本週任務
1. 建立資料庫架構
2. 開發數據收集模組
3. 測試 Gemini API 決策流程

### 本月目標
1. 完成階段一、二
2. 執行首次回測
3. 驗證系統可行性

---

## 參考資源

### 學術研究
- "Deep Reinforcement Learning for Trading" (2020)
- "Sentiment Analysis for Stock Price Prediction" (2021)
- "LLM-based Trading Agents" (2024)

### 開源專案
- FinRL (金融強化學習)
- Backtrader (回測框架)
- Alpaca Trading API (實盤交易)

### 業界案例
- Two Sigma: 使用 ML 做因子選股
- AQR: 結合傳統量化 + AI
- Renaissance: 純數據驅動策略

---

## 風險聲明

> ⚠️ **重要提醒**
> 
> 1. AI 交易系統不保證盈利
> 2. 過去績效不代表未來表現
> 3. 建議先用小資金測試
> 4. 定期監控 AI 決策合理性
> 5. 保持人工監督，AI 僅為輔助工具
