import yfinance as yf
import os

# 定義常數
TICKER = "^GSPC"

def download_gspc(output_path: str = None, return_df: bool = False):
    """
    從 yfinance 下載 S&P 500 (^GSPC) 的歷史資料。
    可以選擇將資料儲存為 Parquet 檔案，或直接返回 DataFrame。

    參數:
        output_path (str, optional): 儲存 Parquet 檔案的完整路徑。預設為 None。
        return_df (bool, optional): 是否直接返回 DataFrame。預設為 False。

    回傳:
        pd.DataFrame or None: 如果 return_df 為 True，則返回 DataFrame，否則返回 None。
    """
    if not output_path and not return_df:
        raise ValueError("必須提供 output_path 或設定 return_df=True")

    # 下載資料
    data = yf.download(TICKER, start="1990-01-01")

    if output_path:
        # 確保輸出目錄存在
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        # 儲存為 Parquet 格式
        data.to_parquet(output_path)
        print(f"資料已成功下載並儲存至 {output_path}")

    if return_df:
        return data
    return None

if __name__ == '__main__':
    # 為了方便獨立執行此腳本，我們在此處定義一個預設的輸出路徑。
    # 這段程式碼只有在 `python src/fetch.py` 被直接執行時才會觸發。
    DEFAULT_OUTPUT_DIR = "data/raw"
    DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, f"{TICKER.replace('^', '')}.parquet")
    download_gspc(DEFAULT_OUTPUT_FILE)
