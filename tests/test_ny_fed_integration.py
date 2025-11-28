# -*- coding: utf-8 -*-
"""
NY Fed 數據整合測試腳本
"""

import sys
sys.path.append('src')

def test_ny_fed_integration():
    """測試 NY Fed 數據整合"""
    try:
        print("測試 NY Fed 數據整合...")

        from pathlib import Path
        from config_manager import ConfigManager
        from ny_fed_integration import NYFedDataLoader, NYFedPressureIndicator
        from datetime import datetime, timedelta

        # 加載配置
        config = ConfigManager(Path('config/roro_config.yaml'))

        # 測試數據載入器
        print("1. 測試 NY Fed 數據載入器...")
        data_loader = NYFedDataLoader(config)

        # 測試數據獲取 (最近6個月)
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        print(f"   獲取數據範圍: {start_date} 到 {end_date}")

        positions_data = data_loader.fetch_ny_fed_data(start_date, end_date)

        if not positions_data.empty:
            print(f"   成功獲取 {len(positions_data)} 筆 NY Fed 數據")
            print(f"   數據範圍: {positions_data.index.min()} 到 {positions_data.index.max()}")
            print(f"   均值: {positions_data.mean():.2f} 百萬美元")
            print(f"   最新值: {positions_data.iloc[-1]:.2f} 百萬美元")
            return True
        else:
            print("   NY Fed 數據獲取失敗")
            return False

    except Exception as e:
        print(f"測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("NY Fed 數據整合測試")
    print("=" * 40)

    success = test_ny_fed_integration()

    if success:
        print("\n測試通過！")
    else:
        print("\n測試失敗！")

    print("=" * 40)
