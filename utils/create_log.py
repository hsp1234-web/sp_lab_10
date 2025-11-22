#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自動建立結構化日誌檔案的工具

此腳本會：
1. 取得當前台北時間
2. 提示使用者輸入簡短描述
3. 生成標準化檔名
4. 建立包含模板的日誌檔案
"""

import os
from datetime import datetime
import pytz

def create_log():
    """建立新的日誌檔案"""
    
    # 取得台北時間
    taipei_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taipei_tz)
    
    # 格式化時間
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H-%M')
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S CST')
    month_dir = now.strftime('%Y-%m')
    
    # 提示使用者輸入
    print("=" * 60)
    print("建立新的開發日誌")
    print("=" * 60)
    print(f"當前時間: {timestamp}")
    print()
    
    description = input("請輸入簡短描述 (例如: fix_numpy_compatibility): ").strip()
    if not description:
        print("❌ 錯誤：描述不能為空")
        return
    
    title = input("請輸入日誌標題: ").strip()
    if not title:
        print("❌ 錯誤：標題不能為空")
        return
    
    author = input("請輸入作者名稱 [Antigravity]: ").strip() or "Antigravity"
    
    # 建立檔名
    filename = f"{date_str}_{time_str}_{description}.md"
    
    # 建立目錄路徑
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, 'docs', 'logs', month_dir)
    os.makedirs(log_dir, exist_ok=True)
    
    filepath = os.path.join(log_dir, filename)
    
    # 檢查檔案是否已存在
    if os.path.exists(filepath):
        print(f"❌ 錯誤：檔案已存在 {filepath}")
        return
    
    # 建立日誌模板
    template = f"""# {title}

**日期**: `{timestamp}`  
**作者**: {author}

## 摘要

[請在此填寫本次變更的簡要說明]

## 主要變更

### [變更類別 1]
- [變更項目 1]
- [變更項目 2]

### [變更類別 2]
- [變更項目 1]
- [變更項目 2]

## 驗證結果

- [ ] [驗證項目 1]
- [ ] [驗證項目 2]

## 備註

[如有其他需要記錄的資訊，請在此填寫]
"""
    
    # 寫入檔案
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print()
    print("=" * 60)
    print(f"✅ 日誌檔案已建立: {filepath}")
    print("=" * 60)
    print()
    print("請使用您的編輯器開啟並填寫日誌內容。")

if __name__ == "__main__":
    try:
        create_log()
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
