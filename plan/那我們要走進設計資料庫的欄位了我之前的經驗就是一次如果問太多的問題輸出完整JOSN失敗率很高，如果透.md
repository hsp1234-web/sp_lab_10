<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# 那我們要走進設計資料庫的欄位了我之前的經驗就是一次如果問太多的問題輸出完整JOSN失敗率很高，如果透過重複請問的方式一次只問你的問題輸出一個問題然後這樣子才回的去做一個詢問然後多次並且最後做一個統計評估可行性很高但是因為迴圈所以整體處理效率會慢但是後續的這些結果會大幅的上升就算是一些4b甚至是1b以下的這些小模型都可以有很好的效果，

以下是我之前寫的來討論一下

# @title 🤖 階段 3：逐欄位模型分析（穩定模式）

import time
import requests
import subprocess
from tqdm.notebook import tqdm

print("=" * 60)
print("🤖 開始模型分析（逐欄位提問，穩定優先）")
print("=" * 60)

# ===== Ollama 環境檢查與設定 =====

MODEL_NAME = "gemma3:4b"

def ensure_ollama():
    """確保 Ollama 已安裝並啟動"""
    print("\n🔧 檢查 Ollama 環境...")

\# 檢查是否已安裝
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        print(f"✅ Ollama 已安裝：{result.stdout.strip()}")
    except FileNotFoundError:
        print("⬇️ 安裝 Ollama...")
        subprocess.run("curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh", shell=True, check=True)
        print("✅ Ollama 安裝完成")

\# 啟動伺服器（背景執行）
    print("🚀 啟動 Ollama 伺服器...")
    subprocess.run("pkill ollama", shell=True)
    time.sleep(2)
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)

\# 確認伺服器就緒
    for _ in range(10):
        try:
            requests.get("http://127.0.0.1:11434", timeout=2)
            print("✅ Ollama 伺服器已就緒")
            break
        except:
            time.sleep(2)

\# 下載模型
    print(f"⬇️ 確保模型 {MODEL_NAME} 已下載...")
    subprocess.run(["ollama", "pull", MODEL_NAME], check=True)
    print("✅ 模型準備完成")

ensure_ollama()

# ===== 模型呼叫函式 =====

def ask_model(prompt, max_retries=3):
    """呼叫 Ollama 模型並返回清理後的回答"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_ctx": 8192,
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            answer = data.get("response", "").strip()
            tokens = data.get("eval_count", 0)
            return answer, tokens
        except Exception as e:
            if attempt == max_retries - 1:
                return "0", 0  \# 失敗返回 0
            time.sleep(2)
    return "0", 0

# ===== 分類對照表 =====

CATEGORY_MAP = {
    "0": "無法判斷",
    "1": "交易策略",
    "2": "數據處理",
    "3": "分析工具",
    "4": "設定檔案",
    "5": "說明文件",
    "6": "研究筆記",
    "7": "測試程式",
    "8": "過時檔案",
    "9": "第三方程式",
}

# ===== 提示詞設計（帶上下文連貫）=====

def get_prompt_summary(filename, filepath, content):
    """欄位 1：Summary 提示詞"""
    return f"""你是專業的程式碼分析助手。請用一句繁體中文描述這個檔案的主要功能。

要求：

- 不超過 30 個字
- 不要說「這個檔案是...」開頭，直接說功能
- 如果無法判斷，回答：0

檔案名稱：{filename}
檔案路徑：{filepath}
檔案內容（前 2000 字）：
{content[:2000]}

你的一句話描述（不超過30字，無法判斷寫0）："""

def get_prompt_category(filename, summary):
    """欄位 2：Category 提示詞（帶 Summary 上下文）"""
    return f"""基於以下資訊，判斷檔案的分類。

檔案：{filename}
功能描述：{summary}

請從以下選項中選擇「一個」最適合的編號：
0 = 無法判斷（內容不足或模糊）
1 = 交易策略（策略邏輯、回測引擎、訊號生成）
2 = 數據處理（資料載入、清洗、轉換、資料庫操作）
3 = 分析工具（視覺化、報表生成、圖表繪製）
4 = 設定檔案（config, yaml, json 等設定）
5 = 說明文件（README, 教學文件、使用指南）
6 = 研究筆記（研究素材、想法紀錄、筆記）
7 = 測試程式（test_xxx.py, 單元測試）
8 = 過時檔案（舊版本、已棄用、備份檔）
9 = 第三方程式（外部專案、第三方函式庫）

