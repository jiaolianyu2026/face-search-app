"""
测试配置管理 API
包括获取配置、更新配置、清除缓存等功能
"""

import pytest
import os
import sys

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestConfigAPI:
    """测试配置 API"""
    
    def test_get_config(self, client):
        """测试获取配置"""
        response = client.get('/api/config')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # 验证配置字段存在
        assert 'similarity_threshold' in data
        assert 'face_detection_model' in data
        assert 'enable_parallel_processing' in data
        assert 'max_worker_threads' in data
        
        # 验证默认值
        assert isinstance(data['similarity_threshold'], float)
        assert data['face_detection_model'] in ['hog', 'cnn']
        assert isinstance(data['enable_parallel_processing'], bool)
        assert isinstance(data['max_worker_threads'], int)
    
    def test_update_similarity_threshold(self, client):
        """测试更新相似度阈值"""
        response = client.put('/api/config', json={
            'similarity_threshold': 0.7
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['config']['similarity_threshold'] == 0.7
        assert 'similarity_threshold' in data['message']
    
    def test_update_face_detection_model(self, client):
        """测试更新人脸检测模型"""
        response = client.put('/api/config', json={
            'face_detection_model': 'cnn'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['config']['face_detection_model'] == 'cnn'
        assert 'face_detection_model' in data['message']
    
    def test_update_parallel_processing(self, client):
        """测试更新并行处理设置"""
        response = client.put('/api/config', json={
            'enable_parallel_processing': False
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['config']['enable_parallel_processing'] == False
        assert 'enable_parallel_processing' in data['message']
    
    def test_update_max_worker_threads(self, client):
        """测试更新工作线程数"""
        response = client.put('/api/config', json={
            'max_worker_threads': 8
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['config']['max_worker_threads'] == 8
        assert 'max_worker_threads' in data['message']
    
    def test_update_multiple_config_fields(self, client):
        """测试同时更新多个配置字段"""
        response = client.put('/api/config', json={
            'similarity_threshold': 0.65,
            'face_detection_model': 'hog',
            'max_worker_threads': 6
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['config']['similarity_threshold'] == 0.65
        assert data['config']['face_detection_model'] == 'hog'
        assert data['config']['max_worker_threads'] == 6
    
    def test_invalid_similarity_threshold(self, client):
        """测试无效的相似度阈值"""
        # 超出范围
        response = client.put('/api/config', json={
            'similarity_threshold': 1.5
        })
        assert response.status_code == 400
        
        # 负数
        response = client.put('/api/config', json={
            'similarity_threshold': -0.1
        })
        assert response.status_code == 400
        
        # 非数字
        response = client.put('/api/config', json={
            'similarity_threshold': 'invalid'
        })
        assert response.status_code == 400
    
    def test_invalid_face_detection_model(self, client):
        """测试无效的人脸检测模型"""
        response = client.put('/api/config', json={
            'face_detection_model': 'invalid_model'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_invalid_max_worker_threads(self, client):
        """测试无效的工作线程数"""
        # 超出范围
        response = client.put('/api/config', json={
            'max_worker_threads': 20
        })
        assert response.status_code == 400
        
        # 小于最小值
        response = client.put('/api/config', json={
            'max_worker_threads': 0
        })
        assert response.status_code == 400
    
    def test_update_config_empty_body(self, client):
        """测试空请求体"""
        response = client.put('/api/config', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestCacheAPI:
    """测试缓存管理 API"""
    
    def test_clear_cache(self, client):
        """测试清除缓存"""
        response = client.post('/api/cache/clear')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'cleared_entries' in data
        assert 'message' in data
        assert isinstance(data['cleared_entries'], int)
        assert data['cleared_entries'] >= 0
    
    def test_clear_thumbnails(self, client):
        """测试清除缩略图"""
        response = client.post('/api/thumbnails/clear')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'cleared_thumbnails' in data
        assert 'message' in data
        assert isinstance(data['cleared_thumbnails'], int)
        assert data['cleared_thumbnails'] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
