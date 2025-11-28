# -*- coding: utf-8 -*-
"""
使用真實數據驗證本金保護區間策略假設
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class RealDataStrategyValidator:
    """真實數據策略驗證器"""

    def __init__(self):
        self.config = {
            'monthly_mdd_limit': 0.05,  # 月度MDD 5%
            'z_score_entry': 2.0,       # 進場Z分數
            'z_score_exit': 0.5,        # 出場Z分數
            'max_holding_days': 20,     # 最大持有天數
            'cash_allocation': 0.6,     # 現金60%
            'pair_allocation': 0.3,     # 配對30%
            'hedge_allocation': 0.1     # 保護10%
        }

    def load_real_data(self):
        """載入真實數據"""
        print("=== 載入真實市場數據 ===")

        try:
            # 載入台灣指數數據
            twii_data = pd.read_csv('data/twii_real_data.csv')
            twii_data['Date'] = pd.to_datetime(twii_data['Date'])
            twii_data = twii_data.sort_values('Date').reset_index(drop=True)

            print(f"台灣指數數據: {len(twii_data)} 筆")
            print(f"數據期間: {twii_data['Date'].min()} 到 {twii_data['Date'].max()}")

            # 載入VIX數據 (如果有)
            try:
                vix_data = pd.read_csv('data/vix_data.csv')
                vix_data['Date'] = pd.to_datetime(vix_data['Date'])
                print(f"VIX數據: {len(vix_data)} 筆")
            except:
                vix_data = None
                print("VIX數據載入失敗")

            return {
                'twii': twii_data,
                'vix': vix_data
            }

        except Exception as e:
            print(f"數據載入失敗: {e}")
            return None

    def calculate_zscore_signals(self, price_data, window=60):
        """計算Z分數配對信號"""
        print("=== 計算Z分數配對信號 ===")

        # 計算移動平均和標準差
        price_data = price_data.copy()
        price_data['ma'] = price_data['Close'].rolling(window=window).mean()
        price_data['std'] = price_data['Close'].rolling(window=window).std()
        price_data['z_score'] = (price_data['Close'] - price_data['ma']) / price_data['std']

        # 生成交易信號
        signals = []

        for i in range(window, len(price_data)):
            current_z = price_data['z_score'].iloc[i]
            current_date = price_data['Date'].iloc[i]
            current_price = price_data['Close'].iloc[i]

            # 進場條件
            if abs(current_z) > self.config['z_score_entry']:
                signal_type = 'long' if current_z < -self.config['z_score_entry'] else 'short'
                signals.append({
                    'date': current_date,
                    'signal_type': signal_type,
                    'z_score': current_z,
                    'price': current_price,
                    'action': 'entry'
                })

            # 出場條件 (簡化版本)
            elif abs(current_z) < self.config['z_score_exit']:
                signals.append({
                    'date': current_date,
                    'signal_type': 'exit',
                    'z_score': current_z,
                    'price': current_price,
                    'action': 'exit'
                })

        signals_df = pd.DataFrame(signals)
        print(f"生成交易信號: {len(signals_df)} 個")

        if len(signals_df) > 0:
            entry_signals = signals_df[signals_df['action'] == 'entry']
            print(f"進場信號: {len(entry_signals)} 個")
            print(f"做多信號: {len(entry_signals[entry_signals['signal_type'] == 'long'])} 個")
            print(f"做空信號: {len(entry_signals[entry_signals['signal_type'] == 'short'])} 個")

        return signals_df

    def simulate_real_trading(self, price_data, signals_df):
        """模擬真實交易"""
        print("=== 模擬真實交易 ===")

        capital = 1000000  # 初始資金100萬
        position = 0  # 當前倉位
        entry_price = None
        entry_date = None

        trades = []
        daily_performance = []

        price_data = price_data.copy()
        signals_df = signals_df.copy()

        # 按日期合併信號
        price_data['date'] = price_data['Date']

        for idx, row in price_data.iterrows():
            current_date = row['Date']
            current_price = row['Close']

            # 檢查是否有信號
            day_signals = signals_df[signals_df['date'] == current_date]

            if not day_signals.empty:
                signal = day_signals.iloc[0]

                if signal['action'] == 'entry' and position == 0:
                    # 開倉
                    position = 0.3 if signal['signal_type'] == 'long' else -0.3  # 30%倉位
                    entry_price = current_price
                    entry_date = current_date

                    print(f"開倉: {current_date.strftime('%Y-%m-%d')} {signal['signal_type']} "
                          f"價格:{current_price:.0f} 倉位:{position}")

                elif signal['action'] == 'exit' and position != 0:
                    # 平倉
                    pnl = (current_price - entry_price) * position * (capital / entry_price)
                    capital += pnl

                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position': position,
                        'pnl': pnl,
                        'holding_days': (current_date - entry_date).days
                    })

                    print(f"平倉: {current_date.strftime('%Y-%m-%d')} "
                          f"價格:{current_price:.0f} PnL:{pnl:.0f}")

                    position = 0
                    entry_price = None
                    entry_date = None

                # 檢查持有時間限制
                elif position != 0 and entry_date and (current_date - entry_date).days >= self.config['max_holding_days']:
                    # 強制平倉
                    pnl = (current_price - entry_price) * position * (capital / entry_price)
                    capital += pnl

                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position': position,
                        'pnl': pnl,
                        'holding_days': (current_date - entry_date).days,
                        'forced_exit': True
                    })

                    print(f"強制平倉: {current_date.strftime('%Y-%m-%d')} "
                          f"價格:{current_price:.0f} PnL:{pnl:.0f} (持有{self.config['max_holding_days']}天)")

                    position = 0
                    entry_price = None
                    entry_date = None

            # 記錄每日表現
            daily_performance.append({
                'date': current_date,
                'capital': capital,
                'price': current_price,
                'position': position
            })

        trades_df = pd.DataFrame(trades)
        performance_df = pd.DataFrame(daily_performance)

        # 總結交易統計
        if len(trades_df) > 0:
            print("\n交易統計:")
            print(f"總交易數: {len(trades_df)}")
            print(f"盈利交易: {len(trades_df[trades_df['pnl'] > 0])}")
            print(f"虧損交易: {len(trades_df[trades_df['pnl'] < 0])}")
            win_rate = len(trades_df[trades_df['pnl'] > 0]) / len(trades_df)
            print(f"勝率: {win_rate:.1%}")
            print(f"平均持倉天數: {trades_df['holding_days'].mean():.1f}")
            print(f"總盈虧: {trades_df['pnl'].sum():.0f}")
            if 'forced_exit' in trades_df.columns:
                forced_rate = trades_df['forced_exit'].sum() / len(trades_df) * 100
                print(f"強制平倉比例: {forced_rate:.1f}%")

        return performance_df, trades_df

    def calculate_monthly_performance(self, daily_performance):
        """計算月度表現"""
        print("=== 計算月度表現 ===")

        perf_df = pd.DataFrame(daily_performance)
        perf_df['month'] = perf_df['date'].dt.to_period('M')

        monthly_results = []

        for month, group in perf_df.groupby('month'):
            if len(group) >= 5:  # 至少5個交易日
                start_capital = group['capital'].iloc[0]
                end_capital = group['capital'].iloc[-1]
                monthly_return = (end_capital - start_capital) / start_capital

                # 計算月度最大回撤
                capital_series = group['capital'].values
                peak = capital_series[0]
                max_drawdown = 0

                for capital in capital_series:
                    if capital > peak:
                        peak = capital
                    drawdown = (peak - capital) / peak
                    max_drawdown = max(max_drawdown, drawdown)

                monthly_results.append({
                    'month': str(month),
                    'start_capital': start_capital,
                    'end_capital': end_capital,
                    'monthly_return': monthly_return,
                    'max_drawdown': max_drawdown
                })

        monthly_df = pd.DataFrame(monthly_results)

        if len(monthly_df) > 0:
            print("\n月度統計:")
            print(f"分析月份: {len(monthly_df)}")
            positive_months = len(monthly_df[monthly_df['monthly_return'] > 0])
            print(f"正報酬月數: {positive_months}")
            positive_ratio = positive_months / len(monthly_df)
            print(f"正報酬比例: {positive_ratio:.2%}")
            print(f"平均月報酬: {monthly_df['monthly_return'].mean():.2%}")
            print(f"最大月虧損: {monthly_df['monthly_return'].min():.2%}")
            print(f"最大月度回撤: {monthly_df['max_drawdown'].max():.2%}")

        return monthly_df

    def validate_key_assumptions(self, monthly_performance, trades_df):
        """驗證關鍵假設"""
        print("=== 驗證關鍵假設 ===")

        assumptions_results = {}

        # 假設1: 月度MDD < 5%
        max_mdd = monthly_performance['max_drawdown'].max()
        assumptions_results['mdd_assumption'] = {
            'assumption': '月度MDD < 5%',
            'actual': max_mdd,
            'passed': max_mdd < 0.05,
            'result': '.2%' if max_mdd < 0.05 else '.2%'
        }

        # 假設2: 配對交易有正勝率
        if len(trades_df) > 0:
            win_rate = len(trades_df[trades_df['pnl'] > 0]) / len(trades_df)
            assumptions_results['win_rate_assumption'] = {
                'assumption': '配對交易勝率 > 40%',
                'actual': win_rate,
                'passed': win_rate > 0.4,
                'result': '.1%' if win_rate > 0.4 else '.1%'
            }
        else:
            assumptions_results['win_rate_assumption'] = {
                'assumption': '配對交易勝率 > 40%',
                'actual': 0,
                'passed': False,
                'result': '無交易數據'
            }

        # 假設3: 平均月報酬為正
        avg_monthly_return = monthly_performance['monthly_return'].mean()
        assumptions_results['monthly_return_assumption'] = {
            'assumption': '平均月報酬 > 0%',
            'actual': avg_monthly_return,
            'passed': avg_monthly_return > 0,
            'result': '.2%' if avg_monthly_return > 0 else '.2%'
        }

        # 假設4: 季度正報酬率 > 75%
        quarterly_returns = []
        for i in range(0, len(monthly_performance), 3):
            quarter_data = monthly_performance.iloc[i:i+3]
            if len(quarter_data) >= 3:
                quarter_return = (quarter_data['end_capital'].iloc[-1] - quarter_data['start_capital'].iloc[0]) / quarter_data['start_capital'].iloc[0]
                quarterly_returns.append(quarter_return)

        if quarterly_returns:
            quarterly_win_rate = len([r for r in quarterly_returns if r > 0]) / len(quarterly_returns)
            assumptions_results['quarterly_assumption'] = {
                'assumption': '季度正報酬率 > 75%',
                'actual': quarterly_win_rate,
                'passed': quarterly_win_rate > 0.75,
                'result': '.1%' if quarterly_win_rate > 0.75 else '.1%'
            }
        else:
            assumptions_results['quarterly_assumption'] = {
                'assumption': '季度正報酬率 > 75%',
                'actual': 0,
                'passed': False,
                'result': '數據不足'
            }

        # 輸出驗證結果
        print("\n假設驗證結果:")
        for key, result in assumptions_results.items():
            status = "[通過]" if result['passed'] else "[未通過]"
            print(f"  {result['assumption']}: {status}")
            print(f"    實際值: {result['result']}")

        return assumptions_results

    def run_validation(self):
        """執行完整驗證"""
        print("=== 本金保護區間策略真實數據假設驗證 ===")
        print("=" * 60)

        # 1. 載入數據
        data = self.load_real_data()
        if not data or 'twii' not in data:
            print("數據載入失敗")
            return

        # 2. 計算Z分數信號
        signals_df = self.calculate_zscore_signals(data['twii'])

        # 3. 模擬真實交易
        daily_perf, trades_df = self.simulate_real_trading(data['twii'], signals_df)

        # 4. 計算月度表現
        monthly_perf = self.calculate_monthly_performance(daily_perf)

        # 5. 驗證關鍵假設
        assumptions_results = self.validate_key_assumptions(monthly_perf, trades_df)

        # 保存結果
        results = {
            'daily_performance': daily_perf,
            'monthly_performance': monthly_perf,
            'trades': trades_df,
            'signals': signals_df,
            'assumptions_validation': assumptions_results,
            'config': self.config
        }

        # 保存到文件
        self.save_validation_results(results)

        print("\n" + "=" * 60)
        print("驗證完成！")
        print("=" * 60)

        return results

    def save_validation_results(self, results):
        """保存驗證結果"""
        import json

        # 準備可序列化的結果
        serializable_results = {
            'config': results['config'],
            'summary': {
                'total_days': len(results['daily_performance']),
                'total_months': len(results['monthly_performance']),
                'total_signals': len(results['signals']),
                'total_trades': len(results['trades'])
            },
            'assumptions_validation': results['assumptions_validation']
        }

        # 保存JSON結果
        with open('data/strategy_validation_results.json', 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False, default=str)

        # 保存詳細數據
        results['monthly_performance'].to_csv('data/monthly_performance_real.csv', index=False)
        results['trades'].to_csv('data/trades_real.csv', index=False)
        results['signals'].to_csv('data/signals_real.csv', index=False)

        print("驗證結果已保存至 data/ 目錄")

def main():
    """主函數"""
    validator = RealDataStrategyValidator()
    results = validator.run_validation()

    if results:
        print("\n最終總結:")
        validation = results['assumptions_validation']

        passed_count = sum(1 for v in validation.values() if v['passed'])
        total_count = len(validation)

        print(f"假設驗證: {passed_count}/{total_count} 項通過")

        if passed_count >= 3:  # 至少3項通過
            print("策略基本假設成立，可以繼續優化")
        else:
            print("策略假設需要重大調整")

if __name__ == "__main__":
    main()
