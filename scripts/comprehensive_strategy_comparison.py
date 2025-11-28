#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
綜合策略比較分析腳本
比較法人策略、PCR策略、月度買進持有策略的表現
特別關注市場波動時期的表現
"""
import sys
import os
import io
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# 設置 UTF-8 輸出
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', line_buffering=True)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_strategy_comparison.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 添加 lo2cin4bt 到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'lo2cin4bt-main'))

def load_and_merge_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """載入並合併所有需要的數據"""
    import duckdb
    import pandas as pd

    logger.info("開始載入數據...")

    # 載入期貨數據
    con = duckdb.connect('data/taifex.db')
    futures_query = """
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
    futures_data = con.execute(futures_query).fetchdf()
    con.close()

    logger.info(f"期貨數據載入完成: {futures_data.shape}")

    # 載入法人數據
    con2 = duckdb.connect('data/taifex_official.db')

    # 合併三大法人的數據
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

    # 載入PCR數據
    pcr_query = """
    SELECT
        date,
        pcr_ratio,
        call_volume,
        put_volume,
        total_volume
    FROM pcr_data
    WHERE date >= '2018-01-01'
    ORDER BY date
    """
    pcr_data = con2.execute(pcr_query).fetchdf()

    con2.close()

    logger.info(f"法人數據載入完成: {institutional_data.shape}")
    logger.info(f"PCR數據載入完成: {pcr_data.shape}")

    # 合併數據
    merged_data = futures_data.copy()

    # 合併法人數據
    if not institutional_data.empty:
        merged_data = merged_data.merge(
            institutional_data,
            left_on='original_date',
            right_on='date',
            how='left'
        )

    # 合併PCR數據
    if not pcr_data.empty:
        merged_data = merged_data.merge(
            pcr_data,
            left_on='original_date',
            right_on='date',
            how='left'
        )

    logger.info(f"數據合併完成: {merged_data.shape}")

    return merged_data, institutional_data, pcr_data

def test_strategy(strategy_class, strategy_name: str, data: pd.DataFrame, params: Dict) -> Dict:
    """測試單個策略的表現"""
    logger.info(f"\n=== 測試 {strategy_name} ===")

    try:
        # 建立策略實例
        strategy = strategy_class(data, params, logger)

        # 生成信號
        signals = strategy.generate_signals()

        # 模擬交易
        trades = []
        current_position = 0
        entry_price = 0
        entry_date = None
        position_size = 1

        for idx, row in data.iterrows():
            if row['Close'] <= 0:
                continue

            if signals[idx] == 1 and current_position <= 0:
                # 進場多頭
                current_position = position_size
                entry_price = row['Close']
                entry_date = row['original_date']
                trades.append({
                    'type': 'LONG_ENTRY',
                    'date': entry_date,
                    'price': entry_price
                })

            elif signals[idx] == -1 and current_position > 0:
                # 出場多頭
                exit_price = row['Close']
                pnl = (exit_price - entry_price) / entry_price * 100
                trades.append({
                    'type': 'LONG_EXIT',
                    'date': row['original_date'],
                    'price': exit_price,
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'pnl_pct': pnl,
                    'holding_days': (pd.to_datetime(row['original_date']) - pd.to_datetime(entry_date)).days
                })
                current_position = 0

        # 統計結果
        completed_trades = [t for t in trades if 'pnl_pct' in t]

        if completed_trades:
            avg_pnl = sum(t['pnl_pct'] for t in completed_trades) / len(completed_trades)
            win_rate = len([t for t in completed_trades if t['pnl_pct'] > 0]) / len(completed_trades) * 100
            avg_holding_days = sum(t['holding_days'] for t in completed_trades) / len(completed_trades)
            max_win = max(t['pnl_pct'] for t in completed_trades)
            max_loss = min(t['pnl_pct'] for t in completed_trades)

            # 月度統計
            monthly_returns = {}
            for trade in completed_trades:
                month = trade['date'][:7]  # YYYY-MM
                if month not in monthly_returns:
                    monthly_returns[month] = []
                monthly_returns[month].append(trade['pnl_pct'])

            monthly_stats = {}
            for month, returns in monthly_returns.items():
                monthly_stats[month] = sum(returns) / len(returns) if returns else 0

            # 分析市場波動時期
            volatility_periods = identify_volatility_periods(data)
            volatility_performance = analyze_volatility_performance(completed_trades, volatility_periods)

            results = {
                'strategy_name': strategy_name,
                'total_trades': len(completed_trades),
                'win_rate': win_rate,
                'avg_pnl': avg_pnl,
                'avg_holding_days': avg_holding_days,
                'max_win': max_win,
                'max_loss': max_loss,
                'monthly_returns': monthly_stats,
                'volatility_performance': volatility_performance,
                'total_signals': len(signals[signals != 0])
            }
        else:
            results = {
                'strategy_name': strategy_name,
                'total_trades': 0,
                'win_rate': 0,
                'avg_pnl': 0,
                'avg_holding_days': 0,
                'max_win': 0,
                'max_loss': 0,
                'monthly_returns': {},
                'volatility_performance': {},
                'total_signals': 0
            }

        logger.info(f"{strategy_name} 測試完成:")
        logger.info(f"  總交易: {results['total_trades']}")
        logger.info(f"  勝率: {results['win_rate']:.1f}%")
        logger.info(f"  平均PnL: {results['avg_pnl']:.2f}%")
        logger.info(f"  平均持有天數: {results['avg_holding_days']:.1f}")

        return results

    except Exception as e:
        logger.error(f"{strategy_name} 測試失敗: {e}")
        return {
            'strategy_name': strategy_name,
            'error': str(e)
        }

