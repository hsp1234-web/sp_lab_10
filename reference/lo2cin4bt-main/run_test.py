"""
自動執行台指期貨小規模測試

此腳本直接調用 autorunner 模組,無需互動式輸入
"""
import sys
import os

# 添加 lo2cin4bt-main 到 Python 路徑
sys.path.insert(0, os.path.dirname(__file__))

import logging
from autorunner.Base_autorunner import BaseAutorunner

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """執行自動化回測"""
    try:
        logger.info("=== 開始執行台指期貨小規模測試 ===")
        
        # 創建 autorunner 實例
        autorunner = BaseAutorunner(logger=logger)
        
        # 指定配置文件
        config_path = os.path.join(
            os.path.dirname(__file__),
            "records",
            "autorunner",
            "taifex_test_small.json"
        )
        
        logger.info(f"使用配置文件: {config_path}")
        
        # 執行回測
        autorunner._run_single_config(config_path)
        
        logger.info("=== 測試執行完成 ===")
        
    except Exception as e:
        logger.error(f"執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
