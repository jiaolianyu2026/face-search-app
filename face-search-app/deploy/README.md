# 人脸识别搜索应用 - 部署包

## 📦 包含内容

```
FaceRecognitionSearch_v1.0.0/
├── backend/              # 后端应用程序
│   ├── *.py             # Python 源代码
│   └── requirements.txt # Python 依赖列表
├── frontend/            # 前端应用程序
│   ├── src/            # React 源代码
│   ├── package.json    # Node.js 依赖列表
│   └── vite.config.js  # Vite 配置
├── scripts/             # 自动化脚本
│   ├── install.bat     # 安装脚本
│   ├── start.bat       # 启动脚本
│   ├── stop.bat        # 停止脚本
│   └── build_frontend.bat  # 前端构建脚本
├── tests/               # 测试文件
├── docs/                # 文档
├── README.md            # 项目说明
├── INSTALLATION.md      # 详细安装手册
├── USAGE_GUIDE.md       # 使用指南
├── .env.example         # 环境变量示例
├── deploy_config.json   # 部署配置
└── VERSION.txt          # 版本信息
```

## 🚀 快速开始

### 第一次安装

1. **解压安装包**
   ```
   解压到目标目录，例如：C:\FaceRecognitionSearch
   ```

2. **安装依赖**
   ```batch
   双击运行 scripts\install.bat
   等待 5-10 分钟完成安装
   ```

3. **启动应用**
   ```batch
   双击运行 scripts\start.bat
   浏览器会自动打开 http://localhost:3000
   ```

### 日常使用

- **启动应用**：双击 `scripts\start.bat`
- **停止应用**：双击 `scripts\stop.bat`
- **查看文档**：打开 `USAGE_GUIDE.md`

## 💻 系统要求

### 最低配置

- **操作系统**：Windows 10 (64位)
- **处理器**：Intel Core i5 或同等性能
- **内存**：4GB RAM
- **磁盘空间**：2GB 可用空间
- **软件**：Python 3.10+, Node.js 16+

### 推荐配置

- **操作系统**：Windows 11 (64位)
- **处理器**：Intel Core i7 或更高
- **内存**：8GB RAM 或更高
- **磁盘空间**：5GB 可用空间（包含缓存）
- **软件**：Python 3.11+, Node.js 18+

## 📋 版本信息

- **版本号**：1.0.0
- **发布日期**：2026-02-14
- **构建类型**：生产版本
- **支持平台**：Windows 10/11 (64位)

## 🔧 核心功能

- ✅ 图片上传（支持 JPG, PNG, WebP）
- ✅ 人脸检测（基于 dlib 深度学习模型）
- ✅ 人脸搜索（128维特征向量匹配）
- ✅ 实时进度跟踪
- ✅ 结果导出（自动创建文件夹）
- ✅ 特征缓存（SQLite 数据库）

## 📚 文档说明

| 文档 | 说明 |
|-----|------|
| `INSTALLATION.md` | 详细安装步骤和故障排查 |
| `USAGE_GUIDE.md` | 使用指南和功能说明 |
| `QUICK_REFERENCE.md` | 快速参考（常用命令） |
| `README.md` | 项目概述和技术架构 |
| `RELEASE_NOTES.md` | 发布说明和版本信息 |
| `VERSION.txt` | 版本信息和构建详情 |
| `backend/API_DOCUMENTATION.md` | API 接口文档 |

## ⚙️ 配置说明

### 环境变量配置

复制 `.env.example` 为 `.env` 并根据需要修改：

```bash
# 后端端口
FLASK_PORT=5000

# 前端端口
VITE_PORT=3000

# 相似度阈值
SIMILARITY_THRESHOLD=0.6

# 最大文件大小（MB）
MAX_FILE_SIZE_MB=10
```

### 部署配置

编辑 `deploy_config.json` 可以修改：
- 端口设置
- 性能参数
- 安全配置
- 功能开关

## 🛠️ 脚本说明

### install.bat - 安装脚本

自动完成以下操作：
1. 检查 Python 和 Node.js 环境
2. 创建 Python 虚拟环境
3. 安装后端依赖（dlib, face_recognition 等）
4. 安装前端依赖（React, Vite 等）
5. 创建必要的目录

**使用方法**：
```batch
scripts\install.bat
```

### start.bat - 启动脚本

启动前端和后端服务：
- 后端：http://localhost:5000
- 前端：http://localhost:3000

**使用方法**：
```batch
scripts\start.bat
```

### stop.bat - 停止脚本

停止所有运行中的服务。

**使用方法**：
```batch
scripts\stop.bat
```

### build_frontend.bat - 前端构建脚本

构建前端生产版本（用于部署到 Web 服务器）。

**使用方法**：
```batch
scripts\build_frontend.bat
```

## 🔍 验证安装

安装完成后，可以通过以下方式验证：

1. **检查服务状态**
   ```
   前端：访问 http://localhost:3000
   后端：访问 http://localhost:5000
   ```

2. **测试基本功能**
   - 上传一张包含人脸的图片
   - 等待人脸检测完成
   - 查看检测结果

3. **查看日志**
   ```batch
   type backend\app.log
   ```

## ❓ 常见问题

### Q: 安装时提示"未检测到 Python"？

**A**: 请先安装 Python 3.10 或更高版本，并确保勾选"Add Python to PATH"。

### Q: 启动时提示"端口被占用"？

**A**: 运行 `scripts\stop.bat` 停止其他服务，或修改配置文件更改端口。

### Q: 人脸检测失败？

**A**: 
1. 确保图片清晰且包含人脸
2. 检查图片格式（支持 JPG, PNG, WebP）
3. 查看后端日志：`backend\app.log`

### Q: 如何更新到新版本？

**A**:
1. 备份 `backend/temp_uploads` 和 `backend/cache` 目录
2. 停止服务
3. 解压新版本覆盖旧文件
4. 运行 `scripts\install.bat`
5. 恢复备份数据

更多问题请查看 `INSTALLATION.md` 的"常见问题"章节。

## 📞 技术支持

如果遇到问题，请提供：
1. 系统信息（Windows 版本、Python 版本、Node.js 版本）
2. 错误截图
3. 后端日志（`backend\app.log`）
4. 操作步骤

## 📄 许可证

MIT License

---

**重要提示**：
- 首次安装请务必阅读 `INSTALLATION.md`
- 使用前请查看 `USAGE_GUIDE.md`
- 遇到问题请先查看文档的"常见问题"章节
