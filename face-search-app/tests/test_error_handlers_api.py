"""
错误处理器的 API 集成测试
测试错误处理器在 Flask 应用中的实际工作
"""

import pytest
import json
import sys
import os
import tempfile
import shutil
from io import BytesIO

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app
from config import TEMP_UPLOAD_DIR


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # 清理
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


class TestUploadErrorHandling:
    """测试上传端点的错误处理"""
    
    def test_upload_no_file_validation_error(self, client):
        """测试未提供文件时返回验证错误"""
        response = client.post('/api/upload')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "未提供文件" in data["error"]["message"]
        assert data["error"]["field"] == "file"
    
    def test_upload_empty_filename_validation_error(self, client):
        """测试空文件名时返回验证错误"""
        response = client.post(
            '/api/upload',
            data={'file': (BytesIO(b''), '')}
        )
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "未选择文件" in data["error"]["message"]
    
    def test_upload_invalid_format_validation_error(self, client):
        """测试无效文件格式时返回验证错误"""
        response = client.post(
            '/api/upload',
            data={'file': (BytesIO(b'test'), 'test.txt')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "不支持" in data["error"]["message"].lower() or "unsupported" in data["error"]["message"].lower()


class TestDetectErrorHandling:
    """测试检测端点的错误处理"""
    
    def test_detect_missing_image_id_validation_error(self, client):
        """测试缺少 imageId 时返回验证错误"""
        response = client.post(
            '/api/detect',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "imageId" in data["error"]["message"]
    
    def test_detect_image_not_found_error(self, client):
        """测试图片不存在时返回未找到错误"""
        response = client.post(
            '/api/detect',
            data=json.dumps({"imageId": "nonexistent-id"}),
            content_type='application/json'
        )
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data["error"]["code"] == "NOT_FOUND"
        assert data["error"]["resourceType"] == "image"
        assert data["error"]["resourceId"] == "nonexistent-id"


class TestSearchErrorHandling:
    """测试搜索端点的错误处理"""
    
    def test_search_missing_parameters_validation_error(self, client):
        """测试缺少必需参数时返回验证错误"""
        # 缺少所有参数
        response = client.post(
            '/api/search',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"]["code"] == "VALIDATION_ERROR"
        
        # 只有 imageId
        response = client.post(
            '/api/search',
            data=json.dumps({"imageId": "test"}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "faceId" in data["error"]["message"]
    
    def test_search_invalid_threshold_validation_error(self, client, temp_dir):
        """测试无效阈值时返回验证错误"""
        # 阈值超出范围
        response = client.post(
            '/api/search',
            data=json.dumps({
                "imageId": "test",
                "faceId": "test",
                "searchFolder": temp_dir,
                "threshold": 1.5
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "threshold" in data["error"]["message"]
    
    def test_search_folder_not_found_validation_error(self, client):
        """测试搜索文件夹不存在时返回验证错误"""
        response = client.post(
            '/api/search',
            data=json.dumps({
                "imageId": "test",
                "faceId": "test",
                "searchFolder": "/nonexistent/folder"
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "不存在" in data["error"]["message"]


class TestSearchStatusErrorHandling:
    """测试搜索状态端点的错误处理"""
    
    def test_get_status_task_not_found_error(self, client):
        """测试任务不存在时返回未找到错误"""
        response = client.get('/api/search/nonexistent-task-id')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data["error"]["code"] == "NOT_FOUND"
        assert data["error"]["resourceType"] == "task"
        assert data["error"]["resourceId"] == "nonexistent-task-id"


class TestCancelSearchErrorHandling:
    """测试取消搜索端点的错误处理"""
    
    def test_cancel_task_not_found_error(self, client):
        """测试取消不存在的任务时返回未找到错误"""
        response = client.post('/api/search/nonexistent-task-id/cancel')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data["error"]["code"] == "NOT_FOUND"
        assert data["error"]["resourceType"] == "task"


class TestExportErrorHandling:
    """测试转存端点的错误处理"""
    
    def test_export_missing_parameters_validation_error(self, client):
        """测试缺少必需参数时返回验证错误"""
        response = client.post(
            '/api/export',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"]["code"] == "VALIDATION_ERROR"
    
    def test_export_invalid_image_paths_validation_error(self, client, temp_dir):
        """测试无效的 imagePaths 参数时返回验证错误"""
        # imagePaths 不是数组
        response = client.post(
            '/api/export',
            data=json.dumps({
                "imagePaths": "not-an-array",
                "targetFolder": temp_dir
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "数组" in data["error"]["message"]
        
        # imagePaths 为空数组
        response = client.post(
            '/api/export',
            data=json.dumps({
                "imagePaths": [],
                "targetFolder": temp_dir
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "不能为空" in data["error"]["message"]
    
    def test_export_target_folder_not_found_error(self, client):
        """测试目标文件夹不存在时返回未找到错误"""
        response = client.post(
            '/api/export',
            data=json.dumps({
                "imagePaths": ["/some/image.jpg"],
                "targetFolder": "/nonexistent/folder"
            }),
            content_type='application/json'
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["error"]["code"] == "NOT_FOUND"
        assert data["error"]["resourceType"] == "folder"


class TestHTTPErrorHandlers:
    """测试 HTTP 错误处理器"""
    
    def test_404_route_not_found(self, client):
        """测试访问不存在的路由"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data["error"]["code"] == "ROUTE_NOT_FOUND"
    
    def test_405_method_not_allowed(self, client):
        """测试使用不支持的 HTTP 方法"""
        # /api/upload 只支持 POST
        response = client.get('/api/upload')
        assert response.status_code == 405
        
        data = json.loads(response.data)
        assert data["error"]["code"] == "METHOD_NOT_ALLOWED"


class TestErrorResponseConsistency:
    """测试错误响应的一致性"""
    
    def test_all_errors_have_standard_format(self, client, temp_dir):
        """测试所有错误响应都遵循标准格式"""
        # 收集各种错误响应
        responses = [
            client.post('/api/upload'),  # 验证错误
            client.get('/api/preview/nonexistent'),  # 未找到错误
            client.get('/api/nonexistent'),  # 路由未找到
            client.post('/api/detect', data=json.dumps({}), content_type='application/json'),  # 验证错误
        ]
        
        for response in responses:
            data = json.loads(response.data)
            
            # 验证标准格式
            assert "error" in data
            assert isinstance(data["error"], dict)
            assert "code" in data["error"]
            assert "message" in data["error"]
            assert isinstance(data["error"]["code"], str)
            assert isinstance(data["error"]["message"], str)
            
            # 验证错误代码是大写
            assert data["error"]["code"].isupper()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
