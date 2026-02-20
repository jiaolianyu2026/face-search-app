# 快速参考 - Quick Reference

## 🚀 常用命令

### 安装和启动

```batch
# 首次安装
scripts\install.bat

# 启动应用
scripts\start.bat

# 停止应用
scripts\stop.bat
```

### 访问地址

- **前端界面**：http://localhost:3000
- **后端 API**：http://localhost:5000

---

## 📦 部署相关

### 创建部署包

```batch
# 打包
scripts\package.bat

# 测试部署包
scripts\test_package.bat

# 构建前端生产版本
scripts\build_frontend.bat
```

---

## 🔧 开发命令

### 后端

```batch
# 激活虚拟环境
cd backend
venv\Scripts\activate.bat

# 运行后端
python app.py

# 运行测试
pytest tests/ -v

# 运行属性测试
pytest tests/test_*_properties.py -v

# 检查依赖
python check_dependencies.py
```

### 前端

```batch
# 安装依赖
cd frontend
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

---

## 📝 日志和调试

### 查看日志

```batch
# 查看后端日志
type backend\app.log

# 实时监控日志
powershell Get-Content backend\app.log -Tail 20 -Wait

# 查看最后 50 行
powershell Get-Content backend\app.log -Tail 50
```

### 检查服务状态

```batch
# 检查端口占用
netstat -ano | findstr :3000
netstat -ano | findstr :5000

# 结束进程（替换 PID）
taskkill /F /PID <PID>
```

---

## 🗂️ 文件位置

### 重要目录

```
backend/temp_uploads/    # 上传的图片
backend/cache/           # 人脸特征缓存
backend/app.log          # 后端日志
frontend/dist/           # 前端构建输出
```

### 配置文件

```
backend/config.py        # 后端配置
.env                     # 环境变量
deploy_config.json       # 部署配置
```

---

## 🔍 故障排查

### 常见问题

| 问题 | 解决方案 |
|-----|---------|
| 端口被占用 | `netstat -ano \| findstr :5000` 查找进程并结束 |
| Python 未找到 | 重新安装 Python，勾选"Add to PATH" |
| Node.js 未找到 | 重新安装 Node.js |
| 依赖安装失败 | 使用国内镜像源 |
| 人脸检测失败 | 检查图片格式和大小，查看日志 |

### 重置应用

```batch
# 停止服务
scripts\stop.bat

# 清理临时文件
rmdir /s /q backend\temp_uploads
rmdir /s /q backend\cache
del backend\app.log

# 重新创建目录
mkdir backend\temp_uploads
mkdir backend\cache

# 重启服务
scripts\start.bat
```

---

## 🧪 测试

### 运行测试

```batch
# 所有测试
pytest tests/ -v

# 单个模块
pytest tests/test_face_detection.py -v

# 带覆盖率
pytest tests/ --cov=backend --cov-report=html

# 只运行属性测试
pytest tests/test_*_properties.py -v
```

---

## 📊 性能优化

### 清理缓存

```batch
# 清理人脸特征缓存
del backend\cache\face_cache.db

# 清理上传文件
del /q backend\temp_uploads\*
```

### 配置调整

编辑 `backend/config.py`：

```python
# 相似度阈值（越高越严格）
SIMILARITY_THRESHOLD = 0.6

# 最大文件大小（MB）
MAX_FILE_SIZE_MB = 10

# 批处理大小
BATCH_SIZE = 100
```

---

## 🔐 安全

### 检查配置

```batch
# 确保没有 .env 文件泄露
dir .env

# 检查 CORS 配置
findstr "CORS" backend\app.py
```

---

## 📚 文档

### 主要文档

| 文档 | 用途 |
|-----|------|
| `INSTALLATION.md` | 详细安装指南 |
| `USAGE_GUIDE.md` | 使用说明 |
| `README.md` | 项目概述 |
| `RELEASE_NOTES.md` | 版本信息 |
| `DEPLOYMENT_CHECKLIST.md` | 部署清单 |
| `QUICK_REFERENCE.md` | 本文档 |

---

## 💡 提示

### 开发技巧

1. **使用虚拟环境**
   ```batch
   cd backend
   venv\Scripts\activate.bat
   ```

2. **实时日志监控**
   ```batch
   powershell Get-Content backend\app.log -Tail 20 -Wait
   ```

3. **快速重启**
   ```batch
   scripts\stop.bat && scripts\start.bat
   ```

### 性能建议

1. 上传前压缩图片（< 2MB）
2. 定期清理缓存
3. 搜索文件夹不要太大（< 1000 张）
4. 调整相似度阈值减少匹配数量

---

## 🆘 获取帮助

### 查看文档

```batch
# 打开安装手册
start INSTALLATION.md

# 打开使用指南
start USAGE_GUIDE.md
```

### 联系支持

- 📧 技术支持：[support@example.com]
- 🐛 Bug 报告：[GitHub Issues]
- 💬 反馈建议：[feedback@example.com]

---

## 📌 快捷键

### Windows 命令提示符

| 快捷键 | 功能 |
|-------|------|
| `Ctrl + C` | 停止当前进程 |
| `Ctrl + A` | 全选 |
| `Ctrl + V` | 粘贴 |
| `↑` / `↓` | 历史命令 |
| `Tab` | 自动补全 |

### 浏览器

| 快捷键 | 功能 |
|-------|------|
| `F12` | 打开开发者工具 |
| `Ctrl + Shift + R` | 强制刷新 |
| `Ctrl + Shift + I` | 打开检查器 |

---

## 🔄 版本管理

### 检查版本

```batch
# Python 版本
python --version

# Node.js 版本
node --version

# npm 版本
npm --version

# 应用版本
type VERSION.txt
```

### 更新依赖

```batch
# 更新 Python 依赖
cd backend
venv\Scripts\activate.bat
pip install --upgrade -r requirements.txt

# 更新 Node.js 依赖
cd frontend
npm update
```

---

**最后更新**：2026-02-14  
**版本**：1.0.0
