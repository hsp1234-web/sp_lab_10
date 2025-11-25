# -*- coding: utf-8 -*-
"""
回測結果檢視器

這個腳本會執行以下操作：
1. 連接到指定的回測結果資料庫 (DuckDB)。
2. 查詢 'results' 表，獲取所有已完成的回測數據。
3. 解析、排序並以美觀的表格形式顯示結果。
"""
import duckdb
import pandas as pd
import argparse
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

# --- 路徑設定 ---
PROJECT_ROOT = Path(__file__).parent.parent

def parse_and_format_results(df: pd.DataFrame) -> pd.DataFrame:
    """解析 JSON 欄位，並格式化 DataFrame 以便顯示。"""

    # 1. 解析 JSON 欄位
    # 使用 .apply(json.loads) 將 JSON 字串轉為 Python 字典
    # 再用 pd.json_normalize 將其展平為新的 DataFrame
    params_df = pd.json_normalize(df['params'].apply(json.loads))
    metrics_df = pd.json_normalize(df['metrics'].apply(json.loads))

    # 2. 合併解析後的數據
    # 將原始的 backtest_id 與解析出的 params 和 metrics 合併
    results_df = pd.concat([df['backtest_id'], params_df, metrics_df], axis=1)

    # 3. 數據排序
    # 根據 sharpe_ratio (夏普比率) 進行降序排序
    if 'sharpe_ratio' in results_df.columns:
        results_df.sort_values(by='sharpe_ratio', ascending=False, inplace=True)

    return results_df

def display_results_table(df: pd.DataFrame, job_id: str):
    """使用 Rich 函式庫生成並打印美觀的結果表格。"""

    console = Console()
    table = Table(
        title=f"[bold green]回測績效報告: {job_id}[/bold green]",
        show_header=True,
        header_style="bold magenta"
    )

    # 定義表格欄位
    table.add_column("排名", style="dim", width=5)
    table.add_column("Backtest ID", style="cyan", no_wrap=True)

    # 動態添加參數欄位
    param_cols = [col for col in df.columns if col.startswith('params.')]
    for col in param_cols:
        table.add_column(col.replace('params.', ''), style="yellow")

    # 添加績效指標欄位
    table.add_column("夏普比率", justify="right", style="green")
    table.add_column("總報酬率", justify="right")
    table.add_column("最大回撤", justify="right")

    # 填充表格數據
    for index, row in enumerate(df.itertuples()):
        # 格式化績效指標
        sharpe = f"{getattr(row, 'sharpe_ratio', 0):.3f}"
        total_return = f"{getattr(row, 'total_return', 0):+.2%}"
        max_drawdown = f"{getattr(row, 'max_drawdown', 0):.2%}"

        # 準備要添加到 row 的數據列表
        row_data = [
            str(index + 1),
            getattr(row, 'backtest_id', 'N/A'),
            *[str(getattr(row, col, 'N/A')) for col in param_cols], # 獲取所有參數值
            sharpe,
            total_return,
            max_drawdown
        ]
        table.add_row(*row_data)

    console.print(table)


def view_results(db_path: Path, job_id: str):
    """
    連接資料庫，查詢並顯示指定 job_id 的回測結果。
    """
    if not db_path.exists():
        print(f"❌ 錯誤：資料庫檔案不存在於 '{db_path}'")
        return

    print(f"--- 正在從 '{db_path.name}' 讀取結果 ---")
    con = duckdb.connect(str(db_path))

    query = "SELECT * FROM results WHERE job_id = ?"
    try:
        results_df = con.execute(query, [job_id]).df()
    except duckdb.CatalogException:
        print(f"❌ 錯誤：資料表中找不到 'results'。請確認資料庫是否正確。")
        con.close()
        return

    con.close()

    if results_df.empty:
        print(f"🟡 警告：在資料庫中找不到任何關於 Job ID '{job_id}' 的結果。")
        return

    print(f"✅ 成功查詢到 {len(results_df)} 筆關於 '{job_id}' 的回測結果。正在處理...")

    # 解析、排序並格式化數據
    formatted_df = parse_and_format_results(results_df)

    # 顯示結果
    display_results_table(formatted_df, job_id)


def main():
    parser = argparse.ArgumentParser(description="回測結果檢視器")
    parser.add_argument("--db", type=str, default="output/results/quick_feedback.db", help="回測結果資料庫的路徑")
    parser.add_argument("--job", type=str, default="default_job", help="要檢視的 Job ID")
    args = parser.parse_args()

    db_path = PROJECT_ROOT / args.db
    view_results(db_path, args.job)

if __name__ == "__main__":
    main()
