#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整理研究檔案腳本
將drive-download資料夾中的檔案分類整理到research資料夾的對應子資料夾中

作者: AI Agent
日期: 2025-11-27
"""

import os
import shutil
from pathlib import Path

def organize_research_files():
    """整理研究檔案到對應分類資料夾"""

    # 定義檔案分類規則
    categories = {
        "trading_strategies": [
            "刀疤老二交易策略與心法.docx",
            "刀疤老二交易策略深度研究_.docx",
            "股海戰神策略整理.docx",
            "量化交易.docx",
            "專業交易進化論：心法、風控與實戰策略 (純內文版).docx",
            "交易醫生分享.docx"
        ],
        "options_research": [
            "台股多空期權量化研究.docx",
            "選擇權交易策略實戰 Options Trading Strategy & Operations Manual.docx",
            "選擇權交易策略實戰.docx",
            "選擇權交易策略與操作-善群.docx",
            "選擇權交易策略與操作.docx",
            "選擇權套利.docx",
            "台灣選擇權裸賣（Naked Short Put）原始保證金計算整理.docx",
            "美股選擇權籌碼gex分析與應用.docx",
            "美股期權支撐壓力研究_.docx"
        ],
        "risk_management": [
            "風險評估程式-小作文.docx",
            "投資倉位管理深度研究.docx",
            "整合孟格檢查表與倉位管理_.docx",
            "整合孟格檢查表與倉位管理_(1).docx",
            "美股日內風險計算系統研究_.docx",
            "美股風險評估系統開發_.docx",
            "設計美股多時間維度風險計算系統.docx",
            "台美股Max Pain分析流程設計.docx"
        ],
        "market_analysis": [
            "台灣期貨配對交易研究_.docx",
            "運用流動性商品「配對」輔助判斷市場風險.docx",
            "狼友小作文- VIX策略（VXM）.docx",
            "估值_牛熊_避險-善.docx",
            "估值_牛熊.docx",
            "基差交易觀察.docx",
            "股市投資觀點與策略統整.docx",
            "台股期貨開盤預測分析.docx",
            "外匯風險研究.docx",
            "債券市場異常現象深度研究.docx",
            "債券量價邏輯.docx",
            "衍生品避險與收益策略_.docx"
        ],
        "system_development": [
            "AI 輔助開發：最高指導原則與作戰手冊 v6.5.docx",
            "🎯🖥️通用 AI 輔助開發：最高指導原則與作戰手冊 v3.1.docx",
            "👑🎉0708量化交易遺傳演算法應用研究.docx",
            "💪實戰基因算法_.docx",
            "Finlab 研究pro.docx",
            "Finlab.docx",
            "多維度專案進度 -善.docx"
        ],
        "financial_research": [
            "台灣金融三業債券投資分析_.docx",
            "Vincent余鄭文的投資心法與市場洞察.docx",
            "台灣金融債券曝險與避險.docx",
            "台灣金融市場解析_.docx",
            "台灣金融歷史數據查詢_.docx",
            "美國一級交易商風險分析.docx",
            "美國債券供需分析.docx",
            "美國債券市場深度研究.docx",
            "美股估值系統設計研究.docx",
            "新台幣升值壽險業影響分析.docx",
            "新台幣升值波動風險分析.docx",
            "階段一TWD 匯率風險評估工具.docx",
            "階段一TWD_USD 風險圖表規劃.docx",
            "2-2新台幣風險指標量化與閾值.docx",
            "3-1TWD_USD 匯率風險位階定義.docx",
            "新台幣匯率風險儀表板 - 專案規劃總結報告 v1.5 (修訂版).docx",
            "V1綜合金融風險儀表板 - 專案狀態總結 (2025-05-06) - Cell 1 確認正常.docx",
            "善狼.docx",
            "善甲狼a機智生活聯發科演講 20240605.docx",
            "戰略指標深度研究方法論_.docx",
            "PTT 交易者 Comemail 文章內容彙整與投資邏輯.docx",
            "分享會重點整理.docx",
            "台灣外匯市場數據分析_.docx",
            "4月6號關稅衝擊下的市場回顧與專業分析.docx",
            "4紅綠燈與交易機會掃描.docx",
            "9月小作文-債市、避險.docx"
        ]
    }

    # 來源和目標路徑
    source_dir = Path("drive-download-20251126T202650Z-1-001")
    target_base_dir = Path("research")

    print("開始整理研究檔案...")
    print("=" * 50)

    # 確保目標資料夾存在
    target_base_dir.mkdir(exist_ok=True)

    total_files = 0
    success_count = 0

    # 處理每個分類
    for category, files in categories.items():
        target_dir = target_base_dir / category
        target_dir.mkdir(exist_ok=True)

        print(f"\n處理分類: {category} ({len(files)} 個檔案)")

        for file in files:
            source_file = source_dir / file
            target_file = target_dir / file

            if source_file.exists():
                try:
                    shutil.copy2(source_file, target_file)
                    print(f"  [OK] {file}")
                    success_count += 1
                except Exception as e:
                    print(f"  [ERROR] {file} - 複製失敗: {e}")
            else:
                print(f"  [MISSING] {file} - 來源檔案不存在")

            total_files += 1

    # 檢查是否有未分類的檔案
    all_source_files = set(f.name for f in source_dir.glob("*.docx"))
    classified_files = set()
    for files in categories.values():
        classified_files.update(files)

    unclassified_files = all_source_files - classified_files

    print("\n" + "=" * 50)
    print("整理結果總結:")
    print(f"總檔案數: {total_files}")
    print(f"成功複製: {success_count}")
    print(f"複製失敗: {total_files - success_count}")

    if unclassified_files:
        print(f"\n未分類檔案 ({len(unclassified_files)} 個):")
        for file in sorted(unclassified_files):
            print(f"  - {file}")
    else:
        print("\n所有檔案均已分類整理完成！")

    print("\n整理完成！請查看 research/ 資料夾")

if __name__ == "__main__":
    organize_research_files()
