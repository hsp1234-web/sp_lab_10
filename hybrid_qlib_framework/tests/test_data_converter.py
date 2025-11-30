import pytest
import pandas as pd
from pathlib import Path
from src.data_converter import DataConverter

class TestDataConverter:
    
    def test_validate_data_success(self, sample_data):
        """測試資料驗證 - 成功案例"""
        converter = DataConverter(test_mode=True)
        assert converter.validate_data(sample_data) == True
        
    def test_validate_data_missing_col(self, sample_data):
        """測試資料驗證 - 缺欄位"""
        converter = DataConverter(test_mode=True)
        bad_data = sample_data.drop(columns=['close'])
        assert converter.validate_data(bad_data) == False
        
    def test_validate_data_invalid_value(self, sample_data):
        """測試資料驗證 - 負值"""
        converter = DataConverter(test_mode=True)
        bad_data = sample_data.copy()
        bad_data.loc[0, 'close'] = -100
        assert converter.validate_data(bad_data) == False
        
    def test_convert_to_qlib_format(self, sample_data):
        """測試格式轉換"""
        converter = DataConverter(test_mode=True)
        df_qlib = converter.convert_to_qlib_format(sample_data)
        
        assert 'instrument' in df_qlib.columns
        assert '$close' in df_qlib.columns
        assert df_qlib.iloc[0]['instrument'] == 'TX'
        
    def test_full_flow(self, sample_parquet, temp_output_dir):
        """測試完整流程"""
        converter = DataConverter(test_mode=True)
        converter.convert(sample_parquet, temp_output_dir)
        
        # 檢查是否有輸出檔案
        # 根據目前的實作，可能會輸出 csv 或 parquet
        assert any(temp_output_dir.iterdir())