def identify_volatility_periods(data: pd.DataFrame) -> Dict[str, List[str]]:
    """識別市場波動時期"""
    # 計算日收益率
    data = data.copy()
    data['returns'] = data['Close'].pct_change()

    # 計算20日滾動波動率
    data['volatility'] = data['returns'].rolling(20).std() * np.sqrt(252)

    # 識別高波動時期 (波動率 > 75百分位數)
    vol_threshold = data['volatility'].quantile(0.75)
    high_vol_dates = data[data['volatility'] > vol_threshold]['original_date'].tolist()

    # 識別重大下跌時期 (單日跌幅 > 3%)
    major_down_dates = data[data['returns'] < -0.03]['original_date'].tolist()

    # 識別重大上漲時期 (單日漲幅 > 3%)
    major_up_dates = data[data['returns'] > 0.03]['original_date'].tolist()

    return {
        'high_volatility': high_vol_dates,
        'major_down': major_down_dates,
        'major_up': major_up_dates
    }

def analyze_volatility_performance(trades: List[Dict], volatility_periods: Dict) -> Dict:
    """分析在波動時期的表現"""
    vol_performance = {}

    for period_name, dates in volatility_periods.items():
        period_trades = []
        for trade in trades:
            # 檢查交易是否在波動時期
            trade_dates = []
            if 'entry_date' in trade and 'date' in trade:
                start_date = pd.to_datetime(trade['entry_date'])
                end_date = pd.to_datetime(trade['date'])
                trade_dates = pd.date_range(start_date, end_date).strftime('%Y/%m/%d').tolist()

            if any(trade_date in dates for trade_date in trade_dates):
                period_trades.append(trade)

        if period_trades:
            avg_pnl = sum(t['pnl_pct'] for t in period_trades) / len(period_trades)
            win_rate = len([t for t in period_trades if t['pnl_pct'] > 0]) / len(period_trades) * 100
        else:
            avg_pnl = 0
            win_rate = 0

        vol_performance[period_name] = {
            'trades_count': len(period_trades),
            'avg_pnl': avg_pnl,
            'win_rate': win_rate
        }

    return vol_performance

