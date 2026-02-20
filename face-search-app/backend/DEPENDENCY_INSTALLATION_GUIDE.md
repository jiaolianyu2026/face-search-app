# 依赖安装完整指南

## 当前依赖状态

### ✅ 已安装的包
- Python 3.14.3
- numpy 2.4.2
- opencv-python 4.13.0.92
- Pillow 12.1.1
- Flask 3.1.2
- Flask-CORS 6.0.2
- click 8.3.1
- 其他辅助包（blinker, itsdangerous, jinja2, markupsafe, werkzeug）

### ❌ 未安装的包
- **face_recognition** - 核心人脸识别库
- **dlib** - face_recognition 的依赖

## 问题诊断

### 问题根源
虚拟环境中安装了 Python 的 `cmake` 包（4.2.1），但这个包与 dlib 的构建过程冲突。dlib 需要系统级的 CMake 工具，而不是 Python 包。

### 错误信息
```
ModuleNotFoundError: No module named 'cmake'
CMake is not installed on your system!
```

## 解决方案

### 方案 1：安装系统级 CMake（推荐）

#### 步骤 1：下载并安装 CMake
1. 访问 https://cmake.org/download/
2. 下载 Windows x64 Installer：`cmake-3.xx.x-windows-x86_64.msi`
3. 运行安装程序
4. **重要**：勾选 "Add CMake to the system PATH for all users"
5. 完成安装

#### 步骤 2：验证安装
打开**新的**命令提示符窗口：
```cmd
cmake --version
```
应该看到：`cmake version 3.xx.x`

#### 步骤 3：移除虚拟环境中的 cmake Python 包
```cmd
cd backend
.\venv\Scripts\activate
pip uninstall cmake -y
```

#### 步骤 4：安装 dlib 和 face_recognition
```cmd
pip install --no-cache-dir dlib
pip install --no-cache-dir face_recognition
```

### 方案 2：使用预编译的 wheel 文件

如果方案 1 失败，可以尝试从第三方源下载预编译的 dlib wheel 文件。

#### 步骤 1：下载预编译 wheel
访问：https://github.com/z-mahmud22/Dlib_Windows_Python3.x

根据您的 Python 版本（3.14）和系统（Windows x64）下载对应的 .whl 文件。

#### 步骤 2：安装 wheel 文件
```cmd
cd backend
.\venv\Scripts\activate
pip install path\to\downloaded\dlib-xx.x.x-cpXX-cpXX-win_amd64.whl
pip install face_recognition
```

### 方案 3：使用 Conda（替代方案）

如果上述方案都失败，可以考虑使用 Conda 环境：

```cmd
conda create -n face-search python=3.11
conda activate face-search
conda install -c conda-forge dlib
pip install face_recognition opencv-python Flask Flask-CORS
```

## 验证安装

安装完成后，运行以下命令验证：

```cmd
cd backend
.\venv\Scripts\activate
python -c "import face_recognition; print('face_recognition version:', face_recognition.__version__)"
python -c "import dlib; print('dlib version:', dlib.__version__)"
```

应该看到版本信息而不是错误。

## 完整依赖检查脚本

创建并运行以下脚本检查所有依赖：

```python
# check_dependencies.py
import sys

required_packages = {
    'face_recognition': '1.3.0',
    'cv2': '4.8.0',  # opencv-python
    'numpy': '1.26.0',
    'PIL': '10.0.0',  # Pillow
    'flask': '3.0.0',
    'flask_cors': '4.0.0'
}

print("检查依赖包安装状态...\n")
print(f"Python 版本: {sys.version}\n")

for package, min_version in required_packages.items():
    try:
        if package == 'cv2':
            import cv2
            version = cv2.__version__
            package_name = 'opencv-python'
        elif package == 'PIL':
            from PIL import Image
            version = Image.__version__
            package_name = 'Pillow'
        else:
            module = __import__(package)
            version = getattr(module, '__version__', 'unknown')
            package_name = package
        
        print(f"✅ {package_name:20} 已安装 (版本: {version})")
    except ImportError:
        print(f"❌ {package:20} 未安装 (需要: >={min_version})")

print("\n检查完成！")
```

运行：
```cmd
python check_dependencies.py
```

## 下一步

依赖安装完成后，可以继续执行任务 2：实现图片上传模块。
