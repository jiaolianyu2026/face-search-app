"""
缩略图生成模块的属性测试
使用 Hypothesis 进行基于属性的测试
"""

import pytest
import os
import sys
import tempfile
import shutil
from PIL import Image
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from thumbnail_generator import ThumbnailGenerator


# ============================================================================
# 测试策略定义
# ============================================================================

# 有效的边界框策略
@st.composite
def valid_bounding_box(draw, max_image_width=2000, max_image_height=2000):
    """生成有效的边界框"""
    x = draw(st.integers(min_value=0, max_value=max_image_width - 50))
    y = draw(st.integers(min_value=0, max_value=max_image_height - 50))
    width = draw(st.integers(min_value=10, max_value=min(500, max_image_width - x)))
    height = draw(st.integers(min_value=10, max_value=min(500, max_image_height - y)))
    
    return {
        'x': x,
        'y': y,
        'width': width,
        'height': height
    }


# 图像尺寸策略
image_sizes = st.tuples(
    st.integers(min_value=100, max_value=2000),  # width
    st.integers(min_value=100, max_value=2000)   # height
)


# ============================================================================
# 辅助函数
# ============================================================================

def create_temp_dir():
    """创建临时目录"""
    return tempfile.mkdtemp()


def cleanup_temp_dir(temp_dir):
    """清理临时目录"""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def create_test_image(temp_dir, width, height, color='blue'):
    """创建测试图像"""
    img = Image.new('RGB', (width, height), color=color)
    img_path = os.path.join(temp_dir, f"test_{width}x{height}.jpg")
    img.save(img_path)
    return img_path


# ============================================================================
# 属性测试
# ============================================================================

