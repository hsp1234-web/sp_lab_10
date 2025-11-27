# 🚀 RORO 動態風險管理策略使用指南

## 概述

RORO (Risk-On/Risk-Off) 動態風險管理策略是一個量化交易系統，能夠根據市場寬度和系統壓力動態調整資產配置，實現「最大回撤 < 10%」的風險控制目標。

## 🎯 核心理念

- **動態調整**: 結合市場寬度指標和系統壓力指數，動態調整風險敞口
- **跨資產配置**: TXF (台灣指數期貨) + TLT (長天期美債ETF) + GLD (黃金ETF)
- **高容錯設計**: 不依賴即時數據，適合波段持有策略

## 📊 策略邏輯

```
市場寬度指標 → 系統壓力指數 → RORO 狀態 → 資產配置
     ↓              ↓              ↓          ↓
  台灣股市健康度    宏觀風險評估    風險等級    TXF/TLT/GLD配比
```

## 🏗️ 系統架構

### 核心模塊

1. **市場寬度指標** (`market_indicators.py`)
   - 計算台灣股市的騰落線 (A/D Line)
   - 評估市場參與度和健康狀況

2. **系統壓力指數** (`pressure_index.py`)
   - 整合 SOFR、利差、VIX、MOVE 等宏觀指標
   - 綜合評估系統性風險水平

3. **RORO 狀態引擎** (`roro_engine.py`)
   - 將指標轉換為風險狀態 (強/弱 Risk-On/Off)
   - 生成資產配置決策

4. **信號生成器** (`roro_signal_generator.py`)
   - 整合所有模塊的主程式
   - 提供回測和報告功能

5. **信號驗證器** (`signal_validator.py`)
   - 評估信號品質和預測能力
   - 統計檢定和穩健性分析

## 🚀 快速開始

### 環境準備

```bash
# 安裝依賴包
pip install pandas numpy yfinance requests matplotlib seaborn scipy scikit-learn

# 安裝選用包 (用於宏觀數據)
pip install fredapi statsmodels
```

### 基本使用

```python
from src.roro_signal_generator import ROROSignalGenerator

# 初始化信號生成器
generator = ROROSignalGenerator()

# 生成 RORO 信號 (最近一年)
signals = generator.generate_signals(
    start_date='2024-01-01',
    end_date='2024-12-01'
)

# 查看最新信號
if signals:
    print("最新 RORO 狀態:", signals['roro_state'].iloc[-1])
    print("投資決策:", signals['investment_decision'].iloc[-1])
    print("資產配置:", generator.roro_engine.get_asset_allocation(
        generator.roro_engine.generate_investment_decision(
            signals['roro_state'].iloc[-1]
        )
    ))
```

### 回測分析

```python
# 運行回測
backtest_results = generator.run_backtest(signals)

# 生成報告
report_path = generator.generate_report(signals, backtest_results, 'html')

# 創建可視化
plot_files = generator.create_visualizations(signals, backtest_results)
```

### 信號驗證

```python
from src.signal_validator import SignalValidator

validator = SignalValidator()
validation_results = validator.validate_signal_quality(signals)

# 生成驗證報告
validation_report = validator.generate_validation_report(validation_results)
print(validation_report)
```

## 📈 風險狀態說明

| 狀態 | 數值 | 市場寬度 | 系統壓力 | 資產配置 (TXF/TLT/GLD) |
|------|------|----------|----------|----------------------|
| 強風險開啟 | 2 | 健康 | 低 | 60%/30%/10% |
| 弱風險開啟 | 1 | 一般 | 中等 | 40%/40%/20% |
| 中性 | 0 | 中性 | 中等 | 20%/50%/30% |
| 弱風險關閉 | -1 | 轉弱 | 升高 | 10%/60%/30% |
| 強風險關閉 | -2 | 惡化 | 極高 | 0%/70%/30% |

## 🔧 配置說明

### FRED API 配置

```python
# 在 config/roro_config.yaml 中設置
api_keys:
  fred: "your_fred_api_key_here"
```

獲取 FRED API 金鑰: https://fred.stlouisfed.org/docs/api/api_key.html

### 自定義參數

