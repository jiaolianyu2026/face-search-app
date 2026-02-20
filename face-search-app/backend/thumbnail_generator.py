"""
缩略图生成模块
为人像库生成缩略图
"""

import os
import logging
from PIL import Image, ImageOps
from typing import Tuple, Optional
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    """
    缩略图生成器类
    负责从原始图片中裁剪人像区域并生成固定尺寸的缩略图
    """
    
    # 缩略图配置
    THUMBNAIL_SIZE = (150, 150)  # 固定尺寸
    THUMBNAIL_FORMAT = 'JPEG'  # 输出格式
    THUMBNAIL_QUALITY = 85  # JPEG质量
    PADDING_RATIO = 0.2  # 边距比例（相对于人像尺寸）
    
    def __init__(self, thumbnail_dir: str = 'backend/cache/thumbnails'):
        """
        初始化缩略图生成器
        
        Args:
            thumbnail_dir: 缩略图保存目录
        """
        self.thumbnail_dir = thumbnail_dir
        self._ensure_thumbnail_dir()
    
    def _ensure_thumbnail_dir(self):
        """确保缩略图目录存在"""
        Path(self.thumbnail_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"缩略图目录已准备: {self.thumbnail_dir}")
    
    def generateThumbnail(self, image_path: str, bounding_box: dict, 
                         output_filename: str) -> Optional[str]:
        """
        生成人像缩略图
        
        Args:
            image_path: 原始图片路径
            bounding_box: 人像边界框 {x: int, y: int, width: int, height: int}
            output_filename: 输出文件名（不含路径）
            
        Returns:
            缩略图文件的完整路径，失败返回 None
        """
        try:
            # 打开原始图片
            with Image.open(image_path) as img:
                # 转换为 RGB 模式（确保兼容性）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 计算裁剪区域（添加边距）
                crop_box = self._calculate_crop_box(
                    bounding_box, 
                    img.size
                )
                
                # 裁剪人像区域
                face_img = img.crop(crop_box)
                
                # 生成缩略图（保持宽高比）
                thumbnail = self._create_thumbnail(face_img)
                
                # 保存缩略图
                output_path = os.path.join(self.thumbnail_dir, output_filename)
                thumbnail.save(
                    output_path, 
                    format=self.THUMBNAIL_FORMAT,
                    quality=self.THUMBNAIL_QUALITY
                )
                
                logger.info(f"缩略图已生成: {output_path}")
                return output_path
                
        except FileNotFoundError:
            logger.error(f"图片文件不存在: {image_path}")
            return self._create_placeholder(output_filename)
        except Exception as e:
            logger.error(f"生成缩略图失败: {str(e)}")
            return self._create_placeholder(output_filename)
    
    def _calculate_crop_box(self, bounding_box: dict, 
                           image_size: Tuple[int, int]) -> Tuple[int, int, int, int]:
        """
        计算裁剪区域（添加边距）
        
        Args:
            bounding_box: 人像边界框
            image_size: 图片尺寸 (width, height)
            
        Returns:
            裁剪区域 (left, top, right, bottom)
        """
        x = bounding_box['x']
        y = bounding_box['y']
        width = bounding_box['width']
        height = bounding_box['height']
        
        # 计算边距
        padding_x = int(width * self.PADDING_RATIO)
        padding_y = int(height * self.PADDING_RATIO)
        
        # 计算裁剪区域（确保不超出图片边界）
        left = max(0, x - padding_x)
        top = max(0, y - padding_y)
        right = min(image_size[0], x + width + padding_x)
        bottom = min(image_size[1], y + height + padding_y)
        
        return (left, top, right, bottom)
    
    def _create_thumbnail(self, face_img: Image.Image) -> Image.Image:
        """
        创建固定尺寸的缩略图（保持宽高比）
        
        Args:
            face_img: 裁剪后的人像图片
            
        Returns:
            缩略图图片对象
        """
        # 使用 ImageOps.fit 进行居中裁剪
        # 这会保持宽高比并填充整个目标尺寸
        thumbnail = ImageOps.fit(
            face_img,
            self.THUMBNAIL_SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5)
        )
        
        return thumbnail
    
    def _create_placeholder(self, output_filename: str) -> Optional[str]:
        """
        创建默认占位图
        
        Args:
            output_filename: 输出文件名
            
        Returns:
            占位图路径，失败返回 None
        """
        try:
            # 创建灰色占位图
            placeholder = Image.new('RGB', self.THUMBNAIL_SIZE, color=(200, 200, 200))
            
            output_path = os.path.join(self.thumbnail_dir, output_filename)
            placeholder.save(
                output_path,
                format=self.THUMBNAIL_FORMAT,
                quality=self.THUMBNAIL_QUALITY
            )
            
            logger.info(f"占位图已创建: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"创建占位图失败: {str(e)}")
            return None
    
    def delete_thumbnail(self, thumbnail_path: str) -> bool:
        """
        删除缩略图文件
        
        Args:
            thumbnail_path: 缩略图路径
            
        Returns:
            删除成功返回 True
        """
        try:
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                logger.info(f"缩略图已删除: {thumbnail_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除缩略图失败: {str(e)}")
            return False
    
    def clearThumbnails(self) -> int:
        """
        清除所有缩略图文件
        
        Returns:
            清除的文件数量
        """
        try:
            count = 0
            if os.path.exists(self.thumbnail_dir):
                for filename in os.listdir(self.thumbnail_dir):
                    file_path = os.path.join(self.thumbnail_dir, filename)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            count += 1
                        except Exception as e:
                            logger.warning(f"无法删除缩略图 {file_path}: {str(e)}")
            logger.info(f"已清除 {count} 个缩略图")
            return count
        except Exception as e:
            logger.error(f"清除缩略图失败: {str(e)}")
            return 0
