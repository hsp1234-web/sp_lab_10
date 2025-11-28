# -*- coding: utf-8 -*-
"""
優化版 RORO 動態風險管理策略

核心改進：
1. 熊市保護機制 - 寧可錯過機會，不要虧大錢
2. 止損止盈機制 - 單筆虧損控制在10%以內
3. 降低交易頻率 - 從每日改為每周決策
4. 市場狀態識別 - 區分牛熊震盪行情
5. 動態倉位調整 - 根據市場狀態靈活調整
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import duckdb
from typing import Dict, List, Tuple, Optional

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OptimizedROROStrategy:
    """
    優化版 RORO 動態風險管理策略

    核心原則：熊市保護第一，風險控制優先
    """

    def __init__(self):
        """初始化優化策略"""
        # 風險控制參數
        self.max_loss_per_trade = 0.10  # 單筆最大虧損10%
        self.max_holding_days = 60      # 最大持有天數
        self.min_holding_days = 5       # 最小持有天數
        self.stop_loss_buffer = 0.05    # 止損緩衝區

        # 倉位管理
        self.max_position_size = 1.0    # 最大倉位100%
        self.min_position_size = -0.5   # 最小倉位-50% (空頭保護)

        # 信號參數
        self.signal_confirmation_days = 3  # 信號確認天數
        self.market_trend_window = 20      # 市場趨勢窗口

        # 市場狀態閾值
        self.market_state_thresholds = {
            'strong_bull': 0.05,     # 月漲幅 > 5%
            'moderate_bull': 0.02,   # 月漲幅 > 2%
            'neutral': -0.02,        # -2% < 月漲幅 < 2%
            'moderate_bear': -0.05,  # 月跌幅 > 5%
            'strong_bear': -0.08,    # 月跌幅 > 8%
        }

        # 策略狀態
        self.current_position = 0.0
        self.entry_price = None
        self.entry_date = None
        self.last_signal_date = None

        logger.info("優化版 RORO 策略初始化完成")

    def load_market_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        載入市場數據

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            市場數據 DataFrame
        """
        try:
            logger.info(f"載入市場數據: {start_date} 到 {end_date}")

            con = duckdb.connect('data/taifex.db')
            query = """
            SELECT
                Date as original_date,
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

            data = con.execute(query, [start_date, end_date]).fetchdf()
            con.close()

            # 設置日期索引
            data['date'] = pd.to_datetime(data['date'])
            data = data.set_index('date').sort_index()

            logger.info(f"成功載入 {len(data)} 筆市場數據")
            return data

        except Exception as e:
            logger.error(f"載入市場數據失敗: {str(e)}")
            raise

    def identify_market_state(self, data: pd.DataFrame, current_date: pd.Timestamp) -> str:
        """
        識別市場狀態

        Args:
            data: 市場數據
            current_date: 當前日期

        Returns:
            市場狀態 ('strong_bull', 'moderate_bull', 'neutral', 'moderate_bear', 'strong_bear')
        """
        try:
            # 獲取最近一個月的數據
            end_date = current_date
            start_date = end_date - pd.DateOffset(months=1)

            monthly_data = data.loc[start_date:end_date]

            if len(monthly_data) < 5:  # 至少需要5個交易日
                return 'neutral'

            # 計算月度收益
            monthly_return = (monthly_data['Close'].iloc[-1] - monthly_data['Close'].iloc[0]) / monthly_data['Close'].iloc[0]

            # 根據收益識別市場狀態
            if monthly_return >= self.market_state_thresholds['strong_bull']:
                return 'strong_bull'
            elif monthly_return >= self.market_state_thresholds['moderate_bull']:
                return 'moderate_bull'
            elif monthly_return >= self.market_state_thresholds['neutral']:
                return 'neutral'
            elif monthly_return >= self.market_state_thresholds['moderate_bear']:
                return 'moderate_bear'
            else:
                return 'strong_bear'

        except Exception as e:
            logger.error(f"識別市場狀態失敗: {str(e)}")
            return 'neutral'

    def calculate_technical_signals(self, data: pd.DataFrame, current_date: pd.Timestamp) -> Dict[str, float]:
        """
        計算技術信號

        Args:
            data: 市場數據
            current_date: 當前日期

        Returns:
            技術信號字典
        """
        try:
            # 獲取最近數據
            recent_data = data.loc[:current_date].tail(50)  # 最近50個交易日

            if len(recent_data) < 20:
                return {'trend': 0, 'momentum': 0, 'volatility': 0.5}

            close_prices = recent_data['Close']

            # 趨勢指標 (短期均線 vs 長期均線)
            ma_short = close_prices.rolling(10).mean().iloc[-1]
            ma_long = close_prices.rolling(30).mean().iloc[-1]
            trend = (ma_short - ma_long) / ma_long if ma_long != 0 else 0

            # 動能指標 (最近5日累計收益)
            momentum = (close_prices.iloc[-1] - close_prices.iloc[-5]) / close_prices.iloc[-5] if len(close_prices) >= 5 else 0

            # 波動率指標
            volatility = close_prices.pct_change().rolling(20).std().iloc[-1]

            return {
                'trend': trend,
                'momentum': momentum,
                'volatility': volatility,
                'current_price': close_prices.iloc[-1]
            }

        except Exception as e:
            logger.error(f"計算技術信號失敗: {str(e)}")
            return {'trend': 0, 'momentum': 0, 'volatility': 0.5, 'current_price': data['Close'].iloc[-1]}

    def should_exit_position(self, current_price: float, entry_price: float,
                           entry_date: pd.Timestamp, current_date: pd.Timestamp) -> Tuple[bool, str]:
        """
        判斷是否應該出場

        Args:
            current_price: 當前價格
            entry_price: 進場價格
            entry_date: 進場日期
            current_date: 當前日期

        Returns:
            (是否出場, 出場原因)
        """
        try:
            # 計算持有天數
            holding_days = (current_date - entry_date).days

            # 計算損益百分比
            pnl_pct = (current_price - entry_price) / entry_price

            # 止損條件
            if pnl_pct <= -self.max_loss_per_trade:
                return True, f"止損: 虧損{pnl_pct:.1%}"

            # 止盈條件 (獲利10%就落袋為安)
            if pnl_pct >= 0.10:
                return True, f"止盈: 獲利{pnl_pct:.1%}"

            # 時間止損
            if holding_days >= self.max_holding_days:
                return True, f"時間止損: 持有{holding_days}天"

            # 最小持有期檢查 (避免過度頻繁交易)
            if holding_days < self.min_holding_days:
                return False, "持有期太短"

            return False, "繼續持有"

        except Exception as e:
            logger.error(f"判斷出場條件失敗: {str(e)}")
            return False, "計算錯誤"

    def generate_trading_decision(self, market_state: str, signals: Dict[str, float]) -> Dict[str, any]:
        """
        生成交易決策

        Args:
            market_state: 市場狀態
            signals: 技術信號

        Returns:
            交易決策字典
        """
        try:
            trend = signals['trend']
            momentum = signals['momentum']
            volatility = signals['volatility']

            decision = {
                'action': 'HOLD',  # HOLD, BUY, SELL, EXIT
                'position_size': 0.0,
                'reason': '',
                'confidence': 0.5
            }

            # 根據市場狀態和信號生成決策
            if market_state == 'strong_bear':
                # 強熊市: 保護模式，最多空頭50%
                if trend < -0.02 and momentum < -0.03:
                    decision.update({
                        'action': 'SELL' if self.current_position > 0 else 'HOLD',
                        'position_size': -0.3,  # 30%空頭保護
                        'reason': '強熊市保護模式',
                        'confidence': 0.8
                    })

            elif market_state == 'moderate_bear':
                # 中等熊市: 減倉或空頭
                if trend < -0.01:
                    decision.update({
                        'action': 'REDUCE' if self.current_position > 0.5 else 'HOLD',
                        'position_size': 0.0,  # 現金持有
                        'reason': '中等熊市觀望',
                        'confidence': 0.7
                    })

            elif market_state == 'neutral':
                # 中性市: 小倉位操作
                if abs(trend) > 0.01 and volatility < 0.03:
                    if trend > 0 and momentum > 0:
                        decision.update({
                            'action': 'BUY',
                            'position_size': 0.4,  # 40%倉位
                            'reason': '中性市小多頭',
                            'confidence': 0.6
                        })
                    elif trend < 0 and momentum < 0:
                        decision.update({
                            'action': 'SELL',
                            'position_size': -0.2,  # 小空頭
                            'reason': '中性市小空頭',
                            'confidence': 0.6
                        })

            elif market_state == 'moderate_bull':
                # 中等牛市: 適度參與
                if trend > 0.02 and momentum > 0.01:
                    decision.update({
                        'action': 'BUY',
                        'position_size': 0.6,  # 60%倉位
                        'reason': '中等牛市參與',
                        'confidence': 0.7
                    })

            elif market_state == 'strong_bull':
                # 強牛市: 全力參與
                if trend > 0.03 and momentum > 0.02 and volatility < 0.04:
                    decision.update({
                        'action': 'BUY',
                        'position_size': 0.8,  # 80%倉位
                        'reason': '強牛市全力參與',
                        'confidence': 0.9
                    })

            return decision

        except Exception as e:
            logger.error(f"生成交易決策失敗: {str(e)}")
            return {
                'action': 'HOLD',
                'position_size': 0.0,
                'reason': '決策錯誤',
                'confidence': 0.0
            }

    def run_backtest(self, start_date: str, end_date: str) -> Dict[str, any]:
        """
        運行回測

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            回測結果
        """
        try:
            logger.info(f"開始優化 RORO 策略回測: {start_date} 到 {end_date}")

            # 載入數據
            data = self.load_market_data(start_date, end_date)

            # 初始化結果記錄
            trades = []
            daily_pnl = []
            position_history = []

            # 重置策略狀態
            self.current_position = 0.0
            self.entry_price = None
            self.entry_date = None
            self.last_signal_date = None

            # 逐日模擬交易
            for i, (current_date, row) in enumerate(data.iterrows()):
                current_price = row['Close']

                # 記錄每日倉位
                position_history.append({
                    'date': current_date,
                    'position': self.current_position,
                    'price': current_price
                })

                # 只有在有足夠數據時才生成信號 (每5日檢查一次)
                if i >= 30 and i % 5 == 0:  # 每5個交易日檢查一次
                    try:
                        # 識別市場狀態
                        market_state = self.identify_market_state(data, current_date)

                        # 計算技術信號
                        signals = self.calculate_technical_signals(data, current_date)

                        # 生成交易決策
                        decision = self.generate_trading_decision(market_state, signals)

                        # 檢查是否需要出場 (如果有持倉)
                        if self.current_position != 0 and self.entry_price is not None:
                            should_exit, exit_reason = self.should_exit_position(
                                current_price, self.entry_price, self.entry_date, current_date
                            )

                            if should_exit:
                                # 計算出場PnL
                                exit_pnl = (current_price - self.entry_price) / self.entry_price * abs(self.current_position)

                                trades.append({
                                    'entry_date': self.entry_date,
                                    'exit_date': current_date,
                                    'entry_price': self.entry_price,
                                    'exit_price': current_price,
                                    'position': self.current_position,
                                    'pnl': exit_pnl,
                                    'holding_days': (current_date - self.entry_date).days,
                                    'exit_reason': exit_reason,
                                    'market_state': market_state
                                })

                                # 重置持倉
                                self.current_position = 0.0
                                self.entry_price = None
                                self.entry_date = None

                        # 執行新決策 (如果沒有持倉或決策改變)
                        if decision['action'] in ['BUY', 'SELL'] and self.current_position == 0:
                            new_position = decision['position_size']

                            # 記錄進場
                            self.current_position = new_position
                            self.entry_price = current_price
                            self.entry_date = current_date
                            self.last_signal_date = current_date

                            trades.append({
                                'entry_date': current_date,
                                'entry_price': current_price,
                                'position': new_position,
                                'market_state': market_state,
                                'signal': decision['reason'],
                                'confidence': decision['confidence']
                            })

                    except Exception as e:
                        logger.warning(f"處理日期 {current_date} 失敗: {str(e)}")
                        continue

                # 計算每日PnL
                if self.current_position != 0 and self.entry_price is not None:
                    daily_return = (current_price - self.entry_price) / self.entry_price * self.current_position
                    daily_pnl.append({
                        'date': current_date,
                        'pnl': daily_return,
                        'position': self.current_position
                    })

            # 計算績效指標
            performance = self.calculate_performance_metrics(trades, daily_pnl, data)

            results = {
                'trades': trades,
                'daily_pnl': daily_pnl,
                'position_history': position_history,
                'performance': performance,
                'summary': {
                    'total_trades': len([t for t in trades if 'exit_date' in t]),
                    'winning_trades': len([t for t in trades if 'pnl' in t and t['pnl'] > 0]),
                    'losing_trades': len([t for t in trades if 'pnl' in t and t['pnl'] < 0]),
                    'total_return': performance.get('total_return', 0),
                    'max_drawdown': performance.get('max_drawdown', 0),
                    'sharpe_ratio': performance.get('sharpe_ratio', 0)
                }
            }

            logger.info("優化 RORO 策略回測完成")
            return results

        except Exception as e:
            logger.error(f"回測執行失敗: {str(e)}")
            raise

    def calculate_performance_metrics(self, trades: list, daily_pnl: list, market_data: pd.DataFrame) -> Dict[str, float]:
        """
        計算績效指標

        Args:
            trades: 交易記錄
            daily_pnl: 每日PnL
            market_data: 市場數據

        Returns:
            績效指標字典
        """
        try:
            if not trades:
                return {'total_return': 0, 'max_drawdown': 0, 'sharpe_ratio': 0}

            # 計算總收益
            completed_trades = [t for t in trades if 'pnl' in t]
            total_return = sum(t['pnl'] for t in completed_trades) if completed_trades else 0

            # 計算累計收益曲線
            if daily_pnl:
                pnl_df = pd.DataFrame(daily_pnl).set_index('date')
                cumulative_returns = (1 + pnl_df['pnl']).cumprod() - 1
                peak = cumulative_returns.expanding().max()
                drawdown = (cumulative_returns - peak) / (1 + peak)
                max_drawdown = drawdown.min() if not drawdown.empty else 0
            else:
                max_drawdown = 0

            # 計算夏普比率
            if daily_pnl:
                daily_returns = pd.DataFrame(daily_pnl).set_index('date')['pnl']
                if len(daily_returns) > 1:
                    excess_returns = daily_returns - 0.02/252  # 假設無風險利率2%
                    sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0
                else:
                    sharpe_ratio = 0
            else:
                sharpe_ratio = 0

            # 計算勝率
            winning_trades = len([t for t in completed_trades if t['pnl'] > 0])
            total_trades = len(completed_trades)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0

            # 計算平均獲利/虧損
            winning_pnl = [t['pnl'] for t in completed_trades if t['pnl'] > 0]
            losing_pnl = [t['pnl'] for t in completed_trades if t['pnl'] < 0]

            avg_win = np.mean(winning_pnl) if winning_pnl else 0
            avg_loss = np.mean(losing_pnl) if losing_pnl else 0

            return {
                'total_return': total_return,
                'annualized_return': total_return * 12 / len(market_data.resample('M').last()) if len(market_data) > 0 else 0,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': abs(sum(winning_pnl) / sum(losing_pnl)) if losing_pnl and sum(losing_pnl) != 0 else float('inf'),
                'total_trades': total_trades
            }

        except Exception as e:
            logger.error(f"計算績效指標失敗: {str(e)}")
            return {'total_return': 0, 'max_drawdown': 0, 'sharpe_ratio': 0}

    def print_results_summary(self, results: Dict[str, any]):
        """打印結果摘要"""
        try:
            perf = results.get('performance', {})
            summary = results.get('summary', {})

            print("\n" + "="*80)
            print("🎯 優化版 RORO 策略回測結果")
            print("="*80)

            print("\n📊 整體績效:")
            print(".2f")
            print(".4f")
            print(".2f")
            print(".3f")

            print("\n📈 交易統計:")
            print(f"  總交易數: {summary.get('total_trades', 0)}")
            print(f"  勝率: {perf.get('win_rate', 0):.1%}")
            print(".2f")
            print(".2f")
            print(".2f")

            print("\n⚖️  風險指標:")
            print(".2f")
            print(".3f")
            print(".2f")

            print("\n" + "="*80)

        except Exception as e:
            print(f"打印結果摘要失敗: {str(e)}")


def main():
    """主函數"""
    try:
        print("優化版 RORO 策略回測")
        print("核心改進: 熊市保護 + 止損機制 + 降低頻率")

        # 初始化策略
        strategy = OptimizedROROStrategy()

        # 運行回測
        results = strategy.run_backtest('2020-01-01', '2024-12-01')

        # 打印結果
        strategy.print_results_summary(results)

        # 保存詳細結果
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)

        import json
        result_file = output_dir / f'optimized_roro_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        # 將不可序列化的對象轉換為可序列化格式
        serializable_results = {}
        for key, value in results.items():
            if key == 'performance':
                serializable_results[key] = value
            elif key == 'summary':
                serializable_results[key] = value
            elif key == 'trades':
                serializable_results[key] = value[:10]  # 只保存前10筆交易作為示例
            else:
                serializable_results[key] = f"{type(value)} object"

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2, default=str)

        print(f"✅ 詳細結果已保存: {result_file}")

    except Exception as e:
        logger.error(f"主程序執行失敗: {str(e)}")
        raise


if __name__ == "__main__":
    main()
