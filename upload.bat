@echo off
:: 啟用 conda 環境（可選）
:: call conda activate your-env-name

:: 顯示目前 git 狀態
echo ========== Git Status ==========
git status

:: 請使用者輸入 commit 訊息
set /p commit_msg=請輸入 commit 訊息：

:: 加入所有變更
echo.
echo 🔄 加入所有修改中...
git add .

:: 提交變更
echo 💾 提交中...
git commit -m "%commit_msg%"

:: 拉取遠端最新變更（避免衝突）
echo 🌐 拉取遠端版本...
git pull origin main

:: 推送到遠端
echo 🚀 推送中...
git push origin main

echo.
echo ✅ 上傳完成！
pause
