# WSL 本地開發指南

## 🎯 目標

在 **記憶體 < 600MB** 的 WSL 環境中,完成 Qlib 框架的開發與測試,然後在 Colab 終端機執行完整回測。

---

## 📋 開發階段規劃

### 階段一:環境建置 (30 分鐘)
**目標**:建立可運行的 Python 環境,安裝最小依賴

**步驟**:
```bash
# 1. 確認 WSL 環境
cd /mnt/c/SP_DOC/sp_lab_v10/hybrid_qlib_framework
pwd

# 2. 檢查 Python 版本
python3 --version  # 需要 3.10+

# 3. 檢查可用記憶體
free -h

# 4. 初始化 uv (如果尚未安裝)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 5. 初始化專案
uv init

# 6. 安裝最小依賴 (分批安裝,避免記憶體不足)
uv add duckdb
uv add pandas
uv add pyarrow
```

**驗證**:
```bash
# 測試 DuckDB 是否正常
python3 -c "import duckdb; print('DuckDB OK')"

# 測試 Pandas 是否正常
python3 -c "import pandas; print('Pandas OK')"
```

---

### 階段二:資料準備 (1 小時)
**目標**:從 `taifex.db` 提取測試資料 (單月),轉換為 Parquet

**實作 `scripts/prepare_test_data.py`**:
```python
#!/usr/bin/env python3
"""
準備測試資料 - 只提取 2024-01 單月資料
記憶體優化:使用 DuckDB Streaming,避免一次載入全部資料
"""
import duckdb
import sys
from pathlib import Path

def prepare_test_data(db_path, output_dir, test_month='2024-01'):
    """
    從 SQLite 提取單月資料,存為 Parquet
    
    Args:
        db_path: taifex.db 路徑
        output_dir: 輸出目錄
        test_month: 測試月份 (格式: YYYY-MM)
    """
    print(f"📊 準備測試資料: {test_month}")
    
    # 建立輸出目錄
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用 DuckDB 讀取 SQLite (記憶體友善)
    conn = duckdb.connect(':memory:')
    
    # 查詢單月資料
    query = f"""
        SELECT 
            date,
            symbol,
            open,
            high,
            low,
            close,
            volume
        FROM sqlite_scan('{db_path}', 'daily_data')
        WHERE strftime('%Y-%m', date) = '{test_month}'
        ORDER BY date, symbol
    """
    
    print(f"🔍 執行查詢...")
    df = conn.execute(query).fetch_df()
    
    print(f"✅ 提取 {len(df)} 筆資料")
    print(f"📅 日期範圍: {df['date'].min()} ~ {df['date'].max()}")
    print(f"📈 商品數量: {df['symbol'].nunique()}")
    
    # 存為 Parquet
    output_file = output_dir / f"test_data_{test_month}.parquet"
    df.to_parquet(output_file, index=False)
    
    print(f"💾 已儲存: {output_file}")
    print(f"📦 檔案大小: {output_file.stat().st_size / 1024:.2f} KB")
    
    return output_file

if __name__ == '__main__':
    # 路徑設定
    DB_PATH = '/mnt/c/SP_DOC/sp_lab_v10/data/taifex.db'
    OUTPUT_DIR = './data/test'
    
    # 執行
    prepare_test_data(DB_PATH, OUTPUT_DIR, test_month='2024-01')
```

**執行測試**:
```bash
# 建立 scripts 目錄
mkdir -p scripts

# 執行資料準備
python3 scripts/prepare_test_data.py

# 驗證輸出
ls -lh data/test/
```

---

### 階段三:資料轉換模組 (2 小時)
**目標**:實作 `src/data_converter.py`,將 Parquet 轉為 Qlib Binary

**關鍵設計**:
- 使用 Generator 模式,逐批處理
- 支援測試模式 (只處理小資料)
- 記憶體監控,避免 OOM

