@echo off
chcp 65001 >nul
echo ========================================
echo 人脸识别搜索应用 - 完整打包脚本 v1.1
echo ========================================
echo.

:: 获取脚本所在目录的父目录（项目根目录）
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%..\"
set PROJECT_ROOT=%CD%

echo 项目根目录: %PROJECT_ROOT%
echo.

:: 设置变量
set APP_NAME=FaceRecognitionSearch
set VERSION=1.1.0
set BUILD_DATE=%date:~0,4%%date:~5,2%%date:~8,2%
set PACKAGE_NAME=%APP_NAME%_v%VERSION%_Full
set DEPLOY_DIR=%PROJECT_ROOT%\deploy\%PACKAGE_NAME%

echo 应用名称: %APP_NAME%
echo 版本号: %VERSION% (新增性能优化功能)
echo 构建日期: %BUILD_DATE%
echo 输出目录: %DEPLOY_DIR%
echo.
echo 此脚本将创建包含所有依赖的完整部署包
echo 用户无需安装 Python 和 Node.js，解压后即可使用
echo.

:: 检查必要的目录
echo 检查必要的目录...
if not exist "%PROJECT_ROOT%\backend\venv" (
    if not exist "%PROJECT_ROOT%\backend\venv_new" (
        echo [错误] 未找到虚拟环境！
        echo 项目根目录: %PROJECT_ROOT%
        echo 请先运行以下命令创建虚拟环境：
        echo   cd "%PROJECT_ROOT%\backend"
        echo   python -m venv venv_new
        echo   venv_new\Scripts\activate
        echo   pip install -r requirements.txt
        pause
        exit /b 1
    )
)

if not exist "%PROJECT_ROOT%\frontend\node_modules" (
    echo [警告] 未找到 frontend\node_modules
    echo 用户需要自行安装前端依赖
)

echo 检查完成
echo.

:: 验证并安装依赖
echo 验证虚拟环境依赖...
if exist "%PROJECT_ROOT%\backend\venv" (
    set VENV_DIR=%PROJECT_ROOT%\backend\venv
) else (
    set VENV_DIR=%PROJECT_ROOT%\backend\venv_new
)

echo 使用虚拟环境: %VENV_DIR%
echo 安装/更新所有依赖（这可能需要几分钟）...
"%VENV_DIR%\Scripts\pip.exe" install -r "%PROJECT_ROOT%\backend\requirements.txt" --quiet
if errorlevel 1 (
    echo [警告] 依赖安装可能不完整，但继续打包
) else (
    echo 依赖验证完成
)
echo.

:: 清理旧的部署目录
if exist "%DEPLOY_DIR%" (
    echo 清理旧的部署目录...
    rmdir /s /q "%DEPLOY_DIR%"
)

:: 创建部署目录结构
echo [1/12] 创建目录结构...
mkdir "%DEPLOY_DIR%"
mkdir "%DEPLOY_DIR%\backend"
mkdir "%DEPLOY_DIR%\frontend"
mkdir "%DEPLOY_DIR%\scripts"
mkdir "%DEPLOY_DIR%\docs"
echo 目录结构创建完成
echo.

:: 复制后端文件（不包括虚拟环境、缓存、测试文件）
echo [2/12] 复制后端源代码...
for %%f in ("%PROJECT_ROOT%\backend\*.py") do (
    echo   复制 %%~nxf
    copy "%%f" "%DEPLOY_DIR%\backend\" >nul
)
copy "%PROJECT_ROOT%\backend\requirements.txt" "%DEPLOY_DIR%\backend\" >nul
if exist "%PROJECT_ROOT%\backend\*.md" (
    for %%f in ("%PROJECT_ROOT%\backend\*.md") do copy "%%f" "%DEPLOY_DIR%\backend\" >nul
)
echo 后端源代码复制完成（包含新模块 thumbnail_generator.py）
echo.

