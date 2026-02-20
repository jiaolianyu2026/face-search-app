@echo off
chcp 65001 >nul
echo ========================================
echo 人脸识别搜索应用 - 完整打包脚本
echo ========================================
echo.

:: 设置变量
set APP_NAME=FaceRecognitionSearch
set VERSION=1.0.0
set BUILD_DATE=%date:~0,4%%date:~5,2%%date:~8,2%
set PACKAGE_NAME=%APP_NAME%_v%VERSION%_Full
set DEPLOY_DIR=deploy\%PACKAGE_NAME%

echo 应用名称: %APP_NAME%
echo 版本号: %VERSION%
echo 构建日期: %BUILD_DATE%
echo 输出目录: %DEPLOY_DIR%
echo.
echo 此脚本将创建包含所有依赖的完整部署包
echo.

:: 清理旧的部署目录
if exist %DEPLOY_DIR% (
    echo 清理旧的部署目录...
    rmdir /s /q %DEPLOY_DIR%
)

:: 创建部署目录结构
echo [1/10] 创建目录结构...
mkdir %DEPLOY_DIR%
mkdir %DEPLOY_DIR%\backend
mkdir %DEPLOY_DIR%\frontend
mkdir %DEPLOY_DIR%\scripts
mkdir %DEPLOY_DIR%\docs
echo 目录结构创建完成
echo.

:: 复制后端文件（不包括虚拟环境和缓存）
echo [2/10] 复制后端源代码...
for %%f in (backend\*.py) do copy "%%f" "%DEPLOY_DIR%\backend\" >nul
copy backend\requirements.txt %DEPLOY_DIR%\backend\ >nul
if exist backend\*.md copy backend\*.md %DEPLOY_DIR%\backend\ >nul
echo 后端源代码复制完成
echo.

:: 复制虚拟环境
echo [3/10] 复制虚拟环境（这可能需要几分钟）...
xcopy backend\venv_new %DEPLOY_DIR%\backend\venv_new\ /E /I /Y /Q
echo 虚拟环境复制完成
echo.

:: 复制前端源代码
echo [4/10] 复制前端源代码...
xcopy frontend\src %DEPLOY_DIR%\frontend\src\ /E /I /Y /Q
if exist frontend\public xcopy frontend\public %DEPLOY_DIR%\frontend\public\ /E /I /Y /Q 2>nul
copy frontend\package.json %DEPLOY_DIR%\frontend\ >nul
copy frontend\vite.config.js %DEPLOY_DIR%\frontend\ >nul
copy frontend\index.html %DEPLOY_DIR%\frontend\ >nul
if exist frontend\*.md copy frontend\*.md %DEPLOY_DIR%\frontend\ >nul
echo 前端源代码复制完成
echo.

:: 复制前端依赖
echo [5/10] 复制前端依赖（这可能需要几分钟）...
if exist frontend\node_modules (
    xcopy frontend\node_modules %DEPLOY_DIR%\frontend\node_modules\ /E /I /Y /Q
    echo 前端依赖复制完成
) else (
    echo 警告：前端依赖未找到，用户需要运行 npm install
)
echo.

:: 复制脚本文件
echo [6/10] 复制脚本文件...
copy scripts\start.bat %DEPLOY_DIR%\scripts\ >nul
copy scripts\stop.bat %DEPLOY_DIR%\scripts\ >nul
echo 脚本文件复制完成
echo.

:: 复制文档
echo [7/10] 复制文档...
copy README.md %DEPLOY_DIR%\ >nul
copy INSTALLATION.md %DEPLOY_DIR%\ >nul
copy USAGE_GUIDE.md %DEPLOY_DIR%\ >nul
copy QUICK_REFERENCE.md %DEPLOY_DIR%\ >nul
copy .env.example %DEPLOY_DIR%\ >nul
copy deploy_config.json %DEPLOY_DIR%\ >nul
if exist backend\API_DOCUMENTATION.md copy backend\API_DOCUMENTATION.md %DEPLOY_DIR%\docs\ >nul
echo 文档复制完成
echo.

:: 创建版本信息文件
echo [8/10] 创建版本信息...
(
echo 应用名称: %APP_NAME%
echo 版本号: %VERSION%
echo 构建日期: %BUILD_DATE%
echo 构建时间: %time%
echo 构建类型: 完整安装包（包含所有依赖）
echo.
echo 系统要求:
echo - Windows 10/11 ^(64位^)
echo - 无需安装 Python 和 Node.js
echo - 8GB RAM ^(推荐^)
echo - 2GB 磁盘空间
echo.
echo 快速开始:
echo 1. 解压到目标目录
echo 2. 运行 scripts\start.bat 启动应用
echo 3. 访问 http://localhost:3000
echo.
echo 详细说明请查看 INSTALLATION.md
) > %DEPLOY_DIR%\VERSION.txt
echo 版本信息创建完成
echo.

:: 创建快速启动说明
echo [9/10] 创建快速启动说明...
(
echo ========================================
echo 人脸识别搜索应用 v%VERSION%
echo 快速启动指南
echo ========================================
echo.
echo 此安装包包含所有运行依赖，无需安装 Python 和 Node.js
echo.
echo 快速开始：
echo 1. 双击运行 scripts\start.bat
echo 2. 等待服务启动（约 10 秒）
echo 3. 浏览器会自动打开 http://localhost:3000
echo.
echo 停止应用：
echo - 双击运行 scripts\stop.bat
echo.
echo 详细使用说明：
echo - 查看 USAGE_GUIDE.md
echo - 查看 QUICK_REFERENCE.md
echo.
echo 技术支持：
echo - 查看 INSTALLATION.md 的常见问题章节
echo.
echo ========================================
) > %DEPLOY_DIR%\快速开始.txt
echo 快速启动说明创建完成
echo.

:: 显示打包结果
echo [10/10] 打包完成！
echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 输出位置: %DEPLOY_DIR%
echo.
echo 包含内容:
echo - 后端应用 + 虚拟环境 ^(backend/^)
echo - 前端应用 + node_modules ^(frontend/^)
echo - 启动脚本 ^(scripts/^)
echo - 完整文档 ^(*.md^)
echo.
echo 安装包大小: 约 500MB-1GB
echo.
echo 下一步:
echo 1. 将 %DEPLOY_DIR% 文件夹打包为 ZIP
echo 2. 分发给用户
echo 3. 用户解压后直接运行 scripts\start.bat
echo.
echo 提示: 可以使用 7-Zip 或 WinRAR 压缩此文件夹
echo.
