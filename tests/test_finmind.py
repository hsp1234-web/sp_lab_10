#!/usr/bin/env python3
"""
測試FinMind API是否能夠免費使用
"""

from FinMind.data import DataLoader
import pandas as pd

def test_finmind_api():
    """測試FinMind API"""
    try:
        print("測試FinMind API...")

        # 初始化DataLoader
        print("初始化DataLoader...")
        api = DataLoader()

        # 測試獲取台指期資料
        print("嘗試獲取台指期資料 (TX)...")
        df = api.taiwan_futures_daily(futures_id="TX", start_date="2024-01-01")

        if df.empty:
            print("無法獲取資料 - 可能需要API金鑰")
            return False
        else:
            print(f"成功獲取資料! 共 {len(df)} 筆記錄")
            print(f"資料日期範圍: {df['date'].min()} ~ {df['date'].max()}")
            print(f"欄位名稱: {list(df.columns)}")
            print("\n前5筆資料預覽:")
            print(df.head())

            # 測試選擇權資料
            print("\n測試選擇權資料...")
            try:
                df_options = api.taiwan_option_daily(
                    futures_id="TXO",
                    call_put="call",
                    start_date="2024-01-01"
                )
            except Exception as e:
                print(f"選擇權API參數錯誤: {e}")
                print("嘗試其他參數...")
                try:
                    # 嘗試不同的參數名稱
                    df_options = api.taiwan_option_daily(
                        symbol_id="TXO",
                        start_date="2024-01-01"
                    )
                except:
                    df_options = pd.DataFrame()  # 空的DataFrame

            if not df_options.empty:
                print(f"選擇權資料也可用! 共 {len(df_options)} 筆記錄")
                print(f"選擇權資料日期範圍: {df_options['date'].min()} ~ {df_options['date'].max()}")
            else:
                print("選擇權資料可能需要付費或有其他限制")

            return True

    except Exception as e:
        print(f"API測試失敗: {e}")
        if "token" in str(e).lower() or "api" in str(e).lower():
            print("錯誤訊息顯示可能需要API金鑰")
            return "needs_token"
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("FinMind API 免費使用測試")
    print("=" * 60)

    result = test_finmind_api()

    print("\n" + "=" * 60)
    if result == True:
        print("結論: FinMind API 可以免費使用!")
        print("建議: 可以整合到專案中作為資料來源")
    elif result == "needs_token":
        print("結論: FinMind API 需要API金鑰")
        print("建議: 需要註冊並獲取免費或付費金鑰")
    else:
        print("結論: 無法確定API狀態")
        print("建議: 請檢查網路連線或FinMind服務狀態")
    print("=" * 60)
