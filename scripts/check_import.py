import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.getcwd(), "lo2cin4bt-main"))

try:
    print("Attempting to import IncrementalBacktestEngine...")
    from lo2cin4bt.backtester.IncrementalBacktestEngine import IncrementalBacktestEngine
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
