# -*- coding: utf-8 -*-
"""
RORO 策略 vs 買進持有策略回測比較

比較 RORO 動態風險管理策略與月初買入月底賣出的買進持有策略績效。
實現每日檢查機制，分析不同市場條件下的表現差異。
"""

import sys
import os
import io
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import duckdb
from typing import Dict, List, Tuple, Optional

# 設置 UTF-8 輸出
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', line_buffering=True)

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('roro_backtest_comparison.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ROROBuyHoldComparison:
    """
    RORO 策略與買進持有策略比較分析
    """

    def __init__(self, start_date: str = '2020-01-01', end_date: str = '2024-12-01'):
        """
        初始化比較分析

        Args:
            start_date: 開始日期
            end_date: 結束日期
        """
        self.start_date = start_date
        self.end_date = end_date

        # 數據存儲
        self.price_data = None
        self.roro_signals = {}
        self.buy_hold_returns = {}
        self.roro_returns = {}
        self.comparison_results = {}

        logger.info(f"初始化 RORO vs 買進持有比較分析 ({start_date} 到 {end_date})")

    def load_price_data(self) -> pd.DataFrame:
        """
        載入價格數據

        Returns:
            價格數據 DataFrame
        """
        try:
            logger.info("載入台指期價格數據...")

            # 使用現有的數據載入方式
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

            data = con.execute(query, [self.start_date, self.end_date]).fetchdf()
            con.close()

            # 設置日期索引
            data['date'] = pd.to_datetime(data['date'])
            data = data.set_index('date')
            data = data.sort_index()

            self.price_data = data
            logger.info(f"成功載入 {len(data)} 筆價格數據")

            return data

        except Exception as e:
            logger.error(f"載入價格數據失敗: {str(e)}")
            raise

    def generate_roro_signals(self) -> Dict[str, pd.Series]:
        """
        生成簡化的 RORO 信號 (模擬版本)

        基於簡單的技術指標生成買賣信號，模擬 RORO 策略的行為

        Returns:
            RORO 信號字典
        """
        try:
            logger.info("生成簡化的 RORO 信號...")

            if self.price_data is None:
                raise ValueError("請先載入價格數據")

            close_prices = self.price_data['Close']

            # 簡單的 RORO 信號生成邏輯
            # 基於移動平均線和 RSI 生成風險信號

            # 計算技術指標
            ma_short = close_prices.rolling(20).mean()
            ma_long = close_prices.rolling(50).mean()

            # 簡單的趨勢指標
            trend_score = (ma_short - ma_long) / ma_long

            # 波動率指標
            volatility = close_prices.rolling(20).std() / close_prices.rolling(20).mean()

            # 綜合風險評分 (簡化版本)
            risk_score = trend_score - volatility * 2  # 趨勢減去波動

            # 生成 RORO 狀態
            roro_state = pd.Series(0, index=close_prices.index, name='roro_state')

            # 強風險開啟: 趨勢向上且波動不高
            bullish_condition = (trend_score > 0.02) & (volatility < 0.03)
            roro_state[bullish_condition] = 2

            # 弱風險開啟: 趨勢向上但波動中等
            weak_bullish_condition = (trend_score > 0.01) & (trend_score <= 0.02) & (volatility < 0.05)
            roro_state[weak_bullish_condition] = 1

            # 弱風險關閉: 趨勢向下但波動不高
            weak_bearish_condition = (trend_score < -0.01) & (trend_score >= -0.02) & (volatility < 0.05)
            roro_state[weak_bearish_condition] = -1

            # 強風險關閉: 趨勢向下且波動高
            bearish_condition = (trend_score < -0.02) | (volatility > 0.05)
            roro_state[bearish_condition] = -2

            # 生成投資決策 (將狀態轉換為決策)
            investment_decision = roro_state.apply(lambda x: x / 2.0)  # 將狀態轉換為 -1 到 1 的決策

            signals = {
                'roro_state': roro_state,
                'investment_decision': investment_decision,
                'trend_score': trend_score,
                'volatility': volatility,
                'risk_score': risk_score
            }

            self.roro_signals = signals
            logger.info(f"成功生成 {len(signals)} 項簡化 RORO 信號")

            return signals

        except Exception as e:
            logger.error(f"生成 RORO 信號失敗: {str(e)}")
            return {}

    def calculate_buy_hold_returns(self) -> pd.Series:
        """
        計算買進持有策略收益 (月初買入月底賣出)

        Returns:
            買進持有策略的月度收益序列
        """
        try:
            logger.info("計算買進持有策略收益...")

            if self.price_data is None:
                raise ValueError("請先載入價格數據")

            # 按月重採樣，獲取每月第一天和最後一天的價格
            monthly_data = self.price_data.resample('M')['Close'].agg(['first', 'last'])

            # 計算月度收益
            monthly_returns = (monthly_data['last'] - monthly_data['first']) / monthly_data['first']

            # 轉換為累計收益
            cumulative_returns = (1 + monthly_returns).cumprod() - 1

            self.buy_hold_returns = {
                'monthly_returns': monthly_returns,
                'cumulative_returns': cumulative_returns,
                'total_return': cumulative_returns.iloc[-1] if len(cumulative_returns) > 0 else 0,
                'annualized_return': self._calculate_annualized_return(monthly_returns),
                'volatility': monthly_returns.std() * np.sqrt(12),
                'sharpe_ratio': self._calculate_sharpe_ratio(monthly_returns),
                'max_drawdown': self._calculate_max_drawdown(cumulative_returns)
            }

            logger.info("買進持有策略收益計算完成")
            return monthly_returns

        except Exception as e:
            logger.error(f"計算買進持有策略收益失敗: {str(e)}")
            raise

    def calculate_roro_strategy_returns(self) -> pd.Series:
        """
        計算 RORO 策略收益

        Returns:
            RORO 策略的日度收益序列
        """
        try:
            logger.info("計算 RORO 策略收益...")

            if not self.roro_signals or self.price_data is None:
                raise ValueError("請先生成 RORO 信號並載入價格數據")

            # 獲取投資決策和資產配置
            investment_decisions = self.roro_signals.get('investment_decision', pd.Series())
            asset_allocation = self._extract_asset_allocations(self.roro_signals)

            if investment_decisions.empty:
                logger.warning("無有效的投資決策數據")
                return pd.Series()

            # 計算每日收益
            price_returns = self.price_data['Close'].pct_change()

            # 簡單的收益計算：基於投資決策調整權重
            # 正決策 = 多頭，負決策 = 空頭，中性 = 零權重
            position_weights = investment_decisions.apply(self._decision_to_weight)

            # 對齊數據
            common_index = price_returns.index.intersection(position_weights.index)
            aligned_returns = price_returns.loc[common_index]
            aligned_weights = position_weights.loc[common_index]

            # 計算策略收益
            strategy_daily_returns = aligned_returns * aligned_weights

            # 按月匯總
            monthly_strategy_returns = strategy_daily_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)

            # 計算累計收益
            cumulative_strategy_returns = (1 + monthly_strategy_returns).cumprod() - 1

            self.roro_returns = {
                'daily_returns': strategy_daily_returns,
                'monthly_returns': monthly_strategy_returns,
                'cumulative_returns': cumulative_strategy_returns,
                'total_return': cumulative_strategy_returns.iloc[-1] if len(cumulative_strategy_returns) > 0 else 0,
                'annualized_return': self._calculate_annualized_return(monthly_strategy_returns),
                'volatility': monthly_strategy_returns.std() * np.sqrt(12),
                'sharpe_ratio': self._calculate_sharpe_ratio(monthly_strategy_returns),
                'max_drawdown': self._calculate_max_drawdown(cumulative_strategy_returns),
                'total_signals': len(investment_decisions),
                'avg_signal_per_month': len(investment_decisions) / max(1, len(monthly_strategy_returns))
            }

            logger.info("RORO 策略收益計算完成")
            return monthly_strategy_returns

        except Exception as e:
            logger.error(f"計算 RORO 策略收益失敗: {str(e)}")
            raise

    def _decision_to_weight(self, decision: float) -> float:
        """
        將投資決策轉換為持倉權重

        Args:
            decision: 投資決策值

        Returns:
            持倉權重 (-1 到 1)
        """
        # 簡單的線性映射
        if decision > 0.5:  # 強風險開啟
            return 1.0
        elif decision > 0:  # 弱風險開啟
            return 0.5
        elif decision > -0.5:  # 中性
            return 0.0
        elif decision > -1:  # 弱風險關閉
            return -0.5
        else:  # 強風險關閉
            return -1.0

    def _extract_asset_allocations(self, signals: Dict[str, pd.Series]) -> pd.DataFrame:
        """
        提取資產配置信息

        Args:
            signals: 信號字典

        Returns:
            資產配置 DataFrame
        """
        allocation_cols = [col for col in signals.keys() if col.startswith('allocation_')]
        if allocation_cols:
            return pd.DataFrame({col: signals[col] for col in allocation_cols})
        return pd.DataFrame()

    def _calculate_annualized_return(self, monthly_returns: pd.Series) -> float:
        """計算年化收益"""
        if monthly_returns.empty:
            return 0.0
        total_months = len(monthly_returns)
        if total_months == 0:
            return 0.0
        cumulative_return = (1 + monthly_returns).prod()
        return (cumulative_return ** (12 / total_months) - 1) if cumulative_return > 0 else -1

    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """計算夏普比率"""
        if returns.empty or returns.std() == 0:
            return 0.0
        excess_returns = returns - risk_free_rate/12  # 月度無風險利率
        return excess_returns.mean() / returns.std() * np.sqrt(12)

    def _calculate_max_drawdown(self, cumulative_returns: pd.Series) -> float:
        """計算最大回撤"""
        if cumulative_returns.empty:
            return 0.0
        peak = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - peak) / (1 + peak)
        return drawdown.min()

    def run_comparison_analysis(self) -> Dict[str, any]:
        """
        執行比較分析

        Returns:
            比較分析結果
        """
        try:
            logger.info("開始執行策略比較分析...")

            # 載入數據
            self.load_price_data()

            # 生成 RORO 信號
            self.generate_roro_signals()

            # 計算兩種策略的收益
            self.calculate_buy_hold_returns()
            self.calculate_roro_strategy_returns()

            # 生成比較分析
            self.comparison_results = self._generate_comparison_report()

            # 保存結果
            self._save_results()

            logger.info("策略比較分析完成")
            return self.comparison_results

        except Exception as e:
            logger.error(f"比較分析失敗: {str(e)}")
            raise

    def _generate_comparison_report(self) -> Dict[str, any]:
        """
        生成比較分析報告

        Returns:
            比較分析結果字典
        """
        try:
            bh = self.buy_hold_returns
            roro = self.roro_returns

            # 基本比較
            comparison = {
                'analysis_period': {
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'total_months': len(bh.get('monthly_returns', []))
                },

                'buy_hold_strategy': {
                    'total_return': bh.get('total_return', 0),
                    'annualized_return': bh.get('annualized_return', 0),
                    'volatility': bh.get('volatility', 0),
                    'sharpe_ratio': bh.get('sharpe_ratio', 0),
                    'max_drawdown': bh.get('max_drawdown', 0)
                },

                'roro_strategy': {
                    'total_return': roro.get('total_return', 0),
                    'annualized_return': roro.get('annualized_return', 0),
                    'volatility': roro.get('volatility', 0),
                    'sharpe_ratio': roro.get('sharpe_ratio', 0),
                    'max_drawdown': roro.get('max_drawdown', 0),
                    'total_signals': roro.get('total_signals', 0),
                    'avg_signal_per_month': roro.get('avg_signal_per_month', 0)
                },

                'performance_comparison': {
                    'return_difference': roro.get('total_return', 0) - bh.get('total_return', 0),
                    'annualized_return_difference': roro.get('annualized_return', 0) - bh.get('annualized_return', 0),
                    'volatility_difference': roro.get('volatility', 0) - bh.get('volatility', 0),
                    'sharpe_ratio_difference': roro.get('sharpe_ratio', 0) - bh.get('sharpe_ratio', 0),
                    'drawdown_improvement': bh.get('max_drawdown', 0) - roro.get('max_drawdown', 0),  # 正值表示改善
                    'outperformance_ratio': (roro.get('total_return', 0) / max(abs(bh.get('total_return', 0)), 0.01)) if bh.get('total_return', 0) != 0 else float('inf')
                },

                'market_conditions_analysis': self._analyze_market_conditions(),

                'monthly_performance': self._analyze_monthly_performance(),

                'risk_adjusted_metrics': self._calculate_risk_adjusted_metrics()
            }

            return comparison

        except Exception as e:
            logger.error(f"生成比較報告失敗: {str(e)}")
            return {}

    def _analyze_market_conditions(self) -> Dict[str, any]:
        """
        分析不同市場條件下的表現

        Returns:
            市場條件分析結果
        """
        try:
            if not self.price_data or self.roro_returns.get('monthly_returns') is None:
                return {}

            # 計算市場趨勢
            monthly_prices = self.price_data.resample('M')['Close'].last()
            monthly_returns = monthly_prices.pct_change()

            # 定義市場條件
            bullish_months = monthly_returns > 0.03  # 月漲幅 > 3%
            bearish_months = monthly_returns < -0.03  # 月跌幅 > 3%
            neutral_months = (monthly_returns >= -0.03) & (monthly_returns <= 0.03)

            conditions = {
                'bullish': {
                    'count': bullish_months.sum(),
                    'buy_hold_avg_return': monthly_returns[bullish_months].mean(),
                    'roro_avg_return': self.roro_returns['monthly_returns'][bullish_months].mean() if len(self.roro_returns['monthly_returns']) > 0 else 0
                },
                'bearish': {
                    'count': bearish_months.sum(),
                    'buy_hold_avg_return': monthly_returns[bearish_months].mean(),
                    'roro_avg_return': self.roro_returns['monthly_returns'][bearish_months].mean() if len(self.roro_returns['monthly_returns']) > 0 else 0
                },
                'neutral': {
                    'count': neutral_months.sum(),
                    'buy_hold_avg_return': monthly_returns[neutral_months].mean(),
                    'roro_avg_return': self.roro_returns['monthly_returns'][neutral_months].mean() if len(self.roro_returns['monthly_returns']) > 0 else 0
                }
            }

            return conditions

        except Exception as e:
            logger.error(f"市場條件分析失敗: {str(e)}")
            return {}

    def _analyze_monthly_performance(self) -> Dict[str, any]:
        """
        分析月度表現差異

        Returns:
            月度表現分析結果
        """
        try:
            bh_monthly = self.buy_hold_returns.get('monthly_returns', pd.Series())
            roro_monthly = self.roro_returns.get('monthly_returns', pd.Series())

            if bh_monthly.empty or roro_monthly.empty:
                return {}

            # 確保索引對齊
            common_index = bh_monthly.index.intersection(roro_monthly.index)
            bh_aligned = bh_monthly.loc[common_index]
            roro_aligned = roro_monthly.loc[common_index]

            # 計算差異
            return_diff = roro_aligned - bh_aligned

            return {
                'months_analyzed': len(common_index),
                'roro_better_months': (return_diff > 0).sum(),
                'buy_hold_better_months': (return_diff < 0).sum(),
                'equal_months': (return_diff == 0).sum(),
                'avg_monthly_outperformance': return_diff.mean(),
                'best_month_outperformance': return_diff.max(),
                'worst_month_outperformance': return_diff.min(),
                'outperformance_volatility': return_diff.std()
            }

        except Exception as e:
            logger.error(f"月度表現分析失敗: {str(e)}")
            return {}

    def _calculate_risk_adjusted_metrics(self) -> Dict[str, any]:
        """
        計算風險調整後的指標

        Returns:
            風險調整指標
        """
        try:
            bh = self.buy_hold_returns
            roro = self.roro_returns

            return {
                'sortino_ratio_bh': self._calculate_sortino_ratio(bh.get('monthly_returns', pd.Series())),
                'sortino_ratio_roro': self._calculate_sortino_ratio(roro.get('monthly_returns', pd.Series())),
                'calmar_ratio_bh': abs(bh.get('total_return', 0) / bh.get('max_drawdown', 1)),
                'calmar_ratio_roro': abs(roro.get('total_return', 0) / roro.get('max_drawdown', 1)),
                'information_ratio': self._calculate_information_ratio()
            }

        except Exception as e:
            logger.error(f"風險調整指標計算失敗: {str(e)}")
            return {}

    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """計算索提諾比率"""
        if returns.empty:
            return 0.0

        excess_returns = returns - risk_free_rate/12
        downside_returns = returns[returns < 0]

        if downside_returns.empty or downside_returns.std() == 0:
            return float('inf') if excess_returns.mean() > 0 else float('-inf')

        return excess_returns.mean() / downside_returns.std() * np.sqrt(12)

    def _calculate_information_ratio(self) -> float:
        """計算資訊比率"""
        try:
            bh_returns = self.buy_hold_returns.get('monthly_returns', pd.Series())
            roro_returns = self.roro_returns.get('monthly_returns', pd.Series())

            if bh_returns.empty or roro_returns.empty:
                return 0.0

            # 對齊數據
            common_index = bh_returns.index.intersection(roro_returns.index)
            bh_aligned = bh_returns.loc[common_index]
            roro_aligned = roro_returns.loc[common_index]

            # 計算超額收益
            excess_returns = roro_aligned - bh_aligned

            if excess_returns.std() == 0:
                return 0.0

            return excess_returns.mean() / excess_returns.std() * np.sqrt(12)

        except Exception:
            return 0.0

    def _save_results(self):
        """保存分析結果"""
        try:
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)

            # 保存比較結果為 JSON
            import json
            result_file = output_dir / f'roro_vs_buyhold_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(self.comparison_results, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"比較結果已保存到: {result_file}")

        except Exception as e:
            logger.error(f"保存結果失敗: {str(e)}")

    def create_simple_visualization(self):
        """創建簡單的可視化圖表"""
        try:
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)

            # 設置中文字體
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            # 累計收益比較圖
            fig, ax = plt.subplots(figsize=(12, 6))

            if 'cumulative_returns' in self.buy_hold_returns:
                bh_cum = self.buy_hold_returns['cumulative_returns']
                ax.plot(bh_cum.index, bh_cum.values * 100, label='買進持有策略', linewidth=2, color='blue')

            if 'cumulative_returns' in self.roro_returns:
                roro_cum = self.roro_returns['cumulative_returns']
                ax.plot(roro_cum.index, roro_cum.values * 100, label='RORO 動態策略', linewidth=2, color='red')

            ax.set_title('RORO 策略 vs 買進持有策略 - 累計收益比較', fontsize=14)
            ax.set_ylabel('累計收益 (%)', fontsize=12)
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)

            plt.xticks(rotation=45)
            plt.tight_layout()

            plot_file = output_dir / f'roro_vs_buyhold_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.savefig(plot_file, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(f"比較圖已保存: {plot_file}")
            return str(plot_file)

        except Exception as e:
            logger.error(f"創建可視化失敗: {str(e)}")
            return None

    def print_comparison_report(self):
        """打印比較報告"""
        try:
            if not self.comparison_results:
                print("無比較結果可顯示")
                return

            comp = self.comparison_results

            print("\n" + "="*80)
            print("🎯 RORO 策略 vs 買進持有策略 - 比較分析報告")
            print("="*80)

            # 分析期間
            period = comp.get('analysis_period', {})
            print(f"\n📅 分析期間: {period.get('start_date')} 到 {period.get('end_date')}")
            print(f"📊 總月份數: {period.get('total_months')}")

            # 買進持有策略績效
            bh = comp.get('buy_hold_strategy', {})
            print(f"\n🏠 買進持有策略 (月初買入月底賣出):")
            print(f"  總收益: {bh.get('total_return', 0):.2%}")
            print(f"  年化收益: {bh.get('annualized_return', 0):.2%}")
            print(f"  波動率: {bh.get('volatility', 0):.2%}")
            print(f"  夏普比率: {bh.get('sharpe_ratio', 0):.3f}")
            print(f"  最大回撤: {bh.get('max_drawdown', 0):.2%}")

            # RORO 策略績效
            roro = comp.get('roro_strategy', {})
            print(f"\n🚀 RORO 動態策略:")
            print(f"  總收益: {roro.get('total_return', 0):.2%}")
            print(f"  年化收益: {roro.get('annualized_return', 0):.2%}")
            print(f"  波動率: {roro.get('volatility', 0):.2%}")
            print(f"  夏普比率: {roro.get('sharpe_ratio', 0):.3f}")
            print(f"  最大回撤: {roro.get('max_drawdown', 0):.2%}")
            print(f"  總信號數: {roro.get('total_signals', 0)}")
            print(f"  月均信號數: {roro.get('avg_signal_per_month', 0):.1f}")

            # 績效比較
            perf_comp = comp.get('performance_comparison', {})
            print(f"\n⚖️  績效比較:")
            print(f"  總收益差異: {perf_comp.get('return_difference', 0):.2%}")
            print(f"  年化收益差異: {perf_comp.get('annualized_return_difference', 0):.2%}")
            print(f"  波動率差異: {perf_comp.get('volatility_difference', 0):.2%}")
            print(f"  夏普比率差異: {perf_comp.get('sharpe_ratio_difference', 0):.3f}")
            print(f"  回撤改善: {perf_comp.get('drawdown_improvement', 0):.2%}")
            print(f"  相對表現倍數: {perf_comp.get('outperformance_ratio', 0):.2f}x")

            # 月度表現分析
            monthly = comp.get('monthly_performance', {})
            if monthly:
                print(f"\n📈 月度表現分析:")
                print(f"  分析月份數: {monthly.get('months_analyzed', 0)}")
                print(f"  RORO 較好月份: {monthly.get('roro_better_months', 0)}")
                print(f"  買進持有較好月份: {monthly.get('buy_hold_better_months', 0)}")
                print(f"  平均月度超額收益: {monthly.get('avg_monthly_outperformance', 0):.2%}")
                print(f"  最佳月份超額收益: {monthly.get('best_month_outperformance', 0):.2%}")
                print(f"  最差月份超額收益: {monthly.get('worst_month_outperformance', 0):.2%}")

            # 風險調整指標
            risk_adj = comp.get('risk_adjusted_metrics', {})
            if risk_adj:
                print(f"\n🎲 風險調整指標:")
                print(f"  索提諾比率 - 買進持有: {risk_adj.get('sortino_ratio_bh', 0):.3f}")
                print(f"  索提諾比率 - RORO: {risk_adj.get('sortino_ratio_roro', 0):.3f}")
                print(f"  卡爾瑪比率 - 買進持有: {risk_adj.get('calmar_ratio_bh', 0):.3f}")
                print(f"  卡爾瑪比率 - RORO: {risk_adj.get('calmar_ratio_roro', 0):.3f}")
                print(f"  資訊比率: {risk_adj.get('information_ratio', 0):.3f}")

            print("\n" + "="*80)

        except Exception as e:
            print(f"打印比較報告失敗: {str(e)}")


def main():
    """主函數"""
    try:
        # 初始化比較分析
        comparison = ROROBuyHoldComparison(
            start_date='2020-01-01',
            end_date='2024-12-01'
        )

        # 執行比較分析
        results = comparison.run_comparison_analysis()

        # 打印報告
        comparison.print_comparison_report()

        # 創建簡單的可視化
        plot_file = comparison.create_simple_visualization()
        if plot_file:
            print(f"📊 比較圖表已保存: {plot_file}")

        print("✅ RORO vs 買進持有策略比較分析完成！")
        print("📊 詳細結果已保存到 output/ 目錄")

    except Exception as e:
        logger.error(f"分析執行失敗: {str(e)}")
        raise


if __name__ == "__main__":
    main()
