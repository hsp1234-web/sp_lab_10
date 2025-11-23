import os
from pathlib import Path
import codecs

def convert_encoding(source_dir, source_encoding='cp950', target_encoding='utf-8'):
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"Source directory {source_path} does not exist.")
        return

    files = list(source_path.glob('*.csv'))
    total_files = len(files)
    
    print(f"Found {total_files} CSV files in {source_path}")
    
    for i, file_path in enumerate(files, 1):
        try:
            print(f"[{i}/{total_files}] Converting {file_path.name}...")
            
            # Read with source encoding
            with codecs.open(file_path, 'r', encoding=source_encoding) as f:
                content = f.read()
            
            # Write with target encoding
            with codecs.open(file_path, 'w', encoding=target_encoding) as f:
                f.write(content)
                
            print(f"Done: {file_path.name}")
            
        except UnicodeDecodeError:
            print(f"Error: Failed to decode {file_path.name} with {source_encoding}. It might be in a different encoding.")
        except Exception as e:
            print(f"Failed to convert {file_path.name}: {e}")

if __name__ == "__main__":
    project_root = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1")
    target_directory = project_root / "data" / "taifex_extracted"
    
    # Convert from cp950 (Big5) to utf-8
    convert_encoding(target_directory, source_encoding='cp950', target_encoding='utf-8')
