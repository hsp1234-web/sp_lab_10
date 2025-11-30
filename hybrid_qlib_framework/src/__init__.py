"""
Hybrid Qlib Framework - 邏輯驅動的量化交易系統

核心模組：
- data_converter: 資料轉換管線 (Parquet -> Qlib Binary)
- factor_lib: 因子定義庫 (Alpha158 + 自定義因子) [待實作]
- model_runner: 回測引擎與模型訓練 [待實作]
"""

__version__ = "0.1.0"
__author__ = "HSP Trading Team"

# 只導入已存在的模組
from . import data_converter

__all__ = ["data_converter"]
