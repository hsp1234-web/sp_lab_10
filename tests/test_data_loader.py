#!/usr/bin/env python3
"""
測試 DataLoader 功能的基本腳本
"""

from pathlib import Path
from src.data_loader import DataLoader

def main():
    print("開始測試 DataLoader 功能...")

    # Test basic import
    print("DataLoader import successful")

    # Test initialization
    data_dir = Path('data')
    data_loader = DataLoader(data_dir)
    print("DataLoader initialization successful")

    # Test loading small amount of data
    print("Testing data loading...")
    try:
        test_data = data_loader.load_yahoo_finance_data('AAPL', '2024-01-01', '2024-01-05')
        if not test_data.empty:
            print(f"Test data loading successful: {test_data.shape}")
            print(f"Columns: {list(test_data.columns)}")
        else:
            print("Test data loading returned empty DataFrame")
    except Exception as e:
        print(f"Test data loading failed: {e}")

    print("測試完成")

if __name__ == "__main__":
    main()
