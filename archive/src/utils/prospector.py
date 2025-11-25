# -*- coding: utf-8 -*-
# @title 🚀 智能型期交所數據整合管道 v8.0 (Local Windows Edition)
# Adapted for local usage

import os
import io
import time
import zipfile
import sqlite3
import pytz
import json
import shutil
import hashlib
import threading
from datetime import datetime
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed

# --- Configuration ---
# Define paths relative to this script (src/utils/prospector.py)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET_FOLDER_PATH = os.path.join(PROJECT_ROOT, "data", "taifex_raw")
LOG_DIRECTORY = os.path.join(PROJECT_ROOT, "output", "logs", "prospector_v8")
LOG_DATABASE_NAME = "Prospector_Log_v8.db"
FINAL_REPORT_NAME = "Mission_Report_v8.txt"

ALLOWED_EXTENSIONS = ".txt,.csv,.json,.html,.parquet"
MEMORY_THRESHOLD_PERCENT = 80
USE_PERSISTENT_CACHE = True
ENABLE_PERFORMANCE_TELEMETRY = True
PROSPECT_LINE_COUNT = 10
CONSOLE_PREVIEW_LINE_COUNT = 5
CONSOLE_PREVIEW_SUMMARY_COUNT = 60

# --- Dependencies ---
try:
    import psutil
except ImportError:
    print("⚠️ Warning: 'psutil' not found. Performance telemetry will be limited.")
    psutil = None

# --- Global Settings ---
TAIPEI_TZ = pytz.timezone('Asia/Taipei')
# Use a local temp directory for cache instead of /dev/shm
RAM_CACHE_PATH = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'processing_cache_v8')
DISK_CACHE_PATH = os.path.join(PROJECT_ROOT, 'output', 'cache_v8')
PRINT_LOCK = threading.Lock()

# --- Helper Functions ---
def get_taipei_time_iso(): return datetime.now(TAIPEI_TZ).isoformat()
def get_taipei_time_str(): return datetime.now(TAIPEI_TZ).strftime('%Y-%m-%d %H:%M:%S')
def human_readable_size(b):
    if b == 0: return "0 B"
    n = ["B", "KB", "MB", "GB", "TB"]; i = int(b.bit_length()/10)
    p = 1024**i; s = round(b / p, 2); return f"{s} {n[i]}"
def get_file_hash(file_path):
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while b := f.read(8192): h.update(b)
    return h.hexdigest()

