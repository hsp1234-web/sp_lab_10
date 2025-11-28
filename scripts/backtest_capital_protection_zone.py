# -*- coding: utf-8 -*-
"""
本金保護區間策略真實數據回測

使用真實歷史數據驗證策略表現
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class CapitalProtectionZoneBacktest:
    """本金保護區間策略回測"""

    def __init__(self):
        self.config = {
            # 風險控制參數
            'monthly_mdd_limit': 0.05,  # 月度最大回撤5%
            'quarterly_target_return': 0.03,  # 季度目標報酬3%
            'annual_target_return': 0.08,  # 年度目標報酬8%

            # 倉位分配
            'cash_allocation': 0.60,  # 現金占比60%
            'pair_trading_allocation': 0.30,  # 配對交易占比30%
            'options_hedge_allocation': 0.10,  # 選擇權保護占比10%

            # 配對交易參數
            'z_score_entry': 2.0,  # 進場Z分數閾值
            'z_score_exit': 0.5,   # 出場Z分數閾值
            'max_holding_days': 20,  # 最大持有天數

            # 選擇權參數
            'hedge_ratio': 0.05,  # 保護比例5%
            'option_strike_buffer': 0.02,  # 履約價緩衝
        }

        # 回測結果
        self.results = {}

    def load_market_data(self, start_date: str, end_date: str):
        """載入市場數據"""
        print(f"載入市場數據: {start_date} 到 {end_date}")

        try:
            # 載入台指期數據
            con = duckdb.connect('data/taifex.db')
            futures_query = """
            SELECT
                strptime(Date, '%Y/%m/%d') as date,
                Symbol,
                Open,
                High,
                Low,
                Close,
                Volume
            FROM futures_data
            WHERE Symbol = 'TX'
            AND strptime(Date, '%Y/%m/%d') >= strptime(?, '%Y-%m-%d')
            AND strptime(Date, '%Y/%m/%d') <= strptime(?, '%Y-%m-%d')
            AND Close IS NOT NULL AND Close > 1000 AND Close < 30000
            ORDER BY strptime(Date, '%Y/%m/%d')
            """

            tx_df = con.execute(futures_query, [start_date, end_date]).fetchdf()
            con.close()

            print(f"台指期數據載入完成: {len(tx_df)} 條記錄")

            return {'TX': tx_df}

        except Exception as e:
            print(f"數據載入失敗: {e}")
            return {}

    def load_pcr_data(self):
        """載入PCR數據"""
        try:
            pcr_file = Path('data/taifex_official/processed_pcr_20251028_20251127.csv')
            if pcr_file.exists():
                df = pd.read_csv(pcr_file)
                # 處理日期格式
                df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d')
                df = df.sort_values('date')
                print(f"PCR數據載入完成: {len(df)} 條記錄")
                return df
            else:
                print("PCR數據文件不存在")
                return pd.DataFrame()
        except Exception as e:
            print(f"PCR數據載入失敗: {e}")
            return pd.DataFrame()

    def calculate_monthly_buy_hold(self, tx_df: pd.DataFrame):
        """計算月度買進持有策略"""
        if tx_df.empty:
            return pd.DataFrame()

        # 按月分組計算每月報酬
        tx_df['month'] = tx_df['date'].dt.to_period('M')
        monthly_returns = []

        for month, group in tx_df.groupby('month'):
            if len(group) >= 2:  # 至少有2個交易日
                month_start = group['Close'].iloc[0]
                month_end = group['Close'].iloc[-1]
                monthly_return = (month_end - month_start) / month_start
                monthly_returns.append({
                    'month': str(month),
                    'start_price': month_start,
                    'end_price': month_end,
                    'monthly_return': monthly_return,
                    'days': len(group)
                })

        return pd.DataFrame(monthly_returns)

    def calculate_pair_trading_signals(self, tx_df: pd.DataFrame, window: int = 60):
        """計算配對交易信號（簡化版）"""
        if tx_df.empty:
            return pd.DataFrame()

        signals = []
        tx_prices = tx_df.set_index('date')['Close']

        # 計算移動平均和標準差
        rolling_mean = tx_prices.rolling(window=window).mean()
        rolling_std = tx_prices.rolling(window=window).std()

        # 計算Z分數
        z_scores = (tx_prices - rolling_mean) / rolling_std

        for i in range(window, len(z_scores)):
            current_z = z_scores.iloc[i]
            current_date = z_scores.index[i]

            # 進場條件
            if abs(current_z) > self.config['z_score_entry']:
                signal_type = 'long' if current_z < -self.config['z_score_entry'] else 'short'
                signals.append({
                    'date': current_date,
                    'signal_type': signal_type,
                    'z_score': current_z,
                    'price': tx_prices.iloc[i],
                    'expected_return': abs(current_z) * 0.02  # 簡化估計
                })

        return pd.DataFrame(signals)

    def simulate_strategy_performance(self, tx_df: pd.DataFrame, pair_signals: pd.DataFrame):
        """模擬策略表現"""
        # 初始化資金
        initial_capital = 1000000  # 100萬
        capital = initial_capital

        # 倉位狀態
        current_position = 0.0  # 當前倉位大小 (-1到1)
        entry_price = None
        entry_date = None

        # 月度追蹤
        monthly_records = []
        current_month = None
        monthly_start_capital = capital

        performance_records = []

        # 將數據按日期排序
        tx_df = tx_df.sort_values('date').reset_index(drop=True)

        for idx, row in tx_df.iterrows():
            current_date = row['date']
            current_price = row['Close']

            # 月度初始化
            month_key = current_date.strftime('%Y-%m')
            if current_month != month_key:
                if current_month is not None:
                    # 保存上月記錄
                    monthly_return = (capital - monthly_start_capital) / monthly_start_capital
                    monthly_records.append({
                        'month': current_month,
                        'start_capital': monthly_start_capital,
                        'end_capital': capital,
                        'monthly_return': monthly_return,
                        'max_drawdown': 0.0
                    })

                current_month = month_key
                monthly_start_capital = capital

            # 檢查是否有新信號
            current_signals = pair_signals[pair_signals['date'] == current_date]

            if not current_signals.empty:
                signal = current_signals.iloc[0]

                # 檢查是否可以開倉
                if current_position == 0.0:  # 沒有持倉
                    # 決定倉位大小 (簡化：固定30%倉位)
                    position_size = 0.3 if signal['signal_type'] == 'long' else -0.3
                    entry_price = current_price
                    entry_date = current_date

                    # 檢查月度風險限額
                    potential_loss = abs(position_size) * self.config['monthly_mdd_limit'] * 0.1
                    if potential_loss < (capital * self.config['monthly_mdd_limit']):
                        current_position = position_size
                        print(f"開倉: {current_date} {signal['signal_type']} 價格:{current_price:.0f} 倉位:{current_position}")

                elif current_position != 0.0:  # 有持倉，檢查是否平倉
                    # 檢查持有天數
                    if entry_date and (current_date - entry_date).days >= self.config['max_holding_days']:
                        # 強制平倉
                        pnl = (current_price - entry_price) * current_position * (capital / entry_price)
                        capital += pnl
                        current_position = 0.0
                        entry_price = None
                        entry_date = None
                        print(f"強制平倉: {current_date} 價格:{current_price:.0f} PnL:{pnl:.0f}")

                    # 檢查Z分數退出條件 (簡化：價格回歸)
                    elif abs(signal.get('z_score', 0)) < self.config['z_score_exit']:
                        pnl = (current_price - entry_price) * current_position * (capital / entry_price)
                        capital += pnl
                        current_position = 0.0
                        entry_price = None
                        entry_date = None
                        print(f"訊號平倉: {current_date} 價格:{current_price:.0f} PnL:{pnl:.0f}")

            # 記錄每日表現
            performance_records.append({
                'date': current_date,
                'capital': capital,
                'price': current_price,
                'position': current_position
            })

        # 保存最後一個月
        if current_month:
            monthly_return = (capital - monthly_start_capital) / monthly_start_capital
            monthly_records.append({
                'month': current_month,
                'start_capital': monthly_start_capital,
                'end_capital': capital,
                'monthly_return': monthly_return,
                'max_drawdown': 0.0
            })

        return pd.DataFrame(performance_records), pd.DataFrame(monthly_records)

    def run_backtest(self, start_date: str = '2020-01-01', end_date: str = '2024-12-01'):
        """執行完整回測"""
        print("開始本金保護區間策略回測...")
        print(f"回測期間: {start_date} 到 {end_date}")

        # 載入數據
        market_data = self.load_market_data(start_date, end_date)
        pcr_data = self.load_pcr_data()

        if not market_data or 'TX' not in market_data:
            print("市場數據載入失敗")
            return {}

        tx_df = market_data['TX']
        print(f"台指期數據範圍: {tx_df['date'].min()} 到 {tx_df['date'].max()}")

        # 計算基準策略
        buy_hold_monthly = self.calculate_monthly_buy_hold(tx_df)
        print(f"買進持有月度數據: {len(buy_hold_monthly)} 個月")

        # 計算配對交易信號
        pair_signals = self.calculate_pair_trading_signals(tx_df)
        print(f"配對交易信號: {len(pair_signals)} 個")

        # 模擬策略表現
        daily_performance, monthly_performance = self.simulate_strategy_performance(tx_df, pair_signals)

        # 計算統計指標
        stats = self.calculate_performance_stats(daily_performance, monthly_performance, buy_hold_monthly)

        # 保存結果
        self.results = {
            'daily_performance': daily_performance,
            'monthly_performance': monthly_performance,
            'buy_hold_monthly': buy_hold_monthly,
            'pair_signals': pair_signals,
            'statistics': stats,
            'config': self.config
        }

        return self.results

    def calculate_performance_stats(self, daily_perf: pd.DataFrame,
                                  monthly_perf: pd.DataFrame,
                                  buy_hold: pd.DataFrame):
        """計算績效統計指標"""
        stats = {}

        if not monthly_perf.empty:
            # 月度統計
            monthly_returns = monthly_perf['monthly_return'].dropna()
            stats['monthly'] = {
                'total_months': len(monthly_returns),
                'positive_months': (monthly_returns > 0).sum(),
                'positive_ratio': (monthly_returns > 0).mean(),
                'avg_monthly_return': monthly_returns.mean(),
                'monthly_volatility': monthly_returns.std(),
                'max_monthly_loss': monthly_returns.min(),
                'sharpe_ratio': monthly_returns.mean() / monthly_returns.std() if monthly_returns.std() > 0 else 0
            }

            # 年化統計
            annual_return = (1 + monthly_returns.mean()) ** 12 - 1
            annual_volatility = monthly_returns.std() * np.sqrt(12)
            stats['annual'] = {
                'annual_return': annual_return,
                'annual_volatility': annual_volatility,
                'sharpe_ratio': annual_return / annual_volatility if annual_volatility > 0 else 0
            }

        if not buy_hold.empty:
            # 買進持有比較
            bh_returns = buy_hold['monthly_return'].dropna()
            stats['benchmark'] = {
                'bh_avg_monthly_return': bh_returns.mean(),
                'bh_positive_ratio': (bh_returns > 0).mean(),
                'bh_max_loss': bh_returns.min(),
                'bh_annual_return': (1 + bh_returns.mean()) ** 12 - 1
            }

        return stats

    def generate_report(self, save_path: str = 'output/capital_protection_backtest_results.json'):
        """生成回測報告"""
        if not self.results:
            print("沒有回測結果")
            return

        import json

        # 將DataFrame轉換為可序列化格式
        report_data = {
            'config': self.results['config'],
            'statistics': self.results['statistics'],
            'summary': {
                'backtest_period': f"{self.results['daily_performance']['date'].min()} 到 {self.results['daily_performance']['date'].max()}",
                'total_days': len(self.results['daily_performance']),
                'total_months': len(self.results['monthly_performance']),
                'total_signals': len(self.results['pair_signals']),
                'monthly_positive_ratio': self.results['statistics'].get('monthly', {}).get('positive_ratio', 0),
                'annual_return': self.results['statistics'].get('annual', {}).get('annual_return', 0),
                'sharpe_ratio': self.results['statistics'].get('annual', {}).get('sharpe_ratio', 0)
            }
        }

        # 保存報告
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"回測報告已保存到: {save_path}")
        return report_data

    def create_visualizations(self, save_dir: str = 'output/capital_protection_charts/'):
        """創建視覺化圖表"""
        if not self.results:
            return

        os.makedirs(save_dir, exist_ok=True)

        # 月度報酬比較圖
        plt.figure(figsize=(15, 10))

        # 子圖1: 月度報酬比較
        plt.subplot(2, 2, 1)
        if not self.results['monthly_performance'].empty:
            monthly_data = self.results['monthly_performance'].copy()
            monthly_data['month'] = pd.to_datetime(monthly_data['month'] + '-01')
            plt.bar(monthly_data['month'], monthly_data['monthly_return'] * 100,
                   alpha=0.7, label='本金保護策略', color='blue')
        plt.title('月度報酬比較')
        plt.ylabel('月度報酬 (%)')
        plt.legend()
        plt.xticks(rotation=45)

        # 子圖2: 累計報酬曲線
        plt.subplot(2, 2, 2)
        if not self.results['daily_performance'].empty:
            daily_data = self.results['daily_performance'].copy()
            daily_data['cumulative_return'] = (daily_data['capital'] - daily_data['capital'].iloc[0]) / daily_data['capital'].iloc[0]
            plt.plot(daily_data['date'], daily_data['cumulative_return'] * 100, label='本金保護策略')
        plt.title('累計報酬曲線')
        plt.ylabel('累計報酬 (%)')
        plt.legend()

        # 子圖3: 每月正報酬分佈
        plt.subplot(2, 2, 3)
        if not self.results['monthly_performance'].empty:
            monthly_returns = self.results['monthly_performance']['monthly_return'] * 100
            plt.hist(monthly_returns, bins=20, alpha=0.7, color='green', edgecolor='black')
            plt.axvline(x=0, color='red', linestyle='--', alpha=0.7)
        plt.title('月度報酬分佈')
        plt.xlabel('月度報酬 (%)')
        plt.ylabel('頻率')

        # 子圖4: 關鍵指標
        plt.subplot(2, 2, 4)
        stats = self.results['statistics']
        if 'monthly' in stats:
            metrics = [
                ('正報酬月數比例', stats['monthly']['positive_ratio'] * 100),
                ('平均月報酬', stats['monthly']['avg_monthly_return'] * 100),
                ('月度波動率', stats['monthly']['monthly_volatility'] * 100),
                ('最大月虧損', stats['monthly']['max_monthly_loss'] * 100)
            ]
            plt.bar(range(len(metrics)), [m[1] for m in metrics])
            plt.xticks(range(len(metrics)), [m[0] for m in metrics], rotation=45)
        plt.title('關鍵績效指標')

        plt.tight_layout()
        plt.savefig(f'{save_dir}/capital_protection_backtest_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

        print(f"圖表已保存到: {save_dir}")

def main():
    """主函數"""
    print("=== 本金保護區間策略真實數據回測 ===")

    # 初始化回測
    backtest = CapitalProtectionZoneBacktest()

    # 執行回測
    results = backtest.run_backtest('2020-01-01', '2024-12-01')

    if results:
        # 生成報告
        report = backtest.generate_report()

        # 創建視覺化
        backtest.create_visualizations()

        # 輸出總結
        print("\n=== 回測結果總結 ===")
        if 'statistics' in results and 'monthly' in results['statistics']:
            monthly_stats = results['statistics']['monthly']
            annual_stats = results['statistics'].get('annual', {})

            print(f"總月份數: {monthly_stats['total_months']}")
            print(f"正報酬月份: {monthly_stats['positive_months']}")
            print(f"正報酬比例: {monthly_stats['positive_ratio']:.2%}")
            print(f"平均月報酬: {monthly_stats['avg_monthly_return']:.2%}")
            print(f"月度波動率: {monthly_stats['monthly_volatility']:.2%}")
            print(f"最大月虧損: {monthly_stats['max_monthly_loss']:.2%}")
            print(f"夏普比率: {monthly_stats['sharpe_ratio']:.2f}")
            print(f"年化報酬: {annual_stats.get('annual_return', 0):.2%}")
        else:
            print("沒有足夠的數據進行統計分析")
    else:
        print("回測失敗")

if __name__ == "__main__":
    main()
