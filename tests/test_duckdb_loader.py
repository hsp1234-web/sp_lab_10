import sys
from pathlib import Path
import pandas as pd
import traceback

# Add project root to sys.path
project_root = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1")
sys.path.append(str(project_root))
sys.path.append(str(project_root / "lo2cin4bt-main"))

# Fix import path: lo2cin4bt-main is a directory, but it's not a package unless it has __init__.py
# And the folder name has hyphens.
# The code uses relative imports inside the package.
# We need to be careful.
# The structure is:
# lo2cin4bt-main/
#   dataloader/
#     __init__.py
#     duckdb_loader.py

# We should add lo2cin4bt-main to path and import dataloader.duckdb_loader
sys.path.append(str(project_root / "lo2cin4bt-main"))

try:
    from dataloader.duckdb_loader import DuckDBLoader
except ImportError:
    # Try alternative if the above fails (maybe user renamed folder?)
    # But based on file paths, it is lo2cin4bt-main
    pass

def test_loader():
    output_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\test_loader_log.txt")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("Testing DuckDBLoader...\n")
        
        try:
            loader = DuckDBLoader()
            
            # Mock user input
            input_values = iter(["TX", "2024"])
            
            def mock_input(prompt=""):
                f.write(f"Prompt: {prompt} [Mock Input]\n")
                try:
                    val = next(input_values)
                    f.write(f"User entered: {val}\n")
                    return val
                except StopIteration:
                    return ""
                    
            import builtins
            builtins.input = mock_input
            
            # Redirect stdout to file for the duration of load()
            # Because load() prints to console
            # But we can't easily redirect rich console output unless we configure it.
            # We'll just rely on the return value.
            
            df, freq = loader.load()
            
            if df is not None:
                f.write("\nLoad Successful!\n")
                f.write(f"Frequency: {freq}\n")
                f.write(f"Shape: {df.shape}\n")
                f.write("Head:\n")
                f.write(df.head().to_string())
                f.write("\nTail:\n")
                f.write(df.tail().to_string())
            else:
                f.write("\nLoad Failed (None returned)\n")
                
        except Exception as e:
            f.write(f"\nError: {e}\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    test_loader()