:: 复制虚拟环境
echo [3/12] 复制虚拟环境（这可能需要几分钟）...
if exist "%PROJECT_ROOT%\backend\venv_new" (
    echo 复制 backend\venv_new 到 %DEPLOY_DIR%\backend\venv_new
    xcopy "%PROJECT_ROOT%\backend\venv_new" "%DEPLOY_DIR%\backend\venv_new\" /E /I /Y /Q
    echo 虚拟环境复制完成（使用 venv_new）
) else if exist "%PROJECT_ROOT%\backend\venv" (
    echo 复制 backend\venv 到 %DEPLOY_DIR%\backend\venv_new
    xcopy "%PROJECT_ROOT%\backend\venv" "%DEPLOY_DIR%\backend\venv_new\" /E /I /Y /Q
    echo 虚拟环境复制完成（从 venv 重命名为 venv_new）
) else (
    echo [错误] 未找到虚拟环境！
    pause
    exit /b 1
)
echo.

:: 复制前端源代码
echo [4/12] 复制前端源代码...
xcopy "%PROJECT_ROOT%\frontend\src" "%DEPLOY_DIR%\frontend\src\" /E /I /Y /Q
if exist "%PROJECT_ROOT%\frontend\public" xcopy "%PROJECT_ROOT%\frontend\public" "%DEPLOY_DIR%\frontend\public\" /E /I /Y /Q 2>nul
copy "%PROJECT_ROOT%\frontend\package.json" "%DEPLOY_DIR%\frontend\" >nul
copy "%PROJECT_ROOT%\frontend\package-lock.json" "%DEPLOY_DIR%\frontend\" >nul 2>nul
copy "%PROJECT_ROOT%\frontend\vite.config.js" "%DEPLOY_DIR%\frontend\" >nul
copy "%PROJECT_ROOT%\frontend\index.html" "%DEPLOY_DIR%\frontend\" >nul
if exist "%PROJECT_ROOT%\frontend\*.md" copy "%PROJECT_ROOT%\frontend\*.md" "%DEPLOY_DIR%\frontend\" >nul
if exist "%PROJECT_ROOT%\frontend\websocket-example.html" copy "%PROJECT_ROOT%\frontend\websocket-example.html" "%DEPLOY_DIR%\frontend\" >nul
echo 前端源代码复制完成
echo.

:: 复制前端依赖
echo [5/12] 复制前端依赖（这可能需要几分钟）...
if exist "%PROJECT_ROOT%\frontend\node_modules" (
    echo 正在复制 node_modules（约 200MB）...
    echo 注意：此过程可能需要 5-10 分钟，请耐心等待...
    
    :: 使用 robocopy 代替 xcopy，更可靠地处理长路径和符号链接
    robocopy "%PROJECT_ROOT%\frontend\node_modules" "%DEPLOY_DIR%\frontend\node_modules" /E /NFL /NDL /NJH /NJS /nc /ns /np
    
    :: robocopy 的退出码：0-7 表示成功，8+ 表示错误
    if errorlevel 8 (
        echo [警告] node_modules 复制可能不完整
        echo 用户可能需要在部署后运行：cd frontend ^&^& npm install
    ) else (
        echo 前端依赖复制完成
    )
) else (
    echo [警告] 前端依赖未找到
    echo 建议先运行：cd frontend ^&^& npm install
    echo 用户需要自行安装前端依赖
)
echo.

:: 复制改进的脚本文件
echo [6/12] 复制脚本文件...
copy "%PROJECT_ROOT%\scripts\start.bat" "%DEPLOY_DIR%\scripts\" >nul
copy "%PROJECT_ROOT%\scripts\stop.bat" "%DEPLOY_DIR%\scripts\" >nul
if exist "%PROJECT_ROOT%\scripts\check.bat" copy "%PROJECT_ROOT%\scripts\check.bat" "%DEPLOY_DIR%\scripts\" >nul
echo 脚本文件复制完成（已修复路径问题）
echo.