def calculate_buy_and_hold_returns(data: pd.DataFrame) -> Dict:
    """計算買進持有策略的月度回報"""
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

    # 總體統計
    if monthly_returns:
        monthly_pnls = list(monthly_returns.values())
        positive_months = len([r for r in monthly_pnls if r > 0])
        win_rate = positive_months / len(monthly_pnls) * 100
        avg_monthly_return = sum(monthly_pnls) / len(monthly_pnls)

        # 年化回報 (假設每月交易)
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
            'total_months': len(monthly_pnls),
            'win_rate': win_rate,
            'avg_monthly_return': avg_monthly_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'monthly_returns': monthly_returns
        }

    return {'strategy_name': '買進持有', 'error': '無足夠數據'}

def main():
    logger.info("開始綜合策略比較分析")

    try:
        # 載入數據
        merged_data, institutional_data, pcr_data = load_and_merge_data()

        if merged_data.empty:
            logger.error("數據載入失敗")
            return

        # 測試各個策略
        results = []

        # 1. 法人策略
        from backtester.Institutional_Strategy_backtester import InstitutionalStrategy
        institutional_params = {
            'consecutive_days': 3,
            'net_buying_threshold': 70,
            'risk_per_trade': 0.01,
            'stop_loss_atr_multiplier': 2.0,
            'max_monthly_drawdown': 0.05
        }
        institutional_result = test_strategy(
            InstitutionalStrategy, "法人買賣超策略",
            merged_data, institutional_params
        )
        results.append(institutional_result)

        # 2. PCR策略
        from backtester.PCR_Strategy_backtester import PCR_Strategy
        pcr_params = {
            'pcr_high_threshold': 1.2,
            'pcr_low_threshold': 0.8,
            'pcr_ma_window': 5,
            'risk_per_trade': 0.01,
            'stop_loss_atr_multiplier': 2.0,
            'max_monthly_drawdown': 0.05
        }
        pcr_result = test_strategy(
            PCR_Strategy, "PCR比率策略",
            merged_data, pcr_params
        )
        results.append(pcr_result)

        # 3. 月度買進持有 (基準)
        buy_hold_result = calculate_buy_and_hold_returns(merged_data)
        results.append(buy_hold_result)

        # 生成綜合報告
        generate_comprehensive_report(results, merged_data)

        logger.info("綜合策略比較分析完成")

    except Exception as e:
        logger.error(f"分析失敗: {e}")
        import traceback
        traceback.print_exc()

