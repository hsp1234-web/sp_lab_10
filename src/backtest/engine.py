"""
穩定獲利策略回測系統 - 使用 Logging 模組
目標：每年都是正報酬，賺多賠少
"""
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime

# Import strategies
from src.strategies.trend import run_strategy_bollinger
from src.strategies.mean_reversion import run_strategy_zscore
# from src.strategies.forex import run_strategy_forex
# from src.strategies.margin import run_strategy_margin
from src.strategies.weekly_vol import WeeklyVolatilityStrategy

# 設定 logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'backtest_results.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()  # 同時嘗試輸出到終端
    ]
)

logger = logging.getLogger(__name__)

# 常數設定
INITIAL_CAPITAL = 1_000_000
TRANSACTION_COST = 0.0003
SLIPPAGE = 0.001
STOP_LOSS = 0.02
TAKE_PROFIT = 0.05

class ConservativeStrategy:
    """保守趨勢策略"""
    
    def __init__(self, df, capital=INITIAL_CAPITAL):
        self.df = df.copy()
        self.capital = capital
        self.trades = []
        
    def generate_signals(self):
        """生成交易訊號"""
        df = self.df
        
        # 計算技術指標
        df['SMA_50'] = df['TWII_Close'].rolling(50).mean()
        df['SMA_200'] = df['TWII_Close'].rolling(200).mean()
        
        # 進場訊號
        df['Buy_Signal'] = (
            (df['TWII_Close'] > df['SMA_200']) &
            (df['SMA_50'] > df['SMA_200']) &
            (df['RSI_14'] > 30) &
            (df['RSI_14'] < 70)
        ).astype(int)
        
        return df
    
    def backtest(self):
        """執行回測"""
        df = self.generate_signals()
        
        position = 0
        entry_price = 0
        current_capital = self.capital
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            # 進場
            if position == 0 and row['Buy_Signal'] == 1:
                entry_price = row['TWII_Close'] * (1 + SLIPPAGE)
                position = 1
                entry_date = row['Date']
                entry_year = row['Date'].year if isinstance(row['Date'], pd.Timestamp) else pd.to_datetime(row['Date']).year
                
            # 出場
            elif position == 1:
                current_price = row['TWII_Close']
                profit_pct = (current_price - entry_price) / entry_price
                
                should_exit = False
                exit_reason = ""
                
                # 停損
                if profit_pct <= -STOP_LOSS:
                    should_exit = True
                    exit_reason = "停損-2%"
                # 停利
                elif profit_pct >= TAKE_PROFIT:
                    should_exit = True
                    exit_reason = "停利+5%"
                # 跌破均線
                elif current_price < row['SMA_50']:
                    should_exit = True
                    exit_reason = "跌破50MA"
                
                if should_exit:
                    exit_price = current_price * (1 - SLIPPAGE)
                    actual_profit_pct = (exit_price - entry_price) / entry_price - TRANSACTION_COST * 2
                    
                    profit = current_capital * actual_profit_pct
                    current_capital += profit
                    
                    exit_year = row['Date'].year if isinstance(row['Date'], pd.Timestamp) else pd.to_datetime(row['Date']).year
                    
                    self.trades.append({
                        'Entry_Date': entry_date,
                        'Exit_Date': row['Date'],
                        'Entry_Year': entry_year,
                        'Exit_Year': exit_year,
                        'Entry_Price': entry_price,
                        'Exit_Price': exit_price,
                        'Profit_Pct': actual_profit_pct * 100,
                        'Profit': profit,
                        'Capital': current_capital,
                        'Reason': exit_reason
                    })
                    
                    position = 0
        
        return pd.DataFrame(self.trades), current_capital

def analyze_yearly_performance(trades_df, initial_capital):
    """分析年度績效"""
    if len(trades_df) == 0:
        return None
    
    # 確保日期格式正確
    trades_df['Exit_Date'] = pd.to_datetime(trades_df['Exit_Date'])
    trades_df['Exit_Year'] = trades_df['Exit_Date'].dt.year
    
    yearly_stats = []
    
    for year in sorted(trades_df['Exit_Year'].unique()):
        year_trades = trades_df[trades_df['Exit_Year'] == year]
        
        total_profit = year_trades['Profit'].sum()
        annual_return = (total_profit / initial_capital) * 100
        num_trades = len(year_trades)
        win_trades = len(year_trades[year_trades['Profit'] > 0])
        win_rate = (win_trades / num_trades * 100) if num_trades > 0 else 0
        
        yearly_stats.append({
            'Year': int(year),
            'Trades': num_trades,
            'Win_Trades': win_trades,
            'Win_Rate': win_rate,
            'Total_Profit': total_profit,
            'Annual_Return': annual_return,
            'Status': '✅ 獲利' if annual_return > 0 else '❌ 虧損'
        })
    
    return pd.DataFrame(yearly_stats)

