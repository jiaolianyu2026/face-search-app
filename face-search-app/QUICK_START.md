# 快速开始指南

## 🚀 当前项目状态

✅ **任务 1 已完成**：项目结构和核心接口已搭建
- 目录结构已创建
- 数据模型已实现并测试通过
- 配置文件已创建
- 6/7 依赖包已安装

⚠️ **待完成**：安装 face_recognition 包

## 📦 依赖安装状态

| 包名 | 状态 |
|------|------|
| Python 3.14.3 | ✅ |
| opencv-python | ✅ |
| numpy | ✅ |
| Pillow | ✅ |
| Flask | ✅ |
| Flask-CORS | ✅ |
| **face_recognition** | ❌ 待安装 |

## 🔧 立即行动

### 选项 1：安装系统级 CMake（推荐）

```bash
# 1. 下载并安装 CMake
# 访问 https://cmake.org/download/
# 勾选 "Add CMake to the system PATH"

# 2. 打开新终端，验证安装
cmake --version

# 3. 清理并安装
cd backend
.\venv\Scripts\activate
pip uninstall cmake -y
pip install --no-cache-dir dlib face_recognition

# 4. 验证
python check_dependencies.py
```

### 选项 2：使用预编译包

```bash
# 1. 下载 dlib wheel 文件
# 访问 https://github.com/z-mahmud22/Dlib_Windows_Python3.x

# 2. 安装
cd backend
.\venv\Scripts\activate
pip install 下载路径\dlib-xxx.whl
pip install face_recognition

# 3. 验证
python check_dependencies.py
```

## 📖 详细文档

- **依赖状态报告**：`DEPENDENCY_STATUS.md`
- **完整安装指南**：`backend/DEPENDENCY_INSTALLATION_GUIDE.md`
- **项目结构说明**：`backend/PROJECT_STRUCTURE.md`
- **任务列表**：`.kiro/specs/face-recognition-search/tasks.md`

## ✅ 验证安装

```bash
cd backend
.\venv\Scripts\activate
python check_dependencies.py
```

期望输出：
```
✅ 所有依赖包已正确安装！
可以继续执行任务 2：实现图片上传模块
```

## 🎯 下一步

依赖安装完成后：
1. 打开 `.kiro/specs/face-recognition-search/tasks.md`
2. 开始任务 2：实现图片上传模块

## 💡 提示

- 安装 CMake 后必须重启终端
- 使用 `--no-cache-dir` 避免缓存问题
- 遇到问题查看 `DEPENDENCY_STATUS.md` 的故障排除部分
