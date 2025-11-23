@echo off
chcp 65001 >nul
echo ========================================
echo 🗂️  專案檔案整理
echo ========================================
echo.

echo 📁 建立新目錄...
mkdir scripts 2>nul
mkdir output\logs 2>nul
mkdir output\summaries 2>nul
mkdir src\backtest 2>nul
echo    ✅ 目錄建立完成
echo.

echo 📦 移動回測腳本...
if exist demo_run.py move /Y demo_run.py src\backtest\ >nul && echo    ✅ demo_run.py
if exist full_analysis.py move /Y full_analysis.py src\backtest\ >nul && echo    ✅ full_analysis.py
if exist quick_analysis.py move /Y quick_analysis.py src\backtest\ >nul && echo    ✅ quick_analysis.py
if exist check_columns.py move /Y check_columns.py src\backtest\ >nul && echo    ✅ check_columns.py
if exist analyze_results.py move /Y analyze_results.py src\backtest\ >nul && echo    ✅ analyze_results.py
echo.

echo 🔧 移動 WSL 設定腳本...
if exist setup_wsl.sh move /Y setup_wsl.sh scripts\ >nul && echo    ✅ setup_wsl.sh
if exist setup_wsl_venv.sh move /Y setup_wsl_venv.sh scripts\ >nul && echo    ✅ setup_wsl_venv.sh
echo.

echo 📊 移動日誌和摘要...
if exist demo_run.log move /Y demo_run.log output\logs\ >nul && echo    ✅ demo_run.log
if exist demo_summary.txt move /Y demo_summary.txt output\summaries\ >nul && echo    ✅ demo_summary.txt
echo.

echo 🧹 清理虛擬環境...
if exist .venv_lo2cin4bt rmdir /S /Q .venv_lo2cin4bt 2>nul && echo    ✅ .venv_lo2cin4bt
if exist .venv_std rmdir /S /Q .venv_std 2>nul && echo    ✅ .venv_std
if exist .venv_wsl rmdir /S /Q .venv_wsl 2>nul && echo    ✅ .venv_wsl
if exist __pycache__ rmdir /S /Q __pycache__ 2>nul && echo    ✅ __pycache__
echo.

echo ========================================
echo ✅ 整理完成！
echo ========================================
echo.
echo 📋 根目錄檔案：
dir /B /A-D
echo.
echo 🎯 後續使用：
echo    執行回測: python src\backtest\demo_run.py
echo    分析結果: python src\backtest\full_analysis.py
echo.
pause
