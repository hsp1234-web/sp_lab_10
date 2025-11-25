"""簡化版回測結果分析腳本"""
import pandas as pd

# 讀取最新的回測結果
file_path = 'lo2cin4bt-main/records/backtester/20251124_SPY_SPY_Demo_Close_54824e94_.parquet'

try:
    df = pd.read_parquet(file_path)
    
    print("=" * 80)
    print("📊 SPY 20日均線策略回測結果")
    print("=" * 80)
    
    # 基本資訊
    print(f"\n【資料概況】")
    print(f"總記錄數: {len(df):,} 筆")
    print(f"回測期間: {df['Time'].min()} 至 {df['Time'].max()}")
    print(f"回測天數: {(df['Time'].max() - df['Time'].min()).days} 天")
    
    # 績效統計
    initial_capital = df['Total_equity'].iloc[0]
    final_capital = df['Total_equity'].iloc[-1]
    total_return = ((final_capital - initial_capital) / initial_capital) * 100
    max_equity = df['Total_equity'].max()
    min_equity = df['Total_equity'].min()
    max_drawdown = ((max_equity - min_equity) / max_equity) * 100
    
    print(f"\n【資金變化】")
    print(f"初始資金: ${initial_capital:,.2f}")
    print(f"最終資金: ${final_capital:,.2f}")
    print(f"淨利潤: ${final_capital - initial_capital:,.2f}")
    print(f"總報酬率: {total_return:.2f}%")
    print(f"最大權益: ${max_equity:,.2f}")
    print(f"最小權益: ${min_equity:,.2f}")
    print(f"最大回撤: {max_drawdown:.2f}%")
    
    # 交易統計
    trades = df[df['Trade_action'] == 1]
    buys = df[(df['Trade_action'] == 1) & (df['Position'] == 1)]
    sells = df[(df['Trade_action'] == 1) & (df['Position'] == -1)]
    
    print(f"\n【交易統計】")
    print(f"總交易次數: {len(trades)} 次")
    print(f"買入次數: {len(buys)} 次")
    print(f"賣出次數: {len(sells)} 次")
    
    # 計算勝率
    if len(sells) > 0:
        # 找出每次完整交易的盈虧
        profitable_trades = 0
        for i in range(min(len(buys), len(sells))):
            buy_idx = buys.index[i]
            sell_idx = sells.index[i]
            if sell_idx > buy_idx:
                profit = df.loc[sell_idx, 'Total_equity'] - df.loc[buy_idx, 'Total_equity']
                if profit > 0:
                    profitable_trades += 1
        
        win_rate = (profitable_trades / min(len(buys), len(sells))) * 100
        print(f"勝率: {win_rate:.2f}%")
    
    # 年化報酬率
    years = (df['Time'].max() - df['Time'].min()).days / 365.25
    annual_return = ((final_capital / initial_capital) ** (1 / years) - 1) * 100
    print(f"\n【年化績效】")
    print(f"年化報酬率: {annual_return:.2f}%")
    
    # 顯示最近5筆交易
    print(f"\n【最近 5 筆交易】")
    recent_trades = trades.tail(5)[['Time', 'Close', 'Position', 'Total_equity']]
    print(recent_trades.to_string(index=False))
    
    print(f"\n{'=' * 80}")
    print("✅ 分析完成！")
    print("=" * 80)
    
except FileNotFoundError:
    print(f"❌ 找不到檔案: {file_path}")
    print("請確認檔案路徑是否正確")
except Exception as e:
    print(f"❌ 發生錯誤: {e}")
