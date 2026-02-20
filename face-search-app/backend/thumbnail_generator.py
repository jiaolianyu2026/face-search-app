"""
Thumbnail Generator Module for creating image thumbnails.
Optimizes frontend loading by generating smaller preview images.
"""

import os
from PIL import Image
from typing import Optional
from logger import get_logger
from config import THUMBNAIL_SIZE, TEMP_UPLOAD_DIR

# 初始化日志记录器
logger = get_logger('thumbnail_generator')


class ThumbnailGenerator:
    """
    Module for generating image thumbnails.
    
    Provides functionality to create smaller preview images
    for faster loading in the frontend.
    """
    
    def __init__(self, thumbnail_dir: Optional[str] = None):
        """
        Initialize the ThumbnailGenerator.
        
        Args:
            thumbnail_dir: Directory to store thumbnails (default: temp_uploads/thumbnails)
        """
        if thumbnail_dir is None:
            self.thumbnail_dir = os.path.join(TEMP_UPLOAD_DIR, 'thumbnails')
        else:
            self.thumbnail_dir = thumbnail_dir
        
        # Create thumbnail directory if it doesn't exist
        os.makedirs(self.thumbnail_dir, exist_ok=True)
        
        logger.info(f"缩略图生成器初始化，目录: {self.thumbnail_dir}")
    
    def generateThumbnail(
        self,
        image_path: str,
        size: tuple = THUMBNAIL_SIZE,
        quality: int = 85
    ) -> Optional[str]:
        """
        Generate a thumbnail for an image.
        
        Args:
            image_path: Path to the original image
            size: Thumbnail size as (width, height) tuple
            quality: JPEG quality (1-100)
            
        Returns:
            Path to the generated thumbnail, or None if generation failed
            
        Requirements:
            - Generate thumbnails for faster loading (Requirement 9.5)
        """
        try:
            # Check if image exists
            if not os.path.exists(image_path):
                logger.warning(f"图片不存在: {image_path}")
                return None
            
            # Generate thumbnail filename
            image_filename = os.path.basename(image_path)
            image_name, image_ext = os.path.splitext(image_filename)
            thumbnail_filename = f"{image_name}_thumb{image_ext}"
            thumbnail_path = os.path.join(self.thumbnail_dir, thumbnail_filename)
            
            # Check if thumbnail already exists
            if os.path.exists(thumbnail_path):
                # Check if thumbnail is newer than original
                if os.path.getmtime(thumbnail_path) >= os.path.getmtime(image_path):
                    logger.debug(f"使用现有缩略图: {thumbnail_path}")
                    return thumbnail_path
            
            # Open and resize image
            with Image.open(image_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # Create thumbnail (maintains aspect ratio)
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
            
            logger.debug(f"生成缩略图: {image_path} -> {thumbnail_path}")
            return thumbnail_path
        
        except Exception as e:
            logger.error(f"生成缩略图失败: {image_path}, 错误: {str(e)}")
            return None
    
    def getThumbnailPath(self, image_path: str) -> Optional[str]:
        """
        Get the path to a thumbnail if it exists.
        
        Args:
            image_path: Path to the original image
            
        Returns:
            Path to the thumbnail if it exists, None otherwise
        """
        image_filename = os.path.basename(image_path)
        image_name, image_ext = os.path.splitext(image_filename)
        thumbnail_filename = f"{image_name}_thumb{image_ext}"
        thumbnail_path = os.path.join(self.thumbnail_dir, thumbnail_filename)
        
        if os.path.exists(thumbnail_path):
            return thumbnail_path
        return None
    
    def clearThumbnails(self) -> int:
        """
        Clear all generated thumbnails.
        
        Returns:
            Number of thumbnails deleted
        """
        count = 0
        try:
            for filename in os.listdir(self.thumbnail_dir):
                file_path = os.path.join(self.thumbnail_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    count += 1
            
            logger.info(f"清除了 {count} 个缩略图")
            return count
        
        except Exception as e:
            logger.error(f"清除缩略图失败: {str(e)}")
            return count