```python
# 自定義 RORO 引擎參數
from src.roro_engine import ROROEngine

engine = ROROEngine()

# 調整狀態閾值
engine.state_thresholds = {
    'market_width': {
        'strong_bullish': 1.2,    # 調整市場寬度閾值
        'neutral': 0.0,
        'strong_bearish': -1.2,
    },
    'system_pressure': {
        'low_pressure': -0.8,     # 調整壓力閾值
        'high_pressure': 0.8,
    }
}
```

## 📊 數據來源

### 主要數據來源
- **Yahoo Finance**: 台灣股市數據、VIX指數
- **FRED API**: SOFR、利差等宏觀經濟數據
- **台灣證券交易所**: 指數成分股數據 (未來擴展)

### 更新頻率
- 日終數據: 每日收盤後更新
- 實時指標: 視數據源而定 (15分鐘-24小時延遲)
- 宏觀數據: 按公布頻率更新

## 🎛️ 高級功能

### 自定義指標權重

```python
# 在 pressure_index.py 中調整指標權重
self.indicator_weights = {
    'SOFR': 0.20,              # 提高 SOFR 權重
    'spread_10y2y': 0.18,      # 調整利差權重
    'VIX': 0.25,               # 提高 VIX 權重
    'MOVE': 0.17,
    'high_yield_spread': 0.12,
    'industrial_production': 0.08,
}
```

### 添加新指標

```python
# 擴展 SystemPressureIndex 類
def calculate_custom_indicator(self, data: pd.Series) -> pd.Series:
    """添加自定義指標"""
    # 實現你的指標計算邏輯
    return custom_indicator
```

### 自定義資產配置

```python
# 修改 ROROEngine 中的資產配置
engine.asset_allocation[RORODecision.FULL_RISK_ON] = {
    'TXF': 0.7,    # 提高股票配置
    'TLT': 0.2,
    'GLD': 0.1,
}
```

## 📋 績效監控

### 關鍵指標監控
- **最大回撤 (MDD)**: 控制在 10% 以內
- **勝率**: RORO 狀態判斷準確性
- **資訊係數 (IC)**: 信號預測能力
- **年化報酬**: 風險調整後收益

### 定期檢查
1. **每日**: 檢查信號生成是否正常
2. **每週**: 檢視回測績效變化
3. **每月**: 評估整體策略表現
4. **每季**: 調整參數和權重

## ⚠️ 重要注意事項

### 風險提醒
- **歷史回測不保證未來表現**
- **交易前請充分理解策略邏輯**
- **建議從小額資金開始測試**
- **定期監控和調整參數**

### 技術限制
- 台灣股市數據獲取相對有限
- 宏觀指標可能有公布延遲
- API 調用頻率限制
- 市場結構變遷的影響

### 使用建議
- **新手用戶**: 先使用默認參數進行測試
- **進階用戶**: 根據市場情況調整權重
- **機構用戶**: 建議結合其他風險管理工具

## 🆘 故障排除

### 常見問題

**Q: 無法獲取 FRED 數據**
A: 檢查 API 金鑰是否正確設置，或使用 Yahoo Finance 備選方案

**Q: 信號生成失敗**
A: 檢查網路連接和數據源可用性，重試或使用快取數據

**Q: 回測結果不理想**
A: 檢查參數設置，考慮市場條件變化，調整策略邏輯

**Q: 內存使用過高**
A: 減少數據時間範圍，或增加數據採樣間隔

### 技術支援
- 查看日誌文件: `output/roro_debug.log`
- 檢查配置文件: `config/roro_config.yaml`
- 運行測試腳本: `python test_stage2.py`

## 📚 進一步閱讀

- [AI_HANDOVER_DOCUMENT.md](AI_HANDOVER_DOCUMENT.md) - 專案總體設計
- [docs/logs/](docs/logs/) - 開發日誌和歷史記錄
- [research/](research/) - 相關研究文檔

## 🎯 版本信息

- **版本**: 1.0.0 (階段二完成)
- **更新日期**: 2025年11月27日
- **下階段**: 階段三 (回測與優化)

---

**免責聲明**: 本策略僅供研究和教育目的，不構成投資建議。實際使用前請充分評估風險並進行獨立測試。
