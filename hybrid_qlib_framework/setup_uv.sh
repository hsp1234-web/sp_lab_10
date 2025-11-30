#!/usr/bin/env bash
# UV 環境建置腳本：智能安裝 Linux 版 UV，避免 Windows 版本衝突
# 使用方式：在 WSL 終端機中執行 `bash setup_uv.sh`

set -e  # 發生錯誤立即退出

echo "========================================"
echo "🚀 Hybrid Qlib Framework 環境建置 (UV)"
echo "========================================"

# 1️⃣ 檢查並安裝 Linux 版本的 uv
echo -e "\n🔍 [1/5] 檢查 UV 安裝狀態..."

# 檢查是否存在可執行的 uv（排除 Windows 版本）
UV_PATH=$(which uv 2>/dev/null || echo "")

if [ -n "$UV_PATH" ] && [ -x "$UV_PATH" ] && file "$UV_PATH" | grep -q "ELF"; then
    echo "✅ 已安裝 Linux 版 UV: $UV_PATH"
else
    echo "🔧 未找到可用的 Linux 版 UV，開始安裝..."
    
    # 移除可能存在的 Windows 版 uv 路徑（僅在當前 session）
    export PATH=$(echo $PATH | tr ':' '\n' | grep -v "pyenv-win" | tr '\n' ':')
    
    # 安裝 Linux 版 uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # 重新載入環境變數
    export PATH="$HOME/.local/bin:$PATH"
    
    # 再次檢查
    if command -v uv >/dev/null 2>&1; then
        echo "✅ UV 安裝完成: $(which uv)"
    else
        echo "❌ UV 安裝失敗，請手動執行: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
fi

# 2️⃣ 清理舊的虛擬環境（如果存在且損壞）
echo -e "\n🔧 [2/5] 準備虛擬環境..."
if [ -d ".venv" ] && [ ! -f ".venv/bin/activate" ]; then
    echo "⚠️ 發現損壞的 .venv，正在清理..."
    rm -rf .venv
fi

# 3️⃣ 建立虛擬環境
if [ -d ".venv" ]; then
    echo "✅ .venv 已存在，跳過建立"
else
    echo "🔧 使用 UV 建立虛擬環境..."
    uv venv .venv
    echo "✅ 虛擬環境建立完成"
fi

# 4️⃣ 啟動虛擬環境並安裝相依套件
echo -e "\n📦 [3/5] 安裝相依套件..."
source .venv/bin/activate

if [ -f "requirements.txt" ]; then
    echo "🚀 使用 UV 快速安裝套件（比 pip 快 10-100 倍）..."
    uv pip install -r requirements.txt
    echo "✅ 相依套件安裝完成"
else
    echo "❌ 找不到 requirements.txt"
    exit 1
fi

# 5️⃣ 執行驗證腳本
echo -e "\n🧪 [4/5] 執行驗證腳本..."
if [ -f "verify_setup.sh" ]; then
    chmod +x verify_setup.sh
    ./verify_setup.sh
else
    echo "⚠️ verify_setup.sh 不存在，跳過驗證"
fi

# 6️⃣ 完成
echo -e "\n========================================"
echo "✅ UV 環境建置與驗證全部完成！"
echo "========================================"
echo ""
echo "💡 後續使用方式："
echo "   1. 啟動虛擬環境: source .venv/bin/activate"
echo "   2. 使用 UV 安裝套件: uv pip install <package>"
echo "   3. 執行測試: pytest -v"
echo "   4. 離開虛擬環境: deactivate"
echo ""
echo "🚀 UV 的優勢："
echo "   - 安裝速度比 pip 快 10-100 倍"
echo "   - 自動解決相依性衝突"
echo "   - 完全相容 pip 指令"