def generate_comprehensive_report(results: List[Dict], data: pd.DataFrame):
    """生成綜合報告"""
    logger.info("\n" + "="*80)
    logger.info("🎯 綜合策略比較報告")
    logger.info("="*80)

    # 基本統計比較
    logger.info("\n📊 基本統計比較:")
    logger.info("-" * 80)
    logger.info(f"{'策略名稱':<25} {'總交易':<8} {'勝率%':<8} {'平均PnL%':<10} {'持有天數':<8}")
    logger.info("-" * 80)

    for result in results:
        if 'error' not in result:
            name = result['strategy_name'][:12]
            trades = result.get('total_trades', result.get('total_months', 0))
            win_rate = result.get('win_rate', 0)
            avg_return = result.get('avg_pnl', result.get('avg_monthly_return', 0))
            holding_days = result.get('avg_holding_days', 0)
            logger.info(f"{name:<25} {trades:<8} {win_rate:<8.1f} {avg_return:<10.2f} {holding_days:<8.1f}")

    # 月度盈利能力分析
    logger.info("\n💰 月度盈利能力分析:")
    logger.info("-" * 80)
    logger.info(f"{'策略名稱':<25} {'盈利月':<8} {'總月數':<8} {'月勝率%':<10} {'平均月回報%':<12} {'最差月%':<10}")
    logger.info("-" * 80)

    for result in results:
        if 'monthly_returns' in result and result['monthly_returns']:
            monthly_rets = list(result['monthly_returns'].values())
            profitable_months = len([r for r in monthly_rets if r > 0])
            total_months = len(monthly_rets)
            monthly_win_rate = profitable_months / total_months * 100 if total_months > 0 else 0
            avg_monthly = sum(monthly_rets) / len(monthly_rets) if monthly_rets else 0
            max_loss_month = min(monthly_rets) if monthly_rets else 0

            logger.info(f"{result['strategy_name']:<25} {profitable_months:<8} {total_months:<8} {monthly_win_rate:<10.1f} {avg_monthly:<12.2f} {max_loss_month:<10.2f}")

    # 波動時期表現分析
    logger.info("\n🌊 市場波動時期表現分析:")
    logger.info("-" * 80)
    logger.info(f"{'策略名稱':<25} {'時期':<10} {'交易數':<8} {'勝率%':<8} {'平均PnL%':<10}")
    logger.info("-" * 80)

    for result in results:
        if 'volatility_performance' in result:
            for period_name, perf in result['volatility_performance'].items():
                period_display = {
                    'high_volatility': '高波動',
                    'major_down': '重大下跌',
                    'major_up': '重大上漲'
                }.get(period_name, period_name)

                logger.info(f"{result['strategy_name']:<25} {period_display:<10} {perf['trades_count']:<8} {perf['win_rate']:<8.1f} {perf['avg_pnl']:<10.2f}"))

    # 風險控制評估
    logger.info("\n⚠️ 風險控制評估:")
    logger.info("-" * 80)

    for result in results:
        if 'error' not in result:
            strategy_name = result['strategy_name']
            max_drawdown = result.get('max_drawdown', 0)
            win_rate = result.get('win_rate', 0)
            avg_return = result.get('avg_pnl', result.get('avg_monthly_return', 0))

            # 評估風險等級
            if max_drawdown > 20:
                risk_level = "🔴 高風險"
            elif max_drawdown > 10:
                risk_level = "🟡 中風險"
            else:
                risk_level = "🟢 低風險"

            # 評估虧損控制
            if avg_return >= -5:
                loss_control = "✅ 優秀 (虧損<5%)"
            elif avg_return >= -10:
                loss_control = "⚠️ 一般 (虧損<10%)"
            else:
                loss_control = "❌ 需改進"

            logger.info(f"{strategy_name}:")
            logger.info(f"  最大回撤: {max_drawdown:.1f}% - {risk_level}")
            logger.info(f"  虧損控制: {loss_control}")
            logger.info("")

    # 最終建議
    logger.info("🎯 最終建議:")
    logger.info("-" * 80)

    # 找出最佳策略
    valid_results = [r for r in results if 'error' not in r]
    if valid_results:
        best_strategy = max(valid_results,
                          key=lambda x: x.get('win_rate', 0) * 0.4 +
                                       (-x.get('avg_pnl', x.get('avg_monthly_return', 0))) * 0.3 +
                                       (-x.get('max_drawdown', 0)) * 0.3)

        logger.info(f"🏆 推薦策略: {best_strategy['strategy_name']}")
        logger.info(f"   勝率: {best_strategy.get('win_rate', 0):.1f}%")
        logger.info(f"   平均回報: {best_strategy.get('avg_pnl', best_strategy.get('avg_monthly_return', 0)):.2f}%")
        logger.info(f"   最大回撤: {best_strategy.get('max_drawdown', 0):.1f}%")

    logger.info("\n📈 後續優化方向:")
    logger.info("1. 優化參數設定，提升勝率")
    logger.info("2. 加入更多過濾條件，減少假訊號")
    logger.info("3. 實作策略組合，分散風險")
    logger.info("4. 加入機器學習優化")

    # 導出詳細結果
    output_file = 'output/comprehensive_strategy_comparison.csv'
    import pandas as pd
    comparison_df = pd.DataFrame(results)
    comparison_df.to_csv(output_file, index=False, encoding='utf-8')
    logger.info(f"\n📄 詳細結果已導出到: {output_file}")

if __name__ == "__main__":
    main()

