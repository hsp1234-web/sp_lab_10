import sqlite3
import os
import shutil
import argparse
from datetime import datetime

# Configuration
DB_PATH = r"c:\SP_DOC\sp_lab_v10\project_analysis.db"
PROJECT_ROOT = r"c:\SP_DOC\sp_lab_v10"
REPORT_PATH = r"c:\SP_DOC\sp_lab_v10\dry_run_report.txt"

# Category Mapping
CATEGORY_MAP = {
    '說明文件': 'docs',
    '設定檔案': 'config',
    '交易策略': 'strategies',
    '工具腳本': 'tools',
    '數據資料': 'data', # Special handling: if .py, maybe tools/ or data_scripts/
    '測試程式': 'tests',
    '數據處理': 'data_scripts', # New folder for data scripts
    '分析工具': 'tools',
    '研究筆記': 'docs/research',
    '第三方程式': 'tools/third_party'
}

# Archive Rules
TEMP_PREFIXES = ['demo_', 'temp_', 'test_temp_', 'tmp_']
TEMP_KEYWORDS = ['checklist', 'todo', 'draft']

def get_target_folder(filename, category, decision, reason):
    # 1. Archive Priority
    if decision == '刪除':
        return 'archive'
    
    # 2. Test File Cleanup
    if category == '測試程式':
        is_temp = any(filename.lower().startswith(p) for p in TEMP_PREFIXES)
        if is_temp:
            return 'archive'
        return 'tests'

    # 3. Category Mapping
    if category in CATEGORY_MAP:
        target = CATEGORY_MAP[category]
        # Special case: Data scripts vs Data files
        if category == '數據資料' and filename.endswith('.py'):
            return 'data_scripts'
        return target
    
    return None # No move

def main(dry_run=True):
    print(f"Starting organization... Dry Run: {dry_run}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all files
    cursor.execute("""
        SELECT f.id, f.filename, f.filepath, a.category, a.keep_decision, a.reason 
        FROM files f 
        LEFT JOIN analysis a ON f.id = a.file_id
    """)
    files = cursor.fetchall()
    
    moves = []
    
    for file_id, filename, filepath, category, decision, reason in files:
        # Skip if file doesn't exist
        full_path = os.path.join(PROJECT_ROOT, filepath)
        if not os.path.exists(full_path):
            continue
            
        # Skip if already in a subdirectory (simple check)
        # We only want to move files that are in the root or need reorganization
        # For now, let's focus on files in the root directory to avoid messing up existing subfolders too much
        # unless they are clearly misplaces.
        # BUT, the user wants a general cleanup. Let's check if it's in root.
        in_root = os.path.dirname(filepath) == ''
        if not in_root:
            # If it's already in a folder, check if it needs to be archived
            if decision == '刪除':
                pass # Continue to process for archive
            else:
                continue # Skip organization for already organized files for safety
        
        target_folder = get_target_folder(filename, category, decision, reason)
        
        if target_folder:
            target_path = os.path.join(PROJECT_ROOT, target_folder, filename)
            
            # Don't move if source and target are the same
            if os.path.abspath(full_path) == os.path.abspath(target_path):
                continue
                
            moves.append((full_path, target_path, target_folder))

    # Execute or Report
    report_lines = []
    report_lines.append(f"Organization Report - {datetime.now()}")
    report_lines.append(f"Dry Run: {dry_run}")
    report_lines.append("-" * 30)
    
    for src, dst, folder in moves:
        status = "PENDING"
        if not dry_run:
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                
                # Handle duplicate filename in archive
                if os.path.exists(dst) and folder == 'archive':
                    base, ext = os.path.splitext(os.path.basename(dst))
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_dst = os.path.join(os.path.dirname(dst), f"{base}_{timestamp}{ext}")
                    dst = new_dst
                
                shutil.move(src, dst)
                status = "MOVED"
                
                # Update DB (Optional, but good practice)
                # cursor.execute("UPDATE files SET filepath = ? WHERE filepath = ?", (os.path.relpath(dst, PROJECT_ROOT), os.path.relpath(src, PROJECT_ROOT)))
                
            except Exception as e:
                status = f"ERROR: {e}"
        
        line = f"[{status}] {os.path.basename(src)} -> {folder}/"
        print(line)
        report_lines.append(line)
        
    if not dry_run:
        conn.commit()
    conn.close()
    
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Done. Report saved to {REPORT_PATH}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--execute', action='store_false', dest='dry_run')
    parser.set_defaults(dry_run=True)
    args = parser.parse_args()
    
    main(dry_run=args.dry_run)
