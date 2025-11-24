import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional

class MAEMFEAnalyser:
    """
    MAE (Maximum Adverse Excursion) & MFE (Maximum Favorable Excursion) Analyser
    
    功能：
    1. 計算每筆交易的 MAE 與 MFE。
    2. 計算 Edge Ratio (優勢比率)。
    3. 產生分析報告數據。
    """
    
    def __init__(self, trades_df: pd.DataFrame, ohlcv_data: pd.DataFrame, logger: Optional[logging.Logger] = None):
        self.trades_df = trades_df
        self.ohlcv_data = ohlcv_data
        self.logger = logger or logging.getLogger(__name__)
        
        # 確保 OHLCV 數據有時間索引
        if 'Time' in self.ohlcv_data.columns and not isinstance(self.ohlcv_data.index, pd.DatetimeIndex):
            self.ohlcv_data = self.ohlcv_data.set_index('Time')
        
        # 確保 trades_df 有必要的欄位
        required_cols = ['entry_time', 'exit_time', 'entry_price', 'type'] # type: 1 (Long), -1 (Short)
        # 注意：BacktestEngine 輸出的欄位名稱可能不同，需適配
        # 通常是: 'Entry Time', 'Exit Time', 'Entry Price', 'Type' (Long/Short string or 1/-1)
        
        if self.trades_df.empty:
            return

        self._standardize_trade_columns()

    def _standardize_trade_columns(self):
        """標準化交易列表欄位名稱"""
        col_map = {
            'Entry Time': 'entry_time',
            'Exit Time': 'exit_time',
            'Entry Price': 'entry_price',
            'Exit Price': 'exit_price',
            'Type': 'type',
            'Return': 'return'
        }
        self.trades_df = self.trades_df.rename(columns=col_map)
        
        # 轉換 type 為數值 (如果需要)
        if 'type' in self.trades_df.columns and self.trades_df['type'].dtype == 'O':
            self.trades_df['type'] = self.trades_df['type'].map({'Long': 1, 'Short': -1, 1: 1, -1: -1})

    def analyze(self) -> pd.DataFrame:
        """
        執行 MAE/MFE 分析
        Returns:
            pd.DataFrame: 包含 MAE, MFE, GMFE, BMFE 等欄位的交易列表
        """
        if self.trades_df.empty:
            self.logger.warning("交易列表為空，無法進行 MAE/MFE 分析")
            return self.trades_df
            
        self.logger.info("開始計算 MAE/MFE...")
        
        mae_list = []
        mfe_list = []
        gmfe_list = [] # Global MFE (最大浮盈)
        bmfe_list = [] # Best MFE (最佳浮盈 - 通常等於 MFE)
        
        for idx, trade in self.trades_df.iterrows():
            entry_time = trade['entry_time']
            exit_time = trade['exit_time']
            entry_price = trade['entry_price']
            trade_type = trade['type']
            
            # 取得持有期間的 OHLCV
            mask = (self.ohlcv_data.index >= entry_time) & (self.ohlcv_data.index <= exit_time)
            period_data = self.ohlcv_data.loc[mask]
            
            if period_data.empty:
                mae_list.append(0)
                mfe_list.append(0)
                continue
                
            if trade_type == 1: # Long
                # MAE: (Entry - Min Low) / Entry
                min_low = period_data['Low'].min()
                mae = (entry_price - min_low) / entry_price
                
                # MFE: (Max High - Entry) / Entry
                max_high = period_data['High'].max()
                mfe = (max_high - entry_price) / entry_price
                
            else: # Short
                # MAE: (Max High - Entry) / Entry
                max_high = period_data['High'].max()
                mae = (max_high - entry_price) / entry_price
                
                # MFE: (Entry - Min Low) / Entry
                min_low = period_data['Low'].min()
                mfe = (entry_price - min_low) / entry_price
            
            # 確保非負值 (理論上 MAE/MFE 應該 >= 0，除非數據異常)
            mae = max(0, mae)
            mfe = max(0, mfe)
            
            mae_list.append(mae)
            mfe_list.append(mfe)
            
        self.trades_df['MAE'] = mae_list
        self.trades_df['MFE'] = mfe_list
        
        # 計算 Edge Ratio
        avg_mae = self.trades_df['MAE'].mean()
        avg_mfe = self.trades_df['MFE'].mean()
        
        if avg_mae > 0:
            edge_ratio = avg_mfe / avg_mae
        else:
            edge_ratio = np.inf
            
        self.logger.info(f"MAE/MFE 分析完成。Edge Ratio: {edge_ratio:.2f}")
        
        return self.trades_df

    def get_summary_stats(self) -> Dict[str, Any]:
        """取得統計摘要"""
        if 'MAE' not in self.trades_df.columns:
            return {}
            
        return {
            'Avg MAE': self.trades_df['MAE'].mean(),
            'Avg MFE': self.trades_df['MFE'].mean(),
            'Max MAE': self.trades_df['MAE'].max(),
            'Max MFE': self.trades_df['MFE'].max(),
            'Edge Ratio': self.trades_df['MFE'].mean() / self.trades_df['MAE'].mean() if self.trades_df['MAE'].mean() > 0 else 0
        }
