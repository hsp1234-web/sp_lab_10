# -*- coding: utf-8 -*-
"""
FRED API 測試腳本

測試提供的 FRED API 金鑰並獲取關鍵宏觀經濟數據。
"""

import sys
sys.path.append('src')

from config_manager import ConfigManager
from pressure_index import SystemPressureIndex
import pandas as pd
from datetime import datetime, timedelta
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_fred_api():
    """測試 FRED API 連接和數據獲取"""
    try:
        print("測試 FRED API 連接...")

        # 加載配置
        from pathlib import Path
        config = ConfigManager(Path('config/roro_config.yaml'))
        fred_key = config.get('api_keys.fred')

        if not fred_key:
            print("未找到 FRED API 金鑰")
            return False

        print(f"已加載 FRED API 金鑰: {fred_key[:8]}****")

        # 創建壓力指數實例
        pressure_index = SystemPressureIndex(fred_api_key=fred_key, config_manager=config)

        if not pressure_index.fred_client:
            print("FRED 客戶端初始化失敗")
            return False

        print("FRED 客戶端初始化成功")

        # 測試關鍵指標數據獲取
        test_indicators = {
            'SOFR': 'SOFR',
            '聯邦基金利率': 'DFF',
            '10年期國債': 'DGS10',
            'VIX指數': 'VIX'
        }

        print("\n測試關鍵指標數據獲取...")
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        results = {}

        for name, series_code in test_indicators.items():
            try:
                if series_code in ['VIX']:
                    # Yahoo Finance 數據
                    data = pressure_index.fetch_yahoo_data(f'^{series_code}', start_date, end_date)
                else:
                    # FRED 數據
                    data = pressure_index.fetch_fred_data(series_code, start_date, end_date)

                if not data.empty:
                    latest_value = data.iloc[-1] if len(data) > 0 else 'N/A'
                    results[name] = {
                        'status': '成功',
                        'count': len(data),
                        'latest': latest_value,
                        'start_date': data.index.min().strftime('%Y-%m-%d') if not data.empty else 'N/A',
                        'end_date': data.index.max().strftime('%Y-%m-%d') if not data.empty else 'N/A'
                    }
                    print(f"成功 {name} ({series_code}): {len(data)} 筆數據, 最新值: {latest_value}")
                else:
                    results[name] = {'status': '失敗', 'error': '無數據'}
                    print(f"失敗 {name} ({series_code}): 獲取失敗")

            except Exception as e:
                results[name] = {'status': '失敗', 'error': str(e)}
                print(f"失敗 {name} ({series_code}): 錯誤 - {str(e)}")

        # 測試綜合壓力指數計算
        print("\n測試綜合壓力指數計算...")
        try:
            pressure_data = pressure_index.calculate_composite_pressure_index(start_date, end_date)

            if pressure_data:
                print("綜合壓力指數計算成功")
                for key, series in pressure_data.items():
                    if not series.empty:
                        latest = series.iloc[-1] if len(series) > 0 else 'N/A'
                        print(f"  - {key}: {len(series)} 筆數據, 最新值: {latest}")
            else:
                print("綜合壓力指數計算失敗")

        except Exception as e:
            print(f"綜合壓力指數計算錯誤: {str(e)}")

        # 總結報告
        print("\n測試總結:")
        print(f"總指標數: {len(test_indicators)}")
        success_count = sum(1 for r in results.values() if r['status'] == '成功')
        print(f"成功獲取: {success_count}")
        print(f"失敗數量: {len(test_indicators) - success_count}")

        return success_count > 0

    except Exception as e:
        print(f"測試過程中發生錯誤: {str(e)}")
        return False

def research_fred_data():
    """研究 FRED 數據的可用性和特點"""
    try:
        print("\nFRED 數據研究分析...")

        config = ConfigManager(Path('config/roro_config.yaml'))
        fred_key = config.get('api_keys.fred')

        if not fred_key:
            print("未找到 FRED API 金鑰")
            return

        pressure_index = SystemPressureIndex(fred_api_key=fred_key, config_manager=config)

        # 分析關鍵宏觀指標
        research_indicators = {
            '貨幣政策': {
                'SOFR': 'SOFR',
                '聯邦基金利率': 'DFF',
                '準備金利率': 'IORR'
            },
            '殖利率': {
                '1年期國債': 'DGS1',
                '5年期國債': 'DGS5',
                '10年期國債': 'DGS10',
                '30年期國債': 'DGS30'
            },
            '利差': {
                '10Y-2Y利差': 'T10Y2Y',
                '10Y-3M利差': 'T10Y3M'
            },
            '經濟指標': {
                '工業生產': 'INDPRO',
                'M2貨幣供應': 'M2SL'
            }
        }

        print("研究各類宏觀指標的可用性:")

        for category, indicators in research_indicators.items():
            print(f"\n{category}:")
            for name, series_code in indicators.items():
                try:
                    # 獲取最近3年的數據來分析
                    start_date = (datetime.now() - timedelta(days=1095)).strftime('%Y-%m-%d')
                    end_date = datetime.now().strftime('%Y-%m-%d')

                    data = pressure_index.fetch_fred_data(series_code, start_date, end_date)

                    if not data.empty:
                        stats = {
                            '數據點數': len(data),
                            '開始日期': data.index.min().strftime('%Y-%m-%d'),
                            '結束日期': data.index.max().strftime('%Y-%m-%d'),
                            '最新值': f"{data.iloc[-1]:.4f}" if len(data) > 0 else 'N/A',
                            '均值': f"{data.mean():.4f}",
                            '標準差': f"{data.std():.4f}",
                            '更新頻率': data.index.to_series().diff().median().days if len(data) > 1 else 'N/A'
                        }

                        print(f"  成功 {name} ({series_code}):")
                        for stat_name, stat_value in stats.items():
                            print(f"    - {stat_name}: {stat_value}")
                    else:
                        print(f"  失敗 {name} ({series_code}): 無數據")

                except Exception as e:
                    print(f"  失敗 {name} ({series_code}): 錯誤 - {str(e)}")

        # 分析數據品質和可用性
        print("\nFRED 數據品質分析:")
        print("- 高品質: 官方來源，實時更新，歷史數據完整")
        print("- 更新頻率: 日線級別，適合量化策略")
        print("- 覆蓋範圍: 涵蓋貨幣政策、債券市場、經濟指標")
        print("- 適用性: 非常適合系統壓力指數的構建")

    except Exception as e:
        print(f"數據研究過程中發生錯誤: {str(e)}")

if __name__ == "__main__":
    print("FRED API 測試和研究")
    print("=" * 50)

    # 測試 API 連接
    api_test_success = test_fred_api()

    if api_test_success:
        print("\nFRED API 測試通過，開始數據研究...")
        research_fred_data()
    else:
        print("\nFRED API 測試失敗，請檢查金鑰和網路連接")

    print("\n" + "=" * 50)
    print("FRED API 研究完成")
