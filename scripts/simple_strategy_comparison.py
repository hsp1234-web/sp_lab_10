#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版策略比較分析
"""
import sys
import os
import io
import logging
from pathlib import Path

# 設置 UTF-8 輸出
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', line_buffering=True)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_strategy_comparison.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 添加 lo2cin4bt 到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'lo2cin4bt-main'))

def main():
    logger.info("開始簡化版策略比較分析")

    try:
        import duckdb
        import pandas as pd
        import numpy as np

        # 確保pandas可用
        if 'pd' not in globals():
            import pandas as pd

        # 載入數據
        logger.info("載入台指期數據...")
        con = duckdb.connect('data/taifex.db')
        query = """
        SELECT
            Date as original_date,
            strptime(Date, '%Y/%m/%d') as Time,
            Symbol,
            Open,
            High,
            Low,
            Close,
            Volume
        FROM futures_data
        WHERE Symbol = 'TX'
        AND strptime(Date, '%Y/%m/%d') >= strptime('2018-01-01', '%Y-%m-%d')
        AND strptime(Date, '%Y/%m/%d') <= strptime('2024-12-31', '%Y-%m-%d')
        AND Close IS NOT NULL AND Close > 1000 AND Close < 30000
        ORDER BY strptime(Date, '%Y/%m/%d')
        """
        data = con.execute(query).fetchdf()
        con.close()

        logger.info(f"數據載入完成: {data.shape} 筆")

        # 載入法人和PCR數據
        con2 = duckdb.connect('data/taifex_official.db')

        # 法人數據
        institutional_query = """
        SELECT
            date,
            SUM(CASE WHEN investor_type = 'Foreign_Investor' THEN total_net ELSE 0 END) as foreign_net,
            SUM(CASE WHEN investor_type = 'Investment_Trust' THEN total_net ELSE 0 END) as trust_net,
            SUM(CASE WHEN investor_type = 'Dealer' THEN total_net ELSE 0 END) as dealer_net,
            SUM(total_net) as total_institutional_net
        FROM institutional_investors
        WHERE date >= '2018-01-01'
        GROUP BY date
        ORDER BY date
        """
        institutional_data = con2.execute(institutional_query).fetchdf()

        # PCR數據
        pcr_query = """
        SELECT date, pcr_ratio, call_volume, put_volume
        FROM pcr_data
        WHERE date >= '2018-01-01'
        ORDER BY date
        """
        pcr_data = con2.execute(pcr_query).fetchdf()

        con2.close()

        # 合併數據
        merged_data = data.copy()

        # 添加法人數據欄位
        if not institutional_data.empty:
            institutional_dict = dict(zip(institutional_data['date'], institutional_data['total_institutional_net']))
            merged_data['total_net'] = merged_data['original_date'].map(institutional_dict)

        # 添加PCR數據欄位
        if not pcr_data.empty:
            pcr_dict = dict(zip(pcr_data['date'], pcr_data['pcr_ratio']))
            merged_data['pcr_ratio'] = merged_data['original_date'].map(pcr_dict)

        logger.info(f"數據合併完成: {merged_data.shape}")

        # 測試策略
        results = []

        # 1. 法人策略
        logger.info("\n=== 測試法人買賣超策略 ===")
        from backtester.Institutional_Strategy_backtester import InstitutionalStrategy

        params = {
            'consecutive_days': 3,
            'net_buying_threshold': 70,
            'risk_per_trade': 0.01,
            'stop_loss_atr_multiplier': 2.0,
            'max_monthly_drawdown': 0.05
        }

        strategy = InstitutionalStrategy(merged_data, params, logger)
        signals = strategy.generate_signals()

        # 簡單模擬交易
        trades = simulate_trades(merged_data, signals)
        institutional_result = analyze_trades("法人買賣超策略", trades, merged_data)
        results.append(institutional_result)

        # 2. PCR策略
        logger.info("\n=== 測試PCR比率策略 ===")
        from backtester.PCR_Strategy_backtester import PCR_Strategy

        params = {
            'pcr_high_threshold': 1.2,
            'pcr_low_threshold': 0.8,
            'pcr_ma_window': 5,
            'risk_per_trade': 0.01,
            'stop_loss_atr_multiplier': 2.0,
            'max_monthly_drawdown': 0.05
        }

        strategy = PCR_Strategy(merged_data, params, logger)
        signals = strategy.generate_signals()

        trades = simulate_trades(merged_data, signals)
        pcr_result = analyze_trades("PCR比率策略", trades, merged_data)
        results.append(pcr_result)

        # 3. 買進持有基準
        logger.info("\n=== 計算買進持有基準 ===")
        buy_hold_result = calculate_buy_and_hold(merged_data)
        results.append(buy_hold_result)

        # 生成報告
        generate_report(results, merged_data)

        logger.info("策略比較分析完成")

    except Exception as e:
        logger.error(f"分析失敗: {e}")
        import traceback
        traceback.print_exc()

def simulate_trades(data, signals):
    """模擬交易"""
    import pandas as pd
    trades = []
    current_position = 0
    entry_price = 0
    entry_date = None

    for idx, row in data.iterrows():
        if signals[idx] == 1 and current_position <= 0:
            # 進場
            current_position = 1
            entry_price = row['Close']
            entry_date = row['original_date']

        elif signals[idx] == -1 and current_position > 0:
            # 出場
            exit_price = row['Close']
            pnl = (exit_price - entry_price) / entry_price * 100
            trades.append({
                'entry_date': entry_date,
                'exit_date': row['original_date'],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl_pct': pnl,
                'holding_days': (pd.to_datetime(row['original_date']) - pd.to_datetime(entry_date)).days
            })
            current_position = 0

    return trades

def analyze_trades(strategy_name, trades, data):
    """分析交易結果"""
    if not trades:
        return {
            'strategy_name': strategy_name,
            'total_trades': 0,
            'win_rate': 0,
            'avg_pnl': 0,
            'avg_holding_days': 0,
            'max_win': 0,
            'max_loss': 0,
            'monthly_win_rate': 0,
            'monthly_avg_return': 0,
            'max_monthly_loss': 0
        }

    # 基本統計
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['pnl_pct'] > 0])
    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
    avg_pnl = sum(t['pnl_pct'] for t in trades) / total_trades
    avg_holding_days = sum(t['holding_days'] for t in trades) / total_trades
    max_win = max(t['pnl_pct'] for t in trades)
    max_loss = min(t['pnl_pct'] for t in trades)

    # 月度統計
    monthly_returns = {}
    for trade in trades:
        month = trade['exit_date'][:7]  # YYYY-MM
        if month not in monthly_returns:
            monthly_returns[month] = []
        monthly_returns[month].append(trade['pnl_pct'])

    monthly_stats = {}
    for month, returns in monthly_returns.items():
        monthly_stats[month] = sum(returns) / len(returns) if returns else 0

    monthly_win_rate = len([r for r in monthly_stats.values() if r > 0]) / len(monthly_stats) * 100 if monthly_stats else 0
    monthly_avg_return = sum(monthly_stats.values()) / len(monthly_stats) if monthly_stats else 0
    max_monthly_loss = min(monthly_stats.values()) if monthly_stats else 0

    # 分析波動時期表現
    volatility_analysis = analyze_volatility_performance(trades, data)

    return {
        'strategy_name': strategy_name,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'avg_pnl': avg_pnl,
        'avg_holding_days': avg_holding_days,
        'max_win': max_win,
        'max_loss': max_loss,
        'monthly_win_rate': monthly_win_rate,
        'monthly_avg_return': monthly_avg_return,
        'max_monthly_loss': max_monthly_loss,
        'volatility_analysis': volatility_analysis
    }

def analyze_volatility_performance(trades, data):
    """分析波動時期的表現"""
    import numpy as np
    import pandas as pd

    # 計算日收益率和波動率
    data = data.copy()
    data['returns'] = data['Close'].pct_change()
    data['volatility'] = data['returns'].rolling(20).std() * np.sqrt(252)

    # 識別波動時期
    vol_threshold = data['volatility'].quantile(0.75)
    high_vol_dates = set(data[data['volatility'] > vol_threshold]['original_date'].tolist())
    major_down_dates = set(data[data['returns'] < -0.03]['original_date'].tolist())
    major_up_dates = set(data[data['returns'] > 0.03]['original_date'].tolist())

    # 統計各時期表現
    periods = {
        'high_volatility': high_vol_dates,
        'major_down': major_down_dates,
        'major_up': major_up_dates
    }

    results = {}
    for period_name, dates in periods.items():
        period_trades = []
        for trade in trades:
            # 檢查交易期間是否與波動時期重疊
            trade_dates = set(pd.date_range(trade['entry_date'], trade['exit_date']).strftime('%Y/%m/%d').tolist())
            if trade_dates & dates:  # 有交集
                period_trades.append(trade)

        if period_trades:
            avg_pnl = sum(t['pnl_pct'] for t in period_trades) / len(period_trades)
            win_rate = len([t for t in period_trades if t['pnl_pct'] > 0]) / len(period_trades) * 100
        else:
            avg_pnl = 0
            win_rate = 0

        results[period_name] = {
            'trades_count': len(period_trades),
            'avg_pnl': avg_pnl,
            'win_rate': win_rate
        }

    return results

def calculate_buy_and_hold(data):
    """計算買進持有策略"""
    import pandas as pd
    data = data.copy()
    data['date'] = pd.to_datetime(data['original_date'])
    data['year_month'] = data['date'].dt.to_period('M')

    monthly_returns = {}

    for period, group in data.groupby('year_month'):
        if len(group) > 1:
            month_start_price = group.iloc[0]['Close']
            month_end_price = group.iloc[-1]['Close']
            monthly_return = (month_end_price - month_start_price) / month_start_price * 100
            monthly_returns[str(period)] = monthly_return

    if monthly_returns:
        monthly_pnls = list(monthly_returns.values())
        positive_months = len([r for r in monthly_pnls if r > 0])
        total_months = len(monthly_pnls)
        win_rate = positive_months / total_months * 100 if total_months > 0 else 0
        avg_monthly_return = sum(monthly_pnls) / total_months
        max_monthly_loss = min(monthly_pnls) if monthly_pnls else 0

        # 年化回報
        annualized_return = ((1 + avg_monthly_return/100) ** 12 - 1) * 100

        # 最大回撤
        cumulative = [sum(monthly_pnls[:i+1]) for i in range(len(monthly_pnls))]
        max_drawdown = 0
        peak = cumulative[0]
        for value in cumulative[1:]:
            if value > peak:
                peak = value
            drawdown = peak - value
            max_drawdown = max(max_drawdown, drawdown)

        return {
            'strategy_name': '買進持有',
            'total_trades': total_months,
            'win_rate': win_rate,
            'avg_pnl': annualized_return,  # 年化回報
            'avg_holding_days': 30,  # 平均持有30天
            'max_win': max(monthly_pnls),
            'max_loss': min(monthly_pnls),
            'monthly_win_rate': win_rate,
            'monthly_avg_return': avg_monthly_return,
            'max_monthly_loss': max_monthly_loss,
            'max_drawdown': max_drawdown
        }

    return {'strategy_name': '買進持有', 'error': '無足夠數據'}

def generate_report(results, data):
    """生成綜合報告"""
    logger.info("\n" + "="*80)
    logger.info("🎯 非技術指標策略比較報告")
    logger.info("="*80)

    # 基本統計比較
    logger.info("\n📊 基本統計比較:")
    logger.info("-" * 80)
    logger.info(f"{'策略名稱':<15} {'總交易':<8} {'勝率%':<8} {'平均PnL%':<12} {'持有天數':<10}")
    logger.info("-" * 80)

    for result in results:
        if 'error' not in result:
            name = result['strategy_name'][:14]
            trades = result['total_trades']
            win_rate = result['win_rate']
            avg_pnl = result['avg_pnl']
            holding_days = result['avg_holding_days']
            logger.info(f"{name:<15} {trades:<8} {win_rate:<8.1f} {avg_pnl:<12.2f} {holding_days:<10.1f}")

    # 月度表現分析
    logger.info("\n💰 月度盈利能力分析:")
    logger.info("-" * 80)
    logger.info(f"{'策略名稱':<15} {'月勝率%':<10} {'平均月回報%':<14} {'最差月%':<10} {'最大回撤%':<12}")
    logger.info("-" * 80)

    for result in results:
        if 'error' not in result:
            name = result['strategy_name'][:14]
            monthly_win = result['monthly_win_rate']
            monthly_avg = result['monthly_avg_return']
            max_monthly_loss = result['max_monthly_loss']
            max_drawdown = result.get('max_drawdown', 0)
            logger.info(f"{name:<15} {monthly_win:<10.1f} {monthly_avg:<14.2f} {max_monthly_loss:<10.2f} {max_drawdown:<12.1f}")

    # 波動時期表現分析
    logger.info("\n🌊 市場波動時期表現分析:")
    logger.info("-" * 80)

    period_names = {'high_volatility': '高波動時期', 'major_down': '重大下跌', 'major_up': '重大上漲'}

    for result in results:
        if 'volatility_analysis' in result and result['volatility_analysis']:
            logger.info(f"\n{result['strategy_name']}:")
            for period_key, perf in result['volatility_analysis'].items():
                period_name = period_names.get(period_key, period_key)
                logger.info(f"  {period_name}: {perf['trades_count']}筆交易, 勝率{perf['win_rate']:.1f}%, 平均PnL{perf['avg_pnl']:.2f}%")

    # 風險評估
    logger.info("\n⚠️ 風險控制評估:")
    logger.info("-" * 80)

    for result in results:
        if 'error' not in result:
            strategy_name = result['strategy_name']
            max_drawdown = result.get('max_drawdown', 0)
            win_rate = result['win_rate']
            monthly_avg = result['monthly_avg_return']

            # 評估虧損控制能力
            if monthly_avg >= -2:
                loss_control = "✅ 優秀 (月均虧損<2%)"
            elif monthly_avg >= -5:
                loss_control = "⚠️ 一般 (月均虧損<5%)"
            else:
                loss_control = "❌ 需改進 (月均虧損>5%)"

            logger.info(f"{strategy_name}:")
            logger.info(f"  月均回報: {monthly_avg:.2f}% - {loss_control}")
            logger.info(f"  最大回撤: {max_drawdown:.1f}%")

    # 最終建議
    logger.info("\n🎯 最終建議:")
    logger.info("-" * 80)

    # 找出表現最好的策略
    valid_results = [r for r in results if 'error' not in r]
    if valid_results:
        # 綜合評分：月均回報 * 0.5 + 勝率 * 0.3 - 最大回撤 * 0.2
        best_strategy = max(valid_results,
                          key=lambda x: x['monthly_avg_return'] * 0.5 +
                                       x['win_rate'] * 0.003 -  # 百分比轉換
                                       x.get('max_drawdown', 0) * 0.2)

        logger.info(f"🏆 綜合表現最佳: {best_strategy['strategy_name']}")
        logger.info(f"   月均回報: {best_strategy['monthly_avg_return']:.2f}%")
        logger.info(f"   月勝率: {best_strategy['monthly_win_rate']:.1f}%")
        logger.info(f"   最大回撤: {best_strategy.get('max_drawdown', 0):.1f}%")

        # 判斷是否能每月盈利
        if best_strategy['monthly_avg_return'] > 0:
            logger.info("✅ 可以做到每月盈利！")
        elif best_strategy['monthly_avg_return'] > -5:
            logger.info("⚠️ 可以控制虧損在5%以內")
        else:
            logger.info("❌ 虧損控制需改進")

    logger.info("\n📈 後續優化方向:")
    logger.info("1. 優化參數設定，提升勝率")
    logger.info("2. 加入更多過濾條件，減少假訊號")
    logger.info("3. 實作策略組合，分散風險")
    logger.info("4. 測試機器學習優化")

    # 導出詳細結果
    output_file = 'output/strategy_comparison_results.csv'
    import pandas as pd
    comparison_df = pd.DataFrame(results)
    comparison_df.to_csv(output_file, index=False, encoding='utf-8')
    logger.info(f"\n📄 詳細結果已導出到: {output_file}")

if __name__ == "__main__":
    main()

