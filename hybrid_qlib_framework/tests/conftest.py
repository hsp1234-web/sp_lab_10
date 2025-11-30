import pytest
import pandas as pd
import shutil
from pathlib import Path

@pytest.fixture
def sample_data():
    """提供測試用的 DataFrame"""
    data = {
        'date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
        'symbol': ['TX', 'TX', 'TX'],
        'open': [100.0, 101.0, 102.0],
        'high': [105.0, 106.0, 107.0],
        'low': [95.0, 96.0, 97.0],
        'close': [102.0, 103.0, 104.0],
        'volume': [1000, 1100, 1200]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir(tmp_path):
    """提供暫存輸出目錄"""
    d = tmp_path / "output"
    d.mkdir()
    return d

@pytest.fixture
def sample_parquet(sample_data, temp_output_dir):
    """建立測試用 Parquet 檔案"""
    file_path = temp_output_dir / "test.parquet"
    sample_data.to_parquet(file_path, index=False)
    return file_path
