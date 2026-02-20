"""测试导入"""
print("开始测试导入...")

try:
    print("1. 导入 numpy...")
    import numpy
    print("   ✓ numpy 导入成功")
except Exception as e:
    print(f"   ✗ numpy 导入失败: {e}")

try:
    print("2. 导入 PIL...")
    from PIL import Image
    print("   ✓ PIL 导入成功")
except Exception as e:
    print(f"   ✗ PIL 导入失败: {e}")

try:
    print("3. 导入 cv2...")
    import cv2
    print("   ✓ cv2 导入成功")
except Exception as e:
    print(f"   ✗ cv2 导入失败: {e}")

try:
    print("4. 导入 dlib (from dlib_bin)...")
    import dlib
    print(f"   ✓ dlib 导入成功，版本: {dlib.__version__}")
except Exception as e:
    print(f"   ✗ dlib 导入失败: {e}")

try:
    print("5. 导入 face_recognition...")
    import face_recognition
    print("   ✓ face_recognition 导入成功")
except Exception as e:
    print(f"   ✗ face_recognition 导入失败: {e}")

try:
    print("6. 导入 Flask...")
    from flask import Flask
    print("   ✓ Flask 导入成功")
except Exception as e:
    print(f"   ✗ Flask 导入失败: {e}")

print("\n所有导入测试完成！")
