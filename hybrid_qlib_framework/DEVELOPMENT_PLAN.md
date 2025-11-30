# Hybrid Qlib Framework 開發計畫

## 1. 專案願景與戰略目標 (Strategic Vision)

### 核心目標
建立一個**邏輯驅動 (Logic-Driven)**、**可持續優化**的量化交易系統。我們不追求短期的暴利或隨機的幸運,而是追求:
*   **低最大回撤 (Low MDD)**:首要任務是控制風險,活得久比賺得多更重要。
*   **高夏普值 (High Sharpe)**:追求單位風險下的最大報酬。
*   **真實數據驗證**:所有策略必須基於 `taifex.db` (台指期/選擇權) 真實歷史數據,嚴禁未來函數。

### 開發哲學
*   **拒絕隨機猜測**:每一個因子的開發都必須有背後的經濟邏輯或市場微結構理論支持。
*   **逐步迭代 (Step-by-Step)**:
    1.  先建立穩固的基礎設施 (Infrastructure)。
    2.  再從經典因子 (Alpha158) 建立基準線 (Baseline)。
    3.  最後開發獨有的籌碼面因子 (Unique Alpha) 進行優化。
*   **模組化成長**:系統架構必須允許我們像「堆積木」一樣,不斷加入新的因子或模型,而不需要推翻重來。

---

## 2. 技術決策脈絡 (Technical Context)

為了實現上述目標,並考量執行環境需求,我們做出了以下關鍵決策:

### Terminal-First (終端機優先)
*   **核心策略**:使用 **終端機腳本** 而非 Jupyter Notebook,確保程式碼可在任何環境執行
*   **本地開發**:使用 **WSL (Windows Subsystem for Linux)** 進行開發與測試
*   **Colab 執行**:使用 **Colab 終端機功能** 執行腳本,而非傳統 Notebook
*   **優勢**:
    - 程式碼完全模組化,易於版本控制
    - 本地與雲端環境一致性高
    - 便於自動化與批次處理
    - 避免 Notebook 的狀態管理問題

### Low-Memory Optimization (低記憶體優化)
*   **挑戰**:本地 WSL 環境記憶體 < 600MB
*   **策略**:
    - 使用 **DuckDB Streaming** 分批處理資料
    - 採用 **Parquet 格式** 減少記憶體佔用
    - 實作 **增量處理** 機制,避免一次載入全部資料
    - 使用 **Generator** 模式處理大型資料集
*   **測試原則**:本地只做小規模測試(單月資料),完整回測在 Colab 執行

### Hybrid Development (混合開發)
*   **本地 WSL**:
    - 程式碼開發與編輯
    - 小規模單元測試(單月資料,2024-01)
    - 資料格式驗證
    - 因子邏輯驗證
*   **Colab 終端機**:
    - 完整資料轉換(2017-2024)
    - 大規模回測
    - GPU 加速訓練
    - 最終報告產出
*   **優勢**:結合本地開發便利性與雲端運算能力

### Script-Based (全腳本化)
*   **原因**:所有邏輯封裝為 `.py` 腳本,確保流程可重複 (Reproducible) 且易於版本控制
*   **執行方式**:
    - 本地:直接在 WSL 終端機執行 `python main.py --test-mode`
    - Colab:在 Colab 終端機執行 `python main.py --full-backtest`
    - 無需 Notebook,完全使用命令列介面

---

## 3. 專案架構與執行計畫

### 環境需求

#### 本地 WSL 環境
*   **作業系統**: WSL2 (Ubuntu 或其他 Linux 發行版)
*   **Python**: 3.10+ (建議 3.12 與 Colab 一致)
*   **記憶體限制**: < 600MB 可用記憶體
*   **用途**: 開發、小規模測試、程式碼驗證

#### Colab 終端機環境
*   **執行環境**: Google Colab (免費版即可,Pro 版更佳)
*   **Python**: 3.12 (Colab 預設)
*   **記憶體**: 12GB RAM (免費版) / 52GB RAM (Pro 版)
*   **GPU**: Tesla T4 (可選,用於深度學習)
*   **用途**: 完整回測、大規模運算、最終驗證