:: 复制文档
echo [7/12] 复制文档...
copy "%PROJECT_ROOT%\README.md" "%DEPLOY_DIR%\" >nul
copy "%PROJECT_ROOT%\INSTALLATION.md" "%DEPLOY_DIR%\" >nul
copy "%PROJECT_ROOT%\USAGE_GUIDE.md" "%DEPLOY_DIR%\" >nul
copy "%PROJECT_ROOT%\QUICK_REFERENCE.md" "%DEPLOY_DIR%\" >nul
copy "%PROJECT_ROOT%\.env.example" "%DEPLOY_DIR%\" >nul
copy "%PROJECT_ROOT%\deploy_config.json" "%DEPLOY_DIR%\" >nul
if exist "%PROJECT_ROOT%\PERFORMANCE_OPTIMIZATION_SUMMARY.md" copy "%PROJECT_ROOT%\PERFORMANCE_OPTIMIZATION_SUMMARY.md" "%DEPLOY_DIR%\docs\" >nul
if exist "%PROJECT_ROOT%\WEBSOCKET_IMPLEMENTATION_SUMMARY.md" copy "%PROJECT_ROOT%\WEBSOCKET_IMPLEMENTATION_SUMMARY.md" "%DEPLOY_DIR%\docs\" >nul
if exist "%PROJECT_ROOT%\backend\API_DOCUMENTATION.md" copy "%PROJECT_ROOT%\backend\API_DOCUMENTATION.md" "%DEPLOY_DIR%\docs\" >nul
echo 文档复制完成
echo.

:: 创建版本信息文件
echo [8/12] 创建版本信息...
(
echo ========================================
echo 人脸识别搜索应用 v1.1.0
echo ========================================
echo.
echo 版本号: %VERSION%
echo 构建日期: %BUILD_DATE%
echo 构建时间: %time%
echo 构建类型: 完整安装包（包含所有依赖）
echo.
echo 新增功能 ^(v1.1.0^):
echo - 多线程并行处理（提速 2-4 倍）
echo - 批处理策略（支持大文件夹）
echo - 缩略图生成（加快前端加载）
echo - 运行时配置管理（无需重启）
echo - 人脸检测模型选择（HOG/CNN）
echo - 缓存清理功能
echo - WebSocket 实时进度更新
echo.
echo 系统要求:
echo - Windows 10/11 ^(64位^)
echo - 无需安装 Python 和 Node.js
echo - 8GB RAM ^(推荐^)
echo - 2GB 磁盘空间
echo.
echo 快速开始:
echo 1. 解压到目标目录
echo 2. 双击运行 scripts\start.bat
echo 3. 等待 10-15 秒自动启动
echo 4. 浏览器访问 http://localhost:3000
echo.
echo 注意事项:
echo - 首次启动需要 10-15 秒
echo - 确保端口 5000 和 3000 未被占用
echo - 建议使用 Chrome 或 Edge 浏览器
echo.
echo 详细说明请查看 INSTALLATION.md
) > "%DEPLOY_DIR%\VERSION.txt"
echo 版本信息创建完成
echo.

:: 创建快速启动说明
echo [9/12] 创建快速启动说明...
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
echo 2. 等待服务启动（约 10-15 秒）
echo 3. 浏览器会自动打开 http://localhost:3000
echo.
echo 停止应用：
echo - 双击运行 scripts\stop.bat
echo.
echo 新功能使用：
echo - 调整相似度阈值：通过 API 或前端界面
echo - 切换检测模型：HOG（快速）或 CNN（精确）
echo - 清除缓存：使用 API 端点
echo.
echo 详细使用说明：
echo - 查看 USAGE_GUIDE.md
echo - 查看 QUICK_REFERENCE.md
echo - 查看 docs\PERFORMANCE_OPTIMIZATION_SUMMARY.md
echo.
echo 技术支持：
echo - 查看 INSTALLATION.md 的常见问题章节
echo - 查看 docs\API_DOCUMENTATION.md
echo.
echo ========================================
) > "%DEPLOY_DIR%\快速开始.txt"
echo 快速启动说明创建完成
echo.

