@echo off
chcp 65001 >nul
echo ========================================
echo 安装包完整性检查
echo ========================================
echo.

set ERROR_COUNT=0

:: 检查后端虚拟环境
echo [1/4] 检查后端虚拟环境...
if exist backend\venv_new (
    echo ✓ backend\venv_new 存在
    if exist backend\venv_new\Scripts\python.exe (
        echo ✓ Python 可执行文件存在
    ) else (
        echo ✗ Python 可执行文件不存在
        set /a ERROR_COUNT+=1
    )
) else (
    echo ✗ backend\venv_new 不存在
    set /a ERROR_COUNT+=1
)
echo.

:: 检查后端源代码
echo [2/4] 检查后端源代码...
if exist backend\app.py (
    echo ✓ backend\app.py 存在
) else (
    echo ✗ backend\app.py 不存在
    set /a ERROR_COUNT+=1
)
echo.

:: 检查前端依赖
echo [3/4] 检查前端依赖...
if exist frontend\node_modules (
    echo ✓ frontend\node_modules 存在
) else (
    echo ✗ frontend\node_modules 不存在
    set /a ERROR_COUNT+=1
)
echo.

:: 检查前端源代码
echo [4/4] 检查前端源代码...
if exist frontend\src (
    echo ✓ frontend\src 存在
) else (
    echo ✗ frontend\src 不存在
    set /a ERROR_COUNT+=1
)
if exist frontend\package.json (
    echo ✓ frontend\package.json 存在
) else (
    echo ✗ frontend\package.json 不存在
    set /a ERROR_COUNT+=1
)
echo.

:: 显示结果
echo ========================================
if %ERROR_COUNT%==0 (
    echo ✓ 安装包完整，可以正常使用
    echo.
    echo 下一步：运行 scripts\start.bat 启动应用
) else (
    echo ✗ 发现 %ERROR_COUNT% 个问题
    echo.
    echo 建议：
    echo 1. 重新解压安装包
    echo 2. 确保解压完整
    echo 3. 检查磁盘空间是否充足
)
echo ========================================
echo.
pause
