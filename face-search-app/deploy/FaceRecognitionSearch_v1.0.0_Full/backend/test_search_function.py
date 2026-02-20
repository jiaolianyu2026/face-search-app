"""测试搜索功能"""
import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from face_detection import FaceDetectionModule
from face_search import FaceSearchModule
from models import Progress

# 测试图片和搜索文件夹
TEST_IMAGE = r"D:\AI_workspace\忆颜图谱\微信图片_20260214100654_81_2.jpg"
SEARCH_FOLDER = r"D:\AI_workspace\忆颜图谱"

print("=" * 60)
print("测试人脸搜索功能")
print("=" * 60)

# 检查文件和文件夹是否存在
if not os.path.exists(TEST_IMAGE):
    print(f"✗ 错误: 测试图片不存在: {TEST_IMAGE}")
    sys.exit(1)

if not os.path.exists(SEARCH_FOLDER):
    print(f"✗ 错误: 搜索文件夹不存在: {SEARCH_FOLDER}")
    sys.exit(1)

print(f"\n测试图片: {TEST_IMAGE}")
print(f"搜索文件夹: {SEARCH_FOLDER}")

try:
    # 1. 检测目标图片中的人脸
    print("\n1. 检测目标图片中的人脸...")
    detector = FaceDetectionModule()
    detection_result = detector.detectFaces(TEST_IMAGE)
    
    if detection_result.error or len(detection_result.faces) == 0:
        print(f"✗ 检测失败: {detection_result.error}")
        sys.exit(1)
    
    print(f"✓ 检测成功，找到 {len(detection_result.faces)} 个人脸")
    
    # 使用第一个人脸作为目标
    target_face = detection_result.faces[0]
    print(f"  目标人脸 ID: {target_face.faceId}")
    print(f"  特征维度: {len(target_face.features)}")
    
    # 2. 扫描搜索文件夹
    print(f"\n2. 扫描搜索文件夹...")
    from file_scanner import FileSystemScannerModule
    scanner = FileSystemScannerModule()
    
    try:
        scan_result = scanner.scanFolder(SEARCH_FOLDER)
        image_files = scan_result.imagePaths
        print(f"✓ 找到 {len(image_files)} 个图片文件")
        
        # 显示前 5 个文件
        for i, file_path in enumerate(image_files[:5], 1):
            print(f"  {i}. {os.path.basename(file_path)}")
        if len(image_files) > 5:
            print(f"  ... 还有 {len(image_files) - 5} 个文件")
    except Exception as e:
        print(f"✗ 扫描失败: {e}")
        sys.exit(1)
    
    # 3. 执行搜索
    print(f"\n3. 执行人脸搜索...")
    print(f"   阈值: 0.6")
    print(f"   (这可能需要一些时间...)")
    
    searcher = FaceSearchModule()
    
    # 进度回调
    def progress_callback(progress: Progress):
        if progress.total > 0:
            print(f"\r   进度: {progress.current}/{progress.total} ({progress.percentage:.1f}%) - {progress.currentFile or ''}", end='', flush=True)
    
    search_result = searcher.searchFaces(
        targetFeatures=target_face.features,
        searchFolder=SEARCH_FOLDER,
        threshold=0.6,
        progressCallback=progress_callback
    )
    
    print()  # 换行
    print(f"\n✓ 搜索完成!")
    print(f"  处理文件数: {search_result.totalProcessed}")
    print(f"  找到匹配数: {len(search_result.matches)}")
    print(f"  是否取消: {search_result.cancelled}")
    
    # 4. 显示匹配结果
    if len(search_result.matches) > 0:
        print(f"\n4. 匹配结果:")
        for i, match in enumerate(search_result.matches[:10], 1):
            print(f"\n  匹配 {i}:")
            print(f"    文件: {os.path.basename(match.imagePath)}")
            print(f"    相似度: {match.similarity:.4f}")
            print(f"    位置: x={match.faceLocation['x']}, y={match.faceLocation['y']}, "
                  f"宽={match.faceLocation['width']}, 高={match.faceLocation['height']}")
        
        if len(search_result.matches) > 10:
            print(f"\n  ... 还有 {len(search_result.matches) - 10} 个匹配结果")
    else:
        print(f"\n4. 未找到匹配的人脸")
    
    print("\n" + "=" * 60)
    print("✓ 测试完成!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ 发生错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