只回答一個數字（0-9）："""

def get_prompt_keep(filename, summary, category):
    """欄位 3：Keep Decision 提示詞（帶完整上下文）"""
    return f"""基於以下資訊，判斷是否應該保留這個檔案。

檔案：{filename}
功能：{summary}
分類：{category}

判斷標準：

- 保留：核心功能、最新版本、有價值的研究、重要文件
- 刪除：重複檔案、舊版本、測試殘留、產出檔案、過時內容
- 0：無法判斷（需要更多資訊）

只回答三個選項之一：「保留」、「刪除」或「0」："""

def get_prompt_reason(filename, summary, category, keep_decision):
    """欄位 4：Reason 提示詞（帶所有前置上下文）"""
    return f"""說明為什麼做出這個決定。

檔案：{filename}
功能：{summary}
分類：{category}
決定：{keep_decision}

要求：

- 用一句話說明理由（不超過 20 字）
- 不要重複說「因為...」，直接說理由
- 如果無法說明，回答：0

範例：

- 「核心回測引擎，持續維護」
- 「舊版已被 v2 取代」
- 「重複檔案，內容相同」

你的理由（不超過20字，無法說明寫0）："""

def get_prompt_confidence(filename, summary, category, keep_decision, reason):
    """欄位 5：Confidence 提示詞（帶完整分析上下文）"""
    return f"""評估你對這次分析的信心程度。

檔案：{filename}
分析結果：
  功能：{summary}
  分類：{category}
  決定：{keep_decision}
  理由：{reason}

信心程度：
A = 高信心（檔案內容清晰，判斷明確可靠）
B = 中信心（內容部分模糊，但判斷合理）
C = 低信心（檔案內容不足，建議人工確認）
0 = 無法評估

只回答 A、B、C 或 0："""

# ===== 執行分析 =====

conn = DB_CONN
cursor = conn.cursor()

# 取得需要分析的檔案（排除重複與已自動分類的核心檔案）

cursor.execute("""
SELECT id, filepath, filename, content_text, auto_category
FROM files
WHERE is_duplicate = 0
  AND id NOT IN (SELECT file_id FROM analysis)
ORDER BY filepath
""")
files_to_analyze = cursor.fetchall()

print(f"\n📊 需分析檔案：{len(files_to_analyze)} 個")
print("⏳ 預估時間：約 {:.0f} 分鐘\n".format(len(files_to_analyze) * 0.5))

total_tokens = 0
start_time = time.time()

for idx, (file_id, filepath, filename, content, auto_category) in enumerate(tqdm(files_to_analyze, desc="分析進度", unit="檔"), 1):

file_start = time.time()
    file_tokens = 0

try:
        \# ===== 欄位 1: Summary =====
        prompt = get_prompt_summary(filename, filepath, content)
        summary, tokens = ask_model(prompt)
        file_tokens += tokens

\# ===== 欄位 2: Category（帶 Summary 上下文）=====
        prompt = get_prompt_category(filename, summary)
        category_id, tokens = ask_model(prompt)
        file_tokens += tokens

\# 清理並驗證 category_id
        category_id = category_id.strip()
        if category_id not in CATEGORY_MAP:
            category_id = "0"
        category_name = CATEGORY_MAP[category_id]

\# ===== 欄位 3: Keep Decision（帶完整上下文）=====
        prompt = get_prompt_keep(filename, summary, category_name)
        keep_decision, tokens = ask_model(prompt)
        file_tokens += tokens
        keep_decision = keep_decision.strip()

\# ===== 欄位 4: Reason（帶所有前置上下文）=====
        prompt = get_prompt_reason(filename, summary, category_name, keep_decision)
        reason, tokens = ask_model(prompt)
        file_tokens += tokens

\# ===== 欄位 5: Confidence（帶完整分析結果）=====
        prompt = get_prompt_confidence(filename, summary, category_name, keep_decision, reason)
        confidence, tokens = ask_model(prompt)
        file_tokens += tokens
        confidence = confidence.strip().upper()
        if confidence not in ['A', 'B', 'C', '0']:
            confidence = 'B'

\# 計算處理時間
        file_time = time.time() - file_start
        total_tokens += file_tokens

\# 存入資料庫
        cursor.execute("""
        INSERT OR REPLACE INTO analysis
        (file_id, summary, category, category_id, keep_decision, reason,
         confidence, tokens_used, analysis_time_seconds, analyzed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id, summary, category_name, int(category_id), keep_decision,
            reason, confidence, file_tokens, file_time,
            time.time()
        ))

