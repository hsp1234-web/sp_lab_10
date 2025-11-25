# src/viz.py
# 視覺化與績效報告模組

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # 使用非互動式後端，避免在伺服器上出錯
import matplotlib.pyplot as plt

def plot_equity_curve(equity_curve: pd.DataFrame, output_path: str, performance_metrics: dict = None):
    """
    繪製權益曲線圖並將其保存為檔案。

    參數:
        equity_curve (pd.DataFrame): 包含 'equity' 欄位的 DataFrame，索引為日期。
        output_path (str): 儲存圖表的檔案路徑 (例如 'equity_curve.jpg')。
        performance_metrics (dict, optional): 包含績效指標的字典。如果提供，
                                              指標將會被顯示在圖表的標題中。
    """
    plt.style.use('seaborn-v0_8-darkgrid') # 使用較美觀的樣式
    fig, ax = plt.subplots(figsize=(8, 4.5))

    ax.plot(equity_curve.index, equity_curve['equity'], label='權益曲線', color='royalblue')
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('權益', fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # 格式化標題
    title = "策略權益曲線"
    if performance_metrics:
        total_return = performance_metrics.get('總報酬率', 0) * 100
        max_drawdown = performance_metrics.get('最大回撤 (MDD)', 0) * 100
        sharpe = performance_metrics.get('夏普比率', 0)
        title += (
            f"\\n"
            f"總報酬率: {total_return:.2f}% | "
            f"最大回撤: {max_drawdown:.2f}% | "
            f"夏普比率: {sharpe:.2f}"
        )
    ax.set_title(title, fontsize=12, pad=20)

    # 改善圖表外觀
    plt.tight_layout()
    fig.savefig(output_path, format='jpg', dpi=150) # 提高解析度
    plt.close(fig) # 釋放記憶體