def main():
    logger.info("="*80)
    logger.info("穩定獲利策略回測系統")
    logger.info("="*80)
    logger.info(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    # 載入數據
    logger.info("載入數據...")
    try:
        df = pd.read_csv('../../data/processed/master_dataset.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)
        
        logger.info(f"✓ 數據載入成功")
        logger.info(f"  期間: {df['Date'].min()} 到 {df['Date'].max()}")
        logger.info(f"  總筆數: {len(df):,}")
        logger.info(f"  包含年份: {sorted(df['Date'].dt.year.unique())}")
        logger.info("")
        
    except Exception as e:
        logger.error(f"✗ 數據載入失敗: {e}")
        return
    
    # 執行回測
    logger.info("="*80)
    logger.info("策略: 保守趨勢策略")
    logger.info("="*80)
    logger.info("進場條件:")
    logger.info("  ✓ 價格 > 200日均線")
    logger.info("  ✓ 50日均線 > 200日均線")
    logger.info("  ✓ RSI 在 30-70 之間")
    logger.info("")
    logger.info("出場條件:")
    logger.info("  ✗ 跌破 50日均線")
    logger.info("  ✗ 停損 -2%")
    logger.info("  ✗ 停利 +5%")
    logger.info("")
    
    strategy = ConservativeStrategy(df, INITIAL_CAPITAL)
    trades_df, final_capital = strategy.backtest()
    
    if len(trades_df) == 0:
        logger.warning("⚠️ 無交易訊號")
        return
    
    # 整體績效
    total_return = (final_capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    win_trades = len(trades_df[trades_df['Profit'] > 0])
    win_rate = (win_trades / len(trades_df)) * 100
    
    # 計算最大回撤
    equity_curve = [INITIAL_CAPITAL]
    for profit in trades_df['Profit']:
        equity_curve.append(equity_curve[-1] + profit)
    
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.cummax()
    drawdown = (equity_series - running_max) / running_max * 100
    max_drawdown = drawdown.min()
    
    logger.info("="*80)
    logger.info("整體績效")
    logger.info("="*80)
    logger.info(f"初始資金:     {INITIAL_CAPITAL:>12,} 元")
    logger.info(f"最終資金:     {final_capital:>12,.0f} 元")
    logger.info(f"總報酬率:     {total_return:>12.2f} %")
    logger.info(f"總獲利:       {final_capital - INITIAL_CAPITAL:>12,.0f} 元")
    logger.info(f"交易次數:     {len(trades_df):>12} 次")
    logger.info(f"獲利次數:     {win_trades:>12} 次")
    logger.info(f"虧損次數:     {len(trades_df) - win_trades:>12} 次")
    logger.info(f"勝率:         {win_rate:>12.2f} %")
    logger.info(f"最大回撤:     {max_drawdown:>12.2f} %")
    logger.info(f"平均獲利:     {trades_df['Profit'].mean():>12,.0f} 元")
    logger.info(f"最大單筆獲利: {trades_df['Profit'].max():>12,.0f} 元")
    logger.info(f"最大單筆虧損: {trades_df['Profit'].min():>12,.0f} 元")
    logger.info("")
    
    # 年度績效
    yearly_df = analyze_yearly_performance(trades_df, INITIAL_CAPITAL)
    
    if yearly_df is not None:
        logger.info("="*80)
        logger.info("年度績效分析")
        logger.info("="*80)
        logger.info(f"{'年份':<8} {'交易':<6} {'勝率':<8} {'年報酬率':<12} {'狀態':<10}")
        logger.info("-"*80)
        
        all_positive = True
        for _, row in yearly_df.iterrows():
            logger.info(f"{row['Year']:<8} {row['Trades']:<6} {row['Win_Rate']:<7.1f}% "
                       f"{row['Annual_Return']:>10.2f}%  {row['Status']:<10}")
            if row['Annual_Return'] <= 0:
                all_positive = False
        
        logger.info("")
        if all_positive:
            logger.info("🎉 達成目標！每年都是正報酬！")
        else:
            negative_years = yearly_df[yearly_df['Annual_Return'] <= 0]['Year'].tolist()
            logger.info(f"⚠️ 負報酬年份: {negative_years}")
        logger.info("")
    
    # 儲存結果
    trades_df.to_csv('results/stable_conservative_trades.csv', index=False, encoding='utf-8')
    logger.info(f"✓ 交易記錄已儲存: results/stable_conservative_trades.csv")
    
    if yearly_df is not None:
        yearly_df.to_csv('results/stable_yearly_performance.csv', index=False, encoding='utf-8')
        logger.info(f"✓ 年度績效已儲存: results/stable_yearly_performance.csv")
    
    logger.info("")
    logger.info("="*80)
    logger.info("回測完成！")
    logger.info("="*80)
    logger.info(f"日誌檔案: logs/backtest_results.log")

if __name__ == "__main__":
    main()
