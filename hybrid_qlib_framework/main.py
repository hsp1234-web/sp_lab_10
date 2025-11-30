#!/usr/bin/env python3
"""
Hybrid Qlib Framework 主程式
支援 CLI 介面,整合資料準備、轉換與回測流程
"""
import argparse
import sys
from pathlib import Path
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_prepare_data(args):
    """執行資料準備"""
    from scripts.prepare_test_data import prepare_test_data
    
    logger.info("🚀 啟動資料準備...")
    
    # 嘗試解析路徑
    db_path = Path(args.db_path)
    if not db_path.exists():
        # 嘗試在專案內尋找
        project_db_path = Path(__file__).parent / 'data' / 'taifex.db'
        if project_db_path.exists():
            logger.info(f"使用專案內 DB: {project_db_path}")
            db_path = project_db_path
    
    prepare_test_data(db_path, args.output_dir, args.month)

def run_convert(args):
    """執行資料轉換"""
    from src.data_converter import DataConverter
    
    logger.info("🚀 啟動資料轉換...")
    converter = DataConverter(test_mode=args.test_only)
    
    input_file = Path(args.input_file)
    output_dir = Path(args.output_dir)
    
    if not input_file.exists():
        logger.error(f"輸入檔案不存在: {input_file}")
        return
        
    converter.convert(input_file, output_dir)

def run_backtest(args):
    """執行回測 (Placeholder)"""
    logger.info("🚀 啟動回測 (尚未實作)...")
    logger.info(f"參數: Start={args.start}, End={args.end}, Mode={args.mode}")

def main():
    parser = argparse.ArgumentParser(description='Hybrid Qlib Framework CLI')
    subparsers = parser.add_subparsers(dest='command', help='可用指令')
    
    # 指令: prepare-data
    parser_prep = subparsers.add_parser('prepare-data', help='準備測試資料')
    parser_prep.add_argument('--db-path', default='../data/taifex.db', help='SQLite DB 路徑')
    parser_prep.add_argument('--output-dir', default='./data/test', help='輸出目錄')
    parser_prep.add_argument('--month', default='2024-01', help='指定月份')
    
    # 指令: convert
    parser_conv = subparsers.add_parser('convert', help='轉換資料格式')
    parser_conv.add_argument('--input-file', required=True, help='輸入 Parquet 檔案')
    parser_conv.add_argument('--output-dir', default='./data/bin', help='輸出目錄')
    parser_conv.add_argument('--test-only', action='store_true', help='測試模式 (只處理少量資料)')
    
    # 指令: backtest
    parser_bt = subparsers.add_parser('backtest', help='執行回測')
    parser_bt.add_argument('--start', help='開始日期')
    parser_bt.add_argument('--end', help='結束日期')
    parser_bt.add_argument('--mode', choices=['test', 'full'], default='test', help='回測模式')
    
    args = parser.parse_args()
    
    if args.command == 'prepare-data':
        run_prepare_data(args)
    elif args.command == 'convert':
        run_convert(args)
    elif args.command == 'backtest':
        run_backtest(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