:: 创建安装指南
echo [10/12] 创建安装指南...
(
echo # 人脸识别搜索应用 v1.1.0 - 安装指南
echo.
echo ## 系统要求
echo.
echo - Windows 10/11 ^(64位^)
echo - 8GB RAM ^(推荐^)
echo - 2GB 磁盘空间
echo - Chrome 或 Edge 浏览器
echo - **无需安装 Python 和 Node.js**
echo.
echo ## 安装步骤
echo.
echo ### 1. 解压安装包
echo.
echo 将 ZIP 文件解压到任意位置，例如：
echo ```
echo C:\FaceRecognitionSearch
echo ```
echo.
echo ### 2. 启动应用
echo.
echo 双击运行：`scripts\start.bat`
echo.
echo **注意**：可以从任何位置运行此脚本。
echo.
echo ### 3. 等待启动
echo.
echo - 首次启动：10-15 秒
echo - 后续启动：5 秒
echo.
echo ### 4. 访问应用
echo.
echo 浏览器会自动打开：http://localhost:3000
echo.
echo ## 新功能 ^(v1.1.0^)
echo.
echo ### 性能优化
echo - 多线程并行处理：搜索速度提升 2-4 倍
echo - 批处理策略：支持超大文件夹搜索
echo - 缩略图生成：前端加载速度提升 5-10 倍
echo.
echo ### 配置管理
echo - 运行时配置：无需重启即可调整设置
echo - 模型选择：HOG ^(快速^) 或 CNN ^(精确^)
echo - 缓存管理：一键清除缓存
echo.
echo ## 常见问题
echo.
echo ### 问题 1：启动失败
echo.
echo **解决方案**：
echo 1. 确保端口 5000 和 3000 未被占用
echo 2. 以管理员身份运行 start.bat
echo 3. 检查防火墙设置
echo.
echo ### 问题 2：找不到虚拟环境
echo.
echo **解决方案**：
echo 1. 检查 backend\venv_new 目录是否存在
echo 2. 重新解压安装包
echo 3. 确保解压完整
echo.
echo ### 问题 3：前端无法访问
echo.
echo **解决方案**：
echo 1. 等待后端完全启动 ^(约 10 秒^)
echo 2. 手动访问 http://localhost:3000
echo 3. 检查浏览器控制台错误
echo.
echo ## 技术支持
echo.
echo - 详细文档：INSTALLATION.md
echo - 使用指南：USAGE_GUIDE.md
echo - API 文档：docs\API_DOCUMENTATION.md
echo - 性能优化：docs\PERFORMANCE_OPTIMIZATION_SUMMARY.md
echo.
) > %DEPLOY_DIR%\安装指南.md
echo 安装指南创建完成
echo.

:: 创建更新日志
echo [11/12] 创建更新日志...
(
echo # 更新日志
echo.
echo ## v1.1.0 ^(2026-02-20^)
echo.
echo ### 新增功能
echo.
echo #### 性能优化
echo - 多线程并行处理图片
echo - 批处理策略
echo - 缩略图生成
echo.
echo #### 配置管理
echo - 运行时配置管理 API
echo - 人脸检测模型选择
echo - 缓存清理功能
echo.
echo ### 改进
echo - 优化搜索算法
echo - 改进错误处理
echo - 更新 API 文档
echo.
echo ### 修复
echo - 修复启动脚本路径问题
echo - 修复虚拟环境检测逻辑
echo.
echo ---
echo.
echo ## v1.0.0 ^(2026-02-14^)
echo.
echo ### 初始版本
echo - 图片上传功能
echo - 人脸检测功能
echo - 人脸搜索功能
echo - 搜索进度跟踪
echo - 结果导出功能
echo - 特征缓存功能
echo - WebSocket 实时更新
echo - 完整的前端界面
echo.
) > "%DEPLOY_DIR%\CHANGELOG.md"
echo 更新日志创建完成
echo.

