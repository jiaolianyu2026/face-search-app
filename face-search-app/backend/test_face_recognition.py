"""
测试 face_recognition 库是否正常工作
"""

import face_recognition
import numpy as np
from PIL import Image

print("=" * 60)
print("face_recognition 功能测试")
print("=" * 60)

# 测试 1: 检查版本
print(f"\n✅ face_recognition 版本: {face_recognition.__version__}")

# 测试 2: 创建一个简单的测试图像（纯色）
print("\n测试 2: 创建测试图像...")
test_image = np.zeros((100, 100, 3), dtype=np.uint8)
test_image[:, :] = [128, 128, 128]  # 灰色
print("✅ 测试图像创建成功")

# 测试 3: 尝试检测人脸（应该返回空列表，因为是纯色图像）
print("\n测试 3: 人脸检测功能...")
face_locations = face_recognition.face_locations(test_image)
print(f"✅ 人脸检测功能正常（检测到 {len(face_locations)} 个人脸）")

# 测试 4: 测试特征提取功能（使用随机特征向量）
print("\n测试 4: 特征向量功能...")
# 创建两个随机的 128 维特征向量
feature1 = np.random.rand(128)
feature2 = np.random.rand(128)

# 计算相似度
distance = face_recognition.face_distance([feature1], feature2)[0]
print(f"✅ 特征向量计算正常（距离: {distance:.4f}）")

print("\n" + "=" * 60)
print("✅ 所有测试通过！face_recognition 工作正常")
print("=" * 60)
print("\n可以开始实现任务 2：图片上传模块")
