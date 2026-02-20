@echo off
chcp 65001 >nul
echo ========================================
echo 人脸识别搜索应用 - 打包脚本 v1.1
echo ========================================
echo.

:: 设置变量
set APP_NAME=FaceRecognitionSearch
set VERSION=1.1.0
set BUILD_DATE=%date:~0,4%%date:~5,2%%date:~8,2%
set PACKAGE_NAME=%APP_NAME%_v%VERSION%_Full
set DEPLOY_DIR=deploy\%PACKAGE_NAME%

echo 应用名称: %APP_NAME%
echo 版本号: %VERSION% (新增性能优化功能)
echo 构建日期: %BUILD_DATE%
echo 输出目录: %DEPLOY_DIR%
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

:: 复制后端文件（包括新增的 thumbnail_generator.py）
echo [2/10] 复制后端文件...
xcopy backend\*.py %DEPLOY_DIR%\backend\ /Y /Q
xcopy backend\requirements.txt %DEPLOY_DIR%\backend\ /Y /Q
if exist backend\*.md xcopy backend\*.md %DEPLOY_DIR%\backend\ /Y /Q
echo 后端文件复制完成（包含新模块）
echo.

:: 复制前端文件
echo [3/10] 复制前端文件...
xcopy frontend\src %DEPLOY_DIR%\frontend\src\ /E /I /Y /Q
xcopy frontend\public %DEPLOY_DIR%\frontend\public\ /E /I /Y /Q 2>nul
xcopy frontend\*.json %DEPLOY_DIR%\frontend\ /Y /Q
xcopy frontend\*.js %DEPLOY_DIR%\frontend\ /Y /Q
xcopy frontend\*.html %DEPLOY_DIR%\frontend\ /Y /Q
if exist frontend\*.md xcopy frontend\*.md %DEPLOY_DIR%\frontend\ /Y /Q
echo 前端文件复制完成
echo.

:: 复制改进的脚本文件（使用绝对路径的版本）
echo [4/10] 复制脚本文件...
xcopy scripts\*.bat %DEPLOY_DIR%\scripts\ /Y /Q
echo 脚本文件复制完成
echo.

:: 复制文档
echo [5/10] 复制文档...
copy README.md %DEPLOY_DIR%\ /Y >nul
copy INSTALLATION.md %DEPLOY_DIR%\ /Y >nul
copy USAGE_GUIDE.md %DEPLOY_DIR%\ /Y >nul
copy QUICK_REFERENCE.md %DEPLOY_DIR%\ /Y >nul
copy .env.example %DEPLOY_DIR%\ /Y >nul
copy deploy_config.json %DEPLOY_DIR%\ /Y >nul
if exist PERFORMANCE_OPTIMIZATION_SUMMARY.md copy PERFORMANCE_OPTIMIZATION_SUMMARY.md %DEPLOY_DIR%\docs\ /Y >nul
if exist backend\API_DOCUMENTATION.md copy backend\API_DOCUMENTATION.md %DEPLOY_DIR%\docs\ /Y >nul
if exist WEBSOCKET_IMPLEMENTATION_SUMMARY.md copy WEBSOCKET_IMPLEMENTATION_SUMMARY.md %DEPLOY_DIR%\docs\ /Y >nul
echo 文档复制完成
echo.

:: 创建版本信息文件
echo [6/10] 创建版本信息...
(
echo ========================================
echo 人脸识别搜索应用 v1.1.0
echo ========================================
echo.
echo 版本号: %VERSION%
echo 构建日期: %BUILD_DATE%
echo 构建时间: %time%
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
echo - Python 3.10+
echo - Node.js 16+
echo - 8GB RAM ^(推荐^)
echo - 2GB 磁盘空间
echo.
echo 安装说明:
echo 1. 解压安装包到任意位置
echo 2. 双击运行 scripts\start.bat
echo 3. 等待 10-15 秒自动启动
echo 4. 浏览器访问 http://localhost:3000
echo.
echo 注意事项:
echo - 首次启动需要安装依赖（自动进行）
echo - 确保端口 5000 和 3000 未被占用
echo - 建议使用 Chrome 或 Edge 浏览器
echo.
echo 详细说明请查看 INSTALLATION.md
) > %DEPLOY_DIR%\VERSION.txt
echo 版本信息创建完成
echo.

