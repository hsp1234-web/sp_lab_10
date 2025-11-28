# -*- coding: utf-8 -*-
"""
信號驗證模塊 (Signal Validation Module)

此模塊提供完整的信號品質驗證和測試框架，包括：
- 信號品質指標計算
- 預測能力驗證
- 統計顯著性測試
- 穩健性分析
- 參數敏感性測試
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import TimeSeriesSplit
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple, Union
import warnings

logger = logging.getLogger(__name__)

class SignalValidator:
    """
    信號驗證器類

    提供全面的信號品質評估和驗證方法。
    """

    def __init__(self):
        """初始化信號驗證器"""
        self.validation_results = {}

        # 驗證參數
        self.min_sample_size = 30  # 最小的樣本大小
        self.confidence_level = 0.95  # 信心水平
        self.significance_level = 0.05  # 顯著性水平

        logger.info("SignalValidator 初始化完成")

    def validate_signal_quality(self, signals: Dict[str, pd.Series],
                              future_returns: Optional[pd.Series] = None,
                              benchmark_returns: Optional[pd.Series] = None) -> Dict[str, any]:
        """
        驗證信號品質

        Args:
            signals: 信號數據字典
            future_returns: 未來收益數據 (用於預測能力測試)
            benchmark_returns: 基準收益數據

        Returns:
            驗證結果字典
        """
        try:
            logger.info("開始信號品質驗證")

            results = {}

            # 1. 基本統計驗證
            results['basic_stats'] = self._calculate_basic_signal_stats(signals)

            # 2. 信號穩定性驗證
            results['stability'] = self._assess_signal_stability(signals)

            # 3. 預測能力驗證 (如果有收益數據)
            if future_returns is not None:
                results['predictive_power'] = self._test_predictive_power(signals, future_returns)

            # 4. 相對於基準的表現
            if benchmark_returns is not None:
                results['benchmark_comparison'] = self._compare_with_benchmark(signals, benchmark_returns)

            # 5. 信號相關性分析
            results['correlation_analysis'] = self._analyze_signal_correlations(signals)

            # 6. 整體品質評分
            results['quality_score'] = self._calculate_overall_quality_score(results)

            self.validation_results = results

            logger.info("信號品質驗證完成")
            return results

        except Exception as e:
            logger.error(f"信號品質驗證失敗: {str(e)}")
            return {}

    def _calculate_basic_signal_stats(self, signals: Dict[str, pd.Series]) -> Dict[str, any]:
        """
        計算信號基本統計

        Args:
            signals: 信號數據

        Returns:
            基本統計字典
        """
        try:
            stats_results = {}

            for signal_name, signal_series in signals.items():
                if not isinstance(signal_series, pd.Series) or signal_series.empty:
                    continue

                series = signal_series.dropna()

                if len(series) < self.min_sample_size:
                    logger.warning(f"{signal_name} 樣本大小不足 ({len(series)} < {self.min_sample_size})")
                    continue

                stats_results[signal_name] = {
                    'count': len(series),
                    'mean': series.mean(),
                    'std': series.std(),
                    'min': series.min(),
                    'max': series.max(),
                    'skewness': series.skew(),
                    'kurtosis': series.kurtosis(),
                    'autocorr_1': series.autocorr(lag=1) if len(series) > 1 else 0,
                    'autocorr_5': series.autocorr(lag=5) if len(series) > 5 else 0,
                    'stationarity_pvalue': self._test_stationarity(series),
                    'normality_pvalue': stats.shapiro(series.values)[1] if len(series) >= 3 else 1.0
                }

            return stats_results

        except Exception as e:
            logger.error(f"基本統計計算失敗: {str(e)}")
            return {}

    def _test_stationarity(self, series: pd.Series) -> float:
        """
        測試序列的穩定性 (ADF 檢定)

        Args:
            series: 時間序列

        Returns:
            p值 (越小表示越不穩定)
        """
        try:
            from statsmodels.tsa.stattools import adfuller

            if len(series) < 10:
                return 1.0  # 樣本不足，返回不拒絕原假設

            result = adfuller(series.values, autolag='AIC')
            return result[1]  # p-value

        except ImportError:
            logger.warning("statsmodels 未安裝，跳過穩定性測試")
            return 1.0
        except Exception as e:
            logger.error(f"穩定性測試失敗: {str(e)}")
            return 1.0

    def _assess_signal_stability(self, signals: Dict[str, pd.Series]) -> Dict[str, any]:
        """
        評估信號穩定性

        Args:
            signals: 信號數據

        Returns:
            穩定性評估結果
        """
        try:
            stability_results = {}

            for signal_name, signal_series in signals.items():
                if not isinstance(signal_series, pd.Series) or len(signal_series) < 60:
                    continue

                # 計算滾動統計
                rolling_mean = signal_series.rolling(20).mean()
                rolling_std = signal_series.rolling(20).std()

                # 穩定性指標
                mean_stability = rolling_mean.std() / abs(rolling_mean.mean()) if rolling_mean.mean() != 0 else float('inf')
                volatility_stability = rolling_std.mean()

                # 信號變化頻率
                changes = (signal_series.diff().abs() > signal_series.std() * 0.1).sum()
                change_frequency = changes / len(signal_series)

                stability_results[signal_name] = {
                    'mean_stability_ratio': mean_stability,
                    'avg_volatility': volatility_stability,
                    'change_frequency': change_frequency,
                    'stability_score': 1 / (1 + mean_stability + change_frequency)  # 0-1 分數，越高越穩定
                }

            return stability_results

        except Exception as e:
            logger.error(f"信號穩定性評估失敗: {str(e)}")
            return {}

    def _test_predictive_power(self, signals: Dict[str, pd.Series],
                             future_returns: pd.Series) -> Dict[str, any]:
        """
        測試信號的預測能力

        Args:
            signals: 信號數據
            future_returns: 未來收益數據

        Returns:
            預測能力測試結果
        """
        try:
            predictive_results = {}

            # 對齊數據
            common_index = None
            aligned_signals = {}

            for signal_name, signal_series in signals.items():
                if not isinstance(signal_series, pd.Series):
                    continue

                # 將信號向後移一個期間來預測未來收益
                lagged_signal = signal_series.shift(1)  # 使用昨天的信號預測今天的收益

                # 對齊索引
                aligned_data = pd.DataFrame({
                    'signal': lagged_signal,
                    'returns': future_returns
                }).dropna()

                if len(aligned_data) < self.min_sample_size:
                    continue

                aligned_signals[signal_name] = aligned_data

                if common_index is None:
                    common_index = aligned_data.index

            if not aligned_signals:
                logger.warning("無足夠數據進行預測能力測試")
                return {}

            # 測試每個信號的預測能力
            for signal_name, data in aligned_signals.items():
                signal_values = data['signal']
                returns = data['returns']

                # 分位數分析
                signal_quartiles = pd.qcut(signal_values, q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])

                # 計算各分位數的平均收益
                quartile_returns = returns.groupby(signal_quartiles).mean()

                # 單調性測試
                monotonic_trend = self._test_monotonic_trend(quartile_returns)

                # 相關性分析
                correlation = signal_values.corr(returns)
                correlation_pvalue = self._calculate_correlation_pvalue(signal_values, returns)

                # 資訊係數 (IC)
                ic = correlation
                ic_significance = correlation_pvalue < self.significance_level

                # 勝率分析
                signal_direction = np.sign(signal_values)
                return_direction = np.sign(returns)
                directional_accuracy = (signal_direction == return_direction).mean()

                predictive_results[signal_name] = {
                    'correlation': correlation,
                    'correlation_pvalue': correlation_pvalue,
                    'information_coefficient': ic,
                    'ic_significance': ic_significance,
                    'directional_accuracy': directional_accuracy,
                    'quartile_returns': quartile_returns.to_dict(),
                    'monotonic_trend': monotonic_trend
                }

            return predictive_results

        except Exception as e:
            logger.error(f"預測能力測試失敗: {str(e)}")
            return {}

    def _test_monotonic_trend(self, quartile_returns: pd.Series) -> Dict[str, any]:
        """
        測試分位數收益的單調趨勢

        Args:
            quartile_returns: 分位數收益

        Returns:
            單調性測試結果
        """
        try:
            # 簡單的單調性檢查：檢查是否 Q4 > Q3 > Q2 > Q1
            values = quartile_returns.values
            is_monotonic_increasing = all(values[i] <= values[i+1] for i in range(len(values)-1))
            is_monotonic_decreasing = all(values[i] >= values[i+1] for i in range(len(values)-1))

            # 計算趨勢強度
            trend_strength = abs(values[-1] - values[0]) / abs(values).std() if abs(values).std() > 0 else 0

            return {
                'is_monotonic_increasing': is_monotonic_increasing,
                'is_monotonic_decreasing': is_monotonic_decreasing,
                'trend_strength': trend_strength,
                'trend_direction': 1 if is_monotonic_increasing else (-1 if is_monotonic_decreasing else 0)
            }

        except Exception as e:
            logger.error(f"單調性測試失敗: {str(e)}")
            return {'error': str(e)}

    def _calculate_correlation_pvalue(self, x: pd.Series, y: pd.Series) -> float:
        """
        計算相關係數的 p 值

        Args:
            x: 第一個序列
            y: 第二個序列

        Returns:
            p 值
        """
        try:
            _, p_value = stats.pearsonr(x.values, y.values)
            return p_value
        except Exception:
            return 1.0  # 返回不顯著

    def _compare_with_benchmark(self, signals: Dict[str, pd.Series],
                              benchmark_returns: pd.Series) -> Dict[str, any]:
        """
        比較信號與基準的表現

        Args:
            signals: 信號數據
            benchmark_returns: 基準收益

        Returns:
            比較結果
        """
        try:
            comparison_results = {}

            # 假設信號值代表風險敞口
            for signal_name, signal_series in signals.items():
                if not isinstance(signal_series, pd.Series) or signal_series.empty:
                    continue

                # 對齊數據
                aligned_data = pd.DataFrame({
                    'signal': signal_series,
                    'benchmark': benchmark_returns
                }).dropna()

                if len(aligned_data) < self.min_sample_size:
                    continue

                signal_values = aligned_data['signal']
                bench_returns = aligned_data['benchmark']

                # 計算信號與基準的相關性
                correlation = signal_values.corr(bench_returns)
                correlation_pvalue = self._calculate_correlation_pvalue(signal_values, bench_returns)

                # Beta (信號相對於基準的敏感度)
                covariance = signal_values.cov(bench_returns)
                benchmark_variance = bench_returns.var()
                beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

                # 貢獻度分析
                signal_contribution = abs(correlation) * signal_values.std()

                comparison_results[signal_name] = {
                    'benchmark_correlation': correlation,
                    'benchmark_correlation_pvalue': correlation_pvalue,
                    'beta_to_benchmark': beta,
                    'signal_contribution': signal_contribution,
                    'independence_score': 1 - abs(correlation)  # 與基準的獨立性，越高越好
                }

            return comparison_results

        except Exception as e:
            logger.error(f"基準比較失敗: {str(e)}")
            return {}

    def _analyze_signal_correlations(self, signals: Dict[str, pd.Series]) -> Dict[str, any]:
        """
        分析信號間的相關性

        Args:
            signals: 信號數據

        Returns:
            相關性分析結果
        """
        try:
            # 選擇數值型信號
            numeric_signals = {}
            for name, series in signals.items():
                if isinstance(series, pd.Series) and not series.empty:
                    numeric_signals[name] = series

            if len(numeric_signals) < 2:
                return {'error': '至少需要2個信號進行相關性分析'}

            # 創建數據框
            signals_df = pd.DataFrame(numeric_signals).dropna()

            if signals_df.empty or len(signals_df.columns) < 2:
                return {'error': '無足夠數據進行相關性分析'}

            # 計算相關性矩陣
            correlation_matrix = signals_df.corr()

            # 識別高度相關的信號對
            high_correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.8:  # 高度相關閾值
                        high_correlations.append({
                            'signal1': correlation_matrix.columns[i],
                            'signal2': correlation_matrix.columns[j],
                            'correlation': corr_value
                        })

            # 計算冗餘分數
            redundancy_score = len(high_correlations) / (len(signals_df.columns) * (len(signals_df.columns) - 1) / 2)

            return {
                'correlation_matrix': correlation_matrix.to_dict(),
                'high_correlations': high_correlations,
                'redundancy_score': redundancy_score,
                'signal_independence': 1 - redundancy_score
            }

        except Exception as e:
            logger.error(f"信號相關性分析失敗: {str(e)}")
            return {'error': str(e)}

    def _calculate_overall_quality_score(self, validation_results: Dict[str, any]) -> float:
        """
        計算整體品質評分

        Args:
            validation_results: 驗證結果

        Returns:
            整體品質分數 (0-1)
        """
        try:
            scores = []

            # 穩定性評分
            if 'stability' in validation_results:
                stability_scores = [result.get('stability_score', 0)
                                  for result in validation_results['stability'].values()
                                  if isinstance(result, dict)]
                if stability_scores:
                    scores.append(np.mean(stability_scores))

            # 預測能力評分
            if 'predictive_power' in validation_results:
                predictive_scores = []
                for result in validation_results['predictive_power'].values():
                    if isinstance(result, dict):
                        # 綜合 IC 顯著性和方向準確性
                        ic_sig = 1 if result.get('ic_significance', False) else 0
                        dir_acc = result.get('directional_accuracy', 0.5)
                        pred_score = (ic_sig + dir_acc) / 2
                        predictive_scores.append(pred_score)

                if predictive_scores:
                    scores.append(np.mean(predictive_scores))

            # 基準獨立性評分
            if 'benchmark_comparison' in validation_results:
                independence_scores = [result.get('independence_score', 0)
                                     for result in validation_results['benchmark_comparison'].values()
                                     if isinstance(result, dict)]
                if independence_scores:
                    scores.append(np.mean(independence_scores))

            # 計算整體分數
            if scores:
                overall_score = np.mean(scores)
                # 確保在 0-1 範圍內
                overall_score = max(0, min(1, overall_score))
            else:
                overall_score = 0.5  # 默認中性分數

            return overall_score

        except Exception as e:
            logger.error(f"整體品質評分計算失敗: {str(e)}")
            return 0.5

    def perform_cross_validation(self, signals: Dict[str, pd.Series],
                               future_returns: pd.Series,
                               n_splits: int = 5) -> Dict[str, any]:
        """
        執行時序交叉驗證

        Args:
            signals: 信號數據
            future_returns: 未來收益
            n_splits: 交叉驗證折數

        Returns:
            交叉驗證結果
        """
        try:
            logger.info(f"開始時序交叉驗證 (n_splits={n_splits})")

            if not signals or future_returns.empty:
                return {'error': '數據不足進行交叉驗證'}

            cv_results = {}

            # 對齊數據
            aligned_data = pd.DataFrame()
            for signal_name, signal_series in signals.items():
                if isinstance(signal_series, pd.Series):
                    temp_df = pd.DataFrame({
                        signal_name: signal_series,
                        'future_returns': future_returns
                    }).dropna()

                    if len(temp_df) > self.min_sample_size:
                        if aligned_data.empty:
                            aligned_data = temp_df
                        else:
                            aligned_data = aligned_data.join(temp_df, how='inner')

            if aligned_data.empty or len(aligned_data) < self.min_sample_size:
                return {'error': '交叉驗證數據不足'}

            # 時序交叉驗證
            tscv = TimeSeriesSplit(n_splits=n_splits)

            cv_scores = {}

            for signal_name in [col for col in aligned_data.columns if col != 'future_returns']:
                signal_values = aligned_data[signal_name]
                returns = aligned_data['future_returns']

                fold_scores = []

                for train_idx, test_idx in tscv.split(signal_values):
                    train_signal = signal_values.iloc[train_idx]
                    train_returns = returns.iloc[train_idx]
                    test_signal = signal_values.iloc[test_idx]
                    test_returns = returns.iloc[test_idx]

                    # 計算訓練集上的相關性
                    train_corr = train_signal.corr(train_returns)

                    # 在測試集上評估
                    test_corr = test_signal.corr(test_returns)

                    # 方向準確性
                    train_direction_acc = ((train_signal > 0) == (train_returns > 0)).mean()
                    test_direction_acc = ((test_signal > 0) == (test_returns > 0)).mean()

                    fold_scores.append({
                        'train_correlation': train_corr,
                        'test_correlation': test_corr,
                        'train_direction_accuracy': train_direction_acc,
                        'test_direction_accuracy': test_direction_acc,
                        'overfitting_gap': abs(train_corr - test_corr)
                    })

                # 匯總折疊結果
                cv_scores[signal_name] = {
                    'fold_results': fold_scores,
                    'avg_train_correlation': np.mean([f['train_correlation'] for f in fold_scores]),
                    'avg_test_correlation': np.mean([f['test_correlation'] for f in fold_scores]),
                    'avg_overfitting_gap': np.mean([f['overfitting_gap'] for f in fold_scores]),
                    'cv_stability_score': 1 / (1 + np.std([f['test_correlation'] for f in fold_scores]))
                }

            cv_results = {
                'cross_validation_scores': cv_scores,
                'summary': {
                    'best_signal': max(cv_scores.keys(),
                                     key=lambda x: cv_scores[x]['avg_test_correlation']),
                    'avg_stability': np.mean([s['cv_stability_score'] for s in cv_scores.values()]),
                    'total_folds': n_splits
                }
            }

            logger.info("時序交叉驗證完成")
            return cv_results

        except Exception as e:
            logger.error(f"交叉驗證失敗: {str(e)}")
            return {'error': str(e)}

    def generate_validation_report(self, validation_results: Dict[str, any],
                                 output_path: Optional[str] = None) -> str:
        """
        生成驗證報告

        Args:
            validation_results: 驗證結果
            output_path: 輸出路徑

        Returns:
            報告內容
        """
        try:
            logger.info("生成驗證報告")

            report_lines = []
            report_lines.append("# RORO 信號驗證報告")
            report_lines.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")

            # 整體品質評分
            if 'quality_score' in validation_results:
                score = validation_results['quality_score']
                quality_desc = "優秀" if score > 0.8 else "良好" if score > 0.6 else "一般" if score > 0.4 else "需改進"
                report_lines.append(f"## 整體品質評分: {score:.3f} ({quality_desc})")
                report_lines.append("")

            # 基本統計
            if 'basic_stats' in validation_results and validation_results['basic_stats']:
                report_lines.append("## 信號基本統計")
                for signal_name, stats in validation_results['basic_stats'].items():
                    report_lines.append(f"### {signal_name}")
                    report_lines.append(f"- 樣本數量: {stats['count']}")
                    report_lines.append(f"- 均值: {stats['mean']:.4f}")
                    report_lines.append(f"- 標準差: {stats['std']:.4f}")
                    report_lines.append(f"- 偏度: {stats['skewness']:.4f}")
                    report_lines.append(f"- 峰度: {stats['kurtosis']:.4f}")
                    report_lines.append(f"- 自相關(1): {stats['autocorr_1']:.4f}")
                    report_lines.append(f"- 穩定性p值: {stats['stationarity_pvalue']:.4f}")
                    report_lines.append("")

            # 預測能力
            if 'predictive_power' in validation_results and validation_results['predictive_power']:
                report_lines.append("## 預測能力分析")
                for signal_name, power in validation_results['predictive_power'].items():
                    report_lines.append(f"### {signal_name}")
                    report_lines.append(f"- 相關係數: {power['correlation']:.4f} (p={power['correlation_pvalue']:.4f})")
                    report_lines.append(f"- 資訊係數: {power['information_coefficient']:.4f}")
                    report_lines.append(f"- IC顯著性: {'是' if power['ic_significance'] else '否'}")
                    report_lines.append(f"- 方向準確性: {power['directional_accuracy']:.1%}")
                    report_lines.append("")

            # 驗證摘要
            report_lines.append("## 驗證結論")
            if 'quality_score' in validation_results:
                score = validation_results['quality_score']
                if score > 0.8:
                    report_lines.append("✅ 信號品質優秀，建議用於實際交易。")
                elif score > 0.6:
                    report_lines.append("⚠️ 信號品質良好，但需要持續監控。")
                elif score > 0.4:
                    report_lines.append("⚠️ 信號品質一般，建議進一步優化。")
                else:
                    report_lines.append("❌ 信號品質不佳，需要重大改進。")

            report_content = "\n".join(report_lines)

            # 保存報告
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                logger.info(f"驗證報告已保存: {output_path}")

            return report_content

        except Exception as e:
            logger.error(f"驗證報告生成失敗: {str(e)}")
            return f"報告生成失敗: {str(e)}"


def main():
    """
    主函數 - 用於測試信號驗證器
    """
    # 配置日誌
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 測試信號驗證器
    try:
        validator = SignalValidator()

        # 創建測試信號數據
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        np.random.seed(42)

        # 生成測試信號
        test_signals = {
            'roro_state': pd.Series(np.random.choice([-2, -1, 0, 1, 2], len(dates)), index=dates),
            'market_width_score': pd.Series(np.random.normal(0, 1, len(dates)), index=dates),
            'composite_pressure_index': pd.Series(np.random.normal(0, 0.5, len(dates)), index=dates),
        }

        # 生成測試收益數據
        future_returns = pd.Series(np.random.normal(0.001, 0.02, len(dates)), index=dates)

        logger.info("測試信號驗證器")

        # 執行驗證
        validation_results = validator.validate_signal_quality(test_signals, future_returns)

        if validation_results:
            logger.info(f"驗證完成，品質評分: {validation_results.get('quality_score', 'N/A')}")

            # 生成報告
            report = validator.generate_validation_report(validation_results)
            logger.info("驗證報告已生成")
            print("\n" + "="*50)
            print("驗證報告摘要:")
            print("="*50)
            print(report[:500] + "..." if len(report) > 500 else report)
        else:
            logger.warning("信號驗證失敗")

    except Exception as e:
        logger.error(f"測試失敗: {str(e)}")


if __name__ == "__main__":
    main()



