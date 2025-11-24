# Chandelier Stop 策略 MAE/MFE 分析結果

本資料夾包含 Chandelier Stop 趨勢追蹤策略的回測結果與 MAE/MFE 分析。

## 📁 檔案說明

### 分析結果
- **`analysis_report.md`** - 繁體中文分析報告，包含統計摘要與策略說明
- **`maemfe_charts.html`** - 互動式 Plotly 圖表 (FinLab 風格)，包含 6 個子圖
- **`trades_with_maemfe.csv`** - 完整交易記錄，含 MAE/MFE 數據
- **`trades.csv`** - 原始交易記錄

### 專案文件
- **`implementation_plan.md`** - 實作計畫 (繁體中文)
- **`task.md`** - 任務清單
- **`run_mae_mfe.py`** - 執行腳本

## 📊 圖表內容

`maemfe_charts.html` 包含以下圖表：

1. **Return Distribution** - 報酬分布直方圖
2. **Edge Ratio Time Series** - 滾動優勢比率時序圖
3. **MAE vs Return** - 最大不利幅度 vs 報酬散點圖
4. **MFE vs MAE** - 最大有利幅度 vs 最大不利幅度散點圖
5. **MFE/MAE Ratio Distribution** - 優勢比率分布
6. **MAE Density** - MAE 密度分佈 (獲利 vs 虧損)

## 🔧 策略參數

- **商品**: TX (台指期貨)
- **ATR Length**: 22
- **ATR Multiplier**: 3.0
- **分析期間**: 1998-10-01 至 2024-12-31
- **資料筆數**: 78,773 筆

## 📈 執行方式

```bash
python run_mae_mfe.py
```

## 📝 注意事項

目前回測結果僅產生 1 筆交易，建議後續優化：
- 調整 ATR multiplier (降低至 2.0-2.5)
- 縮短 length (測試 10-15)
- 檢查資料時間序列
- 加入額外進場條件

---

**產生時間**: 2025-11-24  
**框架版本**: lo2cin4bt v9.1.1
