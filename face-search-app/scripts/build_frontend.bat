@echo off
chcp 65001 >nul
echo ========================================
echo 人脸识别搜索应用 - 前端构建脚本
echo ========================================
echo.

:: 检查前端依赖
if not exist frontend\node_modules (
    echo [错误] 前端依赖未安装，请先运行 scripts\install.bat
    pause
    exit /b 1
)

:: 构建前端
echo 开始构建前端生产版本...
cd frontend
call npm run build
if errorlevel 1 (
    echo [错误] 前端构建失败
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo ========================================
echo 前端构建成功！
echo ========================================
echo.
echo 构建输出目录: frontend\dist
echo.
echo 提示：
echo - 可以使用 Nginx 或其他 Web 服务器部署 dist 目录
echo - 或运行 'npm run preview' 预览构建结果
echo.
pause
