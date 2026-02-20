@echo off
chcp 65001 >nul
echo ========================================
echo 人脸识别搜索应用 - 启动脚本
echo ========================================
echo.

:: 获取脚本所在目录的父目录（应用根目录）
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%.."
set APP_ROOT=%CD%

echo 应用根目录: %APP_ROOT%
echo.

:: 检查虚拟环境是否存在（支持 venv 和 venv_new）
if not exist "%APP_ROOT%\backend\venv_new" (
    if not exist "%APP_ROOT%\backend\venv" (
        echo [错误] 虚拟环境不存在
        echo 应用根目录: %APP_ROOT%
        echo 请确保安装包完整，backend\venv_new 目录应该存在
        echo.
        echo 建议：运行 scripts\check.bat 检查安装包完整性
        echo.
        pause
        exit /b 1
    )
    set VENV_DIR=venv
) else (
    set VENV_DIR=venv_new
)

:: 检查前端依赖是否安装
if not exist "%APP_ROOT%\frontend\node_modules" (
    echo [错误] 前端依赖未安装
    echo 应用根目录: %APP_ROOT%
    echo 请确保安装包完整，frontend\node_modules 目录应该存在
    echo.
    echo 建议：运行 scripts\check.bat 检查安装包完整性
    echo.
    pause
    exit /b 1
)

:: 启动后端服务
echo [1/2] 启动后端服务...
echo 使用虚拟环境: %APP_ROOT%\backend\%VENV_DIR%
start "人脸识别后端" cmd /k "cd /d "%APP_ROOT%\backend" && %VENV_DIR%\Scripts\activate.bat && python app.py"
timeout /t 3 /nobreak >nul
echo 后端服务已启动: http://localhost:5000
echo.

:: 启动前端服务
echo [2/2] 启动前端服务...
start "人脸识别前端" cmd /k "cd /d "%APP_ROOT%\frontend" && npm run dev"
timeout /t 3 /nobreak >nul
echo 前端服务已启动: http://localhost:3000
echo.

echo ========================================
echo 应用启动成功！
echo ========================================
echo.
echo 前端地址: http://localhost:3000
echo 后端地址: http://localhost:5000
echo.
echo 提示：
echo - 两个命令行窗口将保持打开状态
echo - 关闭窗口将停止对应的服务
echo - 或运行 scripts\stop.bat 停止所有服务
echo.
echo 按任意键打开浏览器...
pause >nul

:: 打开浏览器
start http://localhost:3000
