import sys
import os
import time
import random
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(project_root, "lo2cin4bt-main"))

from database.BacktestDB import BacktestDB

def run_poc():
    print("🚀 開始增量回測 POC (Proof of Concept)")
    print("="*50)

    db_path = "records/poc_backtest.db"
    job_id = "poc_job_001"
    total_tasks = 100
    batch_size = 10
    
    # 1. 初始化資料庫
    print(f"1. 初始化資料庫: {db_path}")
    db = BacktestDB(db_path)
    
    # 2. 檢查任務是否存在 (模擬續傳)
    existing_job = db.get_job(job_id)
    if existing_job:
        print(f"   發現已存在任務: {job_id}")
        print(f"   狀態: {existing_job['status']}")
        print(f"   已完成: {existing_job['completed_tasks']}/{existing_job['total_tasks']}")
        
        completed_ids = set(db.get_completed_backtest_ids(job_id))
        print(f"   已完成 ID 數量: {len(completed_ids)}")
    else:
        print(f"   建立新任務: {job_id}")
        db.create_job(job_id, {"mode": "poc", "strategy": "test"}, total_tasks)
        completed_ids = set()

    # 3. 模擬執行回測
    print("\n2. 開始執行/恢復回測...")
    
    # 生成所有任務 ID
    all_task_ids = [f"bt_{i:03d}" for i in range(total_tasks)]
    
    # 過濾已完成的任務
    tasks_to_run = [tid for tid in all_task_ids if tid not in completed_ids]
    print(f"   剩餘任務數: {len(tasks_to_run)}")
    
    if not tasks_to_run:
        print("   所有任務已完成！")
        return

    # 分批處理
    for i in range(0, len(tasks_to_run), batch_size):
        batch_tasks = tasks_to_run[i:i+batch_size]
        print(f"   正在處理批次: {batch_tasks[0]} - {batch_tasks[-1]} ({len(batch_tasks)} 個)")
        
        # 模擬運算 (產生隨機結果)
        batch_results = []
        for tid in batch_tasks:
            # 模擬運算時間
            time.sleep(0.01) 
            
            # 模擬隨機績效
            result = {
                "backtest_id": tid,
                "strategy_id": "strat_test",
                "params": {"ma_period": random.randint(10, 200)},
                "total_return": random.uniform(-0.5, 1.5),
                "sharpe_ratio": random.uniform(0, 3.0),
                "max_drawdown": random.uniform(-0.3, 0),
                # 模擬一些交易記錄
                "records": pd.DataFrame({"price": np.random.randn(100)}) 
            }
            batch_results.append(result)
        
        # 寫入資料庫
        print("   💾 寫入資料庫...", end="")
        db.write_batch_results(job_id, batch_results)
        print(" 完成")
        
        # 模擬中斷 (在完成 50% 時)
        current_progress = db.get_job(job_id)['completed_tasks']
        if current_progress >= 50 and current_progress < 60:
            print("\n⚠️  模擬系統中斷/當機！(已完成 50%)")
            print("   請重新執行此腳本以測試續傳功能。")
            sys.exit(0)

    # 4. 完成
    db.finish_job(job_id)
    print("\n✅ 任務全部完成！")
    
    # 5. 驗證數據
    print("\n3. 驗證資料庫數據...")
    conn = duckdb.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM results WHERE job_id = ?", (job_id,)).fetchone()[0]
    print(f"   資料庫中的結果總數: {count}")
    
    # 顯示前 3 筆結果
    print("   前 3 筆結果範例:")
    df = conn.execute("SELECT backtest_id, metrics FROM results WHERE job_id = ? LIMIT 3", (job_id,)).df()
    print(df)
    conn.close()

if __name__ == "__main__":
    run_poc()
