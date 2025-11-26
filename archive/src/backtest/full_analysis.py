"""完整的回測結果分析腳本"""
import pandas as pd
import os

file_path = 'lo2cin4bt-main/records/backtester/20251124_SPY_SPY_Demo_Close_54824e94_.parquet'
output_file = 'output/backtest_analysis.txt'

os.makedirs('output', exist_ok=True)

try:
    df = pd.read_parquet(file_path)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("📊 SPY 20日均線策略回測完整分析\n")
        f.write("=" * 80 + "\n\n")
        
        # 基本資訊
        f.write("【資料概況】\n")
        f.write(f"總記錄數: {len(df):,} 筆\n")
        f.write(f"回測期間: {df['Time'].min()} 至 {df['Time'].max()}\n")
        f.write(f"回測天數: {(df['Time'].max() - df['Time'].min()).days} 天\n\n")
        
        # 績效統計
        initial_capital = df['Equity_value'].iloc[0]
        final_capital = df['Equity_value'].iloc[-1]
        total_return = ((final_capital - initial_capital) / initial_capital) * 100
        max_equity = df['Equity_value'].max()
        min_equity = df['Equity_value'].min()
        max_drawdown = ((max_equity - min_equity) / max_equity) * 100
        
        f.write("【資金變化】\n")
        f.write(f"初始資金: ${initial_capital:,.2f}\n")
        f.write(f"最終資金: ${final_capital:,.2f}\n")
        f.write(f"淨利潤: ${final_capital - initial_capital:,.2f}\n")
        f.write(f"總報酬率: {total_return:.2f}%\n")
        f.write(f"最大權益: ${max_equity:,.2f}\n")
        f.write(f"最小權益: ${min_equity:,.2f}\n")
        f.write(f"最大回撤: {max_drawdown:.2f}%\n\n")
        
        # 交易統計
        trades = df[df['Trade_action'] == 1]
        buys = df[(df['Trade_action'] == 1) & (df['Position_type'] == 'Long')]
        sells = df[(df['Trade_action'] == 1) & (df['Position_type'].isna())]
        
        f.write("【交易統計】\n")
        f.write(f"總交易次數: {len(trades)} 次\n")
        f.write(f"買入次數: {len(buys)} 次\n")
        
        # 獲利交易分析
        profitable_trades = df[df['Trade_return'] > 0]
        losing_trades = df[df['Trade_return'] < 0]
        
        if len(profitable_trades) > 0 or len(losing_trades) > 0:
            total_trades = len(profitable_trades) + len(losing_trades)
            win_rate = (len(profitable_trades) / total_trades * 100) if total_trades > 0 else 0
            
            f.write(f"獲利交易: {len(profitable_trades)} 次\n")
            f.write(f"虧損交易: {len(losing_trades)} 次\n")
            f.write(f"勝率: {win_rate:.2f}%\n")
            
            if len(profitable_trades) > 0:
                avg_win = profitable_trades['Trade_return'].mean() * 100
                f.write(f"平均獲利: {avg_win:.2f}%\n")
            
            if len(losing_trades) > 0:
                avg_loss = losing_trades['Trade_return'].mean() * 100
                f.write(f"平均虧損: {avg_loss:.2f}%\n")
        
        f.write("\n")
        
        # 年化報酬率
        years = (df['Time'].max() - df['Time'].min()).days / 365.25
        annual_return = ((final_capital / initial_capital) ** (1 / years) - 1) * 100
        
        f.write("【年化績效】\n")
        f.write(f"回測年數: {years:.2f} 年\n")
        f.write(f"年化報酬率: {annual_return:.2f}%\n\n")
        
        # 持倉分析
        holding_trades = df[df['Holding_period'].notna()]
        if len(holding_trades) > 0:
            avg_holding = holding_trades['Holding_period'].mean()
            f.write("【持倉分析】\n")
            f.write(f"平均持倉天數: {avg_holding:.1f} 天\n")
            f.write(f"最長持倉: {holding_trades['Holding_period'].max():.0f} 天\n")
            f.write(f"最短持倉: {holding_trades['Holding_period'].min():.0f} 天\n\n")
        
        # 成本分析
        total_cost = df['Transaction_cost'].sum() + df['Slippage_cost'].sum()
        f.write("【成本分析】\n")
        f.write(f"總交易成本: ${total_cost:,.2f}\n")
        f.write(f"手續費: ${df['Transaction_cost'].sum():,.2f}\n")
        f.write(f"滑價成本: ${df['Slippage_cost'].sum():,.2f}\n\n")
        
        # 最近5筆交易
        f.write("【最近 5 筆交易】\n")
        recent_trades = trades.tail(5)[['Time', 'Close', 'Position_type', 'Equity_value', 'Trade_return']]
        f.write(recent_trades.to_string(index=False) + "\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("✅ 分析完成！\n")
        f.write("=" * 80 + "\n")
    
    print(f"✅ 分析結果已儲存至: {output_file}")
    
    # 同時輸出到終端機
    with open(output_file, 'r', encoding='utf-8') as f:
        print(f.read())
    
except FileNotFoundError:
    print(f"❌ 找不到檔案: {file_path}")
except Exception as e:
    print(f"❌ 發生錯誤: {e}")
    import traceback
    traceback.print_exc()
