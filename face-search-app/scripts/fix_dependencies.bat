@echo off
chcp 65001 >nul
echo ========================================
echo 修复虚拟环境依赖
echo ========================================
echo.

echo 此脚本将确保所有依赖都已正确安装
echo.

:: 检查虚拟环境
if exist backend\venv (
    set VENV_DIR=backend\venv
    echo 使用虚拟环境: backend\venv
) else if exist backend\venv_new (
    set VENV_DIR=backend\venv_new
    echo 使用虚拟环境: backend\venv_new
) else (
    echo [错误] 未找到虚拟环境！
    echo 请先创建虚拟环境：
    echo   cd backend
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [1/3] 检查当前已安装的包...
%VENV_DIR%\Scripts\pip.exe list
echo.

echo [2/3] 安装/更新所有依赖...
%VENV_DIR%\Scripts\pip.exe install -r backend\requirements.txt
echo.

echo [3/3] 验证关键依赖...
echo.
echo 检查 Flask:
%VENV_DIR%\Scripts\python.exe -c "import flask; print('✓ Flask:', flask.__version__)" 2>nul || echo ✗ Flask 未安装

echo 检查 flask-socketio:
%VENV_DIR%\Scripts\python.exe -c "import flask_socketio; print('✓ flask-socketio: OK')" 2>nul || echo ✗ flask-socketio 未安装

echo 检查 python-socketio:
%VENV_DIR%\Scripts\python.exe -c "import socketio; print('✓ python-socketio: OK')" 2>nul || echo ✗ python-socketio 未安装

echo 检查 face_recognition:
%VENV_DIR%\Scripts\python.exe -c "import face_recognition; print('✓ face_recognition: OK')" 2>nul || echo ✗ face_recognition 未安装

echo 检查 OpenCV:
%VENV_DIR%\Scripts\python.exe -c "import cv2; print('✓ OpenCV:', cv2.__version__)" 2>nul || echo ✗ OpenCV 未安装

echo 检查 NumPy:
%VENV_DIR%\Scripts\python.exe -c "import numpy; print('✓ NumPy:', numpy.__version__)" 2>nul || echo ✗ NumPy 未安装

echo 检查 Pillow:
%VENV_DIR%\Scripts\python.exe -c "import PIL; print('✓ Pillow:', PIL.__version__)" 2>nul || echo ✗ Pillow 未安装

echo 检查 Flask-CORS:
%VENV_DIR%\Scripts\python.exe -c "import flask_cors; print('✓ Flask-CORS: OK')" 2>nul || echo ✗ Flask-CORS 未安装

echo.
echo ========================================
echo 依赖修复完成！
echo ========================================
echo.
echo 现在可以：
echo 1. 测试后端启动：
echo    cd backend
echo    %VENV_DIR%\Scripts\activate
echo    python app.py
echo.
echo 2. 重新打包：
echo    scripts\package_full_v1.1.bat
echo.
pause
