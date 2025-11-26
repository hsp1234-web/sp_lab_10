# -*- coding: utf-8 -*-
import requests
import time
import os
import sys
import random
from datetime import datetime, timedelta
import warnings
from collections import Counter
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Debug setup
try:
    with open("debug_v27.log", "w", encoding='utf-8') as f:
        f.write("Script started\n")
except Exception as e:
    print(f"Failed to init log: {e}")

def debug_log(msg):
    try:
        with open("debug_v27.log", "a", encoding='utf-8') as f:
            f.write(str(msg) + "\n")
    except:
        pass

debug_log("Imports starting")

# Try to import tqdm, fallback to simple print if not available
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, total=None, desc=""):
        print(f"Processing {desc}...")
        return iterable

try:
    from bs4 import BeautifulSoup
    import chardet
except ImportError:
    debug_log("Installing dependencies...")
    os.system("pip install beautifulsoup4 chardet")
    from bs4 import BeautifulSoup
    import chardet

# --- Configuration ---
# Target Directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BASE_FOLDER = os.path.join(PROJECT_ROOT, "data", "taifex_raw")
PROBLEM_FILES_FOLDER = os.path.join(PROJECT_ROOT, "output", "problem_files_v27")

# Download Settings
DOWNLOAD_ANNUAL_REPORTS = True
START_YEAR = 2009
END_YEAR = 2024

# Disable daily specific range for this task, as we want annual bulk
DOWNLOAD_DAILY_RANGE = False 
START_DATE = '2025-05-21' # Not used
END_DATE = '2025-07-03'   # Not used

# Performance
MAX_WORKERS = 16
MIN_DELAY_SECONDS = 0.5
MAX_DELAY_SECONDS = 1.5

# --- Constants ---
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
]
BASE_URL = "https://www.taifex.com.tw"
log_lock = threading.Lock()

def print_banner():
    print("=======================================================================")
    print("       🚀 TAIFEX Data Downloader v27.0 (Local)       ")
    print("=======================================================================\n")

def setup_storage():
    debug_log("Setting up storage")
    print("--- Step 1: Setup Storage ---")
    os.makedirs(BASE_FOLDER, exist_ok=True)
    os.makedirs(PROBLEM_FILES_FOLDER, exist_ok=True)
    print(f"Target Folder: {BASE_FOLDER}")
    print(f"Problem Files: {PROBLEM_FILES_FOLDER}")
    return BASE_FOLDER, PROBLEM_FILES_FOLDER

def decode_content(content):
    try: return content.decode('utf-8-sig')
    except UnicodeDecodeError:
        try: return content.decode('ms950')
        except UnicodeDecodeError:
          try: return content.decode('big5')
          except UnicodeDecodeError:
              return content.decode(chardet.detect(content)['encoding'] or 'utf-8', errors='replace')

def save_direct_file(response_content, file_path_base):
    is_zip = file_path_base.lower().endswith('.zip') or response_content[:4] == b'PK\x03\x04'
    file_ext = 'zip' if is_zip else 'csv'
    file_path = f"{os.path.splitext(file_path_base)[0]}.{file_ext}"
    with open(file_path, 'wb') as f:
        f.write(response_content)
    return 'success', f"Saved as {file_ext.upper()}", file_path

def execute_download(session, task_info, problem_files_folder, retries=3):
    file_path_base = os.path.join(task_info['folder_path'], task_info['file_name_base'])
    time.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))

    for attempt in range(retries):
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS), 'Referer': task_info.get('referer', BASE_URL)}
            if task_info['type'] == 'POST':
                response = session.post(task_info['url'], data=task_info.get('payload', {}), headers=headers, timeout=120)
            else:
                response = session.get(task_info['url'], headers=headers, timeout=120)

            if response.status_code == 200:
                content_disposition = response.headers.get('Content-Disposition', '')
                content_type = response.headers.get('content-type', '').lower()
                url_lower = task_info['url'].lower()

                if 'attachment' in content_disposition or any(mime in content_type for mime in ['zip', 'csv', 'octet-stream']) or url_lower.endswith(('.zip', '.csv')):
                    return save_direct_file(response.content, file_path_base)

                decoded_content = decode_content(response.content)
                if "查無資料" in decoded_content or len(decoded_content.strip()) < 50:
                    return 'not_found', "No data found", ""

                soup = BeautifulSoup(decoded_content, 'html.parser')
                table = soup.find('table', {'class': 'table_f'}) or soup.find('table', {'class': 'table_a'}) or soup.find('table')
                if table:
                    rows = [",".join([td.get_text(strip=True).replace(',', '') for td in tr.find_all(['td', 'th'])]) for tr in table.find_all('tr') if tr.find_all(['td', 'th'])]
                    data_to_save = "\n".join(rows)
                    if data_to_save.strip():
                        file_path = f"{file_path_base}.csv"
                        with open(file_path, 'w', encoding='utf-8-sig') as f: f.write(data_to_save)
                        return 'success', "Parsed HTML table to CSV", file_path

                problem_path = os.path.join(problem_files_folder, f"{task_info['file_name_base']}.raw.html")
                with open(problem_path, 'wb') as f: f.write(response.content)
                return 'fallback', "Unknown content type, saved raw HTML", problem_path

            elif response.status_code == 404:
                return 'not_found', "404 Not Found", ""
            else:
                if attempt < retries - 1: time.sleep(5 * (attempt + 1)); continue
                return 'error', f"Server Error {response.status_code}", ""
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1: time.sleep(5 * (attempt + 1)); continue
            return 'error', f"Request Failed: {e}", ""
    return 'error', 'Max retries reached', ""

