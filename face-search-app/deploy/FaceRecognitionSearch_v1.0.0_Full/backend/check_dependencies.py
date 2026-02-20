"""
依赖包检查脚本
检查所有必需的 Python 包是否已正确安装
"""

import sys

required_packages = {
    'face_recognition': '1.3.0',
    'cv2': '4.8.0',  # opencv-python
    'numpy': '1.26.0',
    'PIL': '10.0.0',  # Pillow
    'flask': '3.0.0',
    'flask_cors': '4.0.0'
}

print("=" * 60)
print("依赖包安装状态检查")
print("=" * 60)
print(f"\nPython 版本: {sys.version}\n")
print("-" * 60)

all_installed = True

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
    except ImportError as e:
        print(f"❌ {package:20} 未安装 (需要: >={min_version})")
        all_installed = False

print("-" * 60)

if all_installed:
    print("\n✅ 所有依赖包已正确安装！")
    print("\n可以继续执行任务 2：实现图片上传模块")
else:
    print("\n⚠️  部分依赖包未安装")
    print("\n请参考 DEPENDENCY_INSTALLATION_GUIDE.md 完成安装")

print("=" * 60)
