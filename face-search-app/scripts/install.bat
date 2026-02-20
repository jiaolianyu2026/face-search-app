@echo off
chcp 65001 >nul
echo ========================================
echo 人脸识别搜索应用 - 安装脚本
echo ========================================
echo.

:: 检查 Python 是否安装
echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

:: 检查 Node.js 是否安装
echo [2/5] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js 16 或更高版本
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)
node --version
npm --version
echo.

:: 创建后端虚拟环境
echo [3/5] 创建 Python 虚拟环境...
cd backend
if exist venv (
    echo 虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        cd ..
        pause
        exit /b 1
    )
    echo 虚拟环境创建成功
)
echo.

:: 安装后端依赖
echo [4/5] 安装后端依赖（这可能需要几分钟）...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 后端依赖安装失败
    deactivate
    cd ..
    pause
    exit /b 1
)
deactivate
cd ..
echo 后端依赖安装成功
echo.

:: 安装前端依赖
echo [5/5] 安装前端依赖（这可能需要几分钟）...
cd frontend
call npm install
if errorlevel 1 (
    echo [错误] 前端依赖安装失败
    cd ..
    pause
    exit /b 1
)
cd ..
echo 前端依赖安装成功
echo.

:: 创建必要的目录
echo 创建必要的目录...
if not exist backend\temp_uploads mkdir backend\temp_uploads
if not exist backend\cache mkdir backend\cache
echo.

echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 下一步：
echo 1. 运行 scripts\start.bat 启动应用
echo 2. 访问 http://localhost:3000 使用应用
echo.
echo 详细使用说明请查看 INSTALLATION.md
echo.
pause