# --- Core Manager Classes ---
class LogManager:
    def __init__(self, db_path):
        self._db_path = db_path; os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=True)
        self._conn.row_factory = sqlite3.Row; self._setup_database()
    def _setup_database(self):
        with self._conn:
            self._conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY, timestamp_iso TEXT, level TEXT, descriptor TEXT,
                message TEXT, cpu_percent REAL, ram_percent REAL)""")
            self._conn.execute("""
            CREATE TABLE IF NOT EXISTS file_cache (
                file_hash TEXT PRIMARY KEY, processing_result TEXT NOT NULL)""")
    def write(self, level, descriptor, message_dict):
        ts = get_taipei_time_iso()
        cpu = psutil.cpu_percent() if psutil and ENABLE_PERFORMANCE_TELEMETRY else None
        ram = psutil.virtual_memory().percent if psutil and ENABLE_PERFORMANCE_TELEMETRY else None
        try:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO logs (timestamp_iso, level, descriptor, message, cpu_percent, ram_percent) VALUES (?, ?, ?, ?, ?, ?)",
                    (ts, level, descriptor, json.dumps(message_dict, ensure_ascii=False), cpu, ram))
        except Exception as e:
            with PRINT_LOCK: print(f"\r[{get_taipei_time_str()}] [FATAL_ERROR] DB Write Failed: {e}", flush=True)
    def get_cached_result(self, file_hash):
        if not USE_PERSISTENT_CACHE: return None
        cursor = self._conn.cursor(); cursor.execute("SELECT processing_result FROM file_cache WHERE file_hash = ?", (file_hash,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None
    def set_cached_result(self, file_hash, result):
        if not USE_PERSISTENT_CACHE: return
        with self._conn: self._conn.execute("REPLACE INTO file_cache (file_hash, processing_result) VALUES (?, ?)", (file_hash, json.dumps(result)))
    def get_all_logs_for_report(self):
        cursor = self._conn.cursor(); cursor.execute("SELECT * FROM logs ORDER BY id ASC"); return cursor.fetchall()
    def close(self): self._conn.close()

class StatusManager:
    def __init__(self):
        self.total_tasks = 0; self.processed_tasks = 0; self.success_count = 0
        self.fail_count = 0; self.cache_hits = 0; self.current_task = "Initializing...";
        self.cache_mode = "RAM"; self._lock = threading.Lock()
    def update(self, **kwargs):
        with self._lock:
            for key, value in kwargs.items(): setattr(self, key, value)
    def get_status(self):
        with self._lock: return self.__dict__.copy()

class StatusMonitor(threading.Thread):
    def __init__(self, status_manager):
        super().__init__(daemon=True); self._status = status_manager; self._stop_event = threading.Event()
    def run(self):
        while not self._stop_event.is_set():
            s = self._status.get_status()
            p = (s['processed_tasks'] / s['total_tasks'] * 100) if s['total_tasks'] > 0 else 0
            cpu_val = psutil.cpu_percent() if psutil else 0
            ram_val = psutil.virtual_memory().percent if psutil else 0
            line = (f"[{get_taipei_time_str()}] [CPU:{cpu_val:>4.1f}%|RAM:{ram_val:>4.1f}%] [Mode:{s['cache_mode']}] "
                    f"[Prog:{s['processed_tasks']:>4}/{s['total_tasks']:<4} ({p:3.0f}%)] "
                    f"[OK:{s['success_count']:>3}|Fail:{s['fail_count']:>3}|Cache:{s['cache_hits']:>3}] "
                    f"| {s['current_task']:.50s}")
            with PRINT_LOCK: print(f"\r{line}", end="", flush=True)
            time.sleep(0.2)
    def stop(self): self._stop_event.set()

class ConsoleLogger:
    def __init__(self, max_previews, preview_lines):
        self._max_previews = max_previews
        self._preview_lines = preview_lines
        self._preview_count = 0
        self._header_printed = False
        self._seen_headers = set()
    def log(self, level, message):
        with PRINT_LOCK: print(f"\r[{get_taipei_time_str()}] [{level.upper()}] {message}", flush=True)
    def log_file_preview(self, result: dict, from_cache=False):
        if result.get('status') != 'success' or not result.get('preview'): return
        if self._preview_count >= self._max_previews: return

        header = result['preview'][0] if result['preview'] else ""
        if header in self._seen_headers: return

        with PRINT_LOCK:
            print("\r", end="")
            if not self._header_printed:
                print("="*80 + f"\n │ File Format Preview (Max {self._max_previews} unique headers)".center(90) + "\n" + "="*80); self._header_printed = True
            cache_tag = "[CACHE] " if from_cache else ""
            report_lines = [
                f"✅ {cache_tag}[Template #{self._preview_count + 1}] File: {result['descriptor']}",
                f"   Size: {result.get('size', 'N/A')}, Encoding: {result.get('encoding', 'N/A')}", "   Preview:"]
            for i, line_text in enumerate(result['preview'][:self._preview_lines]):
                report_lines.append(f"     L{i+1}: {repr(line_text.strip())}")
            report_lines.append("-" * 80); print("\n".join(report_lines), flush=True)

        self._preview_count += 1
        self._seen_headers.add(header)

def prospect_text_content(stream, line_count):
    try:
        # Try to read lines as bytes first
        byte_lines = [stream.readline() for _ in range(line_count)]
        if not any(byte_lines): return {'status': 'success', 'encoding': 'N/A', 'preview': []}
        
        # Try decoding
        for encoding in ['ms950', 'utf-8', 'utf-8-sig', 'cp950']:
            try: 
                return {'status': 'success', 'encoding': encoding, 'preview': [l.decode(encoding) for l in byte_lines if l]}
            except UnicodeDecodeError: continue
        
        # If text decoding fails, maybe it's binary or parquet?
        return {'status': 'failure', 'error_reason': 'Unable to decode with common encodings (ms950, utf-8)'}
    except Exception as e: return {'status': 'failure', 'error_reason': f'Read error: {e}'}

def worker_task(local_path, original_drive_path, line_count):
    all_results = []
    def process_file(file_path, original_path):
        ext = os.path.splitext(file_path)[1].lower()
        if not os.path.exists(file_path):
            all_results.append({'status': 'failure', 'descriptor': original_path, 'error_reason': 'Local cache file missing'})
            return
        size = os.path.getsize(file_path)
        
        # Handle Parquet specifically
        if ext == '.parquet':
             try:
                import pandas as pd
                df = pd.read_parquet(file_path)
                preview = df.head(line_count).to_string().split('\n')
                all_results.append({'status': 'success', 'descriptor': original_path, 'size': human_readable_size(size), 'encoding': 'parquet', 'preview': preview})
                return
             except ImportError:
                 all_results.append({'status': 'failure', 'descriptor': original_path, 'error_reason': 'pandas not installed for parquet'})
                 return
             except Exception as e:
                 all_results.append({'status': 'failure', 'descriptor': original_path, 'error_reason': f'Parquet read error: {e}'})
                 return

        with open(file_path, 'rb') as f: magic_bytes = f.read(4)
        is_zip = magic_bytes.startswith(b'PK\x03\x04')
        
        if ext == '.zip':
            if not is_zip:
                all_results.append({'status': 'failure', 'descriptor': original_path, 'size': human_readable_size(size), 'error_reason': 'Extension is .zip but not a valid ZIP'})
                return
            all_results.append({'status': 'info', 'descriptor': original_path, 'type': 'zip_summary', 'size': human_readable_size(size)})
            temp_dir = f"{file_path}_extracted_{os.getpid()}_{time.time_ns()}"
            try:
                os.makedirs(temp_dir, exist_ok=True)
                with zipfile.ZipFile(file_path, 'r') as zf:
                    for member in zf.infolist():
                        if member.is_dir(): continue
                        member_local_path = zf.extract(member, path=temp_dir)
                        member_original_path = f"{original_path} -> {member.filename}"
                        process_file(member_local_path, member_original_path)
            except zipfile.BadZipFile: all_results.append({'status': 'failure', 'descriptor': original_path, 'error_reason': 'Bad ZIP file'})
            except Exception as e: all_results.append({'status': 'failure', 'descriptor': original_path, 'error_reason': f'Unzip failed: {e}'})
            finally: 
                if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        else:
            result = {'descriptor': original_path, 'size': human_readable_size(size)}
            with open(file_path, 'rb') as f: result.update(prospect_text_content(f, line_count))
            all_results.append(result)
            
    process_file(local_path, original_drive_path)
    return all_results

def generate_summary_report(log_manager, console_logger):
    all_logs = log_manager.get_all_logs_for_report()
    if not all_logs: return ""
    failures, successes = [], []
    for log in all_logs:
        if log['level'] == 'FAILURE': failures.append(log)
        elif log['level'] == 'SUCCESS': successes.append(log)

    failure_reasons = Counter()
    for log in failures:
        try:
            msg_dict = json.loads(log['message']); reason = msg_dict.get('error_reason', 'Unknown Error'); failure_reasons[reason] += 1
        except: failure_reasons['Log Format Error'] += 1

    unique_headers = {}
    for log in successes:
        try:
            msg_dict = json.loads(log['message']); preview_list = msg_dict.get('preview')
            if not preview_list: continue
            header = preview_list[0]
            if header not in unique_headers: unique_headers[header] = log
        except: continue

    report_parts = ["\n\n" + "="*80, " Mission Debriefing ".center(90), "="*80]
    report_parts.append(f"\n[Summary] Total: {len(successes) + len(failures)}, Success: {len(successes)}, Failure: {len(failures)}")
    report_parts.append(f"\n--- Success Format Diversity (Found {len(unique_headers)} unique headers, showing top {CONSOLE_PREVIEW_SUMMARY_COUNT}) ---")
    if unique_headers:
        for i, log in enumerate(list(unique_headers.values())[:CONSOLE_PREVIEW_SUMMARY_COUNT]):
            msg_dict = json.loads(log['message'])
            report_parts.append(f"  ✅ Template #{i+1}: {log['descriptor']}")
            report_parts.append(f"     Size: {msg_dict.get('size', 'N/A')}, Encoding: {msg_dict.get('encoding', 'N/A')}")
    else: report_parts.append("  (No successful files)")

    report_parts.append("\n--- Failure Analysis ---")
    if failure_reasons:
        for reason, count in failure_reasons.most_common(): report_parts.append(f"  ❌ {reason}: {count}")
    else: report_parts.append("  (No failures)")
    report_parts.append("\n" + "="*80)
    summary_text = "\n".join(report_parts)
    console_logger.log("DEBRIEFING", summary_text)
    return summary_text

def generate_final_report(log_manager, console_logger, full_target_path, summary_text):
    report_path = os.path.join(LOG_DIRECTORY, FINAL_REPORT_NAME); os.makedirs(LOG_DIRECTORY, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(summary_text)
        f.write("\n\n" + "="*80 + "\n" + " Detailed Telemetry Log ".center(90) + "\n" + "="*80 + "\n\n")
        for log in log_manager.get_all_logs_for_report():
            ts = datetime.fromisoformat(log['timestamp_iso']).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            perf = ""
            if ENABLE_PERFORMANCE_TELEMETRY and log['cpu_percent'] is not None:
                perf = f"[CPU:{log['cpu_percent']:>5.1f}%|RAM:{log['ram_percent']:>5.1f}%]"
            f.write(f"[{ts}] {perf} [{log['level'].upper():<9}] {log['descriptor']}\n")
            try:
                msg_dict = json.loads(log['message'])
                if log['level'] == 'SUCCESS':
                    f.write(f"  - Details: Size: {msg_dict.get('size', 'N/A')}, Encoding: {msg_dict.get('encoding', 'N/A')}\n")
                    if msg_dict.get('preview'):
                        for i, line in enumerate(msg_dict['preview']): f.write(f"    L{i+1}: {line.strip()}\n")
                elif log['level'] == 'FAILURE': f.write(f"  - Reason: {msg_dict.get('error_reason', 'Unknown')}\n")
                else: f.write(f"  - Message: {msg_dict.get('message', msg_dict)}\n")
            except: f.write(f"  - Raw Message: {log['message']}\n")
            f.write("-" * 20 + "\n")
    console_logger.log('SUCCESS', f'Report generated: {report_path}')

def run_prospector():
    console_logger = ConsoleLogger(CONSOLE_PREVIEW_SUMMARY_COUNT, CONSOLE_PREVIEW_LINE_COUNT)
    log_db_path = os.path.join(LOG_DIRECTORY, LOG_DATABASE_NAME)
    log_manager = LogManager(log_db_path)
    status_manager = StatusManager(); monitor = StatusMonitor(status_manager); monitor.start()

    try:
        status_manager.update(current_task="System Check...")
        console_logger.log('BATTLE', '🚀 Prospector v8.0 (Local) Started...')
        log_manager.write('BATTLE', 'MissionStart', {'message': 'Mission Start v8.0 Local'})
        cpu_cores = os.cpu_count()
        
        if not os.path.isdir(TARGET_FOLDER_PATH):
            console_logger.log('CRITICAL', f"Target path not found: {TARGET_FOLDER_PATH}")
            return

        status_manager.update(current_task="Scanning files...")
        allowed_exts_tuple = tuple(ext.strip().lower() for ext in ALLOWED_EXTENSIONS.split(',')) + ('.zip',)
        drive_tasks = [os.path.join(r, n) for r, _, fs in os.walk(TARGET_FOLDER_PATH) for n in fs if n.lower().endswith(allowed_exts_tuple)]
        
        if not drive_tasks:
            console_logger.log('WARNING', 'No matching files found in target directory.')
            return
            
        status_manager.update(total_tasks=len(drive_tasks))
        console_logger.log('INFO', f"Scan complete. Found {len(drive_tasks)} files.")

        if os.path.exists(RAM_CACHE_PATH): shutil.rmtree(RAM_CACHE_PATH)
        if os.path.exists(DISK_CACHE_PATH): shutil.rmtree(DISK_CACHE_PATH)
        os.makedirs(RAM_CACHE_PATH, exist_ok=True); os.makedirs(DISK_CACHE_PATH, exist_ok=True)
        
        current_cache_mode = 'RAM'; cache_base_path = RAM_CACHE_PATH
        console_logger.log('INFO', f"Starting pipeline with {cpu_cores} workers...")

        with ProcessPoolExecutor(max_workers=cpu_cores) as executor:
            futures = {}; processed_count = 0
            for i, drive_path in enumerate(drive_tasks):
                status_manager.update(current_task=f"Prep: {os.path.basename(drive_path)}", processed_tasks=processed_count)
                
                # Simple RAM check if psutil is available
                if psutil and current_cache_mode == 'RAM' and psutil.virtual_memory().percent > MEMORY_THRESHOLD_PERCENT:
                    msg = f"Memory > {MEMORY_THRESHOLD_PERCENT}%, switching to DISK cache."
                    console_logger.log('WARNING', msg); log_manager.write('WARNING', 'CacheStrategySwitch', {'message': msg})
                    current_cache_mode = 'DISK'; cache_base_path = DISK_CACHE_PATH; status_manager.update(cache_mode='DISK')
                
                try:
                    local_path = os.path.join(cache_base_path, str(time.time_ns()))
                    shutil.copy2(drive_path, local_path)
                    
                    if USE_PERSISTENT_CACHE:
                        file_hash = get_file_hash(local_path)
                        cached_results = log_manager.get_cached_result(file_hash)
                        if cached_results:
                            status_manager.update(cache_hits=status_manager.get_status()['cache_hits'] + 1)
                            log_manager.write('CACHE_HIT', drive_path, {'hash': file_hash[:12]})
                            for r in cached_results:
                                console_logger.log_file_preview(r, from_cache=True)
                                if r.get('status') == 'success': status_manager.update(success_count=status_manager.get_status()['success_count'] + 1)
                                elif r.get('status') == 'failure': status_manager.update(fail_count=status_manager.get_status()['fail_count'] + 1)
                            processed_count += 1; status_manager.update(processed_tasks=processed_count); os.remove(local_path); continue

                    future = executor.submit(worker_task, local_path, drive_path, PROSPECT_LINE_COUNT)
                    futures[future] = (drive_path, local_path, file_hash if USE_PERSISTENT_CACHE else None)
                except Exception as e:
                    console_logger.log('ERROR', f"Prep failed: {drive_path}, {e}"); log_manager.write('ERROR', drive_path, {'error_reason': f'Prep failed: {e}'})
                    status_manager.update(fail_count=status_manager.get_status()['fail_count'] + 1); processed_count += 1

            status_manager.update(current_task="Waiting for workers...")
            for future in as_completed(futures):
                original_path, local_path, file_hash = futures[future]
                try:
                    results = future.result()
                    if USE_PERSISTENT_CACHE: log_manager.set_cached_result(file_hash, results)
                    for r in results:
                        log_manager.write(r.get('status', 'info').upper(), r['descriptor'], r)
                        console_logger.log_file_preview(r)
                        if r.get('status') == 'success': status_manager.update(success_count=status_manager.get_status()['success_count'] + 1)
                        elif r.get('status') == 'failure': status_manager.update(fail_count=status_manager.get_status()['fail_count'] + 1)
                except Exception as e:
                    msg = f"Worker exception: {e}"; console_logger.log('CRITICAL', msg); log_manager.write('CRITICAL', original_path, {'error_reason': msg})
                    status_manager.update(fail_count=status_manager.get_status()['fail_count'] + 1)
                finally:
                    if os.path.exists(local_path): os.remove(local_path)
                    processed_count += 1
                    status_manager.update(processed_tasks=processed_count)
    finally:
        status_manager.update(current_task="Generating Report...", processed_tasks=status_manager.get_status()['total_tasks'])
        time.sleep(0.5); monitor.stop(); monitor.join()
        print("\r", end="")
        summary_text = generate_summary_report(log_manager, console_logger)
        generate_final_report(log_manager, console_logger, TARGET_FOLDER_PATH, summary_text)
        log_manager.close()
        if os.path.exists(RAM_CACHE_PATH): shutil.rmtree(RAM_CACHE_PATH)
        if os.path.exists(DISK_CACHE_PATH): shutil.rmtree(DISK_CACHE_PATH)
        console_logger.log('BATTLE', 'Mission Complete.')

if __name__ == '__main__':
    run_prospector()