#### 資料來源
*   `taifex.db` (220 MB) - 台指期日線資料
*   `taifex_options.db` (591 MB) - 選擇權資料
*   資料範圍:**2017-2024 年**

#### 核心套件
*   `qlib` - 量化投資框架
*   `duckdb` - 高效能資料處理
*   `pandas` - 資料分析
*   `pyarrow` - Parquet 格式支援
*   `lightgbm` - 機器學習模型

---

### 待執行任務 (Action Items)

#### Step 1: WSL 環境初始化
```bash
# 1. 進入專案目錄
cd /mnt/c/SP_DOC/sp_lab_v10/hybrid_qlib_framework

# 2. 檢查 Python 版本
python3 --version  # 應為 3.10+

# 3. 初始化 uv 環境
uv init

# 4. 安裝核心依賴 (輕量化,避免記憶體不足)
uv add qlib duckdb pandas pyarrow lightgbm
```

#### Step 2: 建立目錄結構
```text
hybrid_qlib_framework/
├── .venv/              # uv 自動建立
├── configs/            # 存放 Qlib YAML 設定檔
│   ├── test_config.yaml      # 測試用設定 (單月資料)
│   └── full_config.yaml      # 完整回測設定
├── data/
│   ├── bin/            # Qlib Binary Format 資料
│   ├── source/         # 原始 Parquet 資料
│   └── test/           # 測試用小資料集 (2024-01)
├── src/                # 原始碼目錄
│   ├── __init__.py
│   ├── data_converter.py    # 資料轉檔 (SQLite → Parquet → Qlib Bin)
│   ├── factor_lib.py        # 因子定義庫 (Alpha158 + 自定義)
│   ├── model_runner.py      # 模型訓練與回測引擎
│   └── utils.py             # 工具函數 (記憶體監控、日誌)
├── tests/              # 單元測試
│   ├── test_data_converter.py
│   ├── test_factor_lib.py
│   └── test_model_runner.py
├── scripts/            # 輔助腳本
│   ├── prepare_test_data.py    # 準備測試資料
│   └── upload_to_colab.sh      # 上傳至 Colab
├── main.py             # 專案入口點
├── pyproject.toml      # uv 管理檔
└── README.md           # 使用說明
```

#### Step 3: 實作核心腳本

**A. `src/data_converter.py`**
*   **目標**:將 SQLite 資料轉換為 Qlib Binary Format
*   **關鍵功能**:
    - 使用 DuckDB 讀取 SQLite,避免記憶體溢位
    - 支援增量轉換 (只處理新資料)
    - 支援測試模式 (只轉換單月資料)
*   **邏輯流程**:
    ```
    SQLite (taifex.db) 
      → DuckDB Streaming 
      → Parquet (中間格式)
      → Qlib Binary (最終格式)
    ```

**B. `src/factor_lib.py`**
*   **目標**:定義因子表達式
*   **階段一**:引入 `Alpha158` 作為 Baseline
*   **階段二**:擴充選擇權籌碼因子 (PCR, IV Spread, OI Change)
*   **記憶體優化**:使用 lazy evaluation,避免一次計算所有因子

**C. `src/model_runner.py`**
*   **目標**:執行回測並產出評估報告
*   **必須輸出的指標**:
    - IC / Rank IC (因子有效性)
    - Annualized Return (年化報酬)
    - Max Drawdown (最大回撤)
    - Sharpe Ratio (夏普值)
    - Win Rate (勝率)
*   **測試模式**:支援小資料集快速驗證

**D. `main.py`**
*   **目標**:串接完整流程,支援命令列參數
*   **使用範例**:
    ```bash
    # 測試模式 (本地 WSL,單月資料)
    python main.py --mode test --month 2024-01
    
    # 完整回測 (Colab 終端機,全部資料)
    python main.py --mode full --start 2017-01-01 --end 2024-12-31
    ```

---

## 4. 開發與測試策略

### 本地 WSL 開發流程

