# 根目錄整理與環境修復

**日期**: `2025-11-24 01:40:00 CST`  
**作者**: Antigravity

## 摘要

本此任務主要針對專案根目錄進行整理，使其符合 `AGENTS.md` 的規範。同時解決了 Python 環境中 `pyenv` 未設定導致的執行錯誤，並修復了 `backtest.py` 的命名衝突。

## 主要變更

### 檔案結構重整
- **Output 檔案**: 將所有日誌與輸出檔 (`*.txt`) 移動至 `output/` 目錄。
- **測試程式**: 將 `simple_test.py` 移動至 `tests/` 目錄。
- **文件**: 將 `Pandas_ta_fix.txt` 移動至 `docs/` 目錄。
- **執行檔**: 將根目錄的 `backtest.py` 移動並重新命名為 `src/run_backtest.py`，以避免與 `src/backtest.py` 模組衝突。

### 程式碼修正
- **`src/run_backtest.py`**: 
    - 修正了 `sys.path` 設定，確保能正確引用專案根目錄的 `config.py`。
    - 補回遺失的 `import time`。

### 環境設定
- **Pyenv**: 發現系統未設定全域 Python 版本，導致 `python` 指令失敗。已協助使用者設定 `pyenv global 3.11.9`，解決了 Silent Output 與執行失敗的問題。

## 驗證結果

- [x] **根目錄檢查**: 確認根目錄僅保留 `main.py`, `config.py` 及必要文件，其餘皆已歸位。
- [x] **程式執行**: 驗證 `src/run_backtest.py` 可成功執行 (Exit Code 0)。
- [x] **環境驗證**: 透過寫入檔案測試，確認 Python 環境功能正常。

## 備註

- 建議使用者未來直接使用 `python src/run_backtest.py` 來執行回測。
- 專案依賴維持在 Python 3.11 以確保最佳相容性。
