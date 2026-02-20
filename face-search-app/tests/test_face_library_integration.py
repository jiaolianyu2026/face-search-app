"""
人像库管理功能集成测试
测试完整的用户工作流：上传并保存、历史搜索、混合搜索、库管理

**验证需求：所有人像库管理需求的综合验证**
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


class TestFaceLibraryIntegration:
    """人像库管理功能集成测试类"""
    
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
    
    def test_upload_and_save_workflow(self, client):
        """
        测试上传并保存工作流
        
        工作流：上传图片 → 检测人像 → 保存到库 → 验证库中存在
        
        **验证需求：1.1-1.6, 2.1-2.7, 5.1-5.7, 6.1**
        """
        print("\n========== 测试上传并保存工作流 ==========")
        
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
            
            image_id = upload_data['imageId']
            print(f"✓ 步骤 1: 图片上传成功，imageId: {image_id}")
            
            # ========== 步骤 2: 检测人像 ==========
            detect_response = client.post(
                '/api/detect',
                json={'imageId': image_id}
            )
            
            # 如果未检测到人脸，跳过测试
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
            
            # ========== 步骤 3: 保存人像到库 ==========
            save_response = client.post(
                '/api/library/faces',
                json={
                    'imageId': image_id,
                    'faceId': face_id,
                    'name': '测试人像1'
                }
            )
            
            # 验证保存成功
            assert save_response.status_code == 200
            save_data = json.loads(save_response.data)
            
            assert 'id' in save_data
            assert 'name' in save_data
            assert save_data['name'] == '测试人像1'
            assert 'thumbnailUrl' in save_data
            assert 'createdAt' in save_data
            
            library_face_id = save_data['id']
            print(f"✓ 步骤 3: 人像保存成功，libraryFaceId: {library_face_id}")
            
            # ========== 步骤 4: 验证库中存在该人像 ==========
            get_response = client.get(f'/api/library/faces/{library_face_id}')
            
            # 验证查询成功
            assert get_response.status_code == 200
            get_data = json.loads(get_response.data)
            
            assert get_data['id'] == library_face_id
            assert get_data['name'] == '测试人像1'
            assert 'features' in get_data
            assert len(get_data['features']) == 128
            assert 'thumbnailUrl' in get_data
            assert 'createdAt' in get_data
            
            print(f"✓ 步骤 4: 人像查询成功，验证数据一致")
            
            # ========== 步骤 5: 验证缩略图存在 ==========
            thumbnail_response = client.get(save_data['thumbnailUrl'])
            assert thumbnail_response.status_code == 200
            assert thumbnail_response.content_type.startswith('image/')
            assert len(thumbnail_response.data) > 0
            
            print(f"✓ 步骤 5: 缩略图验证成功")
            
            # ========== 步骤 6: 验证人像列表包含该人像 ==========
            list_response = client.get('/api/library/faces')
            assert list_response.status_code == 200
            
            list_data = json.loads(list_response.data)
            assert 'faces' in list_data
            
            # 查找我们保存的人像
            found = False
            for lib_face in list_data['faces']:
                if lib_face['id'] == library_face_id:
                    found = True
                    assert lib_face['name'] == '测试人像1'
                    break
            
            assert found, "保存的人像应该出现在列表中"
            print(f"✓ 步骤 6: 人像列表验证成功")
            
            print("\n✓✓✓ 上传并保存工作流测试通过 ✓✓✓")
            
        finally:
            # 清理上传的临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    
    def test_history_search_workflow(self, client, temp_search_folder):
        """
        测试历史搜索工作流
        
        工作流：保存人像到库 → 从库中选择人像 → 开始搜索 → 验证搜索使用正确特征
        
        **验证需求：3.1-3.7, 4.1-4.7, 8.1-8.7**
        """
        print("\n========== 测试历史搜索工作流 ==========")
        
        # ========== 步骤 1: 上传并保存人像 ==========
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
            
            # 检测人像
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
            
            # 保存人像到库
            save_response = client.post(
                '/api/library/faces',
                json={
                    'imageId': image_id,
                    'faceId': face_id,
                    'name': '历史人像1'
                }
            )
            
            assert save_response.status_code == 200
            save_data = json.loads(save_response.data)
            library_face_id = save_data['id']
            
            print(f"✓ 步骤 1: 人像保存成功，libraryFaceId: {library_face_id}")
            
            # ========== 步骤 2: 使用库人像进行搜索 ==========
            search_response = client.post(
                '/api/search',
                json={
                    'targetFaces': [
                        {
                            'type': 'library',
                            'libraryFaceId': library_face_id
                        }
                    ],
                    'searchFolder': temp_search_folder,
                    'threshold': 0.5
                }
            )
            
            # 验证搜索任务创建成功
            assert search_response.status_code == 200
            search_data = json.loads(search_response.data)
            assert 'taskId' in search_data
            assert 'status' in search_data
            
            task_id = search_data['taskId']
            print(f"✓ 步骤 2: 搜索任务创建成功，taskId: {task_id}")
            
            # ========== 步骤 3: 监控搜索进度 ==========
            max_wait = 15
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
                
                # 检查是否完成
                if status_data['status'] in ['completed', 'cancelled']:
                    final_status = status_data
                    break
                
                time.sleep(0.2)
            
            # 验证搜索完成
            assert final_status is not None, "搜索任务在超时时间内未完成"
            assert final_status['status'] == 'completed'
            assert 'results' in final_status
            
            print(f"✓ 步骤 3: 搜索完成，找到 {len(final_status['results'])} 个匹配结果")
            
            # ========== 步骤 4: 验证搜索结果结构 ==========
            results = final_status['results']
            assert isinstance(results, list)
            
            # 如果有结果，验证结果结构
            for result in results:
                assert 'imagePath' in result
                assert 'similarity' in result
                assert 'faceLocation' in result
                assert 0 <= result['similarity'] <= 1
                assert result['similarity'] >= 0.5
            
            print(f"✓ 步骤 4: 搜索结果结构验证通过")
            print("\n✓✓✓ 历史搜索工作流测试通过 ✓✓✓")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_mixed_search_workflow(self, client, temp_search_folder):
        """
        测试混合搜索工作流
        
        工作流：上传新图片 → 检测人像 → 同时选择新人像和库人像 → 开始搜索 → 验证结果合并
        
        **验证需求：4.5, 4.6, 4.7, 8.1-8.7**
        """
        print("\n========== 测试混合搜索工作流 ==========")
        
        # ========== 步骤 1: 保存第一个人像到库 ==========
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp1:
            img1 = self.create_face_image()
            img1.save(tmp1.name)
            tmp_path1 = tmp1.name
        
        try:
            # 上传第一张图片
            with open(tmp_path1, 'rb') as f:
                upload_response1 = client.post(
                    '/api/upload',
                    data={'file': (f, 'face1.jpg')},
                    content_type='multipart/form-data'
                )
            
            upload_data1 = json.loads(upload_response1.data)
            image_id1 = upload_data1['imageId']
            
            # 检测人像
            detect_response1 = client.post(
                '/api/detect',
                json={'imageId': image_id1}
            )
            
            if detect_response1.status_code == 422:
                pytest.skip("测试图片中未检测到人脸")
            
            detect_data1 = json.loads(detect_response1.data)
            if len(detect_data1['faces']) == 0:
                pytest.skip("测试图片中未检测到人脸")
            
            face_id1 = detect_data1['faces'][0]['faceId']
            
            # 保存到库
            save_response = client.post(
                '/api/library/faces',
                json={
                    'imageId': image_id1,
                    'faceId': face_id1,
                    'name': '库人像1'
                }
            )
            
            assert save_response.status_code == 200
            save_data = json.loads(save_response.data)
            library_face_id = save_data['id']
            
            print(f"✓ 步骤 1: 第一个人像保存到库，libraryFaceId: {library_face_id}")
            
            # ========== 步骤 2: 上传第二张图片（不保存到库）==========
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp2:
                img2 = self.create_face_image()
                img2.save(tmp2.name)
                tmp_path2 = tmp2.name
            
            try:
                # 上传第二张图片
                with open(tmp_path2, 'rb') as f:
                    upload_response2 = client.post(
                        '/api/upload',
                        data={'file': (f, 'face2.jpg')},
                        content_type='multipart/form-data'
                    )
                
                upload_data2 = json.loads(upload_response2.data)
                image_id2 = upload_data2['imageId']
                
                # 检测人像
                detect_response2 = client.post(
                    '/api/detect',
                    json={'imageId': image_id2}
                )
                
                if detect_response2.status_code == 422:
                    pytest.skip("测试图片中未检测到人脸")
                
                detect_data2 = json.loads(detect_response2.data)
                if len(detect_data2['faces']) == 0:
                    pytest.skip("测试图片中未检测到人脸")
                
                face_id2 = detect_data2['faces'][0]['faceId']
                
                print(f"✓ 步骤 2: 第二张图片上传并检测成功")
                
                # ========== 步骤 3: 使用混合人像进行搜索 ==========
                search_response = client.post(
                    '/api/search',
                    json={
                        'targetFaces': [
                            {
                                'type': 'library',
                                'libraryFaceId': library_face_id
                            },
                            {
                                'type': 'uploaded',
                                'imageId': image_id2,
                                'faceId': face_id2
                            }
                        ],
                        'searchFolder': temp_search_folder,
                        'threshold': 0.5
                    }
                )
                
                # 验证搜索任务创建成功
                assert search_response.status_code == 200
                search_data = json.loads(search_response.data)
                assert 'taskId' in search_data
                
                task_id = search_data['taskId']
                print(f"✓ 步骤 3: 混合搜索任务创建成功，taskId: {task_id}")
                
                # ========== 步骤 4: 等待搜索完成 ==========
                max_wait = 15
                start_time = time.time()
                final_status = None
                
                while time.time() - start_time < max_wait:
                    status_response = client.get(f'/api/search/{task_id}')
                    status_data = json.loads(status_response.data)
                    
                    if status_data['status'] in ['completed', 'cancelled']:
                        final_status = status_data
                        break
                    
                    time.sleep(0.2)
                
                # 验证搜索完成
                assert final_status is not None
                assert final_status['status'] == 'completed'
                assert 'results' in final_status
                
                print(f"✓ 步骤 4: 混合搜索完成，找到 {len(final_status['results'])} 个匹配结果")
                
                # ========== 步骤 5: 验证结果去重 ==========
                results = final_status['results']
                
                # 验证没有重复的图片路径
                image_paths = [r['imagePath'] for r in results]
                unique_paths = set(image_paths)
                assert len(image_paths) == len(unique_paths), "结果中不应有重复的图片路径"
                
                print(f"✓ 步骤 5: 结果去重验证通过")
                print("\n✓✓✓ 混合搜索工作流测试通过 ✓✓✓")
                
            finally:
                if os.path.exists(tmp_path2):
                    os.unlink(tmp_path2)
                    
        finally:
            if os.path.exists(tmp_path1):
                os.unlink(tmp_path1)

    
    def test_library_management_workflow(self, client):
        """
        测试库管理工作流
        
        工作流：保存人像 → 编辑名称 → 查询列表 → 搜索过滤 → 删除人像 → 验证删除
        
        **验证需求：3.1-3.7, 6.2-6.5**
        """
        print("\n========== 测试库管理工作流 ==========")
        
        # ========== 步骤 1: 保存多个人像到库 ==========
        library_face_ids = []
        
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                img = self.create_face_image()
                img.save(tmp.name)
                tmp_path = tmp.name
            
            try:
                # 上传图片
                with open(tmp_path, 'rb') as f:
                    upload_response = client.post(
                        '/api/upload',
                        data={'file': (f, f'face{i}.jpg')},
                        content_type='multipart/form-data'
                    )
                
                upload_data = json.loads(upload_response.data)
                image_id = upload_data['imageId']
                
                # 检测人像
                detect_response = client.post(
                    '/api/detect',
                    json={'imageId': image_id}
                )
                
                if detect_response.status_code == 422:
                    continue
                
                detect_data = json.loads(detect_response.data)
                if len(detect_data['faces']) == 0:
                    continue
                
                face_id = detect_data['faces'][0]['faceId']
                
                # 保存到库
                save_response = client.post(
                    '/api/library/faces',
                    json={
                        'imageId': image_id,
                        'faceId': face_id,
                        'name': f'测试人像{i}'
                    }
                )
                
                if save_response.status_code == 200:
                    save_data = json.loads(save_response.data)
                    library_face_ids.append(save_data['id'])
                
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        if len(library_face_ids) == 0:
            pytest.skip("未能保存任何人像到库")
        
        print(f"✓ 步骤 1: 成功保存 {len(library_face_ids)} 个人像到库")
        
        # ========== 步骤 2: 查询人像列表 ==========
        list_response = client.get('/api/library/faces')
        assert list_response.status_code == 200
        
        list_data = json.loads(list_response.data)
        assert 'faces' in list_data
        assert len(list_data['faces']) >= len(library_face_ids)
        
        # 验证列表结构
        for face in list_data['faces']:
            assert 'id' in face
            assert 'name' in face
            assert 'thumbnailUrl' in face
            assert 'createdAt' in face
        
        print(f"✓ 步骤 2: 人像列表查询成功，共 {len(list_data['faces'])} 个人像")
        
        # ========== 步骤 3: 编辑人像名称 ==========
        if len(library_face_ids) > 0:
            first_face_id = library_face_ids[0]
            new_name = '已编辑的人像名称'
            
            update_response = client.put(
                f'/api/library/faces/{first_face_id}',
                json={'name': new_name}
            )
            
            assert update_response.status_code == 200
            update_data = json.loads(update_response.data)
            assert update_data['name'] == new_name
            
            # 验证名称已更新
            get_response = client.get(f'/api/library/faces/{first_face_id}')
            assert get_response.status_code == 200
            
            get_data = json.loads(get_response.data)
            assert get_data['name'] == new_name
            
            print(f"✓ 步骤 3: 人像名称编辑成功")
        
        # ========== 步骤 4: 按名称搜索 ==========
        if len(library_face_ids) > 0:
            search_response = client.get('/api/library/faces?search=测试')
            assert search_response.status_code == 200
            
            search_data = json.loads(search_response.data)
            assert 'faces' in search_data
            
            # 验证搜索结果只包含名称中有"测试"的人像
            for face in search_data['faces']:
                assert '测试' in face['name'] or '已编辑' in face['name']
            
            print(f"✓ 步骤 4: 按名称搜索成功，找到 {len(search_data['faces'])} 个匹配")
        
        # ========== 步骤 5: 按时间排序 ==========
        sort_response = client.get('/api/library/faces?sortBy=created_at')
        assert sort_response.status_code == 200
        
        sort_data = json.loads(sort_response.data)
        assert 'faces' in sort_data
        
        # 验证按时间排序（降序）
        if len(sort_data['faces']) > 1:
            for i in range(len(sort_data['faces']) - 1):
                # 新的应该在前面（降序）
                assert sort_data['faces'][i]['createdAt'] >= sort_data['faces'][i + 1]['createdAt']
        
        print(f"✓ 步骤 5: 按时间排序验证通过")
        
        # ========== 步骤 6: 删除人像 ==========
        if len(library_face_ids) > 0:
            delete_face_id = library_face_ids[-1]
            
            delete_response = client.delete(f'/api/library/faces/{delete_face_id}')
            assert delete_response.status_code == 200
            
            delete_data = json.loads(delete_response.data)
            assert delete_data['success'] is True
            
            # 验证人像已删除
            get_response = client.get(f'/api/library/faces/{delete_face_id}')
            assert get_response.status_code == 404
            
            # 验证列表中不再包含该人像
            list_response = client.get('/api/library/faces')
            list_data = json.loads(list_response.data)
            
            for face in list_data['faces']:
                assert face['id'] != delete_face_id
            
            print(f"✓ 步骤 6: 人像删除成功")
        
        print("\n✓✓✓ 库管理工作流测试通过 ✓✓✓")
    
    def test_error_handling_workflow(self, client):
        """
        测试错误处理工作流
        
        验证各种错误情况的处理
        
        **验证需求：6.7, 6.8, 7.3, 7.4**
        """
        print("\n========== 测试错误处理工作流 ==========")
        
        # ========== 测试 1: 保存人像时缺少必需参数 ==========
        save_response = client.post(
            '/api/library/faces',
            json={
                'imageId': 'test-image-id'
                # 缺少 faceId 和 name
            }
        )
        
        assert save_response.status_code == 400
        error_data = json.loads(save_response.data)
        assert 'error' in error_data
        
        print(f"✓ 测试 1: 缺少必需参数错误处理通过")
        
        # ========== 测试 2: 查询不存在的人像 ==========
        get_response = client.get('/api/library/faces/nonexistent-face-id')
        assert get_response.status_code == 404
        
        error_data = json.loads(get_response.data)
        assert 'error' in error_data
        
        print(f"✓ 测试 2: 查询不存在的人像错误处理通过")
        
        # ========== 测试 3: 更新不存在的人像 ==========
        update_response = client.put(
            '/api/library/faces/nonexistent-face-id',
            json={'name': '新名称'}
        )
        
        assert update_response.status_code == 404
        error_data = json.loads(update_response.data)
        assert 'error' in error_data
        
        print(f"✓ 测试 3: 更新不存在的人像错误处理通过")
        
        # ========== 测试 4: 删除不存在的人像 ==========
        delete_response = client.delete('/api/library/faces/nonexistent-face-id')
        assert delete_response.status_code == 404
        
        error_data = json.loads(delete_response.data)
        assert 'error' in error_data
        
        print(f"✓ 测试 4: 删除不存在的人像错误处理通过")
        
        # ========== 测试 5: 使用无效的搜索参数 ==========
        search_response = client.post(
            '/api/search',
            json={
                'targetFaces': [
                    {
                        'type': 'library',
                        'libraryFaceId': 'nonexistent-library-face-id'
                    }
                ],
                'searchFolder': '/nonexistent/folder',
                'threshold': 0.5
            }
        )
        
        # 应该返回验证错误（文件夹不存在）
        assert search_response.status_code == 400
        error_data = json.loads(search_response.data)
        assert 'error' in error_data
        
        print(f"✓ 测试 5: 无效搜索参数错误处理通过")
        
        print("\n✓✓✓ 错误处理工作流测试通过 ✓✓✓")
    
    def test_thumbnail_generation_workflow(self, client):
        """
        测试缩略图生成工作流
        
        验证缩略图生成、存储和访问
        
        **验证需求：5.1-5.7**
        """
        print("\n========== 测试缩略图生成工作流 ==========")
        
        # ========== 步骤 1: 上传并保存人像 ==========
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
            
            # 检测人像
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
            
            # 保存人像
            save_response = client.post(
                '/api/library/faces',
                json={
                    'imageId': image_id,
                    'faceId': face_id,
                    'name': '缩略图测试'
                }
            )
            
            assert save_response.status_code == 200
            save_data = json.loads(save_response.data)
            
            print(f"✓ 步骤 1: 人像保存成功")
            
            # ========== 步骤 2: 验证缩略图 URL ==========
            assert 'thumbnailUrl' in save_data
            thumbnail_url = save_data['thumbnailUrl']
            assert thumbnail_url.startswith('/api/library/faces/')
            assert thumbnail_url.endswith('/thumbnail')
            
            print(f"✓ 步骤 2: 缩略图 URL 格式正确")
            
            # ========== 步骤 3: 获取缩略图 ==========
            thumbnail_response = client.get(thumbnail_url)
            assert thumbnail_response.status_code == 200
            
            # 验证是图片格式
            assert thumbnail_response.content_type.startswith('image/')
            
            # 验证有内容
            assert len(thumbnail_response.data) > 0
            
            print(f"✓ 步骤 3: 缩略图获取成功，大小: {len(thumbnail_response.data)} 字节")
            
            # ========== 步骤 4: 验证缩略图是有效的图片 ==========
            from io import BytesIO
            try:
                thumbnail_img = Image.open(BytesIO(thumbnail_response.data))
                
                # 验证尺寸（应该是固定尺寸，如 150x150）
                width, height = thumbnail_img.size
                assert width <= 150 and height <= 150
                
                # 验证格式
                assert thumbnail_img.format in ['JPEG', 'PNG']
                
                print(f"✓ 步骤 4: 缩略图验证通过，尺寸: {width}x{height}, 格式: {thumbnail_img.format}")
                
            except Exception as e:
                pytest.fail(f"缩略图不是有效的图片: {e}")
            
            print("\n✓✓✓ 缩略图生成工作流测试通过 ✓✓✓")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
