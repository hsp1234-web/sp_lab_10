import finlab

print("=== FINLAB 正確設置和使用 ===")

# 使用您提供的API金鑰登入
api_key = "wnFW0KT5etgpNr6IKZI05kNyRrMQDrIeoaplJBlRc+Twz+RWciylMCjm0jvtL0n5#free"

try:
    # 登入FINLAB
    print("正在登入FINLAB...")
    finlab.login(api_key)
    print("* 登入成功!")

    # 現在可以導入data模塊
    from finlab import data

    print("\n=== 數據功能測試 ===")

    # 測試獲取台灣加權指數數據
    print("正在獲取台灣加權指數數據...")
    twii = data.get('price:收盤價', 'TAIEX')
    print(f"台灣加權指數數據長度: {len(twii)}")
    print("最近5日數據:")
    print(twii.tail(5))

    # 測試台積電數據
    print("\n正在獲取台積電數據...")
    tsmc = data.get('price:收盤價', '2330')
    print(f"台積電數據長度: {len(tsmc)}")
    print("最近5日數據:")
    print(tsmc.tail(5))

    # 查看可用數據類型
    print("\n=== 查看可用數據 ===")
    try:
        available_data = data.get_available_data()
        print(f"可用數據類型總數: {len(available_data)}")
        print("前20個數據類型:")
        for i, data_type in enumerate(available_data[:20]):
            print(f"  {i+1:2d}. {data_type}")
    except Exception as e:
        print(f"獲取可用數據列表失敗: {e}")

    print("\n=== 技術指標測試 ===")
    # 計算簡單移動平均
    sma_20 = twii.rolling(20).mean()
    sma_60 = twii.rolling(60).mean()

    print(f"台灣加權指數最新收盤價: {twii.iloc[-1]:.2f}")
    print(f"20日均線: {sma_20.iloc[-1]:.2f}")
    print(f"60日均線: {sma_60.iloc[-1]:.2f}")

    # 計算Z分數 (用於配對交易)
    returns = twii.pct_change()
    z_score = (returns - returns.rolling(60).mean()) / returns.rolling(60).std()
    print(f"當前Z分數: {z_score.iloc[-1]:.3f}")

except Exception as e:
    print(f"FINLAB設置失敗: {e}")
    print("請檢查API金鑰是否正確")

print("\n=== FINLAB功能總結 ===")
print("FINLAB可以提供:")
print("1. * 台灣股市即時數據")
print("2. * 歷史數據下載")
print("3. * 技術指標計算")
print("4. * 基本面數據")
print("5. * 數據可視化")
print("6. * 策略回測框架")