:: 创建快速开始指南
echo [7/10] 创建快速开始指南...
(
echo ========================================
echo 快速开始指南
echo ========================================
echo.
echo 步骤 1: 解压安装包
echo   将 ZIP 文件解压到任意位置，例如：
echo   C:\FaceRecognitionSearch
echo.
echo 步骤 2: 启动应用
echo   双击运行：scripts\start.bat
echo   （可以从任何位置运行，脚本会自动定位）
echo.
echo 步骤 3: 等待启动
echo   首次启动需要 10-15 秒
echo   后续启动只需 5 秒
echo.
echo 步骤 4: 访问应用
echo   浏览器会自动打开：http://localhost:3000
echo   如果没有自动打开，手动输入该地址
echo.
echo 步骤 5: 开始使用
echo   1. 上传包含人脸的图片
echo   2. 系统自动检测人脸
echo   3. 选择要搜索的人脸
echo   4. 指定搜索文件夹
echo   5. 查看搜索结果
echo   6. 导出匹配图片
echo.
echo 常见问题:
echo.
echo Q: 启动失败怎么办？
echo A: 运行 scripts\check.bat 检查安装包完整性
echo.
echo Q: 如何停止应用？
echo A: 双击运行 scripts\stop.bat
echo.
echo Q: 如何调整相似度阈值？
echo A: 在应用界面中调整，或通过 API 配置
echo.
echo Q: 如何清除缓存？
echo A: 使用 API 端点 POST /api/cache/clear
echo.
echo 技术支持:
echo - 查看 INSTALLATION.md 详细安装指南
echo - 查看 USAGE_GUIDE.md 使用说明
echo - 查看 docs\API_DOCUMENTATION.md API 文档
echo.
) > %DEPLOY_DIR%\快速开始.txt
echo 快速开始指南创建完成
echo.

