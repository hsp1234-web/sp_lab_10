@echo off
chcp 65001 >nul
echo ========================================
echo 📤 上傳專案到 GitHub
echo ========================================
echo.
echo 倉庫: https://github.com/hsp1234-web/sp_lab_v9
echo 分支: v3
echo.

echo 步驟 1/6: 初始化 Git...
git init
echo.

echo 步驟 2/6: 加入所有檔案...
git add .
echo.

echo 步驟 3/6: 提交變更...
git commit -m "v3: Organized backtest project with lo2cin4bt framework"
echo.

echo 步驟 4/6: 重新命名分支為 v3...
git branch -M v3
echo.

echo 步驟 5/6: 設定遠端倉庫...
git remote add origin https://github.com/hsp1234-web/sp_lab_v9.git
echo.

echo 步驟 6/6: 推送到 GitHub...
echo 注意：可能需要輸入 GitHub 帳號密碼或 Token
git push -u origin v3
echo.

echo ========================================
echo ✅ 上傳完成！
echo ========================================
echo.
echo 查看您的專案：
echo https://github.com/hsp1234-web/sp_lab_v9/tree/v3
echo.
pause
