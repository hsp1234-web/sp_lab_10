#!/usr/bin/env python3
"""
台灣期貨交易所官方資料自動更新腳本

每日定時執行，更新最新的交易資料
"""

import sys
import logging
from pathlib import Path

# 添加專案路徑
sys.path.append(str(Path(__file__).parent.parent))

from scripts.taifex_official_downloader import TaifexOfficialDownloader

def main():
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/taifex_official_update.log'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)

    try:
        logger.info("開始更新台灣期貨交易所官方資料")

        # 初始化下載器
        downloader = TaifexOfficialDownloader(logger)

        # 更新最近30天的資料
        downloader.download_recent_data(days_back=30)

        logger.info("官方資料更新完成")

    except Exception as e:
        logger.error(f"資料更新失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
