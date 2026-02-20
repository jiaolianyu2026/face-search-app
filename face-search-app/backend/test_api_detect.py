"""测试 API 的上传和检测功能"""
import requests
import os
import time

# 测试图片路径
TEST_IMAGE = r"D:\AI_workspace\忆颜图谱\微信图片_20260214100654_81_2.jpg"
API_BASE = "http://localhost:5000/api"

print("=" * 60)
print("测试 API 上传和人脸检测")
print("=" * 60)

# 检查文件是否存在
if not os.path.exists(TEST_IMAGE):
    print(f"✗ 错误: 测试图片不存在: {TEST_IMAGE}")
    exit(1)

print(f"\n测试图片: {TEST_IMAGE}")
print(f"文件大小: {os.path.getsize(TEST_IMAGE) / 1024:.2f} KB")

try:
    # 1. 上传图片
    print("\n1. 上传图片...")
    with open(TEST_IMAGE, 'rb') as f:
        files = {'file': (os.path.basename(TEST_IMAGE), f, 'image/jpeg')}
        response = requests.post(f"{API_BASE}/upload", files=files, timeout=10)
    
    if response.status_code != 200:
        print(f"✗ 上传失败: {response.status_code}")
        print(f"响应: {response.text}")
        exit(1)
    
    upload_result = response.json()
    image_id = upload_result['imageId']
    print(f"✓ 上传成功!")
    print(f"  imageId: {image_id}")
    print(f"  previewUrl: {upload_result['previewUrl']}")
    
    # 2. 检测人脸
    print("\n2. 检测人脸...")
    print("   (这可能需要几秒钟...)")
    
    start_time = time.time()
    response = requests.post(
        f"{API_BASE}/detect",
        json={'imageId': image_id},
        timeout=30  # 30秒超时
    )
    elapsed = time.time() - start_time
    
    print(f"   请求耗时: {elapsed:.2f} 秒")
    
    if response.status_code == 422:
        # 未检测到人脸
        result = response.json()
        print(f"✓ 请求成功，但未检测到人脸")
        print(f"  错误信息: {result.get('error')}")
    elif response.status_code == 200:
        # 检测成功
        result = response.json()
        faces = result.get('faces', [])
        print(f"✓ 检测成功!")
        print(f"  检测到 {len(faces)} 个人脸")
        
        for i, face in enumerate(faces, 1):
            bbox = face['boundingBox']
            print(f"\n  人脸 {i}:")
            print(f"    faceId: {face['faceId']}")
            print(f"    位置: x={bbox['x']}, y={bbox['y']}, "
                  f"宽={bbox['width']}, 高={bbox['height']}")
            print(f"    特征维度: {len(face['features'])}")
    else:
        print(f"✗ 检测失败: {response.status_code}")
        print(f"响应: {response.text}")
        exit(1)
    
    print("\n" + "=" * 60)
    print("✓ 测试完成!")
    print("=" * 60)
    
except requests.exceptions.Timeout:
    print("\n✗ 请求超时!")
    print("后端可能在处理大图片时崩溃了")
except requests.exceptions.ConnectionError:
    print("\n✗ 连接失败!")
    print("后端服务可能已停止")
except Exception as e:
    print(f"\n✗ 发生错误: {e}")
    import traceback
    traceback.print_exc()
