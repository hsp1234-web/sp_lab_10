#!/usr/bin/env bash
# 簡化版環境建置腳本：使用 Python 內建 venv
# 使用方式：在 WSL 終端機中執行 `bash setup_simple.sh`

set -e  # 發生錯誤立即退出

echo "========================================"
echo "🚀 Hybrid Qlib Framework 環境建置"
echo "========================================"

# 1️⃣ 檢查 Python 版本
echo -e "\n🔍 [1/5] 檢查 Python 版本..."
python3 --version

# 2️⃣ 建立虛擬環境（使用 Python 內建 venv）
if [ -d ".venv" ]; then
    echo -e "\n🔧 [2/5] 已存在 .venv，跳過建立"
else
    echo -e "\n🔧 [2/5] 建立虛擬環境 .venv..."
    python3 -m venv .venv
    echo "✅ 虛擬環境建立完成"
fi

# 3️⃣ 啟動虛擬環境
echo -e "\n🔧 [3/5] 啟動虛擬環境..."
source .venv/bin/activate

# 4️⃣ 升級 pip 並安裝相依套件
echo -e "\n📦 [4/5] 安裝相依套件..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ 相依套件安裝完成"

# 5️⃣ 執行驗證腳本
echo -e "\n🧪 [5/5] 執行驗證腳本..."
chmod +x verify_setup.sh
./verify_setup.sh

echo -e "\n========================================"
echo "✅ 環境建置與驗證全部完成！"
echo "========================================"
echo ""
echo "💡 後續使用方式："
echo "   1. 啟動虛擬環境: source .venv/bin/activate"
echo "   2. 執行測試: pytest -v"
echo "   3. 離開虛擬環境: deactivate"
