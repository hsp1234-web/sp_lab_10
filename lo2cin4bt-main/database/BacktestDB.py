import duckdb
import pandas as pd
import json
import os
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any, Union

class BacktestDB:
    """
    處理回測系統的資料庫操作，支援增量寫入與斷點續傳。
    使用 DuckDB 作為儲存引擎。
    """
    
    def __init__(self, db_path: str = "records/backtest.db"):
        self.db_path = db_path
        self.conn = None
        self._ensure_db_dir()
        self._init_connection()
        self._init_schema()

    def _ensure_db_dir(self):
        """確保資料庫目錄存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def _init_connection(self):
        """初始化資料庫連接"""
        try:
            self.conn = duckdb.connect(self.db_path)
        except Exception as e:
            logging.error(f"無法連接資料庫 {self.db_path}: {e}")
            raise

    def _init_schema(self):
        """初始化資料表結構"""
        # 1. Jobs Table: 儲存回測任務的元數據
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id VARCHAR PRIMARY KEY,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                status VARCHAR, -- 'PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'PAUSED'
                total_tasks INTEGER,
                completed_tasks INTEGER,
                config JSON,
                system_info JSON,
                error_msg VARCHAR
            )
        """)

        # 2. Results Table: 儲存每個參數組合的績效結果
        # 使用 JSON 欄位儲存複雜的參數結構，避免 schema 過於僵化
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                job_id VARCHAR,
                backtest_id VARCHAR,
                strategy_id VARCHAR,
                params JSON,
                metrics JSON, -- 儲存 Sharpe, Return, Drawdown 等
                trade_count INTEGER,
                is_error BOOLEAN DEFAULT FALSE,
                error_msg VARCHAR,
                created_at TIMESTAMP,
                PRIMARY KEY (job_id, backtest_id)
            )
        """)
        
        # 建立索引以加速查詢
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_results_job_id ON results(job_id)")

    def create_job(self, job_id: str, config: Dict[str, Any], total_tasks: int, system_info: Optional[Dict] = None) -> str:
        """建立一個新的回測任務"""
        now = datetime.now()
        self.conn.execute("""
            INSERT INTO jobs (job_id, created_at, updated_at, status, total_tasks, completed_tasks, config, system_info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id, 
            now, 
            now, 
            'PENDING', 
            total_tasks, 
            0, 
            json.dumps(config), 
            json.dumps(system_info) if system_info else None
        ))
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict]:
        """獲取任務資訊"""
        result = self.conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if result:
            columns = [desc[0] for desc in self.conn.description]
            return dict(zip(columns, result))
        return None

    def get_completed_backtest_ids(self, job_id: str) -> List[str]:
        """獲取該任務已完成的 backtest_id 列表 (用於續傳)"""
        result = self.conn.execute("SELECT backtest_id FROM results WHERE job_id = ?", (job_id,)).fetchall()
        return [row[0] for row in result]

    def write_batch_results(self, job_id: str, results: List[Dict[str, Any]]):
        """
        批量寫入回測結果
        
        Args:
            job_id: 任務 ID
            results: 結果字典列表，每個字典應包含 backtest_id, params, metrics 等
        """
        if not results:
            return

        # 準備數據
        data_to_insert = []
        now = datetime.now()
        
        for res in results:
            # 處理參數和指標，轉為 JSON 字串
            params_json = json.dumps(res.get('params', {}))
            
            # 提取指標 (假設 metrics 在 res 中，或者 res 本身就是 metrics 的集合)
            # 這裡需要根據實際的 VectorBacktestEngine 輸出結構進行調整
            # 目前假設 res 包含了所有資訊
            metrics = {k: v for k, v in res.items() if k not in ['backtest_id', 'strategy_id', 'params', 'records', 'error']}
            metrics_json = json.dumps(metrics)
            
            trade_count = 0
            if 'records' in res and isinstance(res['records'], pd.DataFrame) and not res['records'].empty:
                trade_count = len(res['records'])
            
            data_to_insert.append((
                job_id,
                res.get('backtest_id', 'unknown'),
                res.get('strategy_id', 'unknown'),
                params_json,
                metrics_json,
                trade_count,
                res.get('error') is not None,
                str(res.get('error')) if res.get('error') else None,
                now
            ))

        # 使用 Appender 或 executemany 寫入
        # 使用 DuckDB v0.8.0+ 的標準 UPSERT 語法，明確指定衝突目標
        self.conn.executemany("""
            INSERT INTO results (
                job_id, backtest_id, strategy_id, params, metrics, trade_count, is_error, error_msg, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (job_id, backtest_id) DO UPDATE SET
                strategy_id = excluded.strategy_id,
                params = excluded.params,
                metrics = excluded.metrics,
                trade_count = excluded.trade_count,
                is_error = excluded.is_error,
                error_msg = excluded.error_msg,
                created_at = excluded.created_at
        """, data_to_insert)
        
        # 更新任務進度
        self.update_progress(job_id, len(results))

    def update_progress(self, job_id: str, new_completed_count: int):
        """更新任務進度 (累加)"""
        now = datetime.now()
        self.conn.execute("""
            UPDATE jobs 
            SET completed_tasks = completed_tasks + ?, updated_at = ?, status = 'RUNNING'
            WHERE job_id = ?
        """, (new_completed_count, now, job_id))

    def finish_job(self, job_id: str, status: str = 'COMPLETED', error_msg: Optional[str] = None):
        """標記任務結束"""
        now = datetime.now()
        self.conn.execute("""
            UPDATE jobs 
            SET status = ?, updated_at = ?, error_msg = ?
            WHERE job_id = ?
        """, (status, now, error_msg, job_id))

    def close(self):
        """關閉連接"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