**實作骨架**:
```python
#!/usr/bin/env python3
"""
資料轉換模組
Parquet → Qlib Binary Format
"""
import pandas as pd
import qlib
from pathlib import Path
from typing import Generator

class DataConverter:
    """資料轉換器 - 記憶體優化版本"""
    
    def __init__(self, test_mode=True):
        self.test_mode = test_mode
        
    def load_parquet_streaming(self, file_path: Path, 
                                batch_size: int = 5000) -> Generator:
        """
        串流讀取 Parquet,避免記憶體溢位
        
        Args:
            file_path: Parquet 檔案路徑
            batch_size: 每批次筆數
            
        Yields:
            DataFrame 批次
        """
        # 使用 PyArrow 分批讀取
        import pyarrow.parquet as pq
        
        parquet_file = pq.ParquetFile(file_path)
        
        for batch in parquet_file.iter_batches(batch_size=batch_size):
            yield batch.to_pandas()
    
    def convert_to_qlib(self, input_file: Path, output_dir: Path):
        """
        轉換為 Qlib Binary Format
        
        Args:
            input_file: 輸入 Parquet 檔案
            output_dir: 輸出目錄
        """
        print(f"🔄 開始轉換: {input_file}")
        
        # TODO: 實作轉換邏輯
        # 1. 讀取 Parquet
        # 2. 欄位映射 (symbol → instrument, date → datetime)
        # 3. 呼叫 qlib.run.dump_bin()
        
        pass

if __name__ == '__main__':
    converter = DataConverter(test_mode=True)
    # 測試程式碼
```

---

### 階段四:因子庫開發 (2 小時)
**目標**:實作 `src/factor_lib.py`,定義 Alpha158 因子

**策略**:
- 先使用 Qlib 內建 Alpha158
- 後續再自定義因子

---

### 階段五:回測引擎 (3 小時)
**目標**:實作 `src/model_runner.py`,執行小規模回測

**測試資料**:
- 訓練集: 2024-01-01 ~ 2024-01-15
- 測試集: 2024-01-16 ~ 2024-01-31

---

## 🧪 測試策略

### 單元測試 (pytest)
```bash
# 安裝 pytest
uv add pytest --dev

# 執行所有測試
pytest tests/ -v

# 只測試資料轉換
pytest tests/test_data_converter.py -v
```

### 記憶體監控
```python
import psutil
import os

def check_memory():
    """檢查當前記憶體使用"""
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / 1024 / 1024
    print(f"💾 記憶體使用: {mem_mb:.2f} MB")
    
    if mem_mb > 500:
        print("⚠️ 警告:記憶體使用接近上限!")
```

---

## 🚀 Colab 終端機執行

### 如何在 Colab 開啟終端機

1. 開啟 Google Colab
2. 點選上方選單 **"Tools"** → **"Command palette"**
3. 搜尋 **"Terminal"** 並選擇
4. 終端機會在下方開啟

### 執行流程
```bash
# 1. Clone 專案 (或從 Drive 掛載)
git clone https://github.com/your-repo/hybrid_qlib_framework.git
cd hybrid_qlib_framework

# 2. 安裝依賴
pip install qlib duckdb pandas pyarrow lightgbm

# 3. 執行完整回測
python main.py --mode full --start 2017-01-01 --end 2024-12-31
```

---

## 📊 預期時程

| 階段 | 預估時間 | 執行環境 |
|------|---------|---------|
| 環境建置 | 30 分鐘 | WSL |
| 資料準備 | 1 小時 | WSL |
| 資料轉換模組 | 2 小時 | WSL |
| 因子庫開發 | 2 小時 | WSL |
| 回測引擎 | 3 小時 | WSL |
| 本地測試 | 1 小時 | WSL |
| **總計 (本地)** | **9.5 小時** | - |
| Colab 整合 | 1 小時 | Colab |
| 完整回測 | 30 分鐘 | Colab |
| **總計 (含 Colab)** | **11 小時** | - |

---

## ✅ 下一步行動

1. **立即開始**:環境建置與資料準備
2. **今日目標**:完成階段一、二 (環境 + 測試資料)
3. **明日目標**:完成階段三、四 (轉換 + 因子)
4. **後天目標**:完成階段五並在 Colab 驗證

---

*本指南最後更新:2025-11-30*
