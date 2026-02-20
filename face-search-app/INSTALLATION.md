# 人脸识别搜索应用 - 安装手册

## 目录

1. [系统要求](#系统要求)
2. [快速安装](#快速安装)
3. [详细安装步骤](#详细安装步骤)
4. [启动应用](#启动应用)
5. [验证安装](#验证安装)
6. [常见问题](#常见问题)
7. [卸载说明](#卸载说明)

---

## 系统要求

### 硬件要求

- **处理器**：Intel Core i5 或更高（推荐 i7）
- **内存**：最低 4GB，推荐 8GB 或更高
- **磁盘空间**：至少 2GB 可用空间
- **显示器**：1280x720 或更高分辨率

### 软件要求

- **操作系统**：Windows 10 或 Windows 11（64位）
- **Python**：3.10 或更高版本
- **Node.js**：16.0 或更高版本
- **浏览器**：Chrome、Edge、Firefox 或 Safari（最新版本）

### 网络要求

- 安装过程需要互联网连接（下载依赖包）
- 运行时不需要互联网连接（本地应用）

---

## 快速安装

如果您熟悉命令行操作，可以按以下步骤快速安装：

```batch
# 1. 解压安装包到目标目录
# 2. 打开命令提示符，进入安装目录
cd C:\path\to\face-recognition-search

# 3. 运行安装脚本
scripts\install.bat

# 4. 启动应用
scripts\start.bat
```

---

## 详细安装步骤

### 步骤 1：安装 Python

1. 访问 Python 官网：https://www.python.org/downloads/
2. 下载 Python 3.10 或更高版本（推荐 3.11）
3. 运行安装程序
4. **重要**：勾选 "Add Python to PATH"
5. 点击 "Install Now"
6. 安装完成后，打开命令提示符验证：
   ```batch
   python --version
   ```
   应该显示类似：`Python 3.11.x`

### 步骤 2：安装 Node.js

1. 访问 Node.js 官网：https://nodejs.org/
2. 下载 LTS 版本（推荐）
3. 运行安装程序，使用默认设置
4. 安装完成后，打开命令提示符验证：
   ```batch
   node --version
   npm --version
   ```
   应该显示版本号

### 步骤 3：解压安装包

1. 将下载的安装包解压到目标目录
   - 推荐路径：`C:\Program Files\FaceRecognitionSearch`
   - 或任何您喜欢的位置
2. 确保路径中没有中文字符（避免潜在问题）
3. 确保您对该目录有读写权限

### 步骤 4：运行安装脚本

1. 打开命令提示符（以管理员身份运行）
2. 进入安装目录：
   ```batch
   cd C:\path\to\face-recognition-search
   ```
3. 运行安装脚本：
   ```batch
   scripts\install.bat
   ```
4. 等待安装完成（可能需要 5-10 分钟）

安装脚本会自动完成以下操作：
- ✅ 检查 Python 和 Node.js 环境
- ✅ 创建 Python 虚拟环境
- ✅ 安装后端依赖（dlib, face_recognition, Flask 等）
- ✅ 安装前端依赖（React, Vite 等）
- ✅ 创建必要的目录

### 步骤 5：验证安装

安装完成后，您应该看到以下目录结构：

```
face-recognition-search/
├── backend/
│   ├── venv/              # Python 虚拟环境
│   ├── temp_uploads/      # 临时上传目录
│   ├── cache/             # 缓存目录
│   └── ...
├── frontend/
│   ├── node_modules/      # Node.js 依赖
│   └── ...
├── scripts/
│   ├── install.bat        # 安装脚本
│   ├── start.bat          # 启动脚本
│   └── stop.bat           # 停止脚本
└── INSTALLATION.md        # 本文档
```

---

## 启动应用

### 方法 1：使用启动脚本（推荐）

1. 双击运行 `scripts\start.bat`
2. 等待 3-5 秒，两个服务窗口会自动打开
3. 浏览器会自动打开应用页面

### 方法 2：手动启动

**启动后端**：
```batch
cd backend
venv\Scripts\activate.bat
python app.py
```

**启动前端**（新开一个命令提示符）：
```batch
cd frontend
npm run dev
```

### 访问应用

- **前端界面**：http://localhost:3000
- **后端 API**：http://localhost:5000

---

## 验证安装

### 1. 检查服务状态

打开浏览器，访问：
- http://localhost:3000 - 应该看到上传界面
- http://localhost:5000 - 应该看到 "Face Recognition Search API is running"

### 2. 测试基本功能

1. 准备一张包含人脸的图片
2. 在前端界面上传图片
3. 等待人脸检测完成
4. 如果能看到检测到的人脸，说明安装成功

### 3. 检查日志

如果遇到问题，查看日志文件：
```batch
type backend\app.log
```

---

## 常见问题

### Q1: 安装脚本报错 "未检测到 Python"

**原因**：Python 未安装或未添加到 PATH

**解决方案**：
1. 重新安装 Python，确保勾选 "Add Python to PATH"
2. 或手动添加 Python 到系统环境变量
3. 重启命令提示符

### Q2: 安装依赖时报错 "pip install failed"

**原因**：网络问题或依赖冲突

**解决方案**：
```batch
# 使用国内镜像源
cd backend
venv\Scripts\activate.bat
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q3: dlib 安装失败

**原因**：dlib 需要 C++ 编译器

**解决方案**：
1. 我们使用 `dlib-bin`（预编译版本）避免此问题
2. 如果仍然失败，尝试：
   ```batch
   pip install dlib-bin --no-cache-dir
   ```

### Q4: 前端依赖安装失败

**原因**：npm 网络问题

**解决方案**：
```batch
# 使用淘宝镜像
cd frontend
npm install --registry=https://registry.npmmirror.com
```

### Q5: 启动后端时报错 "Address already in use"

**原因**：端口 5000 被占用

**解决方案**：
```batch
# 查找占用端口的进程
netstat -ano | findstr :5000

# 结束进程（替换 PID）
taskkill /F /PID <PID>
```

### Q6: 浏览器无法访问 localhost:3000

**原因**：防火墙阻止或服务未启动

**解决方案**：
1. 检查服务是否正常运行
2. 临时关闭防火墙测试
3. 添加防火墙例外规则

### Q7: 人脸检测失败

**原因**：图片质量问题或依赖未正确安装

**解决方案**：
1. 使用清晰的人脸图片
2. 确保图片格式正确（JPG, PNG, WebP）
3. 检查后端日志：`backend\app.log`
4. 重新安装依赖

---

## 停止应用

### 方法 1：使用停止脚本

```batch
scripts\stop.bat
```

### 方法 2：手动停止

在启动服务的命令提示符窗口中按 `Ctrl + C`

---

## 卸载说明

### 完全卸载

1. 停止所有服务：
   ```batch
   scripts\stop.bat
   ```

2. 删除安装目录：
   ```batch
   rmdir /s /q C:\path\to\face-recognition-search
   ```

### 保留数据卸载

如果您想保留上传的图片和缓存：

1. 备份以下目录：
   - `backend\temp_uploads\`
   - `backend\cache\`

2. 然后删除其他文件

---

## 更新说明

### 更新到新版本

1. 备份数据（如上所述）
2. 停止服务
3. 解压新版本安装包
4. 运行 `scripts\install.bat`
5. 恢复备份的数据
6. 启动服务

---

## 技术支持

### 获取帮助

如果遇到问题，请提供以下信息：

1. **系统信息**：
   ```batch
   systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
   python --version
   node --version
   ```

2. **错误日志**：
   ```batch
   type backend\app.log
   ```

3. **错误截图**

### 日志位置

- **后端日志**：`backend\app.log`
- **前端日志**：浏览器控制台（F12）

### 调试模式

如果需要更详细的日志：

1. 编辑 `backend\app.py`
2. 找到 `app.run()` 行
3. 修改为：`app.run(debug=True, host='0.0.0.0', port=5000)`
4. 重启后端服务

---

## 性能优化建议

### 1. 硬件优化

- 使用 SSD 存储应用和缓存
- 增加内存到 16GB（处理大量图片时）
- 使用多核 CPU

### 2. 软件优化

- 定期清理 `backend\temp_uploads\` 目录
- 定期清理 `backend\cache\` 目录（如果太大）
- 关闭不必要的后台程序

### 3. 使用建议

- 上传图片前先压缩（推荐 < 2MB）
- 搜索文件夹不要太大（推荐 < 1000 张图片）
- 调整相似度阈值以减少匹配数量

---

## 附录

### A. 目录结构说明

```
face-recognition-search/
├── backend/                    # 后端应用
│   ├── venv/                  # Python 虚拟环境
│   ├── temp_uploads/          # 临时上传文件
│   ├── cache/                 # 人脸特征缓存
│   ├── app.py                 # Flask 应用主文件
│   ├── config.py              # 配置文件
│   ├── models.py              # 数据模型
│   ├── face_detection.py      # 人脸检测模块
│   ├── face_search.py         # 人脸搜索模块
│   ├── file_scanner.py        # 文件扫描模块
│   ├── similarity.py          # 相似度计算模块
│   ├── cache_module.py        # 缓存模块
│   ├── image_export.py        # 图片导出模块
│   ├── error_handlers.py      # 错误处理模块
│   ├── logger.py              # 日志模块
│   └── requirements.txt       # Python 依赖
├── frontend/                   # 前端应用
│   ├── node_modules/          # Node.js 依赖
│   ├── src/                   # 源代码
│   │   ├── components/        # React 组件
│   │   ├── App.jsx           # 主应用组件
│   │   └── main.jsx          # 入口文件
│   ├── package.json           # Node.js 配置
│   └── vite.config.js         # Vite 配置
├── scripts/                    # 脚本文件
│   ├── install.bat            # 安装脚本
│   ├── start.bat              # 启动脚本
│   ├── stop.bat               # 停止脚本
│   └── build_frontend.bat     # 前端构建脚本
├── tests/                      # 测试文件
├── .kiro/                      # Kiro 配置
│   ├── specs/                 # 功能规格
│   └── steering/              # 项目指导文档
├── README.md                   # 项目说明
├── INSTALLATION.md             # 本文档
└── USAGE_GUIDE.md             # 使用指南
```

### B. 端口说明

| 服务 | 端口 | 说明 |
|-----|------|------|
| 前端 | 3000 | React 开发服务器 |
| 后端 | 5000 | Flask API 服务器 |

### C. 配置文件说明

**backend/config.py**：
- `MAX_FILE_SIZE_MB`: 最大文件大小（默认 10MB）
- `SIMILARITY_THRESHOLD`: 相似度阈值（默认 0.6）
- `SUPPORTED_FORMATS`: 支持的图片格式

### D. 依赖版本

**后端依赖**：
- Python: 3.10+
- Flask: 3.0+
- face_recognition: 1.3.0+
- dlib-bin: 19.7.0+
- opencv-python: 4.8.0+
- numpy: 1.26.0+
- Pillow: 10.0.0+

**前端依赖**：
- Node.js: 16+
- React: 18.2.0
- Vite: 5.0.8
- axios: 1.6.2

---

**版本**：1.0.0  
**发布日期**：2026-02-14  
**文档更新**：2026-02-14
