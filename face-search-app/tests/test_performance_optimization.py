"""
测试性能优化功能
包括并行处理、批处理和缩略图生成
"""

import pytest
import os
import sys
import tempfile
import shutil
from PIL import Image
import numpy as np

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from face_search import FaceSearchModule
from thumbnail_generator import ThumbnailGenerator
from config import THUMBNAIL_SIZE


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


class TestThumbnailGenerator:
    """测试缩略图生成功能"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.thumbnail_dir = os.path.join(self.temp_dir, 'thumbnails')
        
        # 创建测试图片
        self.test_image_path = os.path.join(self.temp_dir, 'test_image.jpg')
        self._create_test_image(self.test_image_path, (800, 600))
    
    def teardown_method(self):
        """清理测试环境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_image(self, path: str, size: tuple):
        """创建测试图片"""
        img = Image.new('RGB', size, color='red')
        img.save(path, 'JPEG')
    
    def test_thumbnail_generator_initialization(self):
        """测试缩略图生成器初始化"""
        generator = ThumbnailGenerator(self.thumbnail_dir)
        
        # 验证目录被创建
        assert os.path.exists(self.thumbnail_dir)
        assert generator.thumbnail_dir == self.thumbnail_dir
    
    def test_generate_thumbnail(self):
        """测试生成缩略图"""
        generator = ThumbnailGenerator(self.thumbnail_dir)
        
        # 生成缩略图
        thumbnail_path = generator.generateThumbnail(self.test_image_path)
        
        # 验证缩略图被创建
        assert thumbnail_path is not None
        assert os.path.exists(thumbnail_path)
        
        # 验证缩略图尺寸
        with Image.open(thumbnail_path) as img:
            # 缩略图应该小于或等于指定尺寸
            assert img.width <= THUMBNAIL_SIZE[0]
            assert img.height <= THUMBNAIL_SIZE[1]
    
    def test_thumbnail_caching(self):
        """测试缩略图缓存"""
        generator = ThumbnailGenerator(self.thumbnail_dir)
        
        # 第一次生成
        thumbnail_path1 = generator.generateThumbnail(self.test_image_path)
        mtime1 = os.path.getmtime(thumbnail_path1)
        
        # 第二次生成（应该使用缓存）
        thumbnail_path2 = generator.generateThumbnail(self.test_image_path)
        mtime2 = os.path.getmtime(thumbnail_path2)
        
        # 路径应该相同
        assert thumbnail_path1 == thumbnail_path2
        # 修改时间应该相同（使用了缓存）
        assert mtime1 == mtime2
    
    def test_get_thumbnail_path(self):
        """测试获取缩略图路径"""
        generator = ThumbnailGenerator(self.thumbnail_dir)
        
        # 缩略图不存在时返回 None
        assert generator.getThumbnailPath(self.test_image_path) is None
        
        # 生成缩略图
        thumbnail_path = generator.generateThumbnail(self.test_image_path)
        
        # 现在应该能获取到路径
        assert generator.getThumbnailPath(self.test_image_path) == thumbnail_path
    
    def test_clear_thumbnails(self):
        """测试清除缩略图"""
        generator = ThumbnailGenerator(self.thumbnail_dir)
        
        # 生成几个缩略图
        generator.generateThumbnail(self.test_image_path)
        
        # 创建另一个测试图片
        test_image2 = os.path.join(self.temp_dir, 'test_image2.jpg')
        self._create_test_image(test_image2, (600, 400))
        generator.generateThumbnail(test_image2)
        
        # 清除缩略图
        count = generator.clearThumbnails()
        
        # 验证清除数量
        assert count >= 2
        
        # 验证缩略图目录为空
        remaining_files = [f for f in os.listdir(self.thumbnail_dir) if os.path.isfile(os.path.join(self.thumbnail_dir, f))]
        assert len(remaining_files) == 0
    
    def test_generate_thumbnail_nonexistent_file(self):
        """测试对不存在的文件生成缩略图"""
        generator = ThumbnailGenerator(self.thumbnail_dir)
        
        # 尝试为不存在的文件生成缩略图
        result = generator.generateThumbnail('/nonexistent/path/image.jpg')
        
        # 应该返回 None
        assert result is None


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
