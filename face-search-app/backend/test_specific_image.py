"""测试指定图片的人脸检测"""
import sys
import os
import traceback

# 指定的测试图片路径
TEST_IMAGE = r"D:\AI_workspace\忆颜图谱\微信图片_20260214100654_81_2.jpg"

print("=" * 60)
print("测试指定图片的人脸检测")
print("=" * 60)
print(f"\n测试图片: {TEST_IMAGE}")

# 检查文件是否存在
if not os.path.exists(TEST_IMAGE):
    print(f"✗ 错误: 文件不存在!")
    sys.exit(1)

print(f"✓ 文件存在，大小: {os.path.getsize(TEST_IMAGE) / 1024:.2f} KB")

try:
    print("\n1. 导入必要的库...")
    import face_recognition
    import numpy as np
    from PIL import Image
    print("   ✓ 导入成功")
    
    print("\n2. 加载图片...")
    image = face_recognition.load_image_file(TEST_IMAGE)
    print(f"   ✓ 图片加载成功")
    print(f"   图片尺寸: {image.shape}")
    print(f"   图片类型: {image.dtype}")
    
    print("\n3. 开始检测人脸...")
    print("   (这可能需要几秒钟...)")
    face_locations = face_recognition.face_locations(image)
    print(f"   ✓ 检测完成!")
    print(f"   找到 {len(face_locations)} 个人脸")
    
    if len(face_locations) > 0:
        print("\n4. 人脸位置信息:")
        for i, (top, right, bottom, left) in enumerate(face_locations, 1):
            print(f"   人脸 {i}: top={top}, right={right}, bottom={bottom}, left={left}")
            print(f"          宽度={right-left}, 高度={bottom-top}")
        
        print("\n5. 提取人脸特征...")
        face_encodings = face_recognition.face_encodings(image, face_locations)
        print(f"   ✓ 特征提取成功!")
        print(f"   特征数量: {len(face_encodings)}")
        if len(face_encodings) > 0:
            print(f"   特征维度: {len(face_encodings[0])}")
            print(f"   特征类型: {type(face_encodings[0])}")
    else:
        print("\n   未检测到人脸")
    
    print("\n" + "=" * 60)
    print("✓ 测试完成!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ 发生错误: {e}")
    print("\n完整错误信息:")
    traceback.print_exc()
    sys.exit(1)
