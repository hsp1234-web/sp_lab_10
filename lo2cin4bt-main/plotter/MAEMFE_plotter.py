import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def plot_mae_mfe(trades_df: pd.DataFrame) -> go.Figure:
    """
    繪製 MAE/MFE 分析圖表 (FinLab 風格)
    
    圖表包含：
    1. 報酬分布 (Histogram)
    2. Edge Ratio 時序 (Scatter)
    3. MAE vs Return (Scatter)
    4. MFE vs MAE (Scatter)
    5. MDD vs GMFE (Scatter - 這裡用 MAE vs MFE 替代或衍生)
    6. 密度分布 (Histogram/KDE)
    """
    
    # 確保數據存在
    if 'MAE' not in trades_df.columns or 'MFE' not in trades_df.columns:
        return go.Figure()
        
    # 準備數據
    wins = trades_df[trades_df['return'] > 0]
    losses = trades_df[trades_df['return'] <= 0]
    
    # 建立子圖
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Return Distribution', 'Edge Ratio Time Series', 
            'MAE vs Return', 'MFE vs MAE', 
            'MFE/MAE Ratio Distribution', 'MAE Density'
        ),
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )
    
    # 1. Return Distribution
    fig.add_trace(
        go.Histogram(x=trades_df['return'], name='Return', nbinsx=50, marker_color='blue', opacity=0.7),
        row=1, col=1
    )
    
    # 2. Edge Ratio Time Series (Rolling)
    # 計算滾動 Edge Ratio (例如 20 筆交易)
    window = 20
    if len(trades_df) > window:
        rolling_mfe = trades_df['MFE'].rolling(window).mean()
        rolling_mae = trades_df['MAE'].rolling(window).mean()
        rolling_edge = rolling_mfe / rolling_mae
        
        fig.add_trace(
            go.Scatter(x=trades_df.index, y=rolling_edge, name='Rolling Edge Ratio (20)', mode='lines', line=dict(color='purple')),
            row=1, col=2
        )
        # 添加參考線
        fig.add_hline(y=1, line_dash="dash", line_color="red", row=1, col=2)
    
    # 3. MAE vs Return
    fig.add_trace(
        go.Scatter(
            x=wins['MAE'], y=wins['return'], 
            mode='markers', name='Win', 
            marker=dict(color='blue', size=8, opacity=0.6)
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=losses['MAE'], y=losses['return'], 
            mode='markers', name='Loss', 
            marker=dict(color='red', size=8, opacity=0.6)
        ),
        row=2, col=1
    )
    fig.update_xaxes(title_text="MAE", row=2, col=1)
    fig.update_yaxes(title_text="Return", row=2, col=1)
    
    # 4. MFE vs MAE
    fig.add_trace(
        go.Scatter(
            x=trades_df['MAE'], y=trades_df['MFE'], 
            mode='markers', name='Trade', 
            marker=dict(
                color=trades_df['return'], 
                colorscale='RdBu', 
                showscale=True,
                colorbar=dict(title="Return", len=0.3, y=0.5)
            ),
            text=trades_df.index
        ),
        row=2, col=2
    )
    # 添加 1:1 線
    max_val = max(trades_df['MAE'].max(), trades_df['MFE'].max())
    fig.add_shape(
        type="line", line=dict(dash="dash", color="gray"),
        x0=0, y0=0, x1=max_val, y1=max_val,
        row=2, col=2
    )
    fig.update_xaxes(title_text="MAE", row=2, col=2)
    fig.update_yaxes(title_text="MFE", row=2, col=2)
    
    # 5. MFE/MAE Ratio Distribution (Edge Ratio per trade)
    # 避免除以零
    ratios = trades_df['MFE'] / trades_df['MAE'].replace(0, np.nan)
    fig.add_trace(
        go.Histogram(x=ratios, name='MFE/MAE Ratio', nbinsx=50, marker_color='green', opacity=0.7),
        row=3, col=1
    )
    fig.update_xaxes(title_text="MFE/MAE Ratio", range=[0, 10], row=3, col=1) # 限制範圍避免極端值
    
    # 6. MAE Density (Win vs Loss)
    import plotly.figure_factory as ff
    try:
        # 簡單的 Histogram 替代 KDE，因為 plotly.figure_factory 需要 scipy
        fig.add_trace(
            go.Histogram(x=wins['MAE'], name='Win MAE', marker_color='blue', opacity=0.5, nbinsx=30),
            row=3, col=2
        )
        fig.add_trace(
            go.Histogram(x=losses['MAE'], name='Loss MAE', marker_color='red', opacity=0.5, nbinsx=30),
            row=3, col=2
        )
        fig.update_layout(barmode='overlay')
    except Exception:
        pass
    
    fig.update_layout(
        height=1200, 
        width=1000, 
        title_text="MAE/MFE Analysis",
        showlegend=True
    )
    
    return fig
