import psutil
import platform
import os
import multiprocessing

def check_system_info():
    print("="*40)
    print("🖥️  系統資源檢測報告")
    print("="*40)

    # OS Info
    print(f"作業系統: {platform.system()} {platform.release()} ({platform.version()})")
    print(f"機器類型: {platform.machine()}")
    
    # CPU Info
    print("-" * 40)
    print(f"CPU 實體核心數: {psutil.cpu_count(logical=False)}")
    print(f"CPU 邏輯核心數: {psutil.cpu_count(logical=True)}")
    print(f"CPU 頻率: {psutil.cpu_freq().max:.2f} Mhz" if psutil.cpu_freq() else "N/A")
    
    # Memory Info
    mem = psutil.virtual_memory()
    print("-" * 40)
    print(f"總記憶體: {mem.total / (1024**3):.2f} GB")
    print(f"可用記憶體: {mem.available / (1024**3):.2f} GB")
    print(f"已用記憶體: {mem.used / (1024**3):.2f} GB ({mem.percent}%)")

    # Disk Info (Current Drive)
    print("-" * 40)
    current_drive = os.getcwd().split(':')[0] + ':\\' if platform.system() == 'Windows' else '/'
    try:
        disk = psutil.disk_usage(current_drive)
        print(f"磁碟空間 ({current_drive}):")
        print(f"  總計: {disk.total / (1024**3):.2f} GB")
        print(f"  可用: {disk.free / (1024**3):.2f} GB")
    except Exception as e:
        print(f"無法讀取磁碟資訊: {e}")

    print("="*40)
    
    # Python Multiprocessing Info
    print("🐍 Python 多進程配置")
    print("-" * 40)
    try:
        print(f"預設啟動方法: {multiprocessing.get_start_method()}")
    except:
        print("預設啟動方法: N/A")
    
    print("="*40)

if __name__ == "__main__":
    check_system_info()