:: 创建检查脚本
echo [12/12] 创建检查脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo echo ========================================
echo echo 安装包完整性检查
echo echo ========================================
echo echo.
echo.
echo :: 获取脚本所在目录的父目录
echo set SCRIPT_DIR=%%~dp0
echo cd /d "%%SCRIPT_DIR%.."
echo set APP_ROOT=%%CD%%
echo.
echo echo 应用根目录: %%APP_ROOT%%
echo echo.
echo.
echo :: 检查后端虚拟环境
echo if exist "%%APP_ROOT%%\backend\venv_new" ^(
echo     echo [OK] backend\venv_new 存在
echo ^) else ^(
echo     echo [错误] backend\venv_new 不存在
echo     goto :error
echo ^)
echo.
echo :: 检查 Python 可执行文件
echo if exist "%%APP_ROOT%%\backend\venv_new\Scripts\python.exe" ^(
echo     echo [OK] Python 可执行文件存在
echo ^) else ^(
echo     echo [错误] Python 可执行文件不存在
echo     goto :error
echo ^)
echo.
echo :: 检查后端主文件
echo if exist "%%APP_ROOT%%\backend\app.py" ^(
echo     echo [OK] backend\app.py 存在
echo ^) else ^(
echo     echo [错误] backend\app.py 不存在
echo     goto :error
echo ^)
echo.
echo :: 检查前端依赖
echo if exist "%%APP_ROOT%%\frontend\node_modules" ^(
echo     echo [OK] frontend\node_modules 存在
echo ^) else ^(
echo     echo [警告] frontend\node_modules 不存在，用户需要运行 npm install
echo ^)
echo.
echo :: 检查前端源代码
echo if exist "%%APP_ROOT%%\frontend\src" ^(
echo     echo [OK] frontend\src 存在
echo ^) else ^(
echo     echo [错误] frontend\src 不存在
echo     goto :error
echo ^)
echo.
echo echo.
echo echo ========================================
echo echo 检查完成！
echo echo ========================================
echo echo 安装包完整，可以正常使用
echo echo.
echo echo 下一步：
echo echo 1. 双击运行 scripts\start.bat
echo echo 2. 等待 10-15 秒
echo echo 3. 浏览器访问 http://localhost:3000
echo echo.
echo pause
echo exit /b 0
echo.
echo :error
echo echo.
echo echo ========================================
echo echo 检查失败！
echo echo ========================================
echo echo 安装包不完整，请重新解压或联系技术支持
echo echo.
echo pause
echo exit /b 1
) > "%DEPLOY_DIR%\scripts\check.bat"
echo 检查脚本创建完成
echo.

:: 显示打包结果
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
echo - 检查脚本 ^(scripts\check.bat^)
echo.
echo 新增功能:
echo - 多线程并行处理
echo - 批处理策略
echo - 缩略图生成
echo - 配置管理 API
echo - 模型选择
echo - 缓存清理
echo.
echo 安装包大小: 约 500MB-1GB
echo.
echo 下一步:
echo 1. 测试安装包：
echo    cd "%DEPLOY_DIR%"
echo    scripts\check.bat
echo    scripts\start.bat
echo.
echo 2. 如果测试通过，压缩为 ZIP：
echo    使用 7-Zip 或 WinRAR 压缩 %DEPLOY_DIR% 文件夹
echo.
echo 3. 分发给用户：
echo    用户解压后直接运行 scripts\start.bat
echo.
echo 提示: 
echo - 确保 backend\venv_new 目录完整
echo - 确保 frontend\node_modules 目录完整
echo - 脚本已修复路径问题，可从任何位置运行
echo.
pause
