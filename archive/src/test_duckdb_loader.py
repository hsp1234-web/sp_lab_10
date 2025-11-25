import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
project_root = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1")
sys.path.append(str(project_root))
sys.path.append(str(project_root / "lo2cin4bt-main"))

from lo2cin4bt_main.dataloader.duckdb_loader import DuckDBLoader

def test_loader():
    print("Testing DuckDBLoader...")
    loader = DuckDBLoader()
    
    # Mock user input for symbol and year
    # We need to mock built-in input function or just modify the loader for testing?
    # Or we can just call internal methods if we refactored.
    # But load() is interactive.
    
    # Let's try to monkeypatch input
    input_values = iter(["TX", "2024"])
    
    def mock_input(prompt=""):
        print(f"{prompt} [Mock Input]")
        try:
            val = next(input_values)
            print(f"User entered: {val}")
            return val
        except StopIteration:
            return ""
            
    import builtins
    builtins.input = mock_input
    
    try:
        df, freq = loader.load()
        
        if df is not None:
            print("\nLoad Successful!")
            print(f"Frequency: {freq}")
            print(f"Shape: {df.shape}")
            print("Head:")
            print(df.head())
            print("Tail:")
            print(df.tail())
        else:
            print("\nLoad Failed (None returned)")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_loader()
