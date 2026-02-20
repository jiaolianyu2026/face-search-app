@echo off
chcp 65001 >nul
echo ========================================
echo 路径测试脚本
echo ========================================
echo.

:: 获取脚本所在目录的父目录（应用根目录）
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%.."
set APP_ROOT=%CD%

echo 测试结果：
echo.
echo 1. 脚本文件位置: %~f0
echo 2. 脚本目录: %SCRIPT_DIR%
echo 3. 应用根目录: %APP_ROOT%
echo.
echo 4. 后端目录: %APP_ROOT%\backend
echo 5. 前端目录: %APP_ROOT%\frontend
echo.

:: 验证目录是否存在
if exist "%APP_ROOT%\backend" (
    echo ✓ 后端目录存在
) else (
    echo ✗ 后端目录不存在
)

if exist "%APP_ROOT%\frontend" (
    echo ✓ 前端目录存在
) else (
    echo ✗ 前端目录不存在
)

if exist "%APP_ROOT%\scripts" (
    echo ✓ 脚本目录存在
) else (
    echo ✗ 脚本目录不存在
)

echo.
echo 测试完成！
echo 如果所有目录都存在，说明路径解析正确。
echo.
pause
