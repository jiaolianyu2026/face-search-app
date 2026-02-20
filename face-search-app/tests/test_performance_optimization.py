"""
测试性能优化功能
包括并行处理和配置选项
"""

import pytest
import os
import sys

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from face_search import FaceSearchModule


class TestParallelProcessing:
    """测试并行处理功能"""
    
    def test_parallel_processing_enabled(self):
        """测试并行处理可以启用"""
        searcher = FaceSearchModule()
        
        # 默认应该启用并行处理
        assert hasattr(searcher, 'enable_parallel')
        assert hasattr(searcher, 'max_workers')
        
        # 可以修改设置
        searcher.enable_parallel = False
        assert searcher.enable_parallel == False
        
        searcher.max_workers = 8
        assert searcher.max_workers == 8
    
    def test_process_image_method_exists(self):
        """测试单个图片处理方法存在"""
        searcher = FaceSearchModule()
        
        # 验证私有方法存在
        assert hasattr(searcher, '_processImage')
        assert hasattr(searcher, '_searchFacesSequential')
        assert hasattr(searcher, '_searchFacesParallel')


# 注意：缩略图生成的测试已移至 test_thumbnail.py 和 test_thumbnail_properties.py


class TestConfigurationOptions:
    """测试配置选项功能"""
    
    def test_face_detection_model_configuration(self):
        """测试人脸检测模型配置"""
        from face_detection import FaceDetectionModule
        
        # 测试 HOG 模型
        detector_hog = FaceDetectionModule(model='hog')
        assert detector_hog.model == 'hog'
        
        # 测试 CNN 模型
        detector_cnn = FaceDetectionModule(model='cnn')
        assert detector_cnn.model == 'cnn'
    
    def test_cache_clear_method(self):
        """测试缓存清除方法"""
        from cache_module import CacheModule
        
        cache = CacheModule()
        
        # 验证清除方法存在并返回数量
        count = cache.clearCache()
        assert isinstance(count, int)
        assert count >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
