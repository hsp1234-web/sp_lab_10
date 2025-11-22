# 專案結構復原與清理報告

**日期**: `2025-11-22 19:55:00 CST`  
**作者**: Antigravity

## 摘要

本次任務成功將 `sp_lab_v9` 專案從混亂的 `V8_OLD` 結構恢復為標準化的專案架構。我們將所有核心程式碼遷移至 `src/`，移除了冗餘的 `scripts/` 與 `V8_OLD` 目錄，並建立了根目錄的 `main.py` 作為統一入口。此外，我們更新了 `AGENTS.md` 以強調保持根目錄整潔的重要性。

## 主要變更

### 檔案遷移與清理
- **遷移**: 將 `V8_OLD/src` 下的所有內容（包含 `strategies`, `data`, `backtest`）完整搬移至專案根目錄的 `src/`
- **清理**: 刪除舊版 `scripts/` 目錄與 `V8_OLD` 備份目錄，消除重複檔案造成的混淆
- **入口點**: 更新根目錄 `main.py`，使其作為 `src.main` 的包裝器 (Wrapper)，確保執行指令簡潔且路徑正確

### 文件更新
- **AGENTS.md**: 加入「保持根目錄整潔」的醒目提示，規範未來檔案存放位置
- **PROJECT_STRUCTURE.md**: 確認結構說明與現況一致

## 驗證結果
- ✅ `python main.py --help`: 成功執行，顯示指令說明
- ✅ `python -m src.backtest.engine`: 成功載入回測模組
- ✅ `output/results/`: 確認包含 `stable_conservative_trades.csv` 等關鍵回測結果
