"""简单的人脸检测测试"""
import sys
import traceback

print("=" * 50)
print("开始测试人脸检测...")
print("=" * 50)

try:
    print("\n1. 导入 face_recognition...")
    import face_recognition
    print("   ✓ 导入成功")
    
    print("\n2. 导入 PIL...")
    from PIL import Image
    print("   ✓ 导入成功")
    
    print("\n3. 导入 numpy...")
    import numpy as np
    print("   ✓ 导入成功")
    
    print("\n4. 创建测试图片...")
    # 创建一个简单的测试图片（纯色）
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    print("   ✓ 测试图片创建成功")
    
    print("\n5. 尝试检测人脸（空图片）...")
    face_locations = face_recognition.face_locations(test_image)
    print(f"   ✓ 检测完成，找到 {len(face_locations)} 个人脸")
    
    print("\n6. 检查上传的图片...")
    import os
    temp_dir = "temp_uploads"
    if os.path.exists(temp_dir):
        files = os.listdir(temp_dir)
        print(f"   找到 {len(files)} 个上传的文件")
        if files:
            # 测试第一个文件
            test_file = os.path.join(temp_dir, files[0])
            print(f"\n7. 测试真实图片: {files[0]}")
            try:
                image = face_recognition.load_image_file(test_file)
                print(f"   ✓ 图片加载成功，尺寸: {image.shape}")
                
                print("   开始检测人脸...")
                face_locations = face_recognition.face_locations(image)
                print(f"   ✓ 检测完成，找到 {len(face_locations)} 个人脸")
                
                if len(face_locations) > 0:
                    print("   尝试提取特征...")
                    face_encodings = face_recognition.face_encodings(image, face_locations)
                    print(f"   ✓ 特征提取成功，特征数量: {len(face_encodings)}")
                    if len(face_encodings) > 0:
                        print(f"   特征维度: {len(face_encodings[0])}")
            except Exception as e:
                print(f"   ✗ 错误: {e}")
                traceback.print_exc()
    else:
        print("   temp_uploads 目录不存在")
    
    print("\n" + "=" * 50)
    print("✓ 所有测试完成！")
    print("=" * 50)
    
except Exception as e:
    print(f"\n✗ 发生错误: {e}")
    print("\n完整错误信息:")
    traceback.print_exc()
    sys.exit(1)
