"""
单元测试：扩展的搜索 API
测试 POST /api/search 端点的多人像搜索功能

需求: 4.5, 4.7
"""

import pytest
import os
import sys
import tempfile
import shutil
import json
from PIL import Image
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app
from models import LibraryFace


class TestExtendedSearchAPI:
    """扩展搜索 API 的单元测试"""
    
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
        
        # 创建一些测试图片
        for i in range(3):
            img = Image.new('RGB', (200, 200), color=(i*80, i*80, i*80))
            img.save(os.path.join(temp_dir, f'test_image_{i}.jpg'))
        
        yield temp_dir
        
        # 清理
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def uploaded_image_with_face(self, client):
        """上传一张图片并检测人像，返回 imageId 和 faceId"""
        # 创建测试图片
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = Image.new('RGB', (200, 200), color=(128, 128, 128))
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            # 上传图片
            with open(tmp_path, 'rb') as f:
                response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test.jpg')},
                    content_type='multipart/form-data'
                )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            image_id = data['imageId']
            
            # 检测人像
            response = client.post(
                '/api/detect',
                json={'imageId': image_id}
            )
            
            # 无论是否检测到人像，都使用模拟的 faceId 和特征
            # 这样可以测试 API 逻辑而不依赖实际的人脸检测
            face_id = 'mock-face-id-' + image_id[:8]
            
            # 如果检测失败，手动添加到 detection_cache
            if response.status_code != 200:
                from app import detection_cache
                from models import DetectionResult, Face
                
                # 创建模拟的检测结果
                mock_face = Face(
                    faceId=face_id,
                    boundingBox={'x': 50, 'y': 50, 'width': 100, 'height': 100},
                    features=np.random.rand(128).tolist()
                )
                detection_result = DetectionResult(
                    faces=[mock_face]
                )
                detection_cache[image_id] = detection_result
            else:
                # 如果检测成功，使用实际的 faceId
                data = json.loads(response.data)
                if data.get('faces') and len(data['faces']) > 0:
                    face_id = data['faces'][0]['faceId']
            
            yield {'imageId': image_id, 'faceId': face_id}
        finally:
            # 清理
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    @pytest.fixture
    def library_face(self, client, uploaded_image_with_face):
        """创建一个库人像并返回其 ID"""
        # 保存人像到库
        response = client.post(
            '/api/library/faces',
            json={
                'imageId': uploaded_image_with_face['imageId'],
                'faceId': uploaded_image_with_face['faceId'],
                'name': '测试人像'
            }
        )
        
        if response.status_code == 200:
            data = json.loads(response.data)
            yield data['id']
        else:
            # 如果保存失败，返回一个模拟的 ID
            yield 'mock-library-face-id'
    
    # 测试 1: 新格式的多人像搜索（仅上传人像）
    def test_multi_face_search_uploaded_only(self, client, uploaded_image_with_face, temp_search_folder):
        """
        测试新格式的多人像搜索（仅使用上传的人像）
        需求: 4.5, 4.7
        """
        response = client.post(
            '/api/search',
            json={
                'targetFaces': [
                    {
                        'type': 'uploaded',
                        'imageId': uploaded_image_with_face['imageId'],
                        'faceId': uploaded_image_with_face['faceId']
                    }
                ],
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'taskId' in data
        assert 'status' in data
        assert data['status'] in ['pending', 'running']
        assert 'targetFacesCount' in data
        assert data['targetFacesCount'] == 1
    
    # 测试 2: 新格式的多人像搜索（多个上传人像）
    def test_multi_face_search_multiple_uploaded(self, client, temp_search_folder):
        """
        测试新格式的多人像搜索（多个上传的人像）
        需求: 4.5, 4.7
        """
        from app import detection_cache
        from models import DetectionResult, Face
        
        # 上传并检测两张图片
        uploaded_faces = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                img = Image.new('RGB', (200, 200), color=(i*100, i*100, i*100))
                img.save(tmp.name)
                tmp_path = tmp.name
            
            try:
                with open(tmp_path, 'rb') as f:
                    response = client.post(
                        '/api/upload',
                        data={'file': (f, f'test{i}.jpg')},
                        content_type='multipart/form-data'
                    )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                image_id = data['imageId']
                
                # 检测人像
                response = client.post(
                    '/api/detect',
                    json={'imageId': image_id}
                )
                
                # 使用模拟的 faceId
                face_id = f'mock-face-id-{i}'
                
                # 如果检测失败，手动添加到 detection_cache
                if response.status_code != 200:
                    mock_face = Face(
                        faceId=face_id,
                        boundingBox={'x': 50, 'y': 50, 'width': 100, 'height': 100},
                        features=np.random.rand(128).tolist()
                    )
                    detection_result = DetectionResult(
                        faces=[mock_face]
                    )
                    detection_cache[image_id] = detection_result
                else:
                    data = json.loads(response.data)
                    if data.get('faces') and len(data['faces']) > 0:
                        face_id = data['faces'][0]['faceId']
                
                uploaded_faces.append({'imageId': image_id, 'faceId': face_id})
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        # 使用两个人像进行搜索
        response = client.post(
            '/api/search',
            json={
                'targetFaces': [
                    {
                        'type': 'uploaded',
                        'imageId': uploaded_faces[0]['imageId'],
                        'faceId': uploaded_faces[0]['faceId']
                    },
                    {
                        'type': 'uploaded',
                        'imageId': uploaded_faces[1]['imageId'],
                        'faceId': uploaded_faces[1]['faceId']
                    }
                ],
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'taskId' in data
        assert 'targetFacesCount' in data
        assert data['targetFacesCount'] == 2
    
    # 测试 3: 混合上传和库人像的搜索
    def test_mixed_uploaded_and_library_search(self, client, uploaded_image_with_face, library_face, temp_search_folder):
        """
        测试混合上传和库人像的搜索
        需求: 4.5, 4.7
        """
        from app import detection_cache
        from models import DetectionResult, Face
        
        # 上传另一张图片
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = Image.new('RGB', (200, 200), color=(100, 100, 100))
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test2.jpg')},
                    content_type='multipart/form-data'
                )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            image_id2 = data['imageId']
            
            # 检测人像
            response = client.post(
                '/api/detect',
                json={'imageId': image_id2}
            )
            
            # 使用模拟的 faceId
            face_id2 = 'mock-face-id-2'
            
            # 如果检测失败，手动添加到 detection_cache
            if response.status_code != 200:
                mock_face = Face(
                    faceId=face_id2,
                    boundingBox={'x': 50, 'y': 50, 'width': 100, 'height': 100},
                    features=np.random.rand(128).tolist()
                )
                detection_result = DetectionResult(
                    faces=[mock_face]
                )
                detection_cache[image_id2] = detection_result
            else:
                data = json.loads(response.data)
                if data.get('faces') and len(data['faces']) > 0:
                    face_id2 = data['faces'][0]['faceId']
            
            # 混合搜索：一个上传人像 + 一个库人像
            response = client.post(
                '/api/search',
                json={
                    'targetFaces': [
                        {
                            'type': 'uploaded',
                            'imageId': image_id2,
                            'faceId': face_id2
                        },
                        {
                            'type': 'library',
                            'libraryFaceId': library_face
                        }
                    ],
                    'searchFolder': temp_search_folder,
                    'threshold': 0.6
                }
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'taskId' in data
            assert 'targetFacesCount' in data
            assert data['targetFacesCount'] == 2
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    # 测试 4: 向后兼容性（旧格式）
    def test_backward_compatibility_old_format(self, client, uploaded_image_with_face, temp_search_folder):
        """
        测试向后兼容性：旧格式的搜索请求仍然有效
        需求: 4.7
        """
        response = client.post(
            '/api/search',
            json={
                'imageId': uploaded_image_with_face['imageId'],
                'faceId': uploaded_image_with_face['faceId'],
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'taskId' in data
        assert 'status' in data
        assert data['status'] in ['pending', 'running']
        # 旧格式不应该返回 targetFacesCount
        assert 'targetFacesCount' not in data or data.get('targetFacesCount') is None
    
    # 测试 5: 新格式缺少 targetFaces
    def test_new_format_missing_target_faces(self, client, temp_search_folder):
        """
        测试新格式缺少 targetFaces 参数
        需求: 4.5
        """
        response = client.post(
            '/api/search',
            json={
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        # 应该返回 400 错误，因为既没有 targetFaces 也没有 imageId/faceId
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    # 测试 6: targetFaces 为空数组
    def test_target_faces_empty_array(self, client, temp_search_folder):
        """
        测试 targetFaces 为空数组
        需求: 4.5
        """
        response = client.post(
            '/api/search',
            json={
                'targetFaces': [],
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'targetFaces' in data['error']['message']
    
    # 测试 7: targetFaces 不是数组
    def test_target_faces_not_array(self, client, temp_search_folder):
        """
        测试 targetFaces 不是数组
        需求: 4.5
        """
        response = client.post(
            '/api/search',
            json={
                'targetFaces': 'not-an-array',
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'targetFaces' in data['error']['message']
    
    # 测试 8: 上传人像缺少 imageId
    def test_uploaded_face_missing_image_id(self, client, temp_search_folder):
        """
        测试上传人像缺少 imageId
        需求: 4.5
        """
        response = client.post(
            '/api/search',
            json={
                'targetFaces': [
                    {
                        'type': 'uploaded',
                        'faceId': 'some-face-id'
                    }
                ],
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'imageId' in data['error']['message']
    
    # 测试 9: 上传人像缺少 faceId
    def test_uploaded_face_missing_face_id(self, client, uploaded_image_with_face, temp_search_folder):
        """
        测试上传人像缺少 faceId
        需求: 4.5
        """
        response = client.post(
            '/api/search',
            json={
                'targetFaces': [
                    {
                        'type': 'uploaded',
                        'imageId': uploaded_image_with_face['imageId']
                    }
                ],
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'faceId' in data['error']['message']
    
    # 测试 10: 库人像缺少 libraryFaceId
    def test_library_face_missing_id(self, client, temp_search_folder):
        """
        测试库人像缺少 libraryFaceId
        需求: 4.5
        """
        response = client.post(
            '/api/search',
            json={
                'targetFaces': [
                    {
                        'type': 'library'
                    }
                ],
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'libraryFaceId' in data['error']['message']
    
    # 测试 11: 无效的人像类型
    def test_invalid_face_type(self, client, temp_search_folder):
        """
        测试无效的人像类型
        需求: 4.5
        """
        response = client.post(
            '/api/search',
            json={
                'targetFaces': [
                    {
                        'type': 'invalid-type',
                        'someId': 'some-id'
                    }
                ],
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'type' in data['error']['message'] or 'invalid' in data['error']['message'].lower()
    
    # 测试 12: 不存在的上传图片
    def test_uploaded_face_nonexistent_image(self, client, temp_search_folder):
        """
        测试不存在的上传图片
        需求: 4.5
        """
        response = client.post(
            '/api/search',
            json={
                'targetFaces': [
                    {
                        'type': 'uploaded',
                        'imageId': 'nonexistent-image-id',
                        'faceId': 'some-face-id'
                    }
                ],
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['resourceType'] == 'image'
    
    # 测试 13: 不存在的库人像
    def test_library_face_nonexistent(self, client, temp_search_folder):
        """
        测试不存在的库人像
        需求: 4.5
        """
        response = client.post(
            '/api/search',
            json={
                'targetFaces': [
                    {
                        'type': 'library',
                        'libraryFaceId': 'nonexistent-library-face-id'
                    }
                ],
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['resourceType'] == 'library_face'
    
    # 测试 14: 仅库人像的搜索
    def test_library_face_only_search(self, client, library_face, temp_search_folder):
        """
        测试仅使用库人像的搜索
        需求: 4.5, 4.7
        """
        response = client.post(
            '/api/search',
            json={
                'targetFaces': [
                    {
                        'type': 'library',
                        'libraryFaceId': library_face
                    }
                ],
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'taskId' in data
        assert 'targetFacesCount' in data
        assert data['targetFacesCount'] == 1
    
    # 测试 15: 多个库人像的搜索
    def test_multiple_library_faces_search(self, client, library_face, temp_search_folder):
        """
        测试多个库人像的搜索
        需求: 4.5, 4.7
        """
        # 创建第二个库人像（如果可能）
        # 这里我们假设 library_face fixture 已经创建了一个
        # 为了简化，我们使用同一个库人像两次（实际应用中不会这样做）
        response = client.post(
            '/api/search',
            json={
                'targetFaces': [
                    {
                        'type': 'library',
                        'libraryFaceId': library_face
                    },
                    {
                        'type': 'library',
                        'libraryFaceId': library_face
                    }
                ],
                'searchFolder': temp_search_folder,
                'threshold': 0.6
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'taskId' in data
        assert 'targetFacesCount' in data
        assert data['targetFacesCount'] == 2