def process_task_wrapper(task_info, problem_files_folder):
    with requests.Session() as session:
        os.makedirs(task_info['folder_path'], exist_ok=True)
        base_path = os.path.join(task_info['folder_path'], task_info['file_name_base'])
        # Check for existing files (zip or csv)
        if os.path.exists(f"{base_path}.zip") or os.path.exists(f"{base_path}.csv"):
            return 'exists', "File exists, skipping", f"{base_path}.*", task_info

        status, message, f_path = execute_download(session, task_info, problem_files_folder)
        return status, message, f_path, task_info

def run_downloader():
    debug_log("run_downloader started")
    print_banner()
    base_folder, problem_files_folder = setup_storage()
    
    all_jobs = []

    if DOWNLOAD_ANNUAL_REPORTS:
        try:
            year_range = range(int(START_YEAR), int(END_YEAR) + 1)
            print(f"Mode: Annual Data ({START_YEAR}-{END_YEAR})")
            annual_tasks = {
                'Futures_Daily': {'url': BASE_URL + '/cht/3/futDataDown', 'referer': BASE_URL + '/cht/3/dlFutDailyMarketView'},
            }
            for year in year_range:
                for task_name, params in annual_tasks.items():
                    job = {
                        'task_name': task_name, 'type': 'POST', 'date_str': str(year),
                        'folder_path': base_folder, # Save directly to taifex_raw
                        'file_name_base': f"{task_name}_{year}",
                        'url': params['url'], 'referer': params['referer'],
                        'payload': {'down_type': '2', 'his_year': str(year)}
                    }
                    all_jobs.append(job)
        except (ValueError, TypeError): print("Error: Invalid year format.")

    if not all_jobs: 
        print("No tasks generated.")
        debug_log("No tasks generated")
        return
    
    print(f"Generated {len(all_jobs)} tasks.")
    print(f"Starting parallel download with {MAX_WORKERS} workers...")
    debug_log(f"Starting {len(all_jobs)} tasks")

    results_counter = Counter()
    with tqdm(total=len(all_jobs), desc="Progress") as pbar:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_job = {executor.submit(process_task_wrapper, job, problem_files_folder): job for job in all_jobs}
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                try:
                    status, message, f_path, _ = future.result()
                    results_counter[status] += 1
                    with log_lock:
                        if status == 'error':
                             print(f"  ❌ {job['date_str']} - {job['task_name']}: {message}")
                             debug_log(f"Error: {job['date_str']} - {message}")
                        elif status == 'success':
                             debug_log(f"Success: {job['date_str']}")
                except Exception as exc:
                    results_counter['error'] += 1
                    print(f"  ❌ {job['date_str']}: Exception: {exc}")
                    debug_log(f"Exception: {job['date_str']} - {exc}")
                pbar.update(1)

    print("\n" + "="*50)
    print("Download Complete")
    print(f"Success: {results_counter['success']}")
    print(f"Exists: {results_counter['exists']}")
    print(f"Failed: {results_counter['error']}")
    print(f"Not Found: {results_counter['not_found']}")
    print("="*50)
    debug_log("Finished")

if __name__ == '__main__':
    debug_log("Main block entered")
    try:
        run_downloader()
    except Exception as e:
        debug_log(f"Crash: {e}")
        raise
