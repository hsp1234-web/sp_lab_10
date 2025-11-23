import os
import zipfile
from pathlib import Path

def unzip_all_in_dir(source_dir, target_dir):
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    if not source_path.exists():
        print(f"Source directory {source_path} does not exist.")
        return

    # Create target directory if it doesn't exist
    target_path.mkdir(parents=True, exist_ok=True)
    
    zip_files = list(source_path.glob('*.zip'))
    total_files = len(zip_files)
    
    print(f"Found {total_files} zip files in {source_path}")
    
    for i, zip_file in enumerate(zip_files, 1):
        try:
            print(f"[{i}/{total_files}] Extracting {zip_file.name}...")
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(target_path)
            print(f"Done: {zip_file.name}")
        except zipfile.BadZipFile:
            print(f"Error: {zip_file.name} is a bad zip file.")
        except Exception as e:
            print(f"Failed to extract {zip_file.name}: {e}")

if __name__ == "__main__":
    # Define paths relative to the project root (assuming script is in src/)
    # We can use absolute paths based on the user's workspace info to be safe
    project_root = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1")
    source_directory = project_root / "data" / "taifex_raw"
    target_directory = project_root / "data" / "taifex_extracted"
    
    unzip_all_in_dir(source_directory, target_directory)
