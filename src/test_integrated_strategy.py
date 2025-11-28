"""
測試整合量化策略

使用2022-2023年真實台指期資料測試新策略表現
"""

import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys

# 添加專案根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrated_strategy import IntegratedStrategy, create_default_config


def setup_logging():
    """設定日誌"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('output/integrated_strategy_test.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def load_historical_data():
    """
    載入歷史資料
    """
    try:
        import duckdb

        # 載入台指期資料
        conn = duckdb.connect('data/taifex.db')

        query = """
        SELECT Date, Close, High, Low, Volume, OpenInterest
        FROM futures_data
        WHERE Symbol = 'TX' AND Date BETWEEN '2022-01-01' AND '2023-12-31'
        ORDER BY Date
        """

        df = conn.execute(query).fetchdf()
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')

        logger.info(f"載入歷史資料: {len(df)} 筆記錄")
        logger.info(f"資料期間: {df.index.min()} 到 {df.index.max()}")

        return df

    except Exception as e:
        logger.error(f"載入歷史資料失敗: {e}")
        raise


def create_backtest_engine():
    """
    創建回測引擎
    """
    class SimpleBacktester:
        def __init__(self, strategy, initial_capital=1000000):
            self.strategy = strategy
            self.initial_capital = initial_capital
            self.capital = initial_capital
            self.positions = []
            self.trades = []

        def run_backtest(self, df):
            """執行回測"""
            try:
                # 生成信號
                signals = self.strategy.generate_signals(df)

                # 模擬交易
                position = 0
                entry_price = 0
                entry_date = None

                for i in range(len(df)):
                    current_date = df.index[i]
                    current_price = df['Close'].iloc[i]
                    signal = signals[i]

                    # 進場
                    if signal != 0 and position == 0:
                        position = signal
                        entry_price = current_price
                        entry_date = current_date

                        # 計算口數 (簡化：固定1口)
                        position_size = 1

                        self.positions.append({
                            'entry_date': entry_date,
                            'entry_price': entry_price,
                            'position': position,
                            'size': position_size
                        })

                        logger.info(f"進場: {current_date}, 價格: {current_price}, 方向: {'多頭' if position > 0 else '空頭'}")

                    # 出場
                    elif signal != 0 and position != 0 and np.sign(signal) != np.sign(position):
                        # 計算PnL
                        exit_price = current_price
                        pnl = (exit_price - entry_price) * position * 1000  # 每點1000元

                        trade = {
                            'entry_date': entry_date,
                            'exit_date': current_date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'position': position,
                            'pnl': pnl,
                            'hold_days': (current_date - entry_date).days
                        }

                        self.trades.append(trade)

                        # 更新資金
                        self.capital += pnl

                        logger.info(f"出場: {current_date}, 價格: {exit_price}, PnL: {pnl:.0f}, 總資金: {self.capital:.0f}")

                        # 重置倉位
                        position = 0
                        entry_price = 0
                        entry_date = None

                return self._calculate_metrics()

            except Exception as e:
                logger.error(f"回測執行失敗: {e}")
                raise

        def _calculate_metrics(self):
            """計算績效指標"""
            if len(self.trades) == 0:
                return {}

            trades_df = pd.DataFrame(self.trades)

            # 基本指標
            total_trades = len(trades_df)
            winning_trades = len(trades_df[trades_df['pnl'] > 0])
            losing_trades = len(trades_df[trades_df['pnl'] < 0])

            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            total_pnl = trades_df['pnl'].sum()
            avg_trade_pnl = trades_df['pnl'].mean()
            avg_hold_days = trades_df['hold_days'].mean()

            # 報酬率指標
            total_return = total_pnl / self.initial_capital

            # 最大回撤 (簡化計算)
            cumulative_pnl = trades_df['pnl'].cumsum()
            max_drawdown = (cumulative_pnl - cumulative_pnl.expanding().max()).min()

            # Sharpe比率 (簡化：假設無風險利率為0)
            if len(trades_df) > 1:
                returns = trades_df['pnl'] / self.initial_capital
                sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0
            else:
                sharpe_ratio = 0

            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'total_return': total_return,
                'avg_trade_pnl': avg_trade_pnl,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'avg_hold_days': avg_hold_days,
                'final_capital': self.capital
            }

    return SimpleBacktester


def plot_results(df, signals, trades, metrics):
    """繪製結果圖表"""
    try:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))

        # 價格走勢與信號
        ax1.plot(df.index, df['Close'], label='收盤價', alpha=0.7)
        ax1.plot(df.index, df['MA20'], label='MA20', alpha=0.7)

        # 標記進場點
        long_signals = signals == 1
        short_signals = signals == -1

        if long_signals.any():
            ax1.scatter(df.index[long_signals], df['Close'][long_signals],
                       marker='^', color='green', label='多頭進場', s=100)
        if short_signals.any():
            ax1.scatter(df.index[short_signals], df['Close'][short_signals],
                       marker='v', color='red', label='空頭進場', s=100)

        ax1.set_title('台指期走勢與交易信號')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # PCR比率
        ax2.plot(df.index, df['pcr_ratio'], label='PCR比率', color='purple')
        ax2.axhline(y=1.2, color='green', linestyle='--', alpha=0.7, label='多頭閾值')
        ax2.axhline(y=0.8, color='red', linestyle='--', alpha=0.7, label='空頭閾值')
        ax2.set_title('選擇權PCR情緒指標')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 波動率
        ax3.plot(df.index, df['Volatility'], label='波動率(%)', color='orange')
        ax3.set_title('市場波動率')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()

        # 儲存圖表
        plt.savefig('output/integrated_strategy_backtest.png', dpi=300, bbox_inches='tight')
        plt.close()

        logger.info("回測圖表已儲存至: output/integrated_strategy_backtest.png")

    except Exception as e:
        logger.warning(f"繪製圖表失敗: {e}")


def save_results(metrics, trades):
    """儲存測試結果"""
    try:
        # 建立日誌目錄
        os.makedirs('docs/logs/2025-11', exist_ok=True)

        # 生成報告
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        report_file = f'docs/logs/2025-11/{timestamp}_integrated_strategy_test.md'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f'# 整合策略測試報告\n\n')
            f.write(f'**測試時間:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')

            f.write('## 策略配置\n\n')
            f.write('- **Chandelier Length:** 22\n')
            f.write('- **Chandelier Multiplier:** 3.0\n')
            f.write('- **單筆風險:** 0.5%\n')
            f.write('- **每日最大回撤:** 2%\n')
            f.write('- **每月最大回撤:** 5%\n')
            f.write('- **PCR多頭閾值:** 1.2\n')
            f.write('- **PCR空頭閾值:** 0.8\n\n')

            f.write('## 測試資料\n\n')
            f.write('- **資料期間:** 2022-01-01 到 2023-12-31\n')
            f.write('- **初始資金:** $1,000,000\n')
            f.write('- **交易成本:** 未計入\n\n')

            f.write('## 績效指標\n\n')
            f.write(f'- **總交易次數:** {metrics.get("total_trades", 0)}\n')
            f.write(f'- **勝率:** {metrics.get("win_rate", 0):.1%}\n')
            f.write(f'- **總盈虧:** ${metrics.get("total_pnl", 0):,.0f}\n')
            f.write(f'- **總報酬率:** {metrics.get("total_return", 0):.2%}\n')
            f.write(f'- **最大回撤:** {metrics.get("max_drawdown", 0):.2%}\n')
            f.write(f'- **平均交易盈虧:** ${metrics.get("avg_trade_pnl", 0):,.0f}\n')
            f.write(f'- **Sharpe比率:** {metrics.get("sharpe_ratio", 0):.2f}\n')
            f.write(f'- **平均持有天數:** {metrics.get("avg_hold_days", 0):.1f} 天\n')
            f.write(f'- **最終資金:** ${metrics.get("final_capital", 0):,.0f}\n\n')

            f.write('## 風控評估\n\n')
            max_dd = metrics.get("max_drawdown", 0)
            monthly_target = 0.05

            if max_dd <= monthly_target:
                f.write(f'✅ **風控達標**: 最大回撤 {max_dd:.1%} ≤ 目標 {monthly_target:.0%}\n\n')
            else:
                f.write(f'❌ **風控不達標**: 最大回撤 {max_dd:.1%} > 目標 {monthly_target:.0%}\n\n')

            f.write('## 交易明細\n\n')
            if trades:
                f.write('|進場日期|出場日期|進場價格|出場價格|方向|盈虧|持有天數|\n')
                f.write('|--------|--------|--------|--------|----|----|--------|\n')

                for trade in trades[-20:]:  # 只顯示最後20筆交易
                    direction = '多頭' if trade['position'] > 0 else '空頭'
                    f.write(f"|{trade['entry_date'].strftime('%Y-%m-%d')}|")
                    f.write(f"{trade['exit_date'].strftime('%Y-%m-%d')}|")
                    f.write(f"{trade['entry_price']:.0f}|")
                    f.write(f"{trade['exit_price']:.0f}|")
                    f.write(f"{direction}|")
                    f.write(f"${trade['pnl']:,.0f}|")
                    f.write(f"{trade['hold_days']}|\n")

            f.write('\n## 結論與建議\n\n')

            win_rate = metrics.get("win_rate", 0)
            total_return = metrics.get("total_return", 0)
            total_trades = metrics.get("total_trades", 0)

            if total_return > 0 and max_dd <= monthly_target:
                f.write('✅ **策略表現良好**: 實現正報酬且控制回撤在目標範圍內。\n\n')
            elif total_return > 0 and max_dd > monthly_target:
                f.write('⚠️ **策略需調整**: 雖有正報酬但回撤控制不足，需要優化風控機制。\n\n')
            else:
                f.write('❌ **策略需重大調整**: 報酬為負，需要重新檢視策略邏輯。\n\n')

            f.write('### 改進建議:\n\n')
            if total_trades < 10:
                f.write('- 交易頻率過低，考慮放寬進場條件\n')
            elif total_trades > 50:
                f.write('- 交易頻率過高，考慮收緊進場條件\n')

            if win_rate < 0.4:
                f.write('- 勝率偏低，考慮改善進場時機選擇\n')

            f.write('- 持續監控市場變化，動態調整策略參數\n')
            f.write('- 加入更多市場情緒指標，提升決策準確性\n')

        logger.info(f"測試報告已儲存至: {report_file}")

        # 同時儲存CSV格式的交易記錄
        if trades:
            trades_df = pd.DataFrame(trades)
            csv_file = 'output/integrated_strategy_trades.csv'
            trades_df.to_csv(csv_file, index=False, encoding='utf-8')
            logger.info(f"交易記錄已儲存至: {csv_file}")

    except Exception as e:
        logger.error(f"儲存結果失敗: {e}")


def main():
    """主測試函數"""
    global logger
    logger = setup_logging()

    try:
        logger.info("開始整合策略測試")

        # 載入資料
        logger.info("載入歷史資料...")
        df = load_historical_data()

        if len(df) == 0:
            logger.error("無可用資料，測試終止")
            return

        # 創建策略
        logger.info("初始化整合策略...")
        config = create_default_config()
        strategy = IntegratedStrategy(config, logger)

        # 載入並處理資料
        df = strategy.load_market_data('2022-01-01', '2023-12-31')
        df = strategy.calculate_technical_indicators(df)

        # 創建回測引擎
        logger.info("執行回測...")
        Backtester = create_backtest_engine()
        backtester = Backtester(strategy)

        # 執行回測
        metrics = backtester.run_backtest(df)

        # 輸出結果
        logger.info("=== 回測結果 ===")
        for key, value in metrics.items():
            if isinstance(value, float):
                if 'rate' in key or 'return' in key or 'drawdown' in key:
                    logger.info(f"{key}: {value:.2%}")
                elif 'ratio' in key:
                    logger.info(f"{key}: {value:.2f}")
                else:
                    logger.info(f"{key}: {value:,.0f}")
            else:
                logger.info(f"{key}: {value}")

        # 生成信號用於繪圖
        signals = strategy.generate_signals(df)

        # 繪製結果
        plot_results(df, signals, backtester.trades, metrics)

        # 儲存結果
        save_results(metrics, backtester.trades)

        logger.info("整合策略測試完成")

    except Exception as e:
        logger.error(f"測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
