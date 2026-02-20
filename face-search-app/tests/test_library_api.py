"""
Unit tests for Face Library Management API endpoints.
Tests all 6 library API endpoints with success and error scenarios.

验证需求: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8
"""

import pytest
import os
import sys
import json
import uuid
from PIL import Image, ImageDraw

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, detection_cache
from config import TEMP_UPLOAD_DIR
from models import LibraryFace


class TestLibraryAPI:
    """Test suite for Face Library Management API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def test_image_with_face(self, tmp_path):
        """Create a test image with a face-like pattern."""
        img = Image.new('RGB', (400, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple face-like pattern
        draw.ellipse([100, 100, 300, 300], fill='peachpuff', outline='black')
        draw.ellipse([140, 160, 180, 200], fill='black')  # Left eye
        draw.ellipse([220, 160, 260, 200], fill='black')  # Right eye
        draw.arc([150, 220, 250, 280], 0, 180, fill='black', width=3)  # Mouth
        
        img_path = tmp_path / "test_face.jpg"
        img.save(img_path)
        return img_path
    
    @pytest.fixture
    def uploaded_face_data(self, client, test_image_with_face):
        """Upload an image, detect faces, and return imageId and faceId."""
        # Upload the image
        with open(test_image_with_face, 'rb') as f:
            response = client.post(
                '/api/upload',
                data={'file': (f, 'test_face.jpg')},
                content_type='multipart/form-data'
            )
        
        assert response.status_code == 200
        upload_data = json.loads(response.data)
        image_id = upload_data['imageId']
        
        # Detect faces
        response = client.post(
            '/api/detect',
            data=json.dumps({'imageId': image_id}),
            content_type='application/json'
        )
        
        # Handle both success and no-face cases
        if response.status_code == 200:
            detect_data = json.loads(response.data)
            face_id = detect_data['faces'][0]['faceId']
            return {'imageId': image_id, 'faceId': face_id}
        else:
            # If no face detected, create mock data in cache
            face_id = str(uuid.uuid4())
            from models import Face, DetectionResult
            mock_face = Face(
                faceId=face_id,
                boundingBox={'x': 100, 'y': 100, 'width': 200, 'height': 200},
                features=[0.1] * 128
            )
            detection_cache[image_id] = DetectionResult(
                faces=[mock_face],
                error=None
            )
            return {'imageId': image_id, 'faceId': face_id}
    
    @pytest.fixture
    def saved_face_id(self, client, uploaded_face_data):
        """Save a face to library and return its ID."""
        response = client.post(
            '/api/library/faces',
            data=json.dumps({
                'imageId': uploaded_face_data['imageId'],
                'faceId': uploaded_face_data['faceId'],
                'name': '测试人像'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        return data['id']
    
    # ==================== POST /api/library/faces ====================
    
    def test_save_face_success(self, client, uploaded_face_data):
        """测试成功保存人像到库 - 需求 6.1"""
        response = client.post(
            '/api/library/faces',
            data=json.dumps({
                'imageId': uploaded_face_data['imageId'],
                'faceId': uploaded_face_data['faceId'],
                'name': '张三'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # 验证响应结构
        assert 'id' in data
        assert 'name' in data
        assert 'thumbnail_path' in data
        assert 'created_at' in data
        assert 'source_image_id' in data
        
        # 验证数据内容
        assert data['name'] == '张三'
        assert data['source_image_id'] == uploaded_face_data['imageId']
        # created_at 可能是字符串（ISO 8601）或数字（时间戳）
        assert data['created_at'] is not None
        assert len(str(data['created_at'])) > 0
    
    def test_save_face_missing_imageId(self, client):
        """测试缺少 imageId 参数 - 需求 6.7, 6.8"""
        response = client.post(
            '/api/library/faces',
            data=json.dumps({
                'faceId': 'some-face-id',
                'name': '张三'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert 'imageId' in data['error']['message']
    
    def test_save_face_missing_faceId(self, client, uploaded_face_data):
        """测试缺少 faceId 参数 - 需求 6.7, 6.8"""
        response = client.post(
            '/api/library/faces',
            data=json.dumps({
                'imageId': uploaded_face_data['imageId'],
                'name': '张三'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert 'faceId' in data['error']['message']
    
    def test_save_face_missing_name(self, client, uploaded_face_data):
        """测试缺少 name 参数 - 需求 6.7, 6.8"""
        response = client.post(
            '/api/library/faces',
            data=json.dumps({
                'imageId': uploaded_face_data['imageId'],
                'faceId': uploaded_face_data['faceId']
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert 'name' in data['error']['message']
    
    def test_save_face_nonexistent_image(self, client):
        """测试不存在的图片 ID - 需求 6.7, 6.8"""
        response = client.post(
            '/api/library/faces',
            data=json.dumps({
                'imageId': 'nonexistent-image-id',
                'faceId': 'some-face-id',
                'name': '张三'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['resourceType'] == 'detection_result'
    
    def test_save_face_nonexistent_faceId(self, client, uploaded_face_data):
        """测试不存在的人像 ID - 需求 6.7, 6.8"""
        response = client.post(
            '/api/library/faces',
            data=json.dumps({
                'imageId': uploaded_face_data['imageId'],
                'faceId': 'nonexistent-face-id',
                'name': '张三'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['resourceType'] == 'face'
    
    def test_save_face_empty_request_body(self, client):
        """测试空请求体 - 需求 6.7, 6.8"""
        response = client.post(
            '/api/library/faces',
            data='',
            content_type='application/json'
        )
        
        # Flask 对空请求体返回 400，可能是 HTML 或 JSON
        assert response.status_code == 400
    
    # ==================== GET /api/library/faces ====================
    
    def test_get_all_faces_empty(self, client):
        """测试获取空人像库 - 需求 6.2"""
        response = client.get('/api/library/faces')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'faces' in data
        assert 'total' in data
        assert isinstance(data['faces'], list)
        assert data['total'] == len(data['faces'])
    
    def test_get_all_faces_with_data(self, client, saved_face_id):
        """测试获取包含数据的人像库 - 需求 6.2"""
        response = client.get('/api/library/faces')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'faces' in data
        assert 'total' in data
        assert data['total'] > 0
        assert len(data['faces']) > 0
        
        # 验证人像数据结构（不包含特征向量）
        face = data['faces'][0]
        assert 'id' in face
        assert 'name' in face
        assert 'thumbnail_path' in face
        assert 'created_at' in face
    
    def test_get_all_faces_with_sort_by_name(self, client, saved_face_id):
        """测试按名称排序 - 需求 6.2"""
        response = client.get('/api/library/faces?sortBy=name')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'faces' in data
    
    def test_get_all_faces_with_search(self, client, saved_face_id):
        """测试按名称搜索 - 需求 6.2"""
        response = client.get('/api/library/faces?search=测试')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'faces' in data
    
    # ==================== GET /api/library/faces/{faceId} ====================
    
    def test_get_face_success(self, client, saved_face_id):
        """测试成功获取单个人像 - 需求 6.3"""
        response = client.get(f'/api/library/faces/{saved_face_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # 验证完整响应结构（包含特征向量）
        assert 'id' in data
        assert 'name' in data
        assert 'feature_vector' in data
        assert 'thumbnail_path' in data
        assert 'created_at' in data
        assert 'source_image_id' in data
        
        # 验证特征向量
        assert isinstance(data['feature_vector'], list)
        assert len(data['feature_vector']) == 128
        
        # 验证 ID 匹配
        assert data['id'] == saved_face_id
    
    def test_get_face_not_found(self, client):
        """测试获取不存在的人像 - 需求 6.3, 6.7, 6.8"""
        response = client.get('/api/library/faces/nonexistent-face-id')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['resourceType'] == 'library_face'
    
    # ==================== PUT /api/library/faces/{faceId} ====================
    
    def test_update_face_success(self, client, saved_face_id):
        """测试成功更新人像名称 - 需求 6.4"""
        new_name = '李四'
        response = client.put(
            f'/api/library/faces/{saved_face_id}',
            data=json.dumps({'name': new_name}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'success' in data
        assert data['success'] is True
        assert 'message' in data
        
        # 验证名称已更新
        get_response = client.get(f'/api/library/faces/{saved_face_id}')
        get_data = json.loads(get_response.data)
        assert get_data['name'] == new_name
    
    def test_update_face_missing_name(self, client, saved_face_id):
        """测试缺少 name 参数 - 需求 6.4, 6.7, 6.8"""
        response = client.put(
            f'/api/library/faces/{saved_face_id}',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        # 验证错误消息提到了名称相关的内容
        assert '名称' in data['error']['message'] or 'name' in data['error']['message'].lower()
    
    def test_update_face_not_found(self, client):
        """测试更新不存在的人像 - 需求 6.4, 6.7, 6.8"""
        response = client.put(
            '/api/library/faces/nonexistent-face-id',
            data=json.dumps({'name': '新名称'}),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['resourceType'] == 'library_face'
    
    def test_update_face_empty_request_body(self, client, saved_face_id):
        """测试空请求体 - 需求 6.4, 6.7, 6.8"""
        response = client.put(
            f'/api/library/faces/{saved_face_id}',
            data='',
            content_type='application/json'
        )
        
        # Flask 对空请求体返回 400，可能是 HTML 或 JSON
        assert response.status_code == 400
    
    # ==================== DELETE /api/library/faces/{faceId} ====================
    
    def test_delete_face_success(self, client, saved_face_id):
        """测试成功删除人像 - 需求 6.5"""
        response = client.delete(f'/api/library/faces/{saved_face_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'success' in data
        assert data['success'] is True
        assert 'message' in data
        
        # 验证人像已删除
        get_response = client.get(f'/api/library/faces/{saved_face_id}')
        assert get_response.status_code == 404
    
    def test_delete_face_not_found(self, client):
        """测试删除不存在的人像 - 需求 6.5, 6.7, 6.8"""
        response = client.delete('/api/library/faces/nonexistent-face-id')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['resourceType'] == 'library_face'
    
    # ==================== GET /api/library/faces/{faceId}/thumbnail ====================
    
    def test_get_thumbnail_success(self, client, saved_face_id):
        """测试成功获取缩略图 - 需求 6.6"""
        response = client.get(f'/api/library/faces/{saved_face_id}/thumbnail')
        
        assert response.status_code == 200
        # 验证返回的是图片文件
        assert response.content_type.startswith('image/')
        assert len(response.data) > 0
    
    def test_get_thumbnail_face_not_found(self, client):
        """测试获取不存在人像的缩略图 - 需求 6.6, 6.7, 6.8"""
        response = client.get('/api/library/faces/nonexistent-face-id/thumbnail')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['resourceType'] == 'library_face'
    
    # ==================== 集成测试 ====================
    
    def test_full_workflow(self, client, uploaded_face_data):
        """测试完整工作流：保存 -> 查询 -> 更新 -> 删除"""
        # 1. 保存人像
        save_response = client.post(
            '/api/library/faces',
            data=json.dumps({
                'imageId': uploaded_face_data['imageId'],
                'faceId': uploaded_face_data['faceId'],
                'name': '工作流测试'
            }),
            content_type='application/json'
        )
        assert save_response.status_code == 200
        face_id = json.loads(save_response.data)['id']
        
        # 2. 查询人像
        get_response = client.get(f'/api/library/faces/{face_id}')
        assert get_response.status_code == 200
        get_data = json.loads(get_response.data)
        assert get_data['name'] == '工作流测试'
        
        # 3. 更新名称
        update_response = client.put(
            f'/api/library/faces/{face_id}',
            data=json.dumps({'name': '更新后的名称'}),
            content_type='application/json'
        )
        assert update_response.status_code == 200
        
        # 4. 验证更新
        get_response2 = client.get(f'/api/library/faces/{face_id}')
        get_data2 = json.loads(get_response2.data)
        assert get_data2['name'] == '更新后的名称'
        
        # 5. 获取缩略图
        thumbnail_response = client.get(f'/api/library/faces/{face_id}/thumbnail')
        assert thumbnail_response.status_code == 200
        
        # 6. 删除人像
        delete_response = client.delete(f'/api/library/faces/{face_id}')
        assert delete_response.status_code == 200
        
        # 7. 验证删除
        get_response3 = client.get(f'/api/library/faces/{face_id}')
        assert get_response3.status_code == 404
    
    def test_multiple_faces_in_library(self, client, uploaded_face_data):
        """测试保存多个人像到库"""
        # 保存多个人像
        face_ids = []
        for i in range(3):
            response = client.post(
                '/api/library/faces',
                data=json.dumps({
                    'imageId': uploaded_face_data['imageId'],
                    'faceId': uploaded_face_data['faceId'],
                    'name': f'人像{i+1}'
                }),
                content_type='application/json'
            )
            assert response.status_code == 200
            face_ids.append(json.loads(response.data)['id'])
        
        # 验证所有人像都在库中
        list_response = client.get('/api/library/faces')
        assert list_response.status_code == 200
        list_data = json.loads(list_response.data)
        assert list_data['total'] >= 3
        
        # 验证 ID 唯一性
        saved_ids = [face['id'] for face in list_data['faces']]
        assert len(saved_ids) == len(set(saved_ids))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