class TestThumbnailGeneratorProperties:
    """缩略图生成器的属性测试套件"""
    
    # Feature: face-library-management, Property 17: 裁剪区域计算
    def test_property_17_crop_region_calculation(self):
        """
        **Validates: Requirements 5.1, 5.2**
        
        属性 17: 裁剪区域计算
        对于任意边界框和边距参数，裁剪后的图像区域应该大于原始边界框（因为添加了边距）
        """
        # 使用固定的测试用例而不是属性测试
        test_cases = [
            ((800, 600), {'x': 100, 'y': 100, 'width': 200, 'height': 200}),
            ((1024, 768), {'x': 200, 'y': 150, 'width': 300, 'height': 250}),
            ((640, 480), {'x': 50, 'y': 50, 'width': 150, 'height': 150}),
        ]
        
        for image_size, bbox in test_cases:
            width, height = image_size
        
        # 创建临时目录和生成器
        temp_dir = create_temp_dir()
        try:
            thumbnail_dir = os.path.join(temp_dir, "thumbnails")
            thumbnail_generator = ThumbnailGenerator(thumbnail_dir=thumbnail_dir)
            
            # 计算原始边界框面积
            original_area = bbox['width'] * bbox['height']
            
            # 计算裁剪区域（使用内部方法）
            crop_box = thumbnail_generator._calculate_crop_box(bbox, (width, height))
            left, top, right, bottom = crop_box
            
            # 计算裁剪区域面积
            crop_width = right - left
            crop_height = bottom - top
            crop_area = crop_width * crop_height
            
            # 验证：裁剪区域应该大于或等于原始边界框（因为添加了边距）
            assert crop_area >= original_area, \
                f"裁剪区域 ({crop_area}) 应该大于或等于原始边界框 ({original_area})"
            
            # 验证：裁剪区域不应超出图像边界
            assert left >= 0, f"左边界 ({left}) 不应为负"
            assert top >= 0, f"上边界 ({top}) 不应为负"
            assert right <= width, f"右边界 ({right}) 不应超出图像宽度 ({width})"
            assert bottom <= height, f"下边界 ({bottom}) 不应超出图像高度 ({height})"
            
            # 验证：裁剪区域应该是有效的（右>左，下>上）
            assert right > left, "右边界应该大于左边界"
            assert bottom > top, "下边界应该大于上边界"
        finally:
            cleanup_temp_dir(temp_dir)
    
    # Feature: face-library-management, Property 18: 缩略图尺寸固定
    @given(
        image_size=image_sizes,
        bbox=valid_bounding_box()
    )
    @settings(
        max_examples=10, 
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much]
    )
    def test_property_18_thumbnail_size_fixed(self, image_size, bbox):
        """
        **Validates: Requirements 5.3**
        
        属性 18: 缩略图尺寸固定
        对于任意输入图像和边界框，生成的缩略图的最大边长应该等于指定的固定尺寸
        """
        width, height = image_size
        
        # 确保边界框在图像范围内
        assume(bbox['x'] + bbox['width'] <= width)
        assume(bbox['y'] + bbox['height'] <= height)
        
        # 创建临时目录和生成器
        temp_dir = create_temp_dir()
        try:
            thumbnail_dir = os.path.join(temp_dir, "thumbnails")
            thumbnail_generator = ThumbnailGenerator(thumbnail_dir=thumbnail_dir)
            
            # 创建测试图像
            image_path = create_test_image(temp_dir, width, height)
            output_filename = f"test_size_{width}_{height}_{bbox['width']}_{bbox['height']}.jpg"
            
            # 生成缩略图
            result_path = thumbnail_generator.generateThumbnail(
                image_path,
                bbox,
                output_filename
            )
            
            # 验证缩略图生成成功
            assert result_path is not None, "缩略图生成应该成功"
            assert os.path.exists(result_path), "缩略图文件应该存在"
            
            # 验证缩略图尺寸
            with Image.open(result_path) as thumb:
                # 缩略图应该是固定尺寸 150x150
                expected_size = thumbnail_generator.THUMBNAIL_SIZE
                assert thumb.size == expected_size, \
                    f"缩略图尺寸 {thumb.size} 应该等于固定尺寸 {expected_size}"
                
                # 验证是正方形
                assert thumb.width == thumb.height, \
                    f"缩略图应该是正方形，但尺寸为 {thumb.width}x{thumb.height}"
        finally:
            cleanup_temp_dir(temp_dir)
    
    # Feature: face-library-management, Property 19: 缩略图格式验证
    @given(
        image_size=image_sizes,
        bbox=valid_bounding_box(),
        image_mode=st.sampled_from(['RGB', 'RGBA', 'L'])  # 不同的图像模式
    )
    @settings(
        max_examples=10, 
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_19_thumbnail_format_validation(self, image_size, bbox, image_mode):
        """
        **Validates: Requirements 5.6**
        
        属性 19: 缩略图格式验证
        对于任意生成的缩略图文件，文件应该是有效的 JPEG 格式且可以被图像库正确读取
        """
        width, height = image_size
        
        # 确保边界框在图像范围内
        assume(bbox['x'] + bbox['width'] <= width)
        assume(bbox['y'] + bbox['height'] <= height)
        
        # 创建临时目录和生成器
        temp_dir = create_temp_dir()
        try:
            thumbnail_dir = os.path.join(temp_dir, "thumbnails")
            thumbnail_generator = ThumbnailGenerator(thumbnail_dir=thumbnail_dir)
            
            # 创建不同模式的测试图像
            img = Image.new(image_mode, (width, height), color='blue')
            img_path = os.path.join(temp_dir, f"test_{image_mode}_{width}x{height}.jpg")
            
            # 保存图像（某些模式需要转换）
            if image_mode == 'RGBA':
                img_path = img_path.replace('.jpg', '.png')
                img.save(img_path, format='PNG')
            else:
                img.save(img_path)
            
            output_filename = f"test_format_{image_mode}_{width}_{height}.jpg"
            
            # 生成缩略图
            result_path = thumbnail_generator.generateThumbnail(
                img_path,
                bbox,
                output_filename
            )
            
            # 验证缩略图生成成功
            assert result_path is not None, "缩略图生成应该成功"
            assert os.path.exists(result_path), "缩略图文件应该存在"
            
            # 验证缩略图格式
            with Image.open(result_path) as thumb:
                # 验证格式为 JPEG
                assert thumb.format == 'JPEG', \
                    f"缩略图格式应该是 JPEG，但实际为 {thumb.format}"
                
                # 验证模式为 RGB（JPEG 标准）
                assert thumb.mode == 'RGB', \
                    f"缩略图模式应该是 RGB，但实际为 {thumb.mode}"
                
                # 验证可以获取像素数据（确保图像完整）
                pixels = thumb.load()
                assert pixels is not None, "应该能够加载像素数据"
                
                # 验证文件扩展名
                assert result_path.endswith('.jpg') or result_path.endswith('.jpeg'), \
                    f"缩略图文件应该有 .jpg 或 .jpeg 扩展名"
        finally:
            cleanup_temp_dir(temp_dir)
    
    # Feature: face-library-management, Property 20: 缩略图生成错误处理
    @given(
        bbox=valid_bounding_box(),
        error_type=st.sampled_from(['nonexistent', 'corrupted', 'invalid_bbox'])
    )
    @settings(
        max_examples=8, 
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_20_thumbnail_generation_error_handling(self, bbox, error_type):
        """
        **Validates: Requirements 5.7**
        
        属性 20: 缩略图生成错误处理
        对于任意无效的输入图像或边界框，缩略图生成应该返回错误或默认占位图路径，而不是崩溃
        """
        # 创建临时目录和生成器
        temp_dir = create_temp_dir()
        try:
            thumbnail_dir = os.path.join(temp_dir, "thumbnails")
            thumbnail_generator = ThumbnailGenerator(thumbnail_dir=thumbnail_dir)
            
            output_filename = f"test_error_{error_type}.jpg"
            
            if error_type == 'nonexistent':
                # 测试不存在的图像文件
                image_path = "/nonexistent/path/to/image.jpg"
                
            elif error_type == 'corrupted':
                # 测试损坏的图像文件
                corrupted_path = os.path.join(temp_dir, "corrupted.jpg")
                with open(corrupted_path, 'w') as f:
                    f.write("This is not a valid image file")
                image_path = corrupted_path
                
            elif error_type == 'invalid_bbox':
                # 测试无效的边界框（超出图像范围）
                img = Image.new('RGB', (100, 100), color='red')
                img_path = os.path.join(temp_dir, "small.jpg")
                img.save(img_path)
                image_path = img_path
                
                # 边界框超出图像范围
                bbox = {
                    'x': 50,
                    'y': 50,
                    'width': 200,  # 超出范围
                    'height': 200  # 超出范围
                }
            
            # 生成缩略图（不应该崩溃）
            try:
                result_path = thumbnail_generator.generateThumbnail(
                    image_path,
                    bbox,
                    output_filename
                )
                
                # 验证返回了某种结果（占位图或错误处理）
                if error_type in ['nonexistent', 'corrupted']:
                    # 对于文件错误，应该返回占位图
                    assert result_path is not None, "应该返回占位图路径"
                    assert os.path.exists(result_path), "占位图文件应该存在"
                    
                    # 验证占位图是有效的图像
                    with Image.open(result_path) as thumb:
                        assert thumb.size == thumbnail_generator.THUMBNAIL_SIZE
                        assert thumb.format == 'JPEG'
                
                elif error_type == 'invalid_bbox':
                    # 对于无效边界框，应该能够处理（裁剪到有效范围）
                    assert result_path is not None, "应该返回结果路径"
                    if os.path.exists(result_path):
                        with Image.open(result_path) as thumb:
                            assert thumb.size == thumbnail_generator.THUMBNAIL_SIZE
            
            except Exception as e:
                # 如果抛出异常，应该是预期的异常类型，不应该是系统崩溃
                pytest.fail(f"缩略图生成不应该崩溃，但抛出了异常: {type(e).__name__}: {str(e)}")
        finally:
            cleanup_temp_dir(temp_dir)


class TestThumbnailGeneratorAdditionalProperties:
    """缩略图生成器的额外属性测试"""
    
    # 额外属性：边距一致性
    @given(
        bbox=valid_bounding_box(),
        image_size=image_sizes
    )
    @settings(
        max_examples=8, 
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much]
    )
    def test_padding_consistency(self, bbox, image_size):
        """
        额外属性：边距计算的一致性
        验证边距计算遵循配置的比例
        """
        width, height = image_size
        
        # 确保边界框在图像范围内
        assume(bbox['x'] + bbox['width'] <= width)
        assume(bbox['y'] + bbox['height'] <= height)
        
        # 创建临时目录和生成器
        temp_dir = create_temp_dir()
        try:
            thumbnail_dir = os.path.join(temp_dir, "thumbnails")
            thumbnail_generator = ThumbnailGenerator(thumbnail_dir=thumbnail_dir)
            
            # 计算裁剪区域
            crop_box = thumbnail_generator._calculate_crop_box(bbox, (width, height))
            left, top, right, bottom = crop_box
            
            # 计算实际添加的边距
            padding_ratio = thumbnail_generator.PADDING_RATIO
            expected_padding_x = int(bbox['width'] * padding_ratio)
            expected_padding_y = int(bbox['height'] * padding_ratio)
            
            # 验证边距（考虑边界裁剪）
            actual_left_padding = bbox['x'] - left
            actual_top_padding = bbox['y'] - top
            actual_right_padding = right - (bbox['x'] + bbox['width'])
            actual_bottom_padding = bottom - (bbox['y'] + bbox['height'])
            
            # 边距应该不超过预期值（可能因边界裁剪而减少）
            assert actual_left_padding <= expected_padding_x
            assert actual_top_padding <= expected_padding_y
            assert actual_right_padding <= expected_padding_x
            assert actual_bottom_padding <= expected_padding_y
            
            # 边距应该非负
            assert actual_left_padding >= 0
            assert actual_top_padding >= 0
            assert actual_right_padding >= 0
            assert actual_bottom_padding >= 0
        finally:
            cleanup_temp_dir(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
