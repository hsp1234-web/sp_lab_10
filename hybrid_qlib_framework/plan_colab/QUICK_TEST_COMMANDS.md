# Colab 環境測試指令快速參考

> 🚀 這些是在 Google Colab 終端機中執行的測試指令

---

## ✅ 必要測試（請依序執行）

### 測試 1：安裝 Qlib
```bash
pip install pyqlib --quiet && echo "✅ Qlib 安裝成功" || echo "❌ Qlib 安裝失敗"
```

**預期結果**：顯示 `✅ Qlib 安裝成功`

---

### 測試 2：驗證 Qlib 功能
```python
python3 << 'EOF'
try:
    import qlib
    print(f"✅ Qlib 版本: {qlib.__version__}")
    print("✅ Qlib 可正常導入")
except Exception as e:
    print(f"❌ Qlib 錯誤: {e}")
EOF
```

**預期結果**：顯示 Qlib 版本號

---

### 測試 3：測試 DuckDB 讀取 SQLite
```python
python3 << 'EOF'
import duckdb
import tempfile
import sqlite3

# 建立測試 SQLite 資料庫
with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db_path = f.name

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("CREATE TABLE test (id INTEGER, value TEXT)")
cursor.execute("INSERT INTO test VALUES (1, 'Hello'), (2, 'World')")
conn.commit()
conn.close()

# 使用 DuckDB 讀取
duck_conn = duckdb.connect()
result = duck_conn.execute(f"SELECT * FROM sqlite_scan('{db_path}', 'test')").fetchall()
print(f"✅ DuckDB 可讀取 SQLite: {result}")
duck_conn.close()

import os
os.unlink(db_path)
EOF
```

**預期結果**：顯示 `✅ DuckDB 可讀取 SQLite: [(1, 'Hello'), (2, 'World')]`

---

### 測試 4：檢查記憶體限制
```python
python3 << 'EOF'
import numpy as np

# 測試可分配的最大陣列
try:
    # 嘗試分配 8GB 陣列（12GB RAM 的 2/3）
    size_gb = 8
    arr = np.zeros((size_gb * 1024**3 // 8,), dtype=np.float64)
    print(f"✅ 可分配 {size_gb}GB 記憶體")
    del arr
except MemoryError:
    print(f"⚠️ 無法分配 {size_gb}GB 記憶體")
EOF
```

**預期結果**：顯示 `✅ 可分配 8GB 記憶體`

---

## 📋 一鍵執行所有測試

```bash
echo "=== 測試 1: 安裝 Qlib ===" && \
pip install pyqlib --quiet && echo "✅ Qlib 安裝成功" || echo "❌ Qlib 安裝失敗" && \
echo -e "\n=== 測試 2: 驗證 Qlib ===" && \
python3 -c "import qlib; print(f'✅ Qlib 版本: {qlib.__version__}')" && \
echo -e "\n=== 測試 3: DuckDB 讀取 SQLite ===" && \
python3 << 'EOF'
import duckdb, tempfile, sqlite3, os
with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db_path = f.name
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("CREATE TABLE test (id INTEGER, value TEXT)")
cursor.execute("INSERT INTO test VALUES (1, 'Hello'), (2, 'World')")
conn.commit()
conn.close()
duck_conn = duckdb.connect()
result = duck_conn.execute(f"SELECT * FROM sqlite_scan('{db_path}', 'test')").fetchall()
print(f"✅ DuckDB 可讀取 SQLite: {result}")
duck_conn.close()
os.unlink(db_path)
EOF
echo -e "\n=== 測試 4: 記憶體限制 ===" && \
python3 -c "import numpy as np; arr = np.zeros((8 * 1024**3 // 8,), dtype=np.float64); print('✅ 可分配 8GB 記憶體'); del arr" && \
echo -e "\n=== 所有測試完成 ==="
```

---

## 🔧 選用測試

### 啟用 GPU（如需要）
```python
# 在 Colab Notebook Cell 中執行
import tensorflow as tf
print("GPU 可用:", tf.config.list_physical_devices('GPU'))
```

**啟用方式**：
1. 點選 Colab 選單：`執行階段` → `變更執行階段類型`
2. 硬體加速器：選擇 `T4 GPU`
3. 點選 `儲存`

---

### 掛載 Google Drive
```python
# 在 Colab Notebook Cell 中執行
from google.colab import drive
drive.mount('/content/drive')
```

**驗證掛載**：
```bash
ls -la /content/drive/MyDrive
```

---

### 上傳檔案測試
```python
# 在 Colab Notebook Cell 中執行
from google.colab import files
uploaded = files.upload()
print(f"已上傳: {list(uploaded.keys())}")
```

---

## 📊 測試結果記錄表

請將測試結果填入下表：

| 測試項目 | 狀態 | 備註 |
|---------|------|------|
| 安裝 Qlib | ⬜ 通過 / ⬜ 失敗 | Qlib 版本: _______ |
| 驗證 Qlib | ⬜ 通過 / ⬜ 失敗 | |
| DuckDB 讀取 SQLite | ⬜ 通過 / ⬜ 失敗 | |
| 記憶體限制 | ⬜ 通過 / ⬜ 失敗 | 可分配: _____ GB |
| GPU 啟用 | ⬜ 通過 / ⬜ 未測試 | GPU 型號: _______ |
| Drive 掛載 | ⬜ 通過 / ⬜ 未測試 | |

---

## 🚨 常見問題排除

### Q1: Qlib 安裝失敗
```bash
# 嘗試指定版本
pip install pyqlib==0.9.0 --quiet

# 或使用清華鏡像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyqlib
```

---

### Q2: DuckDB 無法讀取 SQLite
```bash
# 檢查 DuckDB 版本
pip show duckdb

# 升級 DuckDB
pip install --upgrade duckdb
```

---

### Q3: 記憶體不足
```python
# 檢查當前記憶體使用
import psutil
mem = psutil.virtual_memory()
print(f"總記憶體: {mem.total / 1024**3:.2f} GB")
print(f"可用記憶體: {mem.available / 1024**3:.2f} GB")
print(f"使用率: {mem.percent}%")
```

---

## ✅ 測試完成後

請將測試結果回報，包含：
1. 所有測試的通過/失敗狀態
2. Qlib 版本號
3. 任何錯誤訊息
4. 記憶體可分配大小

這些資訊將幫助我們優化後續的開發流程！

---

*本指南最後更新：2025-11-30*
