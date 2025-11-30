import sys
from pathlib import Path
import qlib
from qlib.tests.data import GetData

def download_data(target_dir="data/qlib_data/cn_data"):
    """
    下載 Qlib 範例資料 (CN Data)
    """
    target_path = Path(target_dir)
    if target_path.exists():
        print(f"資料目錄已存在: {target_path}")
        return

    print(f"開始下載 Qlib 範例資料至: {target_path}")
    # GetData().qlib_data(target_dir=str(target_path.parent), exists_skip=True)
    # 修正: GetData 預設會下載到 ~/.qlib/qlib_data/cn_data
    # 我們需要手動處理或使用 qlib.run.get_data
    
    # 使用 qlib 內建指令下載
    # python -m qlib.run.get_data qlib_data --target_dir data/qlib_data/cn_data
    
    # 這裡我們直接呼叫 GetData 的方法
    # 注意: GetData().qlib_data 會下載並解壓
    try:
        GetData().qlib_data(target_dir=str(target_path.parent), version="latest", interval="1d", region="cn")
        print("下載完成！")
    except Exception as e:
        print(f"下載失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_data()
