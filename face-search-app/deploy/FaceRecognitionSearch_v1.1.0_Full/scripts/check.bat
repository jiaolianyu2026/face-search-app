@echo off
chcp 65001 >nul
echo ========================================
echo 安装包完整性检查
echo ========================================
echo.

:: 获取脚本所在目录的父目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR.."
set APP_ROOT=%CD%

echo 应用根目录: %APP_ROOT%
echo.

:: 检查后端虚拟环境
if exist "%APP_ROOT%\backend\venv_new" (
    echo [OK] backend\venv_new 存在
) else (
    echo [错误] backend\venv_new 不存在
    goto :error
)

:: 检查 Python 可执行文件
if exist "%APP_ROOT%\backend\venv_new\Scripts\python.exe" (
    echo [OK] Python 可执行文件存在
) else (
    echo [错误] Python 可执行文件不存在
    goto :error
)

:: 检查后端主文件
if exist "%APP_ROOT%\backend\app.py" (
    echo [OK] backend\app.py 存在
) else (
    echo [错误] backend\app.py 不存在
    goto :error
)

:: 检查前端依赖
if exist "%APP_ROOT%\frontend\node_modules" (
    echo [OK] frontend\node_modules 存在
) else (
    echo [警告] frontend\node_modules 不存在，用户需要运行 npm install
)

:: 检查前端源代码
if exist "%APP_ROOT%\frontend\src" (
    echo [OK] frontend\src 存在
) else (
    echo [错误] frontend\src 不存在
    goto :error
)

echo.
echo ========================================
echo 检查完成！
echo ========================================
echo 安装包完整，可以正常使用
echo.
echo 下一步：
echo 1. 双击运行 scripts\start.bat
echo 2. 等待 10-15 秒
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo 检查失败！
echo ========================================
echo 安装包不完整，请重新解压或联系技术支持
echo.
pause
exit /b 1
