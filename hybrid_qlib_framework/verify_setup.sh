#!/bin/bash
# 驗證腳本：一次性執行所有測試與檢查
# 使用方式：在 WSL 終端機中執行 `bash verify_setup.sh`

set -e  # 若有錯誤立即停止

echo "========================================"
echo "🚀 Hybrid Qlib Framework 驗證程序"
echo "========================================"

# 1. 環境檢查
echo -e "\n🔍 [1/4] 檢查環境..."
python3 --version
pip list | grep -E "duckdb|pandas|pytest" || echo "⚠️  部分套件可能未安裝，請確認環境"

# 2. 準備測試資料
echo -e "\n📊 [2/4] 準備測試資料..."
# 使用相對路徑，確保可攜性
# 假設 taifex.db 在 ../data/taifex.db 或 ./data/taifex.db
python3 scripts/prepare_test_data.py --output-dir ./data/test --month 2024-01

# 3. 執行單元測試
echo -e "\n🧪 [3/4] 執行單元測試..."
python3 -m pytest tests/ -v

# 4. 測試 CLI 功能
echo -e "\n🛠️  [4/4] 測試 CLI 功能..."
# 測試 Help
python3 main.py --help > /dev/null
echo "   - CLI Help: OK"

# 測試轉換功能 (Dry Run)
TEST_PARQUET="./data/test/test_data_2024_01.parquet"
if [ -f "$TEST_PARQUET" ]; then
    python3 main.py convert --input-file "$TEST_PARQUET" --output-dir ./data/bin/test --test-only
    echo "   - Data Convert: OK"
else
    echo "❌ 錯誤：找不到測試資料 $TEST_PARQUET"
    exit 1
fi

echo -e "\n========================================"
echo "✅ 所有驗證步驟完成！"
echo "========================================"
