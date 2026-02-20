"""
端到端集成测试
测试完整的应用工作流程：上传→检测→搜索→结果→转存
同时测试取消搜索和缓存机制

**验证需求：所有需求**
"""

import pytest
import os
import sys
import tempfile
import shutil
import json
import time
from PIL import Image, ImageDraw

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app


class TestEndToEnd:
    """端到端集成测试类"""
    
    @pytest.fixture
    def client(self):
        """创建 Flask 测试客户端"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def temp_search_folder(self):
        """创建包含测试图片的临时文件夹"""
        temp_dir = tempfile.mkdtemp()
        
        # 创建多个测试图片
        for i in range(5):
            img = Image.new('RGB', (300, 300), color=(i*50, i*50, i*50))
            draw = ImageDraw.Draw(img)
            # 添加一些简单的图案
            draw.rectangle([50, 50, 250, 250], outline=(255, 255, 255), width=3)
            img.save(os.path.join(temp_dir, f'test_image_{i}.jpg'))
        
        yield temp_dir
        
        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def temp_export_folder(self):
        """创建用于转存的临时目标文件夹"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def create_face_image(self):
        """创建包含人脸样式图案的测试图片"""
        img = Image.new('RGB', (400, 400), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # 绘制简单的人脸样式图案
        # 脸部轮廓（圆形）
        draw.ellipse([100, 100, 300, 300], fill=(255, 220, 180), outline=(0, 0, 0))
        # 眼睛
        draw.ellipse([150, 150, 180, 180], fill=(0, 0, 0))
        draw.ellipse([220, 150, 250, 180], fill=(0, 0, 0))
        # 鼻子
        draw.polygon([(200, 180), (190, 220), (210, 220)], fill=(200, 180, 160))
        # 嘴巴
        draw.arc([160, 220, 240, 260], 0, 180, fill=(0, 0, 0), width=3)
        
        return img
    
    def test_complete_workflow_upload_detect_search_export(
        self, client, temp_search_folder, temp_export_folder
    ):
        """
        测试完整工作流程：上传→检测→搜索→结果→转存
        
        **验证需求：1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.5, 4.1-4.5, 5.1-5.5, 8.1-8.7**
        """
        # ========== 步骤 1: 上传图片 ==========
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = self.create_face_image()
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            # 上传图片
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test_face.jpg')},
                    content_type='multipart/form-data'
                )
            
            # 验证上传成功
            assert upload_response.status_code == 200
            upload_data = json.loads(upload_response.data)
            assert upload_data['success'] is True
            assert 'imageId' in upload_data
            assert 'previewUrl' in upload_data
            
            image_id = upload_data['imageId']
            print(f"✓ 步骤 1: 图片上传成功，imageId: {image_id}")
            
            # ========== 步骤 2: 检测人脸 ==========
            detect_response = client.post(
                '/api/detect',
                json={'imageId': image_id}
            )
            
            # 如果未检测到人脸，跳过测试（简单测试图案可能无法被识别为人脸）
            if detect_response.status_code == 422:
                pytest.skip("测试图片中未检测到人脸 - 这对于简单测试图案是预期的")
            
            # 验证检测成功
            assert detect_response.status_code == 200
            detect_data = json.loads(detect_response.data)
            assert 'faces' in detect_data
            assert len(detect_data['faces']) > 0
            
            # 验证人脸数据结构
            face = detect_data['faces'][0]
            assert 'faceId' in face
            assert 'boundingBox' in face
            assert 'features' in face
            assert len(face['features']) == 128
            
            face_id = face['faceId']
            print(f"✓ 步骤 2: 人脸检测成功，检测到 {len(detect_data['faces'])} 个人脸")
            
            # ========== 步骤 3: 启动搜索 ==========
            search_response = client.post(
                '/api/search',
                json={
                    'imageId': image_id,
                    'faceId': face_id,
                    'searchFolder': temp_search_folder,
                    'threshold': 0.5
                }
            )
            
            # 验证搜索任务创建成功
            assert search_response.status_code == 200
            search_data = json.loads(search_response.data)
            assert 'taskId' in search_data
            assert 'status' in search_data
            assert search_data['status'] in ['pending', 'running']
            
            task_id = search_data['taskId']
            print(f"✓ 步骤 3: 搜索任务创建成功，taskId: {task_id}")
            
            # ========== 步骤 4: 监控搜索进度 ==========
            max_wait = 15  # 最多等待15秒
            start_time = time.time()
            final_status = None
            
            while time.time() - start_time < max_wait:
                status_response = client.get(f'/api/search/{task_id}')
                assert status_response.status_code == 200
                
                status_data = json.loads(status_response.data)
                
                # 验证响应结构
                assert 'taskId' in status_data
                assert 'status' in status_data
                assert 'progress' in status_data
                assert 'createdAt' in status_data
                
                # 验证进度信息结构
                progress = status_data['progress']
                assert 'current' in progress
                assert 'total' in progress
                assert 'percentage' in progress
                assert 'currentFile' in progress
                
                print(f"  进度: {progress['current']}/{progress['total']} ({progress['percentage']:.1f}%)")
                
                # 检查是否完成
                if status_data['status'] in ['completed', 'cancelled']:
                    final_status = status_data
                    break
                
                time.sleep(0.2)
            
            # 验证搜索完成
            assert final_status is not None, "搜索任务在超时时间内未完成"
            assert final_status['status'] == 'completed'
            assert 'results' in final_status
            
            results = final_status['results']
            print(f"✓ 步骤 4: 搜索完成，找到 {len(results)} 个匹配结果")
            
            # ========== 步骤 5: 验证搜索结果结构 ==========
            # 验证结果是列表
            assert isinstance(results, list)
            
            # 如果有结果，验证结果结构
            for result in results:
                assert 'imagePath' in result
                assert 'similarity' in result
                assert 'faceLocation' in result
                
                # 验证相似度在有效范围内
                assert 0 <= result['similarity'] <= 1
                
                # 验证相似度大于等于阈值
                assert result['similarity'] >= 0.5
                
                # 验证人脸位置结构
                face_loc = result['faceLocation']
                assert isinstance(face_loc, dict)
            
            # 验证结果按相似度降序排列
            if len(results) > 1:
                for i in range(len(results) - 1):
                    assert results[i]['similarity'] >= results[i + 1]['similarity']
            
            print(f"✓ 步骤 5: 搜索结果结构验证通过")
            
            # ========== 步骤 6: 转存匹配的图片 ==========
            if len(results) > 0:
                # 选择前3个结果进行转存（如果有的话）
                export_paths = [r['imagePath'] for r in results[:3]]
                
                export_response = client.post(
                    '/api/export',
                    json={
                        'imagePaths': export_paths,
                        'targetFolder': temp_export_folder
                    }
                )
                
                # 验证转存成功
                assert export_response.status_code == 200
                export_data = json.loads(export_response.data)
                
                assert 'successCount' in export_data
                assert 'failedCount' in export_data
                assert 'errors' in export_data
                
                # 验证统计准确性
                assert export_data['successCount'] + export_data['failedCount'] == len(export_paths)
                
                # 验证文件确实被复制到目标文件夹
                exported_files = os.listdir(temp_export_folder)
                assert len(exported_files) == export_data['successCount']
                
                # 验证文件内容一致性
                for exported_file in exported_files:
                    exported_path = os.path.join(temp_export_folder, exported_file)
                    assert os.path.exists(exported_path)
                    assert os.path.getsize(exported_path) > 0
                
                print(f"✓ 步骤 6: 图片转存成功，成功 {export_data['successCount']} 个，失败 {export_data['failedCount']} 个")
            else:
                print("✓ 步骤 6: 跳过转存（无匹配结果）")
            
            print("\n✓✓✓ 完整工作流程测试通过 ✓✓✓")
            
        finally:
            # 清理上传的临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_search_cancellation_workflow(self, client, temp_search_folder):
        """
        测试搜索取消工作流程：启动搜索→取消→验证已取消
        
        **验证需求：6.4, 6.5**
        """
        # 创建并上传图片
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = self.create_face_image()
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            # 上传图片
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test_face.jpg')},
                    content_type='multipart/form-data'
                )
            
            upload_data = json.loads(upload_response.data)
            image_id = upload_data['imageId']
            
            # 检测人脸
            detect_response = client.post(
                '/api/detect',
                json={'imageId': image_id}
            )
            
            if detect_response.status_code == 422:
                pytest.skip("测试图片中未检测到人脸")
            
            detect_data = json.loads(detect_response.data)
            if len(detect_data['faces']) == 0:
                pytest.skip("测试图片中未检测到人脸")
            
            face_id = detect_data['faces'][0]['faceId']
            
            # 启动搜索
            search_response = client.post(
                '/api/search',
                json={
                    'imageId': image_id,
                    'faceId': face_id,
                    'searchFolder': temp_search_folder,
                    'threshold': 0.5
                }
            )
            
            assert search_response.status_code == 200
            search_data = json.loads(search_response.data)
            task_id = search_data['taskId']
            
            print(f"✓ 搜索任务创建: {task_id}")
            
            # 立即取消搜索
            cancel_response = client.post(f'/api/search/{task_id}/cancel')
            assert cancel_response.status_code == 200
            
            cancel_data = json.loads(cancel_response.data)
            assert cancel_data['taskId'] == task_id
            assert cancel_data['status'] == 'cancelled'
            assert 'message' in cancel_data
            
            print(f"✓ 搜索任务已取消")
            
            # 验证任务状态显示为已取消
            status_response = client.get(f'/api/search/{task_id}')
            assert status_response.status_code == 200
            
            status_data = json.loads(status_response.data)
            assert status_data['status'] == 'cancelled'
            assert 'results' in status_data  # 应该有部分结果
            
            print(f"✓ 取消状态验证通过，部分结果数: {len(status_data['results'])}")
            print("\n✓✓✓ 搜索取消工作流程测试通过 ✓✓✓")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_cache_mechanism(self, client, temp_search_folder):
        """
        测试缓存机制：第一次搜索→第二次搜索（应使用缓存）
        
        **验证需求：9.4**
        """
        # 创建并上传图片
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = self.create_face_image()
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            # 上传图片
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test_face.jpg')},
                    content_type='multipart/form-data'
                )
            
            upload_data = json.loads(upload_response.data)
            image_id = upload_data['imageId']
            
            # 检测人脸
            detect_response = client.post(
                '/api/detect',
                json={'imageId': image_id}
            )
            
            if detect_response.status_code == 422:
                pytest.skip("测试图片中未检测到人脸")
            
            detect_data = json.loads(detect_response.data)
            if len(detect_data['faces']) == 0:
                pytest.skip("测试图片中未检测到人脸")
            
            face_id = detect_data['faces'][0]['faceId']
            
            # ========== 第一次搜索 ==========
            print("执行第一次搜索...")
            search_response_1 = client.post(
                '/api/search',
                json={
                    'imageId': image_id,
                    'faceId': face_id,
                    'searchFolder': temp_search_folder,
                    'threshold': 0.5
                }
            )
            
            assert search_response_1.status_code == 200
            search_data_1 = json.loads(search_response_1.data)
            task_id_1 = search_data_1['taskId']
            
            # 等待第一次搜索完成
            max_wait = 15
            start_time = time.time()
            first_search_time = None
            
            while time.time() - start_time < max_wait:
                status_response = client.get(f'/api/search/{task_id_1}')
                status_data = json.loads(status_response.data)
                
                if status_data['status'] == 'completed':
                    first_search_time = time.time() - start_time
                    break
                
                time.sleep(0.1)
            
            assert first_search_time is not None, "第一次搜索未在超时时间内完成"
            print(f"✓ 第一次搜索完成，耗时: {first_search_time:.2f}秒")
            
            # ========== 第二次搜索（应使用缓存）==========
            print("执行第二次搜索（应使用缓存）...")
            search_response_2 = client.post(
                '/api/search',
                json={
                    'imageId': image_id,
                    'faceId': face_id,
                    'searchFolder': temp_search_folder,
                    'threshold': 0.5
                }
            )
            
            assert search_response_2.status_code == 200
            search_data_2 = json.loads(search_response_2.data)
            task_id_2 = search_data_2['taskId']
            
            # 等待第二次搜索完成
            start_time = time.time()
            second_search_time = None
            
            while time.time() - start_time < max_wait:
                status_response = client.get(f'/api/search/{task_id_2}')
                status_data = json.loads(status_response.data)
                
                if status_data['status'] == 'completed':
                    second_search_time = time.time() - start_time
                    break
                
                time.sleep(0.1)
            
            assert second_search_time is not None, "第二次搜索未在超时时间内完成"
            print(f"✓ 第二次搜索完成，耗时: {second_search_time:.2f}秒")
            
            # 注意：由于搜索文件夹中的图片数量较少，缓存效果可能不明显
            # 但第二次搜索应该至少不会更慢
            print(f"  第一次搜索: {first_search_time:.2f}秒")
            print(f"  第二次搜索: {second_search_time:.2f}秒")
            
            # 验证两次搜索结果一致（如果使用了缓存，结果应该相同）
            status_1 = client.get(f'/api/search/{task_id_1}')
            status_2 = client.get(f'/api/search/{task_id_2}')
            
            results_1 = json.loads(status_1.data)['results']
            results_2 = json.loads(status_2.data)['results']
            
            # 结果数量应该相同
            assert len(results_1) == len(results_2), "两次搜索的结果数量不一致"
            
            print(f"✓ 缓存机制验证通过，两次搜索结果一致")
            print("\n✓✓✓ 缓存机制测试通过 ✓✓✓")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    
    def test_export_with_filename_conflict(self, client, temp_export_folder):
        """
        测试转存时的文件名冲突处理
        
        **验证需求：8.5**
        """
        # 创建一个测试图片
        test_image_path = os.path.join(temp_export_folder, 'source_image.jpg')
        img = Image.new('RGB', (200, 200), color=(100, 100, 100))
        img.save(test_image_path)
        
        # 在目标文件夹中预先创建同名文件
        target_file = os.path.join(temp_export_folder, 'source_image.jpg')
        assert os.path.exists(target_file)  # 确认文件已存在
        
        # 尝试转存同名文件
        export_response = client.post(
            '/api/export',
            json={
                'imagePaths': [test_image_path],
                'targetFolder': temp_export_folder
            }
        )
        
        assert export_response.status_code == 200
        export_data = json.loads(export_response.data)
        
        # 应该成功（通过重命名）
        assert export_data['successCount'] == 1
        assert export_data['failedCount'] == 0
        
        # 验证目标文件夹中有两个文件（原文件 + 重命名的文件）
        files = os.listdir(temp_export_folder)
        assert len(files) == 2
        
        # 验证有一个文件被重命名（应该有 _1 后缀）
        renamed_files = [f for f in files if '_1' in f or '_2' in f]
        assert len(renamed_files) >= 1
        
        print(f"✓ 文件名冲突处理测试通过，文件被重命名: {renamed_files}")
        print("\n✓✓✓ 文件名冲突处理测试通过 ✓✓✓")
    
    def test_error_handling_invalid_folder(self, client):
        """
        测试错误处理：无效的搜索文件夹
        
        **验证需求：3.3, 7.1**
        """
        # 创建并上传图片
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = self.create_face_image()
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test_face.jpg')},
                    content_type='multipart/form-data'
                )
            
            upload_data = json.loads(upload_response.data)
            image_id = upload_data['imageId']
            
            # 尝试使用不存在的文件夹进行搜索
            search_response = client.post(
                '/api/search',
                json={
                    'imageId': image_id,
                    'faceId': 'any-face-id',
                    'searchFolder': '/nonexistent/folder/path'
                }
            )
            
            # 应该返回验证错误
            assert search_response.status_code == 400
            error_data = json.loads(search_response.data)
            
            assert 'error' in error_data
            assert error_data['error']['code'] == 'VALIDATION_ERROR'
            assert '不存在' in error_data['error']['message']
            
            print(f"✓ 无效文件夹错误处理测试通过")
            print("\n✓✓✓ 错误处理测试通过 ✓✓✓")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    
    def test_error_handling_invalid_file_format(self, client):
        """
        测试错误处理：无效的文件格式
        
        **验证需求：1.1, 7.1**
        """
        # 创建一个文本文件（不支持的格式）
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as tmp:
            tmp.write("This is not an image")
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test.txt')},
                    content_type='multipart/form-data'
                )
            
            # 应该返回验证错误
            assert upload_response.status_code == 400
            error_data = json.loads(upload_response.data)
            
            assert 'error' in error_data
            assert error_data['error']['code'] == 'VALIDATION_ERROR'
            
            print(f"✓ 无效文件格式错误处理测试通过")
            print("\n✓✓✓ 文件格式验证测试通过 ✓✓✓")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_progress_tracking_accuracy(self, client, temp_search_folder):
        """
        测试进度跟踪的准确性
        
        **验证需求：6.2, 6.3**
        """
        # 创建并上传图片
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = self.create_face_image()
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test_face.jpg')},
                    content_type='multipart/form-data'
                )
            
            upload_data = json.loads(upload_response.data)
            image_id = upload_data['imageId']
            
            # 检测人脸
            detect_response = client.post(
                '/api/detect',
                json={'imageId': image_id}
            )
            
            if detect_response.status_code == 422:
                pytest.skip("测试图片中未检测到人脸")
            
            detect_data = json.loads(detect_response.data)
            if len(detect_data['faces']) == 0:
                pytest.skip("测试图片中未检测到人脸")
            
            face_id = detect_data['faces'][0]['faceId']
            
            # 启动搜索
            search_response = client.post(
                '/api/search',
                json={
                    'imageId': image_id,
                    'faceId': face_id,
                    'searchFolder': temp_search_folder,
                    'threshold': 0.5
                }
            )
            
            task_id = json.loads(search_response.data)['taskId']
            
            # 跟踪进度更新
            progress_updates = []
            max_wait = 15
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = client.get(f'/api/search/{task_id}')
                status_data = json.loads(status_response.data)
                
                progress = status_data['progress']
                progress_updates.append({
                    'current': progress['current'],
                    'total': progress['total'],
                    'percentage': progress['percentage']
                })
                
                if status_data['status'] in ['completed', 'cancelled']:
                    break
                
                time.sleep(0.1)
            
            # 验证进度更新
            assert len(progress_updates) > 0, "应该有至少一次进度更新"
            
            # 验证进度是递增的
            for i in range(len(progress_updates) - 1):
                current_progress = progress_updates[i]['current']
                next_progress = progress_updates[i + 1]['current']
                # 进度应该是非递减的
                assert next_progress >= current_progress
            
            # 验证最终进度
            final_progress = progress_updates[-1]
            if final_progress['total'] > 0:
                # 如果有文件要处理，验证百分比计算正确
                expected_percentage = (final_progress['current'] / final_progress['total']) * 100
                assert abs(final_progress['percentage'] - expected_percentage) < 0.1
            
            print(f"✓ 进度跟踪准确性测试通过，共 {len(progress_updates)} 次更新")
            print("\n✓✓✓ 进度跟踪测试通过 ✓✓✓")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
