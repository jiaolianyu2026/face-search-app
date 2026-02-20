@echo off
chcp 65001 >nul
echo ========================================
echo 部署包测试脚本
echo ========================================
echo.

:: 设置变量
set TEST_DIR=deploy_test
set PACKAGE_DIR=deploy

echo 此脚本将测试部署包的完整性
echo.
echo 测试步骤：
echo 1. 查找最新的部署包
echo 2. 解压到测试目录
echo 3. 检查文件完整性
echo 4. 验证脚本可执行性
echo.
pause

:: 清理旧的测试目录
if exist %TEST_DIR% (
    echo 清理旧的测试目录...
    rmdir /s /q %TEST_DIR%
)

:: 创建测试目录
mkdir %TEST_DIR%
echo.

:: 查找最新的部署包
echo [1/4] 查找部署包...
set LATEST_PACKAGE=
for /f "delims=" %%i in ('dir /b /od %PACKAGE_DIR%\FaceRecognitionSearch_*.zip 2^>nul') do set LATEST_PACKAGE=%%i

if "%LATEST_PACKAGE%"=="" (
    echo [错误] 未找到部署包
    echo 请先运行 scripts\package.bat 创建部署包
    pause
    exit /b 1
)

echo 找到部署包: %LATEST_PACKAGE%
echo.

:: 解压部署包
echo [2/4] 解压部署包...
if exist "%ProgramFiles%\7-Zip\7z.exe" (
    "%ProgramFiles%\7-Zip\7z.exe" x %PACKAGE_DIR%\%LATEST_PACKAGE% -o%TEST_DIR% -y >nul
    if errorlevel 1 (
        echo [错误] 解压失败
        pause
        exit /b 1
    )
    echo 解压成功
) else (
    echo [错误] 未检测到 7-Zip，无法自动解压
    echo 请手动解压 %PACKAGE_DIR%\%LATEST_PACKAGE% 到 %TEST_DIR% 目录
    pause
    exit /b 1
)
echo.

:: 检查文件完整性
echo [3/4] 检查文件完整性...

set ERROR_COUNT=0

:: 检查必需的目录
if not exist %TEST_DIR%\backend (
    echo [错误] 缺少 backend 目录
    set /a ERROR_COUNT+=1
)
if not exist %TEST_DIR%\frontend (
    echo [错误] 缺少 frontend 目录
    set /a ERROR_COUNT+=1
)
if not exist %TEST_DIR%\scripts (
    echo [错误] 缺少 scripts 目录
    set /a ERROR_COUNT+=1
)
if not exist %TEST_DIR%\tests (
    echo [错误] 缺少 tests 目录
    set /a ERROR_COUNT+=1
)

:: 检查必需的文件
if not exist %TEST_DIR%\README.md (
    echo [错误] 缺少 README.md
    set /a ERROR_COUNT+=1
)
if not exist %TEST_DIR%\INSTALLATION.md (
    echo [错误] 缺少 INSTALLATION.md
    set /a ERROR_COUNT+=1
)
if not exist %TEST_DIR%\USAGE_GUIDE.md (
    echo [错误] 缺少 USAGE_GUIDE.md
    set /a ERROR_COUNT+=1
)
if not exist %TEST_DIR%\.env.example (
    echo [错误] 缺少 .env.example
    set /a ERROR_COUNT+=1
)
if not exist %TEST_DIR%\deploy_config.json (
    echo [错误] 缺少 deploy_config.json
    set /a ERROR_COUNT+=1
)
if not exist %TEST_DIR%\VERSION.txt (
    echo [错误] 缺少 VERSION.txt
    set /a ERROR_COUNT+=1
)

:: 检查后端文件
if not exist %TEST_DIR%\backend\app.py (
    echo [错误] 缺少 backend\app.py
    set /a ERROR_COUNT+=1
)
if not exist %TEST_DIR%\backend\requirements.txt (
    echo [错误] 缺少 backend\requirements.txt
    set /a ERROR_COUNT+=1
)

:: 检查前端文件
if not exist %TEST_DIR%\frontend\package.json (
    echo [错误] 缺少 frontend\package.json
    set /a ERROR_COUNT+=1
)
if not exist %TEST_DIR%\frontend\src (
    echo [错误] 缺少 frontend\src 目录
    set /a ERROR_COUNT+=1
)

:: 检查脚本文件
if not exist %TEST_DIR%\scripts\install.bat (
    echo [错误] 缺少 scripts\install.bat
    set /a ERROR_COUNT+=1
)
if not exist %TEST_DIR%\scripts\start.bat (
    echo [错误] 缺少 scripts\start.bat
    set /a ERROR_COUNT+=1
)
if not exist %TEST_DIR%\scripts\stop.bat (
    echo [错误] 缺少 scripts\stop.bat
    set /a ERROR_COUNT+=1
)

if %ERROR_COUNT%==0 (
    echo ✓ 所有必需文件都存在
) else (
    echo [警告] 发现 %ERROR_COUNT% 个缺失的文件或目录
)
echo.

:: 验证脚本可执行性
echo [4/4] 验证脚本...

:: 检查脚本是否包含 BOM 或编码问题
findstr /C:"@echo off" %TEST_DIR%\scripts\install.bat >nul
if errorlevel 1 (
    echo [警告] install.bat 可能存在编码问题
    set /a ERROR_COUNT+=1
) else (
    echo ✓ install.bat 格式正确
)

findstr /C:"@echo off" %TEST_DIR%\scripts\start.bat >nul
if errorlevel 1 (
    echo [警告] start.bat 可能存在编码问题
    set /a ERROR_COUNT+=1
) else (
    echo ✓ start.bat 格式正确
)

findstr /C:"@echo off" %TEST_DIR%\scripts\stop.bat >nul
if errorlevel 1 (
    echo [警告] stop.bat 可能存在编码问题
    set /a ERROR_COUNT+=1
) else (
    echo ✓ stop.bat 格式正确
)
echo.

:: 显示测试结果
echo ========================================
echo 测试结果
echo ========================================
echo.

if %ERROR_COUNT%==0 (
    echo ✓ 部署包测试通过！
    echo.
    echo 部署包位置: %PACKAGE_DIR%\%LATEST_PACKAGE%
    echo 测试目录: %TEST_DIR%
    echo.
    echo 下一步：
    echo 1. 在干净的环境中测试安装
    echo 2. 运行 %TEST_DIR%\scripts\install.bat
    echo 3. 运行 %TEST_DIR%\scripts\start.bat
    echo 4. 测试所有功能
) else (
    echo ✗ 部署包测试失败
    echo.
    echo 发现 %ERROR_COUNT% 个问题
    echo 请检查上述错误信息并修复
    echo.
    echo 建议：
    echo 1. 检查 scripts\package.bat 脚本
    echo 2. 确保所有文件都已正确复制
    echo 3. 重新运行 scripts\package.bat
)
echo.

:: 显示文件统计
echo 文件统计：
echo - 后端文件: 
dir /b %TEST_DIR%\backend\*.py 2>nul | find /c /v "" 
echo - 前端文件: 
dir /b /s %TEST_DIR%\frontend\src\*.jsx 2>nul | find /c /v "" 
echo - 脚本文件: 
dir /b %TEST_DIR%\scripts\*.bat 2>nul | find /c /v "" 
echo - 测试文件: 
dir /b %TEST_DIR%\tests\*.py 2>nul | find /c /v "" 
echo.

echo 提示：测试目录 %TEST_DIR% 将保留，您可以手动检查
echo 如需清理，请运行: rmdir /s /q %TEST_DIR%
echo.
pause
