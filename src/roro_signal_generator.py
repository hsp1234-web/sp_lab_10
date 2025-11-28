# -*- coding: utf-8 -*-
"""
RORO 信號生成主程式 (RORO Signal Generator Main Program)

此程式整合市場寬度指標、系統壓力指數和 RORO 狀態引擎，
提供完整的動態風險管理策略信號生成流程。

主要功能：
1. 整合所有指標計算
2. 生成 RORO 信號和投資決策
3. 提供資產配置建議
4. 生成分析報告和可視化
5. 回測和驗證框架
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import warnings

from .config_manager import ConfigManager
from .data_loader import DataLoader
from .market_indicators import MarketWidthIndicator
from .pressure_index import SystemPressureIndex
from .roro_engine import ROROEngine, ROROState, RORODecision

logger = logging.getLogger(__name__)

class ROROSignalGenerator:
    """
    RORO 信號生成器主類

    整合所有模塊，提供完整的 RORO 策略執行流程。
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化 RORO 信號生成器

        Args:
            config_path: 配置檔案路徑
        """
        # 初始化配置管理器
        self.config = ConfigManager(config_path)

        # 初始化數據載入器
        self.data_loader = DataLoader(self.config)

        # 初始化各模塊
        self.market_indicator = MarketWidthIndicator(self.config)
        self.pressure_index = SystemPressureIndex(config_manager=self.config)
        self.roro_engine = ROROEngine(self.config)

        # 輸出目錄
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

        # 分析結果存儲
        self.signals_data = {}
        self.backtest_results = {}

        logger.info("ROROSignalGenerator 初始化完成")

    def generate_signals(self, start_date: str, end_date: str,
                        save_results: bool = True) -> Dict[str, pd.Series]:
        """
        生成完整的 RORO 信號

        Args:
            start_date: 開始日期
            end_date: 結束日期
            save_results: 是否保存結果

        Returns:
            信號數據字典
        """
        try:
            logger.info(f"開始生成 RORO 信號: {start_date} 到 {end_date}")

            # 使用 RORO 引擎生成信號
            signals = self.roro_engine.generate_roro_signals(start_date, end_date)

            if signals:
                self.signals_data = signals

                if save_results:
                    self._save_signals_to_file(signals, start_date, end_date)

                logger.info(f"成功生成 {len(signals)} 項信號")
            else:
                logger.warning("未能生成任何信號")

            return signals

        except Exception as e:
            logger.error(f"信號生成失敗: {str(e)}")
            return {}

    def _save_signals_to_file(self, signals: Dict[str, pd.Series],
                            start_date: str, end_date: str):
        """
        保存信號數據到檔案

        Args:
            signals: 信號數據
            start_date: 開始日期
            end_date: 結束日期
        """
        try:
            # 創建輸出檔案名稱
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"roro_signals_{start_date}_{end_date}_{timestamp}.csv"

            # 合併所有信號到一個 DataFrame
            signals_df = pd.DataFrame(signals)

            # 保存到 CSV
            output_path = self.output_dir / filename
            signals_df.to_csv(output_path)

            logger.info(f"信號數據已保存到: {output_path}")

            # 同時保存為 JSON 格式的元數據
            metadata = {
                'generation_time': datetime.now().isoformat(),
                'date_range': {'start': start_date, 'end': end_date},
                'signal_count': len(signals),
                'signal_names': list(signals.keys()),
                'data_points': len(signals_df) if not signals_df.empty else 0
            }

            metadata_path = self.output_dir / f"roro_metadata_{timestamp}.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存信號數據失敗: {str(e)}")

    def run_backtest(self, signals: Dict[str, pd.Series],
                    benchmark_ticker: str = "^TWII") -> Dict[str, any]:
        """
        運行回測分析

        Args:
            signals: 信號數據
            benchmark_ticker: 基準指數代碼

        Returns:
            回測結果字典
        """
        try:
            logger.info("開始運行 RORO 策略回測")

            if not signals or 'investment_decision' not in signals:
                logger.error("無有效信號數據進行回測")
                return {}

            # 獲取基準數據
            end_date = signals['investment_decision'].index.max().strftime('%Y-%m-%d')
            start_date = signals['investment_decision'].index.min().strftime('%Y-%m-%d')

            benchmark_data = self.data_loader.load_yahoo_finance_data(
                benchmark_ticker, start_date, end_date
            )

            if benchmark_data.empty:
                logger.warning(f"無法獲取基準數據 {benchmark_ticker}")
                benchmark_returns = pd.Series()
            else:
                benchmark_returns = benchmark_data['Close'].pct_change()

            # 計算策略收益
            strategy_returns = self._calculate_strategy_returns(signals)

            # 計算績效指標
            performance_metrics = self._calculate_performance_metrics(
                strategy_returns, benchmark_returns
            )

            # 計算風險指標
            risk_metrics = self._calculate_risk_metrics(strategy_returns, benchmark_returns)

            # 整合結果
            backtest_results = {
                'performance': performance_metrics,
                'risk': risk_metrics,
                'strategy_returns': strategy_returns,
                'benchmark_returns': benchmark_returns,
                'signals': signals
            }

            self.backtest_results = backtest_results

            logger.info("回測完成")
            return backtest_results

        except Exception as e:
            logger.error(f"回測失敗: {str(e)}")
            return {}

    def _calculate_strategy_returns(self, signals: Dict[str, pd.Series]) -> pd.Series:
        """
        計算策略收益

        Args:
            signals: 信號數據

        Returns:
            策略收益序列
        """
        try:
            if 'investment_decision' not in signals:
                return pd.Series()

            decisions = signals['investment_decision']

            # 簡化的收益計算：決策值直接作為收益權重
            # 在實際應用中，這裡應該使用具體的資產價格數據
            strategy_returns = decisions * 0.001  # 簡化模型：決策值 * 每日預期收益

            return strategy_returns

        except Exception as e:
            logger.error(f"策略收益計算失敗: {str(e)}")
            return pd.Series()

    def _calculate_performance_metrics(self, strategy_returns: pd.Series,
                                     benchmark_returns: pd.Series) -> Dict[str, float]:
        """
        計算績效指標

        Args:
            strategy_returns: 策略收益
            benchmark_returns: 基準收益

        Returns:
            績效指標字典
        """
        try:
            metrics = {}

            if not strategy_returns.empty:
                # 年化收益
                annual_return = (1 + strategy_returns.mean()) ** 252 - 1
                metrics['annual_return'] = annual_return

                # 年化波動率
                annual_volatility = strategy_returns.std() * np.sqrt(252)
                metrics['annual_volatility'] = annual_volatility

                # Sharpe 比率 (假設無風險利率為 2%)
                risk_free_rate = 0.02
                sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
                metrics['sharpe_ratio'] = sharpe_ratio

                # 最大回撤
                cumulative = (1 + strategy_returns).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = drawdown.min()
                metrics['max_drawdown'] = max_drawdown

            # 相對於基準的指標
            if not benchmark_returns.empty and not strategy_returns.empty:
                # 基準年化收益
                benchmark_annual = (1 + benchmark_returns.mean()) ** 252 - 1
                metrics['benchmark_annual_return'] = benchmark_annual

                # 超額收益
                excess_return = annual_return - benchmark_annual
                metrics['excess_return'] = excess_return

                # 資訊比率
                tracking_error = (strategy_returns - benchmark_returns).std() * np.sqrt(252)
                information_ratio = excess_return / tracking_error if tracking_error > 0 else 0
                metrics['information_ratio'] = information_ratio

            return metrics

        except Exception as e:
            logger.error(f"績效指標計算失敗: {str(e)}")
            return {}

    def _calculate_risk_metrics(self, strategy_returns: pd.Series,
                              benchmark_returns: pd.Series) -> Dict[str, float]:
        """
        計算風險指標

        Args:
            strategy_returns: 策略收益
            benchmark_returns: 基準收益

        Returns:
            風險指標字典
        """
        try:
            risk_metrics = {}

            if not strategy_returns.empty:
                # VaR (95% 信心水平)
                var_95 = np.percentile(strategy_returns.dropna(), 5)
                risk_metrics['var_95'] = var_95

                # CVaR (條件VaR)
                cvar_95 = strategy_returns[strategy_returns <= var_95].mean()
                risk_metrics['cvar_95'] = cvar_95 if not np.isnan(cvar_95) else 0

                # 偏度
                skewness = strategy_returns.skew()
                risk_metrics['skewness'] = skewness

                # 峰度
                kurtosis = strategy_returns.kurtosis()
                risk_metrics['kurtosis'] = kurtosis

            # Beta (相對於基準)
            if not benchmark_returns.empty and not strategy_returns.empty:
                # 確保有共同的日期
                common_index = strategy_returns.index.intersection(benchmark_returns.index)
                if len(common_index) > 30:  # 至少需要30個數據點
                    strat_common = strategy_returns.loc[common_index]
                    bench_common = benchmark_returns.loc[common_index]

                    covariance = strat_common.cov(bench_common)
                    benchmark_variance = bench_common.var()

                    beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
                    risk_metrics['beta'] = beta

            return risk_metrics

        except Exception as e:
            logger.error(f"風險指標計算失敗: {str(e)}")
            return {}

    def generate_report(self, signals: Dict[str, pd.Series],
                       backtest_results: Dict[str, any],
                       output_format: str = 'html') -> str:
        """
        生成分析報告

        Args:
            signals: 信號數據
            backtest_results: 回測結果
            output_format: 輸出格式 ('html', 'markdown', 'json')

        Returns:
            報告檔案路徑
        """
        try:
            logger.info(f"生成 {output_format} 格式的分析報告")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"roro_analysis_report_{timestamp}.{output_format}"

            if output_format == 'html':
                report_path = self._generate_html_report(signals, backtest_results, filename)
            elif output_format == 'markdown':
                report_path = self._generate_markdown_report(signals, backtest_results, filename)
            elif output_format == 'json':
                report_path = self._generate_json_report(signals, backtest_results, filename)
            else:
                raise ValueError(f"不支持的輸出格式: {output_format}")

            logger.info(f"報告已生成: {report_path}")
            return str(report_path)

        except Exception as e:
            logger.error(f"報告生成失敗: {str(e)}")
            return ""

    def _generate_html_report(self, signals: Dict[str, pd.Series],
                            backtest_results: Dict[str, any],
                            filename: str) -> Path:
        """
        生成 HTML 報告

        Args:
            signals: 信號數據
            backtest_results: 回測結果
            filename: 檔案名稱

        Returns:
            報告檔案路徑
        """
        try:
            report_path = self.output_dir / filename

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>RORO 策略分析報告</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1, h2, h3 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .metric {{ font-weight: bold; }}
                    .positive {{ color: green; }}
                    .negative {{ color: red; }}
                </style>
            </head>
            <body>
                <h1>RORO 動態風險管理策略分析報告</h1>
                <p>生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

                <h2>策略概述</h2>
                <p>RORO (Risk-On/Risk-Off) 策略整合市場寬度指標和系統壓力指數，動態調整資產配置。</p>

                <h2>信號統計</h2>
                {self._generate_signals_summary_html(signals)}

                <h2>回測績效</h2>
                {self._generate_performance_summary_html(backtest_results)}

                <h2>風險指標</h2>
                {self._generate_risk_summary_html(backtest_results)}

                <h2>信號狀態分佈</h2>
                {self._generate_state_distribution_html(signals)}
            </body>
            </html>
            """

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return report_path

        except Exception as e:
            logger.error(f"HTML 報告生成失敗: {str(e)}")
            return Path()

    def _generate_signals_summary_html(self, signals: Dict[str, pd.Series]) -> str:
        """生成信號統計 HTML"""
        if not signals:
            return "<p>無信號數據</p>"

        summary = self.roro_engine.get_signal_summary(signals)

        html = "<table>"
        html += "<tr><th>指標</th><th>值</th></tr>"

        for key, value in summary.items():
            if isinstance(value, dict):
                html += f"<tr><td>{key}</td><td>{json.dumps(value, ensure_ascii=False)}</td></tr>"
            else:
                html += f"<tr><td>{key}</td><td>{value}</td></tr>"

        html += "</table>"
        return html

    def _generate_performance_summary_html(self, backtest_results: Dict[str, any]) -> str:
        """生成績效統計 HTML"""
        if 'performance' not in backtest_results:
            return "<p>無績效數據</p>"

        perf = backtest_results['performance']

        html = "<table>"
        html += "<tr><th>指標</th><th>策略</th><th>基準</th></tr>"

        for key, value in perf.items():
            if 'benchmark' in key:
                continue  # 基準數據在下一列顯示

            benchmark_key = f"benchmark_{key.replace('excess_', '')}"
            benchmark_value = perf.get(benchmark_key, 'N/A')

            value_class = 'positive' if isinstance(value, (int, float)) and value > 0 else 'negative'
            html += f"<tr><td>{key}</td><td class='{value_class}'>{value:.4f}</td><td>{benchmark_value}</td></tr>"

        html += "</table>"
        return html

    def _generate_risk_summary_html(self, backtest_results: Dict[str, any]) -> str:
        """生成風險統計 HTML"""
        if 'risk' not in backtest_results:
            return "<p>無風險數據</p>"

        risk = backtest_results['risk']

        html = "<table>"
        html += "<tr><th>風險指標</th><th>值</th></tr>"

        for key, value in risk.items():
            html += f"<tr><td>{key}</td><td>{value:.4f}</td></tr>"

        html += "</table>"
        return html

    def _generate_state_distribution_html(self, signals: Dict[str, pd.Series]) -> str:
        """生成狀態分佈 HTML"""
        if 'roro_state' not in signals:
            return "<p>無狀態數據</p>"

        state_counts = signals['roro_state'].value_counts().sort_index()
        state_names = {
            -2: "強風險關閉",
            -1: "弱風險關閉",
            0: "中性",
            1: "弱風險開啟",
            2: "強風險開啟"
        }

        html = "<table>"
        html += "<tr><th>狀態</th><th>出現次數</th><th>百分比</th></tr>"

        total = state_counts.sum()
        for state_value, count in state_counts.items():
            state_name = state_names.get(state_value, f"狀態{state_value}")
            percentage = (count / total * 100) if total > 0 else 0
            html += f"<tr><td>{state_name}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"

        html += "</table>"
        return html

    def _generate_markdown_report(self, signals: Dict[str, pd.Series],
                                backtest_results: Dict[str, any],
                                filename: str) -> Path:
        """生成 Markdown 報告"""
        try:
            report_path = self.output_dir / filename

            md_content = f"""# RORO 動態風險管理策略分析報告

生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 策略概述

RORO (Risk-On/Risk-Off) 策略整合市場寬度指標和系統壓力指數，動態調整資產配置。

## 信號統計

{self._generate_signals_summary_md(signals)}

## 回測績效

{self._generate_performance_summary_md(backtest_results)}

## 風險指標

{self._generate_risk_summary_md(backtest_results)}

## 信號狀態分佈

{self._generate_state_distribution_md(signals)}
"""

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            return report_path

        except Exception as e:
            logger.error(f"Markdown 報告生成失敗: {str(e)}")
            return Path()

    def _generate_signals_summary_md(self, signals: Dict[str, pd.Series]) -> str:
        """生成信號統計 Markdown"""
        if not signals:
            return "無信號數據"

        summary = self.roro_engine.get_signal_summary(signals)
        md = "| 指標 | 值 |\n|------|-----|\n"

        for key, value in summary.items():
            if isinstance(value, dict):
                md += f"| {key} | {json.dumps(value, ensure_ascii=False)} |\n"
            else:
                md += f"| {key} | {value} |\n"

        return md

    def _generate_performance_summary_md(self, backtest_results: Dict[str, any]) -> str:
        """生成績效統計 Markdown"""
        if 'performance' not in backtest_results:
            return "無績效數據"

        perf = backtest_results['performance']
        md = "| 指標 | 策略 | 基準 |\n|------|------|------|\n"

        for key, value in perf.items():
            if 'benchmark' in key:
                continue

            benchmark_key = f"benchmark_{key.replace('excess_', '')}"
            benchmark_value = perf.get(benchmark_key, 'N/A')
            md += f"| {key} | {value:.4f} | {benchmark_value} |\n"

        return md

    def _generate_risk_summary_md(self, backtest_results: Dict[str, any]) -> str:
        """生成風險統計 Markdown"""
        if 'risk' not in backtest_results:
            return "無風險數據"

        risk = backtest_results['risk']
        md = "| 風險指標 | 值 |\n|----------|-----|\n"

        for key, value in risk.items():
            md += f"| {key} | {value:.4f} |\n"

        return md

    def _generate_state_distribution_md(self, signals: Dict[str, pd.Series]) -> str:
        """生成狀態分佈 Markdown"""
        if 'roro_state' not in signals:
            return "無狀態數據"

        state_counts = signals['roro_state'].value_counts().sort_index()
        state_names = {
            -2: "強風險關閉",
            -1: "弱風險關閉",
            0: "中性",
            1: "弱風險開啟",
            2: "強風險開啟"
        }

        md = "| 狀態 | 出現次數 | 百分比 |\n|------|----------|--------|\n"

        total = state_counts.sum()
        for state_value, count in state_counts.items():
            state_name = state_names.get(state_value, f"狀態{state_value}")
            percentage = (count / total * 100) if total > 0 else 0
            md += f"| {state_name} | {count} | {percentage:.1f}% |\n"

        return md

    def _generate_json_report(self, signals: Dict[str, pd.Series],
                            backtest_results: Dict[str, any],
                            filename: str) -> Path:
        """生成 JSON 報告"""
        try:
            report_path = self.output_dir / filename

            # 轉換 Series 為可序列化的格式
            serializable_signals = {}
            for key, series in signals.items():
                if isinstance(series, pd.Series):
                    serializable_signals[key] = {
                        'index': series.index.strftime('%Y-%m-%d').tolist(),
                        'values': series.tolist()
                    }
                else:
                    serializable_signals[key] = series

            report_data = {
                'generation_time': datetime.now().isoformat(),
                'signals': serializable_signals,
                'backtest_results': backtest_results,
                'summary': self.roro_engine.get_signal_summary(signals) if signals else {}
            }

            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            return report_path

        except Exception as e:
            logger.error(f"JSON 報告生成失敗: {str(e)}")
            return Path()

    def create_visualizations(self, signals: Dict[str, pd.Series],
                            backtest_results: Dict[str, any]) -> List[str]:
        """
        創建可視化圖表

        Args:
            signals: 信號數據
            backtest_results: 回測結果

        Returns:
            生成的圖片檔案路徑列表
        """
        try:
            logger.info("開始創建可視化圖表")

            plot_files = []

            # 設置中文字體
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            # 1. RORO 狀態時間序列圖
            if 'roro_state' in signals:
                fig, ax = plt.subplots(figsize=(15, 8))
                state_names = {
                    -2: "強風險關閉", -1: "弱風險關閉", 0: "中性",
                    1: "弱風險開啟", 2: "強風險開啟"
                }

                states_numeric = signals['roro_state']
                states_named = states_numeric.map(state_names)

                # 繪製狀態變化
                colors = ['red', 'orange', 'yellow', 'lightgreen', 'green']
                for i, state_value in enumerate([-2, -1, 0, 1, 2]):
                    mask = states_numeric == state_value
                    if mask.any():
                        ax.fill_between(states_numeric.index, 0, 1, where=mask,
                                      color=colors[i], alpha=0.7, label=state_names[state_value])

                ax.set_title('RORO 狀態時間序列', fontsize=16)
                ax.set_ylabel('狀態', fontsize=12)
                ax.legend(loc='upper left')
                ax.grid(True, alpha=0.3)

                plt.xticks(rotation=45)
                plt.tight_layout()

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                plot_file = f"roro_state_timeline_{timestamp}.png"
                plot_path = self.output_dir / plot_file
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()

                plot_files.append(str(plot_path))
                logger.info(f"狀態時間序列圖已保存: {plot_path}")

            # 2. 市場寬度 vs 系統壓力散點圖
            if 'market_width_score' in signals and 'composite_pressure_index' in signals:
                fig, ax = plt.subplots(figsize=(12, 8))

                width_scores = signals['market_width_score']
                pressure_scores = signals['composite_pressure_index']

                # 散點圖
                scatter = ax.scatter(pressure_scores, width_scores,
                                   c=signals.get('roro_state', pd.Series()),
                                   cmap='RdYlGn', alpha=0.6, s=50)

                # 添加顏色條
                cbar = plt.colorbar(scatter, ax=ax)
                cbar.set_label('RORO 狀態')

                ax.set_title('市場寬度 vs 系統壓力', fontsize=16)
                ax.set_xlabel('系統壓力指數', fontsize=12)
                ax.set_ylabel('市場寬度評分', fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                ax.axvline(x=0, color='black', linestyle='--', alpha=0.5)

                # 添加象限標籤
                ax.text(0.1, 0.9, '寬度健康/壓力高', transform=ax.transAxes, fontsize=10)
                ax.text(0.1, 0.1, '寬度健康/壓力低', transform=ax.transAxes, fontsize=10)
                ax.text(0.9, 0.9, '寬度惡化/壓力高', transform=ax.transAxes, fontsize=10)
                ax.text(0.9, 0.1, '寬度惡化/壓力低', transform=ax.transAxes, fontsize=10)

                plt.tight_layout()

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                plot_file = f"width_vs_pressure_{timestamp}.png"
                plot_path = self.output_dir / plot_file
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()

                plot_files.append(str(plot_path))
                logger.info(f"寬度壓力散點圖已保存: {plot_path}")

            # 3. 資產配置變化圖
            allocation_cols = [col for col in signals.keys() if col.startswith('allocation_')]
            if allocation_cols:
                fig, ax = plt.subplots(figsize=(15, 8))

                for col in allocation_cols:
                    asset_name = col.replace('allocation_', '')
                    ax.plot(signals[col].index, signals[col].values * 100,
                           label=f'{asset_name} 配置', linewidth=2)

                ax.set_title('動態資產配置變化', fontsize=16)
                ax.set_ylabel('配置比例 (%)', fontsize=12)
                ax.legend(loc='upper left')
                ax.grid(True, alpha=0.3)

                plt.xticks(rotation=45)
                plt.tight_layout()

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                plot_file = f"asset_allocation_{timestamp}.png"
                plot_path = self.output_dir / plot_file
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()

                plot_files.append(str(plot_path))
                logger.info(f"資產配置圖已保存: {plot_path}")

            logger.info(f"成功創建 {len(plot_files)} 個可視化圖表")
            return plot_files

        except Exception as e:
            logger.error(f"可視化創建失敗: {str(e)}")
            return []


def main():
    """
    主函數 - 用於測試 RORO 信號生成器
    """
    # 配置日誌
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 測試 RORO 信號生成器
    try:
        generator = ROROSignalGenerator()

        # 測試期間
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"測試 RORO 信號生成: {start_date} 到 {end_date}")

        # 生成信號
        signals = generator.generate_signals(start_date, end_date)

        if signals:
            logger.info(f"成功生成 {len(signals)} 項信號")

            # 運行回測
            backtest_results = generator.run_backtest(signals)

            if backtest_results:
                logger.info("回測完成")

                # 生成報告
                report_path = generator.generate_report(signals, backtest_results, 'html')
                logger.info(f"HTML 報告已生成: {report_path}")

                # 創建可視化
                plot_files = generator.create_visualizations(signals, backtest_results)
                logger.info(f"生成 {len(plot_files)} 個圖表: {plot_files}")
            else:
                logger.warning("回測失敗")
        else:
            logger.warning("信號生成失敗")

    except Exception as e:
        logger.error(f"測試失敗: {str(e)}")


if __name__ == "__main__":
    main()



