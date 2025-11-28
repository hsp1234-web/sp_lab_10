#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOCX到TXT轉換程式
將DOCX文件轉換為純文字格式，用於分析策略內容

作者: AI Agent
日期: 2025-11-27
"""

import os
import sys
from pathlib import Path
import docx2txt
from tqdm import tqdm
import pandas as pd
from datetime import datetime

def convert_docx_to_txt(docx_path, txt_path):
    """
    將DOCX文件轉換為TXT文字檔

    Args:
        docx_path (str): DOCX檔案路徑
        txt_path (str): 輸出TXT檔案路徑

    Returns:
        tuple: (成功與否, 訊息, 文字內容長度)
    """
    try:
        # 使用docx2txt提取文字內容
        text = docx2txt.process(docx_path)

        # 確保輸出目錄存在
        os.makedirs(os.path.dirname(txt_path), exist_ok=True)

        # 寫入文字檔，使用UTF-8編碼
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)

        return True, "轉換成功", len(text)
    except Exception as e:
        return False, f"轉換失敗: {str(e)}", 0

def batch_convert_docx_folder(input_folder, output_folder):
    """
    批次轉換整個資料夾的DOCX文件

    Args:
        input_folder (str): 輸入DOCX資料夾
        output_folder (str): 輸出TXT資料夾
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)

    # 確保輸出目錄存在
    output_path.mkdir(exist_ok=True)

    # 找出所有DOCX文件
    docx_files = list(input_path.glob("*.docx"))

    if not docx_files:
        print("未找到任何DOCX文件")
        return []

    print(f"找到 {len(docx_files)} 個DOCX文件")
    print("開始轉換...")

    results = []
    success_count = 0
    failed_files = []

    # 使用進度條顯示轉換進度
    for docx_file in tqdm(docx_files, desc="轉換進度", unit="文件"):
        txt_file = output_path / f"{docx_file.stem}.txt"

        success, message, content_length = convert_docx_to_txt(docx_file, txt_file)

        result = {
            '原檔案': docx_file.name,
            '輸出檔案': txt_file.name,
            '檔案大小_MB': round(docx_file.stat().st_size / 1024 / 1024, 2),
            '內容長度': content_length,
            '轉換狀態': '成功' if success else '失敗',
            '訊息': message,
            '轉換時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        results.append(result)

        if success:
            success_count += 1
        else:
            failed_files.append((docx_file.name, message))

    # 輸出轉換結果
    print("\n轉換完成！")
    print(f"總計: {len(docx_files)} 個文件")
    print(f"成功: {success_count} 個文件")
    print(f"失敗: {len(failed_files)} 個文件")

    if failed_files:
        print("\n失敗文件清單:")
        for file_name, error_msg in failed_files:
            print(f"  - {file_name}: {error_msg}")

    # 產生轉換報告
    create_conversion_report(results, output_folder)

    return results

def create_conversion_report(results, output_folder):
    """
    產生轉換報告

    Args:
        results (list): 轉換結果清單
        output_folder (str): 輸出資料夾
    """
    if not results:
        return

    # 建立DataFrame
    df = pd.DataFrame(results)

    # 儲存CSV報告
    report_path = Path(output_folder) / "docx_conversion_report.csv"
    df.to_csv(report_path, index=False, encoding='utf-8-sig')

    # 統計資訊
    print(f"\n轉換統計:")
    print(f"   總文件數: {len(df)}")
    print(f"   成功轉換: {len(df[df['轉換狀態'] == '成功'])}")
    print(f"   轉換失敗: {len(df[df['轉換狀態'] == '失敗'])}")
    print(f"   平均檔案大小: {df['檔案大小_MB'].mean():.2f} MB")
    print(f"   平均內容長度: {df['內容長度'].mean():.0f} 字元")

    print(f"\n詳細報告已儲存至: {report_path}")

def main():
    """主程式"""
    print("DOCX到TXT轉換程式")
    print("=" * 50)

    # 設定輸入和輸出資料夾
    input_folder = "drive-download-20251126T202650Z-1-001"
    output_folder = "output/converted_texts"

    # 檢查輸入資料夾是否存在
    if not os.path.exists(input_folder):
        print(f"輸入資料夾不存在: {input_folder}")
        sys.exit(1)

    print(f"輸入資料夾: {input_folder}")
    print(f"輸出資料夾: {output_folder}")

    # 執行批次轉換
    results = batch_convert_docx_folder(input_folder, output_folder)

    if results:
        print("\n轉換任務完成！")
        print("現在您可以開始分析轉換後的文字內容了。")
    else:
        print("\n沒有成功轉換任何文件。")

if __name__ == "__main__":
    main()