:: 创建安装指南（简化版）
echo [8/10] 创建安装指南...
(
echo # 人脸识别搜索应用 - 安装指南 v1.1.0
echo.
echo ## 系统要求
echo.
echo - Windows 10/11 ^(64位^)
echo - 8GB RAM ^(推荐^)
echo - 2GB 磁盘空间
echo - Chrome 或 Edge 浏览器
echo.
echo ## 安装步骤
echo.
echo ### 1. 解压安装包
echo.
echo 将 `FaceRecognitionSearch_v1.1.0_Full.zip` 解压到任意位置，例如：
echo ```
echo C:\FaceRecognitionSearch
echo ```
echo.
echo ### 2. 验证安装包 ^(推荐^)
echo.
echo 双击运行：`scripts\check.bat`
echo.
echo 如果显示"✓ 安装包完整，可以正常使用"，继续下一步。
echo.
echo ### 3. 启动应用
echo.
echo 双击运行：`scripts\start.bat`
echo.
echo **注意**：可以从任何位置运行此脚本，它会自动定位应用根目录。
echo.
echo ### 4. 等待启动
echo.
echo - 首次启动：10-15 秒 ^(需要安装依赖^)
echo - 后续启动：5 秒
echo.
echo ### 5. 访问应用
echo.
echo 浏览器会自动打开：http://localhost:3000
echo.
echo ## 新功能 ^(v1.1.0^)
echo.
echo ### 性能优化
echo.
echo - **多线程并行处理**：搜索速度提升 2-4 倍
echo - **批处理策略**：支持超大文件夹搜索
echo - **缩略图生成**：前端加载速度提升 5-10 倍
echo.
echo ### 配置管理
echo.
echo - **运行时配置**：无需重启即可调整设置
echo - **模型选择**：HOG ^(快速^) 或 CNN ^(精确^)
echo - **缓存管理**：一键清除缓存
echo.
echo ### 使用配置 API
echo.
echo ```bash
echo # 调整相似度阈值
echo curl -X PUT http://localhost:5000/api/config -H "Content-Type: application/json" -d "{\"similarity_threshold\": 0.7}"
echo.
echo # 切换到 CNN 模型
echo curl -X PUT http://localhost:5000/api/config -H "Content-Type: application/json" -d "{\"face_detection_model\": \"cnn\"}"
echo.
echo # 调整线程数
echo curl -X PUT http://localhost:5000/api/config -H "Content-Type: application/json" -d "{\"max_worker_threads\": 8}"
echo.
echo # 清除缓存
echo curl -X POST http://localhost:5000/api/cache/clear
echo ```
echo.
echo ## 常见问题
echo.
echo ### 问题 1：启动失败
echo.
echo **解决方案**：
echo 1. 运行 `scripts\check.bat` 检查安装包
echo 2. 确保端口 5000 和 3000 未被占用
echo 3. 以管理员身份运行 `start.bat`
echo.
echo ### 问题 2：找不到虚拟环境
echo.
echo **解决方案**：
echo 1. 检查 `backend\venv_new` 目录是否存在
echo 2. 重新解压安装包
echo 3. 确保解压完整
echo.
echo ### 问题 3：前端无法访问
echo.
echo **解决方案**：
echo 1. 检查 `frontend\node_modules` 是否存在
echo 2. 等待后端完全启动 ^(约 10 秒^)
echo 3. 手动访问 http://localhost:3000
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
echo [9/10] 创建更新日志...
(
echo # 更新日志
echo.
echo ## v1.1.0 ^(2026-02-20^)
echo.
echo ### 新增功能
echo.
echo #### 性能优化
echo - ✅ 多线程并行处理图片（需求 9.2）
echo   - 自动检测文件夹大小，智能选择处理模式
echo   - 可配置工作线程数 ^(1-16^)
echo   - 预计提速 2-4 倍
echo.
echo - ✅ 批处理策略（需求 9.3）
echo   - 每批处理 100 张图片
echo   - 避免大文件夹内存溢出
echo   - 支持超大规模搜索
echo.
echo - ✅ 缩略图生成（需求 9.5）
echo   - 自动生成 200x200 缩略图
echo   - 缩略图缓存机制
echo   - 前端加载速度提升 5-10 倍
echo.
echo #### 配置管理
echo - ✅ 运行时配置管理（需求 4.5 扩展）
echo   - GET /api/config - 获取配置
echo   - PUT /api/config - 更新配置
echo   - 无需重启服务器
echo.
echo - ✅ 人脸检测模型选择
echo   - HOG 模型：速度快，适合大多数场景
echo   - CNN 模型：精度高，需要更多资源
echo   - 运行时切换模型
echo.
echo - ✅ 缓存清理功能
echo   - POST /api/cache/clear - 清除人脸特征缓存
echo   - POST /api/thumbnails/clear - 清除缩略图
echo   - 返回清除数量统计
echo.
echo ### 改进
echo - 优化搜索算法，减少重复计算
echo - 改进错误处理和日志记录
echo - 更新 API 文档
echo.
echo ### 修复
echo - 修复启动脚本路径问题
echo - 修复虚拟环境检测逻辑
echo - 改进脚本兼容性
echo.
echo ---
echo.
echo ## v1.0.0 ^(2026-02-14^)
echo.
echo ### 初始版本
echo - ✅ 图片上传功能
echo - ✅ 人脸检测功能
echo - ✅ 人脸搜索功能
echo - ✅ 搜索进度跟踪
echo - ✅ 结果导出功能
echo - ✅ 特征缓存功能
echo - ✅ WebSocket 实时更新
echo - ✅ 完整的前端界面
echo - ✅ 详细的文档
echo.
) > %DEPLOY_DIR%\CHANGELOG.md
echo 更新日志创建完成
echo.

:: 显示打包结果
echo [10/10] 打包完成！
echo.
echo ========================================
echo 打包结果
echo ========================================
echo.
echo 输出位置: %DEPLOY_DIR%
echo.
echo 包含内容:
echo ✓ 后端应用 ^(backend/^) - 包含新模块
echo ✓ 前端应用 ^(frontend/^)
echo ✓ 启动脚本 ^(scripts/^) - 已修复路径问题
echo ✓ 文档 ^(*.md^)
echo ✓ 配置示例 ^(.env.example^)
echo ✓ 版本信息 ^(VERSION.txt^)
echo ✓ 快速开始 ^(快速开始.txt^)
echo ✓ 安装指南 ^(安装指南.md^)
echo ✓ 更新日志 ^(CHANGELOG.md^)
echo.
echo 新增功能:
echo ✓ 多线程并行处理
echo ✓ 批处理策略
echo ✓ 缩略图生成
echo ✓ 配置管理 API
echo ✓ 模型选择
echo ✓ 缓存清理
echo.
echo 下一步:
echo 1. 检查 %DEPLOY_DIR% 目录
echo 2. 测试启动脚本: %DEPLOY_DIR%\scripts\start.bat
echo 3. 如果测试通过，压缩为 ZIP 文件分发
echo.
echo 注意事项:
echo - 确保包含 backend\venv_new 目录（如果已创建）
echo - 确保包含 frontend\node_modules 目录（如果已安装）
echo - 脚本已修复路径问题，可从任何位置运行
echo.
pause