#### 階段一:資料準備與驗證 (記憶體友善)
```bash
# 1. 準備測試資料 (只提取 2024-01 單月)
python scripts/prepare_test_data.py --month 2024-01

# 2. 驗證資料完整性
python -m pytest tests/test_data_converter.py -v

# 3. 轉換測試資料為 Qlib 格式
python main.py --mode convert --test-only
```

#### 階段二:因子開發與測試
```bash
# 1. 測試 Alpha158 因子計算
python -m pytest tests/test_factor_lib.py -v

# 2. 驗證因子數值範圍
python main.py --mode validate-factors --test-only
```

#### 階段三:回測引擎測試
```bash
# 1. 小規模回測 (單月資料)
python main.py --mode backtest --test-only --month 2024-01

# 2. 檢查輸出指標
cat output/test_backtest_report.txt
```

### Colab 終端機執行流程

#### 準備階段
```bash
# 1. 開啟 Colab,啟用終端機功能
# (在 Colab 介面點選 "Tools" → "Command palette" → "Terminal")

# 2. 上傳專案檔案
# 方法一:從 GitHub clone
git clone https://github.com/your-repo/hybrid_qlib_framework.git
cd hybrid_qlib_framework

# 方法二:從 Google Drive 掛載
from google.colab import drive
drive.mount('/content/drive')
cd /content/drive/MyDrive/hybrid_qlib_framework
```

#### 執行完整回測
```bash
# 1. 安裝依賴
pip install qlib duckdb pandas pyarrow lightgbm

# 2. 轉換完整資料
python main.py --mode convert --full

# 3. 執行完整回測 (2017-2024)
python main.py --mode backtest --full --start 2017-01-01 --end 2024-12-31

# 4. 產出報告
python main.py --mode report --output-dir /content/drive/MyDrive/results
```

---

## 5. 記憶體優化技術細節

### DuckDB Streaming 範例
```python
import duckdb

# 分批讀取 SQLite,避免記憶體溢位
def stream_from_sqlite(db_path, batch_size=10000):
    conn = duckdb.connect()
    query = f"""
        SELECT * FROM sqlite_scan('{db_path}', 'daily_data')
        ORDER BY date
    """
    
    for batch in conn.execute(query).fetch_df_chunk(batch_size):
        yield batch  # Generator 模式,逐批處理
```

### Parquet 分區寫入
```python
import pyarrow.parquet as pq

# 按年份分區,減少單檔大小
for year in range(2017, 2025):
    df_year = df[df['date'].dt.year == year]
    pq.write_table(
        pa.Table.from_pandas(df_year),
        f'data/source/taifex_{year}.parquet'
    )
```

---

## 6. 未來優化路徑 (Optimization Path)

*   **因子擴充**:整合 `taifex_options.db`,開發選擇權專用因子
*   **模型升級**:從 LightGBM 升級至 LSTM 或 Transformer (需 GPU)
*   **動態風控**:在回測引擎中加入波動率濾網 (Volatility Filter)
*   **即時監控**:整合 Grafana 視覺化回測結果
*   **自動化部署**:建立 CI/CD 流程,自動執行回測

---

## 7. 檢查清單

### 環境設定
- [ ] WSL 環境確認 (Python 3.10+)
- [ ] uv 安裝與初始化
- [ ] 依賴套件安裝
- [ ] 目錄結構建立

### 資料處理
- [ ] 測試資料準備 (2024-01)
- [ ] 資料轉換模組實作
- [ ] DuckDB Streaming 測試
- [ ] Qlib Binary 格式驗證

### 因子開發
- [ ] Alpha158 因子實作
- [ ] 因子計算測試
- [ ] 因子數值驗證

### 回測引擎
- [ ] 模型訓練模組實作
- [ ] 回測邏輯實作
- [ ] 評估指標計算
- [ ] 本地小規模測試

### Colab 整合
- [ ] 終端機執行測試
- [ ] 完整資料轉換
- [ ] 完整回測執行 (2017-2024)
- [ ] 報告產出與下載

---

*本計畫書最後更新:2025-11-30*
