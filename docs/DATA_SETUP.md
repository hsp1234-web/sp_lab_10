# 資料準備說明

## 📋 概述

由於資料檔案過大 (超過 300MB),未包含在 GitHub repository 中。請依照以下步驟準備資料。

---

## 🎯 方法 1: 從 Google Drive 下載 (推薦)

### 步驟

1. **下載資料壓縮檔**
   - 連結: [待補充 Google Drive 連結]
   - 檔案: `taifex_data.zip` (~300MB)

2. **解壓縮到專案目錄**
   ```powershell
   # 解壓縮到 data 目錄
   Expand-Archive -Path taifex_data.zip -DestinationPath data/
   ```

3. **驗證檔案**
   ```powershell
   # 確認資料庫存在
   Test-Path data/taifex.db
   ```

---

## 🎯 方法 2: 使用自動下載腳本 (開發中)

### 步驟

```powershell
# 執行下載腳本
python scripts/download_data.py
```

### 腳本功能
- 自動從 Google Drive 下載資料
- 驗證檔案完整性
- 解壓縮到正確位置

---

## 🎯 方法 3: 從原始來源載入 (進階)

### 步驟

1. **準備原始資料**
   - 從台灣期貨交易所下載歷史資料
   - 或使用其他資料來源

2. **執行資料載入腳本**
   ```powershell
   python dataloader/main.py
   ```

3. **選擇資料來源**
   - 選擇 `5. DuckDB (Taifex)`
   - 輸入符號: `TX`
   - 輸入年份範圍

---

## 📁 預期的資料結構

完成後,您的專案目錄應該包含:

```
lo2cin4bt-main/
├── data/
│   ├── taifex.db          # DuckDB 資料庫 (~300MB)
│   └── README.md          # 資料說明
├── records/
│   ├── backtester/        # 回測結果 (空)
│   └── metricstracker/    # 績效指標 (空)
└── ...
```

---

## ✅ 驗證資料

### 檢查資料庫

```powershell
# 使用 DuckDB CLI 檢查
duckdb data/taifex.db "SELECT COUNT(*) FROM taifex_futures;"
```

### 預期輸出
```
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│       XXXXX  │  # 實際資料筆數
└──────────────┘
```

---

## ⚠️ 常見問題

### Q1: 下載連結失效
A: 請聯絡專案維護者取得最新連結

### Q2: 解壓縮失敗
A: 確認下載完整,檔案大小應為 ~300MB

### Q3: 資料庫無法開啟
A: 確認已安裝 DuckDB,或使用專案內建的 DuckDB

### Q4: 想要更新資料
A: 重新執行資料載入腳本,選擇更新的年份範圍

---

## 📞 需要協助?

如果遇到問題,請:
1. 檢查 `Troubleshooting.md`
2. 查看 GitHub Issues
3. 聯絡專案維護者

---

**最後更新**: 2025-11-24
**資料版本**: v1.0
**資料範圍**: 2019-2025 台指期貨 (TX)
