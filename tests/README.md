# `tests`：測試代碼目錄

本目錄 (`tests`) 用於存放所有與專案相關的測試代碼，以確保 `src` 目錄中各個模組的正確性、穩定性和可維護性。

本專案遵循**測試驅動開發 (TDD)** 的實踐，理論上 `src` 中的每一個核心功能都應該有對應的測試案例。

## 結構

測試檔案的結構應盡可能地對應 `src` 目錄的結構。例如：

```
tests/
├── test_data/
│   ├── test_fetch.py
│   └── test_process.py
├── test_backtest/
│   └── test_engine.py
└── test_sp_signal.py
```

## 如何執行測試

你可以使用 `pytest` 來執行所有測試。請確保你已經安裝了 `requirements.txt` 中所有的開發依賴。

```bash
# 執行所有測試
pytest

# 執行特定檔案的測試
pytest tests/test_data/test_fetch.py
```

---
*註：此目錄目前為空，我們將在後續的開發階段，為核心功能補上對應的單元測試。*
