@echo off
chcp 65001 >nul
echo ========================================
echo 人脸识别搜索应用 - 停止脚本
echo ========================================
echo.

:: 停止后端服务（Python Flask）
echo [1/2] 停止后端服务...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 (
        echo 后端服务已停止 ^(PID: %%a^)
    )
)

:: 停止前端服务（Node.js Vite）
echo [2/2] 停止前端服务...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 (
        echo 前端服务已停止 ^(PID: %%a^)
    )
)

:: 额外清理：关闭所有标题包含"人脸识别"的命令行窗口
taskkill /FI "WINDOWTITLE eq 人脸识别后端*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 人脸识别前端*" /F >nul 2>&1

echo.
echo ========================================
echo 所有服务已停止
echo ========================================
echo.
pause
