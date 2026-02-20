"""
缩略图生成模块的单元测试
测试 ThumbnailGenerator 的核心功能
"""

import pytest
import os
import sys
from PIL import Image
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from thumbnail_generator import ThumbnailGenerator


class TestThumbnailGenerator:
    """ThumbnailGenerator 的单元测试套件"""
    
    @pytest.fixture
    def thumbnail_generator(self, tmp_path):
        """创建 ThumbnailGenerator 实例"""
        thumbnail_dir = str(tmp_path / "thumbnails")
        return ThumbnailGenerator(thumbnail_dir=thumbnail_dir)
    
    @pytest.fixture
    def sample_image(self, tmp_path):
        """创建测试用的样本图片"""
        img = Image.new('RGB', (400, 300), color='blue')
        img_path = tmp_path / "sample.jpg"
        img.save(img_path)
        return str(img_path)
    
    @pytest.fixture
    def large_image(self, tmp_path):
        """创建大尺寸测试图片"""
        img = Image.new('RGB', (2000, 1500), color='green')
        img_path = tmp_path / "large.jpg"
        img.save(img_path)
        return str(img_path)
    
    def test_thumbnail_directory_creation(self, tmp_path):
        """
        测试缩略图目录自动创建
        验证需求 5.1
        """
        thumbnail_dir = str(tmp_path / "new_thumbnails")
        assert not os.path.exists(thumbnail_dir)
        
        generator = ThumbnailGenerator(thumbnail_dir=thumbnail_dir)
        
        assert os.path.exists(thumbnail_dir)
        assert os.path.isdir(thumbnail_dir)
    
    def test_generate_thumbnail_normal_image(self, thumbnail_generator, sample_image):
        """
        测试正常图像的缩略图生成
        验证需求 5.1, 5.2, 5.3, 5.6
        """
        bounding_box = {
            'x': 100,
            'y': 50,
            'width': 150,
            'height': 150
        }
        output_filename = "test_thumbnail.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            sample_image,
            bounding_box,
            output_filename
        )
        
        # 验证返回路径
        assert result_path is not None
        assert os.path.exists(result_path)
        
        # 验证缩略图文件
        with Image.open(result_path) as thumb:
            # 验证尺寸为 150x150
            assert thumb.size == (150, 150)
            # 验证格式为 JPEG
            assert thumb.format == 'JPEG'
            # 验证模式为 RGB
            assert thumb.mode == 'RGB'
    
    def test_generate_thumbnail_with_padding(self, thumbnail_generator, sample_image):
        """
        测试边距添加功能
        验证需求 5.2
        """
        # 边界框在图片中心
        bounding_box = {
            'x': 150,
            'y': 100,
            'width': 100,
            'height': 100
        }
        output_filename = "padded_thumbnail.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            sample_image,
            bounding_box,
            output_filename
        )
        
        assert result_path is not None
        assert os.path.exists(result_path)
        
        # 验证缩略图成功生成（边距计算正确）
        with Image.open(result_path) as thumb:
            assert thumb.size == (150, 150)
    
    def test_generate_thumbnail_edge_bounding_box(self, thumbnail_generator, sample_image):
        """
        测试边界框在图片边缘的情况
        验证需求 5.2（边距不应超出图片边界）
        """
        # 边界框在左上角
        bounding_box = {
            'x': 0,
            'y': 0,
            'width': 50,
            'height': 50
        }
        output_filename = "edge_thumbnail.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            sample_image,
            bounding_box,
            output_filename
        )
        
        assert result_path is not None
        assert os.path.exists(result_path)
        
        # 验证缩略图成功生成（边距被正确裁剪）
        with Image.open(result_path) as thumb:
            assert thumb.size == (150, 150)
    
    def test_generate_thumbnail_non_square_face(self, thumbnail_generator, sample_image):
        """
        测试非正方形人像区域的处理
        验证需求 5.4, 5.5
        """
        # 宽高比不同的边界框
        bounding_box = {
            'x': 50,
            'y': 50,
            'width': 200,  # 宽
            'height': 100  # 窄
        }
        output_filename = "non_square_thumbnail.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            sample_image,
            bounding_box,
            output_filename
        )
        
        assert result_path is not None
        assert os.path.exists(result_path)
        
        # 验证缩略图为正方形（使用居中裁剪）
        with Image.open(result_path) as thumb:
            assert thumb.size == (150, 150)
            assert thumb.width == thumb.height
    
    def test_generate_thumbnail_tall_face(self, thumbnail_generator, sample_image):
        """
        测试高瘦人像区域的处理
        验证需求 5.4, 5.5
        """
        # 高瘦的边界框
        bounding_box = {
            'x': 150,
            'y': 20,
            'width': 80,   # 窄
            'height': 200  # 高
        }
        output_filename = "tall_thumbnail.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            sample_image,
            bounding_box,
            output_filename
        )
        
        assert result_path is not None
        assert os.path.exists(result_path)
        
        # 验证缩略图为正方形
        with Image.open(result_path) as thumb:
            assert thumb.size == (150, 150)
    
    def test_generate_thumbnail_large_image(self, thumbnail_generator, large_image):
        """
        测试大尺寸图片的缩略图生成
        验证需求 5.3（缩放到固定尺寸）
        """
        bounding_box = {
            'x': 500,
            'y': 400,
            'width': 600,
            'height': 600
        }
        output_filename = "large_thumbnail.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            large_image,
            bounding_box,
            output_filename
        )
        
        assert result_path is not None
        assert os.path.exists(result_path)
        
        # 验证缩略图被缩放到固定尺寸
        with Image.open(result_path) as thumb:
            assert thumb.size == (150, 150)
    
    def test_generate_thumbnail_invalid_image_path(self, thumbnail_generator):
        """
        测试无效图像路径的错误处理
        验证需求 5.7
        """
        bounding_box = {
            'x': 50,
            'y': 50,
            'width': 100,
            'height': 100
        }
        output_filename = "error_thumbnail.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            "/nonexistent/image.jpg",
            bounding_box,
            output_filename
        )
        
        # 应该返回占位图路径
        assert result_path is not None
        assert os.path.exists(result_path)
        
        # 验证占位图是有效的图片
        with Image.open(result_path) as thumb:
            assert thumb.size == (150, 150)
            assert thumb.format == 'JPEG'
    
    def test_generate_thumbnail_corrupted_image(self, thumbnail_generator, tmp_path):
        """
        测试损坏图像的错误处理
        验证需求 5.7
        """
        # 创建一个无效的图片文件
        corrupted_path = tmp_path / "corrupted.jpg"
        with open(corrupted_path, 'w') as f:
            f.write("This is not an image")
        
        bounding_box = {
            'x': 50,
            'y': 50,
            'width': 100,
            'height': 100
        }
        output_filename = "corrupted_thumbnail.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            str(corrupted_path),
            bounding_box,
            output_filename
        )
        
        # 应该返回占位图路径
        assert result_path is not None
        assert os.path.exists(result_path)
        
        # 验证占位图是有效的图片
        with Image.open(result_path) as thumb:
            assert thumb.size == (150, 150)
    
    def test_generate_thumbnail_rgba_image(self, thumbnail_generator, tmp_path):
        """
        测试 RGBA 图像的处理（转换为 RGB）
        验证需求 5.6
        """
        # 创建 RGBA 图像
        img = Image.new('RGBA', (300, 300), color=(255, 0, 0, 128))
        img_path = tmp_path / "rgba_image.png"
        img.save(img_path)
        
        bounding_box = {
            'x': 50,
            'y': 50,
            'width': 150,
            'height': 150
        }
        output_filename = "rgba_thumbnail.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            str(img_path),
            bounding_box,
            output_filename
        )
        
        assert result_path is not None
        assert os.path.exists(result_path)
        
        # 验证转换为 RGB 模式
        with Image.open(result_path) as thumb:
            assert thumb.mode == 'RGB'
            assert thumb.format == 'JPEG'
    
    def test_generate_thumbnail_grayscale_image(self, thumbnail_generator, tmp_path):
        """
        测试灰度图像的处理（转换为 RGB）
        验证需求 5.6
        """
        # 创建灰度图像
        img = Image.new('L', (300, 300), color=128)
        img_path = tmp_path / "gray_image.jpg"
        img.save(img_path)
        
        bounding_box = {
            'x': 50,
            'y': 50,
            'width': 150,
            'height': 150
        }
        output_filename = "gray_thumbnail.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            str(img_path),
            bounding_box,
            output_filename
        )
        
        assert result_path is not None
        assert os.path.exists(result_path)
        
        # 验证转换为 RGB 模式
        with Image.open(result_path) as thumb:
            assert thumb.mode == 'RGB'
    
    def test_generate_thumbnail_small_bounding_box(self, thumbnail_generator, sample_image):
        """
        测试小尺寸边界框的处理（放大到固定尺寸）
        验证需求 5.3
        """
        # 非常小的边界框
        bounding_box = {
            'x': 100,
            'y': 100,
            'width': 20,
            'height': 20
        }
        output_filename = "small_thumbnail.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            sample_image,
            bounding_box,
            output_filename
        )
        
        assert result_path is not None
        assert os.path.exists(result_path)
        
        # 验证缩略图被放大到固定尺寸
        with Image.open(result_path) as thumb:
            assert thumb.size == (150, 150)
    
    def test_delete_thumbnail(self, thumbnail_generator, sample_image):
        """
        测试缩略图删除功能
        """
        bounding_box = {
            'x': 50,
            'y': 50,
            'width': 100,
            'height': 100
        }
        output_filename = "delete_test.jpg"
        
        # 生成缩略图
        result_path = thumbnail_generator.generateThumbnail(
            sample_image,
            bounding_box,
            output_filename
        )
        
        assert os.path.exists(result_path)
        
        # 删除缩略图
        success = thumbnail_generator.delete_thumbnail(result_path)
        
        assert success is True
        assert not os.path.exists(result_path)
    
    def test_delete_nonexistent_thumbnail(self, thumbnail_generator):
        """
        测试删除不存在的缩略图
        """
        result = thumbnail_generator.delete_thumbnail("/nonexistent/thumbnail.jpg")
        assert result is False
    
    def test_thumbnail_quality(self, thumbnail_generator, sample_image):
        """
        测试缩略图质量设置
        验证需求 5.6（JPEG 格式优化存储）
        """
        bounding_box = {
            'x': 50,
            'y': 50,
            'width': 150,
            'height': 150
        }
        output_filename = "quality_test.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            sample_image,
            bounding_box,
            output_filename
        )
        
        assert result_path is not None
        
        # 验证文件大小合理（JPEG 压缩）
        file_size = os.path.getsize(result_path)
        # 150x150 RGB 图片，压缩后应该小于 50KB
        assert file_size < 50 * 1024


