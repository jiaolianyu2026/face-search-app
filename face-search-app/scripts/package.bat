@echo off
chcp 65001 >nul
echo ========================================
echo 人脸识别搜索应用 - 打包脚本
echo ========================================
echo.

:: 设置变量
set APP_NAME=FaceRecognitionSearch
set VERSION=1.0.0
set BUILD_DATE=%date:~0,4%%date:~5,2%%date:~8,2%
set PACKAGE_NAME=%APP_NAME%_v%VERSION%_%BUILD_DATE%
set DEPLOY_DIR=deploy\%PACKAGE_NAME%

echo 应用名称: %APP_NAME%
echo 版本号: %VERSION%
echo 构建日期: %BUILD_DATE%
echo 输出目录: %DEPLOY_DIR%
echo.

:: 清理旧的部署目录
if exist deploy\%PACKAGE_NAME% (
    echo 清理旧的部署目录...
    rmdir /s /q deploy\%PACKAGE_NAME%
)

:: 创建部署目录结构
echo [1/8] 创建目录结构...
mkdir %DEPLOY_DIR%
mkdir %DEPLOY_DIR%\backend
mkdir %DEPLOY_DIR%\frontend
mkdir %DEPLOY_DIR%\scripts
mkdir %DEPLOY_DIR%\docs
mkdir %DEPLOY_DIR%\tests
echo 目录结构创建完成
echo.

:: 复制后端文件
echo [2/8] 复制后端文件...
xcopy backend\*.py %DEPLOY_DIR%\backend\ /Y /Q
xcopy backend\requirements.txt %DEPLOY_DIR%\backend\ /Y /Q
if exist backend\*.md xcopy backend\*.md %DEPLOY_DIR%\backend\ /Y /Q
echo 后端文件复制完成
echo.

:: 复制前端文件
echo [3/8] 复制前端文件...
xcopy frontend\src %DEPLOY_DIR%\frontend\src\ /E /I /Y /Q
xcopy frontend\public %DEPLOY_DIR%\frontend\public\ /E /I /Y /Q 2>nul
xcopy frontend\*.json %DEPLOY_DIR%\frontend\ /Y /Q
xcopy frontend\*.js %DEPLOY_DIR%\frontend\ /Y /Q
xcopy frontend\*.html %DEPLOY_DIR%\frontend\ /Y /Q
if exist frontend\*.md xcopy frontend\*.md %DEPLOY_DIR%\frontend\ /Y /Q
echo 前端文件复制完成
echo.

:: 复制脚本文件
echo [4/8] 复制脚本文件...
xcopy scripts\*.bat %DEPLOY_DIR%\scripts\ /Y /Q
echo 脚本文件复制完成
echo.

:: 复制测试文件
echo [5/8] 复制测试文件...
xcopy tests\*.py %DEPLOY_DIR%\tests\ /Y /Q
echo 测试文件复制完成
echo.

:: 复制文档
echo [6/8] 复制文档...
copy README.md %DEPLOY_DIR%\ /Y >nul
copy INSTALLATION.md %DEPLOY_DIR%\ /Y >nul
copy USAGE_GUIDE.md %DEPLOY_DIR%\ /Y >nul
copy .env.example %DEPLOY_DIR%\ /Y >nul
copy deploy_config.json %DEPLOY_DIR%\ /Y >nul
if exist backend\API_DOCUMENTATION.md copy backend\API_DOCUMENTATION.md %DEPLOY_DIR%\docs\ /Y >nul
if exist QUICK_START.md copy QUICK_START.md %DEPLOY_DIR%\docs\ /Y >nul
echo 文档复制完成
echo.

:: 创建版本信息文件
echo [7/8] 创建版本信息...
(
echo 应用名称: %APP_NAME%
echo 版本号: %VERSION%
echo 构建日期: %BUILD_DATE%
echo 构建时间: %time%
echo.
echo 系统要求:
echo - Windows 10/11 ^(64位^)
echo - Python 3.10+
echo - Node.js 16+
echo - 8GB RAM ^(推荐^)
echo - 2GB 磁盘空间
echo.
echo 安装说明:
echo 1. 运行 scripts\install.bat 安装依赖
echo 2. 运行 scripts\start.bat 启动应用
echo 3. 访问 http://localhost:3000
echo.
echo 详细说明请查看 INSTALLATION.md
) > %DEPLOY_DIR%\VERSION.txt
echo 版本信息创建完成
echo.

:: 创建压缩包
echo [8/8] 创建压缩包...
if exist "%ProgramFiles%\7-Zip\7z.exe" (
    "%ProgramFiles%\7-Zip\7z.exe" a -tzip deploy\%PACKAGE_NAME%.zip .\%DEPLOY_DIR%\* -mx=9
    if errorlevel 1 (
        echo [警告] 压缩失败，但文件已复制到 %DEPLOY_DIR%
    ) else (
        echo 压缩包创建成功: deploy\%PACKAGE_NAME%.zip
    )
) else (
    echo [提示] 未检测到 7-Zip，跳过压缩
    echo [提示] 您可以手动压缩 %DEPLOY_DIR% 目录
)
echo.

:: 显示打包结果
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 输出位置:
echo - 文件夹: %DEPLOY_DIR%
if exist deploy\%PACKAGE_NAME%.zip echo - 压缩包: deploy\%PACKAGE_NAME%.zip
echo.
echo 包含内容:
echo - 后端应用 ^(backend/^)
echo - 前端应用 ^(frontend/^)
echo - 启动脚本 ^(scripts/^)
echo - 测试文件 ^(tests/^)
echo - 文档 ^(*.md^)
echo - 配置示例 ^(.env.example^)
echo.
echo 下一步:
echo 1. 将压缩包或文件夹分发给用户
echo 2. 用户解压后运行 scripts\install.bat
echo 3. 运行 scripts\start.bat 启动应用
echo.
pause
