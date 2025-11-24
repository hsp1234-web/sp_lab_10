# -*- coding: utf-8 -*-
"""
主執行腳本 (Orchestrator)

這個腳本是整個量化研究專案的單一進入點。它負責解析命令列參數，
讀取 YAML 配置文件，並根據指定的任務 (task) 來調度執行對應的
工作流程。
"""

import sys
import os
import argparse
import yaml
from rich.console import Console

# --- 將專案根目錄加入 Python PATH ---
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# --- 核心模組導入 ---
from src.task_runner import TaskRunner

def main():
    """
    程式主進入點：
    1. 解析命令列參數。
    2. 讀取並解析 YAML 配置文件。
    3. 執行指定的任務。
    """
    console = Console()

    # --- 步驟 1: 設定與解析命令列參數 ---
    parser = argparse.ArgumentParser(description="自動化量化研究執行器")
    parser.add_argument(
        '-t', '--task',
        type=str,
        required=True,
        help="要執行的任務名稱 (定義於 YAML 配置文件中)"
    )
    parser.add_argument(
        '-f', '--config-file',
        type=str,
        default='config/tasks.yaml',
        help="指定配置文件的路徑 (預設: config/tasks.yaml)"
    )
    args = parser.parse_args()

    # --- 步驟 2: 讀取並解析 YAML 配置文件 ---
    try:
        with open(args.config_file, 'r', encoding='utf-8') as f:
            all_tasks = yaml.safe_load(f)
            if not isinstance(all_tasks, dict):
                console.print(f"[bold red]錯誤：[/bold red] 配置文件 {args.config_file} 格式不正確，頂層應為字典。")
                sys.exit(1)
    except FileNotFoundError:
        console.print(f"[bold red]錯誤：[/bold red] 配置文件 {args.config_file} 不存在。")
        sys.exit(1)
    except yaml.YAMLError as e:
        console.print(f"[bold red]錯誤：[/bold red] 解析 YAML 文件時發生錯誤：{e}")
        sys.exit(1)

    # --- 步驟 3: 尋找並驗證指定的任務 ---
    task_config = all_tasks.get(args.task)
    if not task_config:
        console.print(f"[bold red]錯誤：[/bold red] 在 {args.config_file} 中找不到名為 '{args.task}' 的任務。")
        sys.exit(1)
    
    if 'steps' not in task_config or not isinstance(task_config['steps'], list):
        console.print(f"[bold red]錯誤：[/bold red] 任務 '{args.task}' 的結構不正確，缺少 'steps' 列表。")
        sys.exit(1)

    # --- 步驟 4: 執行任務 ---
    description = task_config.get('description', '無描述')
    console.print(f"\n[bold green]🚀 開始執行任務：[/bold green] [cyan]{args.task}[/cyan] ({description})")
    console.print(f"[bold blue]📄 使用配置文件：[/bold blue] {args.config_file}\n")

    # --- 呼叫 TaskRunner 來執行任務 ---
    runner = TaskRunner()
    success = runner.run(task_config['steps'])

    # --- 顯示最終結果 ---
    if success:
        console.print("\n[bold green]✅ 任務成功完成！[/bold green]")
    else:
        console.print("\n[bold red]❌ 任務執行失敗。[/bold red]")

if __name__ == "__main__":
    main()
