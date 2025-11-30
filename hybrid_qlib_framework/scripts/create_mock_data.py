#!/usr/bin/env python3
"""
建立測試用模擬資料
當真實的 taifex.db 不可用時，產生模擬資料供測試使用
"""
import pandas as pd
from pathlib import Path
import sys

def create_mock_test_data(output_dir='./data/test', test_month='2024-01'):
    """
    建立模擬測試資料
    
    Args:
        output_dir: 輸出目錄
        test_month: 測試月份
    """
    print(f"📊 建立模擬測試資料: {test_month}")
    
    # 建立輸出目錄
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 產生模擬資料（台指期 TX）
    dates = pd.date_range(start=f'{test_month}-01', end=f'{test_month}-31', freq='D')
    
    data = []
    base_price = 17000
    
    for i, date in enumerate(dates):
        # 模擬價格波動
        open_price = base_price + (i * 10) + (i % 5) * 20
        high_price = open_price + 50
        low_price = open_price - 50
        close_price = open_price + (i % 3 - 1) * 30
        volume = 50000 + (i * 1000)
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'symbol': 'TX',
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    
    print(f"✅ 產生 {len(df)} 筆模擬資料")
    print(f"📅 日期範圍: {df['date'].min()} ~ {df['date'].max()}")
    print(f"📊 欄位: {list(df.columns)}")
    
    # 存為 Parquet
    output_file = output_dir / f"test_data_{test_month.replace('-', '_')}.parquet"
    df.to_parquet(output_file, index=False)
    
    print(f"💾 已儲存: {output_file}")
    print(f"📦 檔案大小: {output_file.stat().st_size / 1024:.2f} KB")
    
    return output_file

if __name__ == '__main__':
    result = create_mock_test_data(output_dir='./data/test', test_month='2024-01')
    
    if result:
        print(f"\n✅ 模擬測試資料建立完成!")
        print(f"💡 提示: 這是模擬資料，僅供測試框架使用")
    else:
        print(f"\n❌ 模擬資料建立失敗")
        sys.exit(1)
