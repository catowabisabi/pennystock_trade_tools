@echo off
:: 設定你要 commit 的訊息
set /p commit_msg=請輸入 commit 訊息：

:: 顯示目前狀態
echo.
echo ========== Git Status ==========
git status
echo.

:: 暫存當前修改
echo Stashing local changes...
git stash

:: 拉取最新版本
echo Pulling from remote...
git pull origin main

:: 套用暫存的修改
echo Popping stashed changes...
git stash pop

:: 顯示衝突提示（如果有）
echo.
echo ========== Git Status After Pop ==========
git status
echo.

:: 加入所有修改
echo Adding all changes...
git add .

:: 提交修改
echo Committing...
git commit -m "%commit_msg%"

:: 推送到遠端
echo Pushing to origin/main...
git push origin main

echo.
echo 🎉 完成同步！請確認是否有衝突需要手動解決。
pause
