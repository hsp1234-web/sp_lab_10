# `src`：核心原始碼目錄

本目錄 (`src`) 包含了所有量化研究專案的核心程式碼，是整個系統的引擎室。這裡的模組負責從數據獲取、清洗、特徵工程、訊號生成，到回測與視覺化的完整流程。

## 目錄結構

```
src/
├── backtest/             # 回測引擎相關模組
├── data/                 # 數據處理相關模組
├── output/               # 腳本輸出範例與日誌
├── strategies/           # 交易策略實作
├── __init__.py           # 將 src 標記為一個 Python 套件 (Package)
├── backtest.py           # (舊) 回測引擎主體
├── clean.py              # (舊) 數據清洗腳本
├── cost.py               # 交易成本模型
├── feat.py               # 特徵工程
├── fetch.py              # (舊) 數據獲取腳本
├── generate_report.py    # 產生回測報告
├── main.py               # (舊) 數據管線入口點
├── optimizer.py          # 策略最佳化工具
├── optimizer_utils.py    # 最佳化工具的輔助函式
├── run_optimization.py   # 執行策略最佳化
├── sp_signal.py          # 交易訊號生成
├── stats.py              # 統計分析工具
└── viz.py                # 視覺化工具
```

## 核心模組簡介

-   **數據流程**:
    -   `data/fetch.py`: 從外部 API (如 FinMind) 獲取市場數據。
    -   `data/process.py`: 對原始數據進行清洗、格式化與儲存。
-   **策略與訊號**:
    -   `feat.py`: 計算技術指標 (如移動平均線、RSI) 作為策略特徵。
    -   `sp_signal.py`: 根據特徵生成具體的買賣訊號 (1, -1, 0)。
    -   `strategies/`: 存放具體的策略邏輯腳本。
-   **回測與分析**:
    -   `backtest/engine.py`: 核心回測引擎，根據交易訊號模擬交易過程。
    -   `stats.py`: 對策略結果進行統計分析 (如夏普比率、最大回撤)。
    -   `cost.py`: 模擬交易手續費與滑價。
-   **最佳化**:
    -   `optimizer.py`: 使用基因演算法等工具尋找最佳策略參數。
-   **視覺化與報告**:
    -   `viz.py`: 將回測結果（如權益曲線）繪製成圖表。
    -   `generate_report.py`: 產生包含圖表與關鍵績效指標 (KPIs) 的綜合報告。

*註：標示為 (舊) 的檔案是專案早期版本所使用，目前其功能已被更模組化的腳本 (如 `data/` 和 `backtest/` 中的腳本) 所取代。*
