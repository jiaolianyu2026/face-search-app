# 依赖包安装状态与操作方案

## 📊 当前状态总结

### ✅ 已完成安装（6/7）

| 包名 | 需要版本 | 已安装版本 | 状态 |
|------|---------|-----------|------|
| opencv-python | ≥4.8.0 | 4.13.0.92 | ✅ 已安装 |
| numpy | ≥1.26.0 | 2.4.2 | ✅ 已安装 |
| Pillow | ≥10.0.0 | 12.1.1 | ✅ 已安装 |
| Flask | ≥3.0.0 | 3.1.2 | ✅ 已安装 |
| Flask-CORS | ≥4.0.0 | 6.0.2 | ✅ 已安装 |
| Python | - | 3.14.3 | ✅ 已安装 |

### ❌ 待安装（1/7）

| 包名 | 需要版本 | 状态 | 原因 |
|------|---------|------|------|
| face_recognition | ≥1.3.0 | ❌ 未安装 | 依赖 dlib，dlib 构建失败 |

## 🔍 问题诊断

### 核心问题
**dlib 无法编译安装**

### 问题原因
1. 虚拟环境中有 Python 的 `cmake` 包（4.2.1）
2. 这个 cmake 包与 dlib 构建过程冲突
3. dlib 需要系统级的 CMake 可执行文件，而不是 Python 包
4. 构建时出现 `ModuleNotFoundError: No module named 'cmake'` 错误

### 技术细节
```
错误信息：
- Building wheel for dlib (pyproject.toml) ... error
- ModuleNotFoundError: No module named 'cmake'
- CMake is not installed on your system!
```

## 🛠️ 操作方案

### 方案 A：安装系统级 CMake（推荐）⭐

**优点**：官方推荐方式，最稳定
**缺点**：需要下载安装额外软件

#### 操作步骤：

1. **下载 CMake**
   - 访问：https://cmake.org/download/
   - 下载：`cmake-3.xx.x-windows-x86_64.msi`（最新稳定版）

2. **安装 CMake**
   ```
   - 运行下载的 .msi 文件
   - ⚠️ 重要：勾选 "Add CMake to the system PATH for all users"
   - 完成安装
   ```

3. **验证安装**（打开新的命令提示符）
   ```cmd
   cmake --version
   ```
   应该显示：`cmake version 3.xx.x`

4. **清理虚拟环境中的 cmake 包**
   ```cmd
   cd backend
   .\venv\Scripts\activate
   pip uninstall cmake -y
   ```

5. **安装 face_recognition**
   ```cmd
   pip install --no-cache-dir dlib
   pip install --no-cache-dir face_recognition
   ```

6. **验证安装**
   ```cmd
   python check_dependencies.py
   ```

---

### 方案 B：使用预编译 wheel 文件

**优点**：无需编译，安装快速
**缺点**：需要找到匹配的 wheel 文件，可能不是最新版本

#### 操作步骤：

1. **下载预编译 dlib wheel**
   - 访问：https://github.com/z-mahmud22/Dlib_Windows_Python3.x
   - 或搜索：`dlib wheel python 3.14 windows`
   - 下载对应 Python 3.14 的 .whl 文件

2. **安装 wheel 文件**
   ```cmd
   cd backend
   .\venv\Scripts\activate
   pip install 下载路径\dlib-xx.x.x-cp314-cp314-win_amd64.whl
   pip install face_recognition
   ```

3. **验证安装**
   ```cmd
   python check_dependencies.py
   ```

---

### 方案 C：降级 Python 版本

**优点**：预编译包更容易找到
**缺点**：需要重新创建虚拟环境

#### 操作步骤：

1. **安装 Python 3.11 或 3.10**
   - 从 python.org 下载安装

2. **创建新虚拟环境**
   ```cmd
   cd backend
   python3.11 -m venv venv_py311
   .\venv_py311\Scripts\activate
   ```

3. **安装依赖**
   ```cmd
   pip install -r requirements.txt
   ```

---

### 方案 D：使用 Conda 环境（终极方案）

**优点**：Conda 有预编译的 dlib，安装最简单
**缺点**：需要安装 Anaconda/Miniconda

#### 操作步骤：

1. **安装 Miniconda**
   - 访问：https://docs.conda.io/en/latest/miniconda.html
   - 下载并安装

2. **创建 Conda 环境**
   ```cmd
   conda create -n face-search python=3.11
   conda activate face-search
   ```

3. **安装依赖**
   ```cmd
   conda install -c conda-forge dlib
   pip install face_recognition opencv-python Flask Flask-CORS
   ```

4. **验证安装**
   ```cmd
   cd backend
   python check_dependencies.py
   ```

## 📝 推荐操作流程

**我的建议：先尝试方案 A，如果失败再尝试方案 B**

1. ✅ 方案 A（系统级 CMake）- 最标准的方式
2. ✅ 方案 B（预编译 wheel）- 如果方案 A 失败
3. ✅ 方案 D（Conda）- 如果前两个都失败
4. ⚠️ 方案 C（降级 Python）- 最后的选择

## 🔧 验证工具

安装完成后，运行以下命令验证：

```cmd
cd backend
.\venv\Scripts\activate
python check_dependencies.py
```

或手动测试：

```cmd
python -c "import face_recognition; print('✅ face_recognition 安装成功')"
python -c "import dlib; print('✅ dlib 安装成功')"
```

## 📚 相关文档

- `backend/DEPENDENCY_INSTALLATION_GUIDE.md` - 详细安装指南
- `backend/INSTALLATION.md` - 原始安装说明
- `backend/check_dependencies.py` - 依赖检查脚本

## ❓ 需要帮助？

如果遇到问题，请提供：
1. 选择的方案编号
2. 执行的命令
3. 完整的错误信息
4. `python --version` 和 `pip list` 的输出