class TestThumbnailGeneratorEdgeCases:
    """缩略图生成器的边缘情况测试"""
    
    @pytest.fixture
    def thumbnail_generator(self, tmp_path):
        """创建 ThumbnailGenerator 实例"""
        thumbnail_dir = str(tmp_path / "thumbnails")
        return ThumbnailGenerator(thumbnail_dir=thumbnail_dir)
    
    def test_bounding_box_exceeds_image_bounds(self, thumbnail_generator, tmp_path):
        """
        测试边界框超出图片边界的情况
        验证需求 5.2
        """
        # 创建小图片
        img = Image.new('RGB', (100, 100), color='red')
        img_path = tmp_path / "small.jpg"
        img.save(img_path)
        
        # 边界框超出图片边界
        bounding_box = {
            'x': 50,
            'y': 50,
            'width': 100,  # 超出右边界
            'height': 100  # 超出下边界
        }
        output_filename = "exceed_bounds.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            str(img_path),
            bounding_box,
            output_filename
        )
        
        # 应该成功生成（自动裁剪到图片边界）
        assert result_path is not None
        assert os.path.exists(result_path)
        
        with Image.open(result_path) as thumb:
            assert thumb.size == (150, 150)
    
    def test_zero_size_bounding_box(self, thumbnail_generator, tmp_path):
        """
        测试零尺寸边界框的处理
        """
        img = Image.new('RGB', (200, 200), color='blue')
        img_path = tmp_path / "test.jpg"
        img.save(img_path)
        
        bounding_box = {
            'x': 50,
            'y': 50,
            'width': 0,
            'height': 0
        }
        output_filename = "zero_size.jpg"
        
        # 应该返回占位图或处理错误
        result_path = thumbnail_generator.generateThumbnail(
            str(img_path),
            bounding_box,
            output_filename
        )
        
        # 验证返回了某种结果（占位图或错误处理）
        assert result_path is not None
    
    def test_negative_bounding_box_coordinates(self, thumbnail_generator, tmp_path):
        """
        测试负坐标边界框的处理
        """
        img = Image.new('RGB', (200, 200), color='green')
        img_path = tmp_path / "test.jpg"
        img.save(img_path)
        
        bounding_box = {
            'x': -10,
            'y': -10,
            'width': 50,
            'height': 50
        }
        output_filename = "negative_coords.jpg"
        
        result_path = thumbnail_generator.generateThumbnail(
            str(img_path),
            bounding_box,
            output_filename
        )
        
        # 应该成功生成（坐标被裁剪到 0）
        assert result_path is not None
        assert os.path.exists(result_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
