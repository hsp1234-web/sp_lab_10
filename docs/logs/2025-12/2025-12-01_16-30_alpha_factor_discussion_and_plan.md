# 2025-12-01_16-30_alpha_factor_discussion_and_plan.md

- 任務名稱：Alpha 因子實現方案討論與下一步計畫
- 日期：2025-12-01 16:30 CST
- 作者：AI Assistant
- 摘要：本次討論聚焦於基於 UC 演講內容，分析現有 Alpha 因子模組的實現現狀，並規劃後續 Alpha158 與 Alpha360 在 Colab 環境下的開發路線。目標是建立一個「窮人版 UC 平台」，以日頻資料實現因子工廠、回測與風險分析。

## 📋 討論與演講分析摘要

### 🎯 UC 演講核心要點：

1.  **核心投資哲學**：追求高 Sharpe Ratio、低 Max Drawdown，量化一切決策。
2.  **因子數量與穩定性**：強調多因子組合（1000+）能有效過濾雜訊，提升策略穩定性。
3.  **Quant 發展階段**：從人工策略演進至平台化、AI 因子、GPU 叢集、自動回測，最終目標是可解釋 AI。
4.  **硬體與算力**：UC 等級機構利用 1000 張 A100 GPU 及 AWS 進行大規模因子訓練、海量回測模擬、強化學習及自動因子挖掘。

### ✅ 您目前的 Alpha 因子模組 (`hybrid_qlib_framework/src/alpha_factors.py`) 現狀：

- 已實現 `AlphaFactorCalculator` 類，包含 6 大類（趨勢、動量、波動性、成交量、技術指標、相關性）約 100+ 個因子。
- 具備 RSI, MACD, Bollinger Bands, Williams %R, KDJ, ATR, OBV, Parkinson Volatility, 線性迴歸斜率等技術指標。

### 💡 建議的實作策略：**混合方式**

- 以現有模組為基礎，參考 Qlib 的因子定義，並針對台期貨市場進行優化。
- 利用 Colab + CPU 資源，實現「日線版本」的因子工廠與回測流程。

## 🚀 建議的實作計劃 (Colab 環境下的「窮人版 UC 平台」)

### 第一階段：完善基礎因子 (預計 1-2 週)

1.  **修復 `create_alpha158_factors()` 因子名稱不匹配問題**：
    - 調整 `alpha158_factors` 列表中的因子名稱，使其與 `AlphaFactorCalculator` 實際產出的因子名稱一致。
    - 調整 `window_sizes` 參數，以支援更多常用的時間窗口（如 14 天）。
2.  **加入台期貨特有因子**：
    - 開發基於未平倉量 (Open Interest, OI) 的因子。
    - 開發基於外資、投信籌碼的因子。
    - 開發台指期貨價差結構因子 (例如近月減遠月)。
    - 開發與台灣加權指數 (TWII) 或 VIX 相關的因子。

### 第二階段：整合台期貨數據 (預計 2-3 週)

1.  **標準化 FinMind 台期貨日資料**：
    - 將 FinMind 數據轉換為 Qlib 要求的 `date, stock_id, open, high, low, close, volume, factor` 欄位結構。
    - 將未平倉量、法人買賣超、大盤指數、VIX 等欄位整合到日資料表中。
    - 將處理後的資料儲存為 SQLite 或 Parquet 格式，方便 Colab 掛載 Google Drive 讀寫。
2.  **將因子計算整合到 DataConverter (或類似流程)**：
    - 修改 `alpha_factors.py`，使其能直接讀取處理後的台期貨數據，並計算出所有因子。
    - 確保因子計算能處理 MultiIndex 數據結構，以適應多標的資料。
    - 優化計算效能，局部導入 `numba` 或其他加速庫。

### 第三階段：因子選擇與優化 (預計 2-3 週)

1.  **計算每個因子的 IC (Information Coefficient)**：
    - 開發工具計算因子值與未來報酬的 Spearman 相關係數。
    - 設定 IC 門檻 (例如 > 0.05) 來篩選有效因子。
2.  **進行分組報酬測試**：
    - 將股票（或期貨合約）依因子值排序分成 5 組 (Q1-Q5)。
    - 檢驗各組的未來報酬是否呈現單調性。
3.  **處理多重共線性問題**：
    - 使用相關係數矩陣識別高度相關的因子，並進行去冗餘。
    - 考慮使用 PCA 或其他降維方法。
4.  **回測驗證**：
    - 使用 Qlib 的 `TopkDropoutStrategy` 進行回測，評估策略的 annualized return, information ratio (IR), max drawdown (MDD) 等指標。

### 第四階段：機器學習整合 (預計 3-4 週)

1.  **因子輸入到 LightGBM 模型**：
    - 將篩選出的因子作為特徵，輸入 LightGBM 等樹模型進行預測。
    - 實現特徵選擇，找出最重要的因子組合。
2.  **建立完整的預測流程**：
    - 建立從因子計算到模型訓練、預測、回測的自動化 pipeline。
    - 考慮導入簡單的強化學習 (Reinforcement Learning) agent 進行組合權重優化。
3.  **LLM 輔助因子研究**：
    - 利用大模型協助解析量化論文，將因子公式轉化為可執行的 Python/Pandas/SQL 程式碼。
    - 讓大模型根據回測結果進行文字分析，解釋因子有效性或失效原因。

## 📚 參考資料

- UC 演講逐字稿與實作討論文件
- Qlib 官方文件與範例
- `hybrid_qlib_framework/src/alpha_factors.py`