\# 每 10 個檔案 commit 一次
        if idx % 10 == 0:
            conn.commit()

\# 顯示進度（每 5 個檔案顯示一次詳細資訊）
        if idx % 5 == 0 or idx == 1:
            print(f"\n[{idx}/{len(files_to_analyze)}] {filename}")
            print(f"  📝 {summary}")
            print(f"  🏷️  {category_name} | {keep_decision} | 信心:{confidence}")

except Exception as e:
        print(f"\n⚠️ 檔案分析失敗：{filename}")
        print(f"   錯誤：{e}")
        \# 記錄失敗但繼續
        cursor.execute("""
        INSERT OR REPLACE INTO analysis
        (file_id, summary, category, keep_decision, reason, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (file_id, "分析失敗", "無法判斷", "0", str(e), "C"))

conn.commit()

# ===== 最終統計 =====

total_time = time.time() - start_time
print("\n" + "=" * 60)
print("📊 分析完成統計：")
print(f"   總檔案：{len(files_to_analyze)}")
print(f"   總耗時：{total_time/60:.1f} 分鐘")
print(f"   平均速度：{total_time/len(files_to_analyze):.1f} 秒/檔")
print(f"   Token 消耗：{total_tokens:,}")
print("=" * 60)

# @title 📂 階段 2：檔案掃描與預處理

import os
import json
import hashlib
from datetime import datetime
from tqdm.notebook import tqdm

print("=" * 60)
print("📂 開始檔案掃描與預處理")
print("=" * 60)

# ===== 智慧排除規則 =====

EXCLUDE_PATTERNS = [
    "archive/",
    "lo2cin4bt-main/",
    "output/",
    "__pycache__/",
    ".git/",
    ".ipynb_checkpoints/",
    "node_modules/",
]

EXCLUDE_EXTENSIONS = [
    ".pyc", ".pyo", ".pyd",
    ".db", ".sqlite", ".sqlite3",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp",
    ".mp4", ".avi", ".mov",
    ".zip", ".tar", ".gz",
]

# ===== 自動分類規則（基於路徑）=====

AUTO_CATEGORY_RULES = {
    "archive/": "過時檔案",
    "tests/": "測試程式",
    "test/": "測試程式",
    "docs/": "說明文件",
    "scripts/": "分析工具",
    "src/": "交易策略",
    "research/": "研究筆記",
    "config/": "設定檔案",
    "utils/": "分析工具",
}

# ===== 工具函式 =====

def should_exclude(filepath):
    """檢查是否應排除此檔案"""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in filepath:
            return True

ext = os.path.splitext(filepath)[1].lower()
    if ext in EXCLUDE_EXTENSIONS:
        return True

return False

def get_auto_category(filepath):
    """基於路徑自動分類"""
    for path_pattern, category in AUTO_CATEGORY_RULES.items():
        if path_pattern in filepath:
            return category
    return None

def convert_ipynb_to_text(filepath):
    """將 .ipynb 轉換為純文字"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            notebook = json.load(f)

text_parts = []
        for cell in notebook.get('cells', []):
            cell_type = cell.get('cell_type')
            source = ''.join(cell.get('source', []))

if cell_type == 'code':
                text_parts.append(f"\# CODE CELL\n{source}\n")
            elif cell_type == 'markdown':
                text_parts.append(f"\# MARKDOWN\n{source}\n")

return '\n'.join(text_parts)
    except Exception as e:
        return f"[無法解析 Notebook: {e}]"

def read_file_content(filepath):
    """讀取檔案內容並轉換為純文字"""
    file_ext = os.path.splitext(filepath)[1].lower()

try:
        if file_ext == '.ipynb':
            return convert_ipynb_to_text(filepath)
        else:
            \# 一般文字檔
            encodings = ['utf-8', 'utf-8-sig', 'cp950', 'big5']
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue

\# 如果所有編碼都失敗，使用 ignore 模式
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        return f"[讀取錯誤: {e}]"

def calculate_hash(content):
    """計算內容的 SHA256 hash"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

# ===== 掃描專案檔案 =====

print("\n🔍 正在掃描專案資料夾...")
all_files = []
target_extensions = ['.py', '.ipynb', '.md', '.txt', '.json', '.yaml', '.yml']

for root, dirs, files in os.walk(PROJECT_ROOT):
    \# 修改 dirs 列表來跳過排除的資料夾
    dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]

for filename in files:
        filepath = os.path.join(root, filename)
        rel_path = os.path.relpath(filepath, PROJECT_ROOT)

\# 檢查是否應排除
        if should_exclude(rel_path):
            continue

\# 檢查副檔名
        ext = os.path.splitext(filename)[1].lower()
        if ext not in target_extensions:
            continue

all_files.append({
            'filepath': rel_path,
            'filename': filename,
            'file_type': ext,
            'full_path': filepath
        })

print(f"✅ 找到 {len(all_files)} 個目標檔案")

# ===== 處理檔案並入庫 =====

print("\n📝 開始處理檔案...")
conn = DB_CONN
cursor = conn.cursor()

processed_hashes = {}  \# 用於偵測重複檔案
duplicate_count = 0

for file_info in tqdm(all_files, desc="處理檔案", unit="檔"):
    filepath = file_info['filepath']
    filename = file_info['filename']
    file_type = file_info['file_type']
    full_path = file_info['full_path']

\# 讀取檔案內容
    content = read_file_content(full_path)
    char_count = len(content)
    file_size = os.path.getsize(full_path)

\# 計算 hash
    content_hash = calculate_hash(content)

\# 檢查是否重複
    is_duplicate = 0
    if content_hash in processed_hashes:
        is_duplicate = 1
        duplicate_count += 1
    else:
        processed_hashes[content_hash] = filepath

\# 自動分類
    auto_category = get_auto_category(filepath)

\# 存入資料庫
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO files
        (filepath, filename, file_type, file_size, content_text, char_count,
         content_hash, is_duplicate, auto_category, preprocessed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            filepath, filename, file_type, file_size, content, char_count,
            content_hash, is_duplicate, auto_category, datetime.now().isoformat()
        ))
    except Exception as e:
        print(f"\n⚠️ 無法插入檔案 {filename}: {e}")

conn.commit()

# ===== 統計資訊 =====

print("\n📊 預處理統計：")
print(f"   總檔案數：{len(all_files)}")
print(f"   重複檔案：{duplicate_count}")

cursor.execute("SELECT auto_category, COUNT(*) FROM files WHERE auto_category IS NOT NULL GROUP BY auto_category")
auto_categorized = cursor.fetchall()
print(f"\n   自動分類檔案：")
for cat, count in auto_categorized:
    print(f"      - {cat}: {count}")

cursor.execute("SELECT COUNT(*) FROM files WHERE auto_category IS NULL AND is_duplicate = 0")
need_analysis = cursor.fetchone()[0]
print(f"\n   需模型分析：{need_analysis} 個檔案")

print("\n" + "=" * 60)
print("🎯 階段 2 完成！準備進入模型分析階段。")
print("=" * 60)

您的實踐經驗非常寶貴！**逐欄位提問 + 上下文累積**的設計確實比一次性JSON輸出穩定得多，這個發現對本地小模型交易系統設計至關重要。我們來將這套方法應用到交易決策系統上。[^1][^2]

## 為什麼逐欄位提問更可靠

### 技術原因

- **降低生成複雜度**：小模型難以同時處理「理解問題+格式化輸出+多維度推理」，分解任務讓每步專注單一目標
- **減少格式錯誤**：只需輸出單一值（數字/關鍵字），避免JSON語法錯誤、括號不匹配等
- **上下文累積**：後續問題能參考前面的答案，形成「推理鏈」，模仿人類分析師的思考流程
- **容錯性高**：單一欄位失敗不影響其他欄位，可設定預設值繼續


## 交易系統資料庫欄位設計（配合逐欄位分析）

### 核心表：`ai_trading_analysis`

```sql
CREATE TABLE ai_trading_analysis (
    -- 基本資訊
    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    
    -- ==== 階段1：市場環境判斷（3個獨立欄位）====
    market_regime VARCHAR(20),      -- 問題1：Bull/Bear/Sideways/Unknown
    market_regime_confidence CHAR(1), -- 問題2：A/B/C (高/中/低信心)
    volatility_level VARCHAR(10),   -- 問題3：Low/Medium/High/Extreme
    
    -- ==== 階段2：技術面評分（4個獨立欄位）====
    trend_score INTEGER,            -- 問題4：趨勢分數 0-100
    momentum_score INTEGER,         -- 問題5：動能分數 0-100
    support_resistance_score INTEGER, -- 問題6：支撐壓力分數 0-100
    technical_summary VARCHAR(50),  -- 問題7：技術面一句話總結
    
    -- ==== 階段3：風險評估（3個獨立欄位）====
    risk_level VARCHAR(10),         -- 問題8：Low/Medium/High
    max_position_pct REAL,          -- 問題9：建議最大倉位 0-1
    stop_loss_pct REAL,             -- 問題10：建議止損比例
    
    -- ==== 階段4：交易決策（4個獨立欄位）====
    action VARCHAR(10),             -- 問題11：BUY/SELL/HOLD/REDUCE
    target_position_pct REAL,       -- 問題12：目標倉位百分比 0-1
    decision_confidence CHAR(1),    -- 問題13：決策信心 A/B/C
    reasoning VARCHAR(100),         -- 問題14：決策理由簡述
    
    -- ==== 執行記錄 ====
    total_tokens_used INTEGER,
    total_analysis_time REAL,
    model_used VARCHAR(50),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(date, symbol)
);
```


### 輔助表：`market_indicators`（預先計算好的指標）

```sql
CREATE TABLE market_indicators (
    date DATE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    
    -- 價格數據
    close_price REAL,
    daily_return REAL,
    
    -- 技術指標（預先計算）
    sma_20 REAL,
    sma_50 REAL,
    sma_200 REAL,
    rsi_14 REAL,
    macd REAL,
    macd_signal REAL,
    atr_14 REAL,
    
    -- 市場環境
    spy_return REAL,
    vix_close REAL,
    sector_relative_strength REAL,
    
    -- 預處理摘要（給AI看的濃縮資訊）
    indicators_summary TEXT,  -- JSON格式的關鍵指標摘要
    
    PRIMARY KEY (date, symbol)
);
```


## 逐欄位提問流程設計

### 階段1：市場環境判斷

```python
def analyze_market_environment(date, symbol):
    """階段1：3個獨立問題判斷市場環境"""
    
    # 取得預處理指標
    indicators = get_indicators_summary(date, symbol)
    
    # 問題1：市場趨勢
    prompt_1 = f"""分析當前市場趨勢狀態。

數據：
- SPY近5日報酬: {indicators['spy_5d_return']:.2%}
- SMA50 vs SMA200: {indicators['sma_50']} vs {indicators['sma_200']}
- {symbol}相對SPY: {indicators['relative_strength']:.2%}

只回答以下之一：Bull / Bear / Sideways / Unknown"""
    
    market_regime = ask_model(prompt_1, max_tokens=10)
    
    # 問題2：信心度（帶上問題1的答案）
    prompt_2 = f"""你剛才判斷市場為「{market_regime}」。

評估這個判斷的信心程度：
- 數據是否充足？
- 訊號是否明確？
- 是否有矛盾指標？

只回答：A（高信心）/ B（中信心）/ C（低信心）"""
    
    confidence = ask_model(prompt_2, max_tokens=5)
    
    # 問題3：波動率水平
    prompt_3 = f"""評估當前波動率水平。

數據：
- VIX: {indicators['vix']:.1f}
- ATR(14): {indicators['atr_14']:.2f}
- 近20日波動率: {indicators['realized_vol_20d']:.2%}

只回答：Low / Medium / High / Extreme"""
    
    volatility = ask_model(prompt_3, max_tokens=10)
    
    return {
        'market_regime': market_regime,
        'market_regime_confidence': confidence,
        'volatility_level': volatility
    }
```


### 階段2：技術面評分

```python
def analyze_technical_scores(date, symbol, market_context):
    """階段2：4個獨立問題評估技術面（帶市場環境上下文）"""
    
    indicators = get_indicators_summary(date, symbol)
    
    # 問題4：趨勢分數
    prompt_4 = f"""當前市場為「{market_context['market_regime']}」，波動率「{market_context['volatility_level']}」。

評估 {symbol} 的趨勢強度：
- SMA20 vs 收盤價: {indicators['price_vs_sma20']:.2%}
- SMA50 vs SMA200: {"黃金交叉" if indicators['sma_50'] > indicators['sma_200'] else "死亡交叉"}
- 價格位置: 距離52週高點 {indicators['dist_to_52w_high']:.1%}

給出0-100分（0=極弱下跌，50=中性，100=極強上漲）："""
    
    trend_score = int(ask_model(prompt_4, max_tokens=5) or "50")
    
    # 問題5：動能分數（帶趨勢分數上下文）
    prompt_5 = f"""趨勢分數為 {trend_score}/100。

評估短期動能：
- RSI(14): {indicators['rsi_14']:.1f}
- MACD狀態: {indicators['macd_status']}
- 成交量相對平均: {indicators['volume_ratio']:.1f}x

給出0-100分（結合趨勢判斷動能是否過熱/過冷）："""
    
    momentum_score = int(ask_model(prompt_5, max_tokens=5) or "50")
    
    # 問題6：支撐壓力分數
    prompt_6 = f"""趨勢{trend_score}分，動能{momentum_score}分。

評估當前位置的支撐壓力：
- 距離關鍵支撐: {indicators['dist_to_support']:.2%}
- 距離關鍵壓力: {indicators['dist_to_resistance']:.2%}
- 均線支撐強度: {indicators['ma_support_strength']}

給出0-100分（0=壓力區易跌，50=中性，100=支撐區易漲）："""
    
    sr_score = int(ask_model(prompt_6, max_tokens=5) or "50")
    
    # 問題7：技術面總結
    prompt_7 = f"""綜合以上分析：
- 市場: {market_context['market_regime']}
- 趨勢: {trend_score}/100
- 動能: {momentum_score}/100
- 支撐壓力: {sr_score}/100

用一句話總結技術面（不超過20字，不要「總結是」開頭）："""
    
    technical_summary = ask_model(prompt_7, max_tokens=30)
    
    return {
        'trend_score': trend_score,
        'momentum_score': momentum_score,
        'support_resistance_score': sr_score,
        'technical_summary': technical_summary
    }
```


### 階段3：風險評估

```python
def assess_risk_parameters(date, symbol, market_context, technical_scores):
    """階段3：3個問題決定風險參數（帶完整上下文）"""
    
    # 問題8：風險等級
    prompt_8 = f"""基於以下分析，評估當前風險等級：

市場環境：
- 趨勢: {market_context['market_regime']} (信心:{market_context['market_regime_confidence']})
- 波動率: {market_context['volatility_level']}

技術面：
- 趨勢分數: {technical_scores['trend_score']}/100
- 動能分數: {technical_scores['momentum_score']}/100
- 總結: {technical_scores['technical_summary']}

只回答：Low / Medium / High"""
    
    risk_level = ask_model(prompt_8, max_tokens=10)
    
    # 問題9：最大倉位（帶風險等級上下文）
    prompt_9 = f"""風險等級為「{risk_level}」。

根據以下規則建議最大倉位：
- Low風險 → 可考慮 15-25%
- Medium風險 → 建議 8-15%
- High風險 → 應限制 3-8%

當前市場波動率: {market_context['volatility_level']}

只回答一個小數（例如 0.15 代表15%）："""
    
    max_position = float(ask_model(prompt_9, max_tokens=10) or "0.10")
    
    # 問題10：止損比例
    prompt_10 = f"""風險{risk_level}，最大倉位{max_position*100:.0f}%。

根據ATR和支撐位建議止損：
- ATR(14): {get_atr(date, symbol):.2f}
- 下方支撐距離: {get_support_distance(date, symbol):.2%}

只回答止損百分比小數（例如 0.05 代表5%止損）："""
    
    stop_loss = float(ask_model(prompt_10, max_tokens=10) or "0.05")
    
    return {
        'risk_level': risk_level,
        'max_position_pct': max_position,
        'stop_loss_pct': stop_loss
    }
```


### 階段4：最終決策

```python
def make_trading_decision(date, symbol, all_context):
    """階段4：4個問題做出交易決策（帶完整分析鏈）"""
    
    # 問題11：交易動作
    prompt_11 = f"""基於完整分析做出交易決策。

市場環境：{all_context['market_regime']}，波動率{all_context['volatility_level']}
技術面：趨勢{all_context['trend_score']}/100，動能{all_context['momentum_score']}/100
風險：{all_context['risk_level']}風險，最大倉位{all_context['max_position_pct']*100:.0f}%

當前持倉：{get_current_position(symbol)*100:.0f}%

只回答以下之一：BUY（買入/加倉）/ SELL（賣出）/ HOLD（持有）/ REDUCE（減倉）"""
    
    action = ask_model(prompt_11, max_tokens=10)
    
    # 問題12：目標倉位（帶動作上下文）
    prompt_12 = f"""決定「{action}」。

當前倉位: {get_current_position(symbol)*100:.0f}%
最大倉位限制: {all_context['max_position_pct']*100:.0f}%
現金可用: {get_available_cash()*100:.0f}%

給出目標倉位百分比小數（例如 0.12 代表12%）："""
    
    target_position = float(ask_model(prompt_12, max_tokens=10) or "0")
    
    # 問題13：決策信心
    prompt_13 = f"""評估這個決策的信心程度。

決策：{action} → 目標倉位{target_position*100:.0f}%
市場信心：{all_context['market_regime_confidence']}
技術面匹配度：趨勢{all_context['trend_score']}/100
風險等級：{all_context['risk_level']}

這個決策的整體信心：A（高）/ B（中）/ C（低）"""
    
    decision_confidence = ask_model(prompt_13, max_tokens=5)
    
    # 問題14：決策理由
    prompt_14 = f"""簡述為何做出這個決策。

決策：{action}
核心依據：市場{all_context['market_regime']}、技術{all_context['technical_summary']}、風險{all_context['risk_level']}

用一句話說明（不超過30字，直接說理由）："""
    
    reasoning = ask_model(prompt_14, max_tokens=50)
    
    return {
        'action': action,
        'target_position_pct': target_position,
        'decision_confidence': decision_confidence,
        'reasoning': reasoning
    }
```


## 完整執行流程

```python
def run_trading_analysis_pipeline(date, symbol):
    """完整14步驟分析流程"""
    
    start_time = time.time()
    total_tokens = 0
    
    # 預先計算所有技術指標（不用AI）
    precompute_indicators(date, symbol)
    
    # 階段1：市場環境（3問）
    market_ctx = analyze_market_environment(date, symbol)
    
    # 階段2：技術評分（4問）
    technical_ctx = analyze_technical_scores(date, symbol, market_ctx)
    
    # 階段3：風險評估（3問）
    risk_ctx = assess_risk_parameters(date, symbol, market_ctx, technical_ctx)
    
    # 階段4：交易決策（4問）
    all_context = {**market_ctx, **technical_ctx, **risk_ctx}
    decision = make_trading_decision(date, symbol, all_context)
    
    # 合併結果並存入資料庫
    final_result = {
        **market_ctx,
        **technical_ctx,
        **risk_ctx,
        **decision,
        'total_tokens_used': total_tokens,
        'total_analysis_time': time.time() - start_time,
        'model_used': MODEL_NAME
    }
    
    save_to_database(date, symbol, final_result)
    
    return final_result
```


## 關鍵優化建議

### 1. 批量處理策略

```python
# 每支股票14個問題，50支股票就是700次API呼叫
# 使用並行處理加速（但要注意Ollama本地限制）
from concurrent.futures import ThreadPoolExecutor

def batch_analyze_portfolio(date, symbols):
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(
            lambda sym: run_trading_analysis_pipeline(date, sym),
            symbols
        ))
    return results
```


### 2. 快取機制

```python
# 市場環境判斷結果可快取（同一天所有股票共用）
@lru_cache(maxsize=100)
def analyze_market_environment_cached(date):
    # 只計算一次，多支股票共用
    return analyze_market_environment(date, 'SPY')
```


### 3. 錯誤處理與預設值

```python
def ask_model_safe(prompt, expected_type='str', default_value=None):
    """安全的模型呼叫，失敗返回預設值"""
    try:
        response = ask_model(prompt)
        if expected_type == 'int':
            return int(response) if response.isdigit() else default_value
        elif expected_type == 'float':
            return float(response) if response.replace('.','').isdigit() else default_value
        return response
    except:
        return default_value
```


## 效能估算

以您的經驗為基礎：

- **單檔案分析**：5個欄位約30秒（gemma3:4b）
- **單股票分析**：14個欄位約60-90秒
- **50支股票組合**：若串行需50-75分鐘，並行3執行緒約20-30分鐘

這個設計充分借鑑您的成功經驗，將複雜決策分解為14個簡單問題，每個問題都帶著前面的上下文累積推理，即使使用1B-4B小模型也能獲得穩定可靠的結果。需要我針對某個階段提供更詳細的提示詞範例或錯誤處理機制嗎？[^2][^1]

<div align="center">⁂</div>

[^1]: Reference_Formats.md

[^2]: Colab_MVP_Implementation.md

