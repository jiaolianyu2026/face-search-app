"""
Image Export Module for copying matched images to a target directory.
Handles file copying with metadata preservation, conflict resolution, and progress tracking.
"""

import os
import shutil
from typing import List, Optional, Callable
from models import ExportResult, Progress
from logger import get_logger

# 初始化日志记录器
logger = get_logger('image_export')


class ImageExportModule:
    """
    Module for exporting (copying) images to a target directory.
    
    Features:
    - Copies files with metadata preservation using shutil.copy2()
    - Detects filename conflicts and auto-renames with numeric suffixes
    - Supports progress callbacks for long operations
    - Collects success/failure statistics
    - Handles errors gracefully (logs and continues)
    """
    
    def __init__(self):
        """Initialize the ImageExportModule."""
        pass
    
    def exportImages(
        self,
        imagePaths: List[str],
        targetFolder: str,
        progressCallback: Optional[Callable[[Progress], None]] = None
    ) -> ExportResult:
        """
        Export (copy) images to a target directory.
        
        Args:
            imagePaths: List of source image file paths to export
            targetFolder: Destination folder path
            progressCallback: Optional callback for progress updates
            
        Returns:
            ExportResult containing success count, failed count, and error details
            
        Requirements:
            - Copies files preserving metadata (Requirement 8.4)
            - Auto-renames on filename conflicts (Requirement 8.5)
            - Reports success/failure statistics (Requirement 8.6)
            - Handles errors gracefully (Requirement 8.7)
        """
        # Validate target folder exists
        if not os.path.exists(targetFolder):
            logger.error(f"目标文件夹不存在: {targetFolder}")
            return ExportResult(
                successCount=0,
                failedCount=len(imagePaths),
                errors=[{
                    'path': targetFolder,
                    'error': 'Target folder does not exist'
                }]
            )
        
        # Validate target folder is writable
        if not os.access(targetFolder, os.W_OK):
            logger.error(f"目标文件夹不可写: {targetFolder}")
            return ExportResult(
                successCount=0,
                failedCount=len(imagePaths),
                errors=[{
                    'path': targetFolder,
                    'error': 'Target folder is not writable'
                }]
            )
        
        logger.info(f"开始转存图片: {len(imagePaths)} 个文件到 {targetFolder}")
        
        # Initialize counters and error list
        success_count = 0
        failed_count = 0
        errors = []
        total_images = len(imagePaths)
        
        # Process each image
        for index, source_path in enumerate(imagePaths):
            # Update progress
            if progressCallback:
                progress = Progress(
                    current=index,
                    total=total_images,
                    currentFile=source_path
                )
                progressCallback(progress)
            
            try:
                # Validate source file exists
                if not os.path.exists(source_path):
                    logger.warning(f"源文件不存在: {source_path}")
                    failed_count += 1
                    errors.append({
                        'path': source_path,
                        'error': 'Source file does not exist'
                    })
                    continue
                
                # Get filename from source path
                filename = os.path.basename(source_path)
                
                # Resolve filename conflicts
                target_path = self._resolveConflict(targetFolder, filename)
                
                # Copy file with metadata preservation (Requirement 8.4)
                shutil.copy2(source_path, target_path)
                
                logger.debug(f"成功转存: {source_path} -> {target_path}")
                success_count += 1
                
            except PermissionError as e:
                # Handle permission errors
                logger.warning(f"权限错误: {source_path}, 错误: {str(e)}")
                failed_count += 1
                errors.append({
                    'path': source_path,
                    'error': f'Permission denied: {str(e)}'
                })
            except IOError as e:
                # Handle I/O errors (disk full, etc.)
                logger.warning(f"I/O错误: {source_path}, 错误: {str(e)}")
                failed_count += 1
                errors.append({
                    'path': source_path,
                    'error': f'I/O error: {str(e)}'
                })
            except Exception as e:
                # Handle any other errors
                logger.error(f"转存失败: {source_path}, 错误: {str(e)}", exc_info=True)
                failed_count += 1
                errors.append({
                    'path': source_path,
                    'error': f'Unexpected error: {str(e)}'
                })
        
        # Final progress update
        if progressCallback:
            progress = Progress(
                current=total_images,
                total=total_images,
                currentFile=None
            )
            progressCallback(progress)
        
        logger.info(f"转存完成: 成功 {success_count}, 失败 {failed_count}")
        
        # Return export result
        return ExportResult(
            successCount=success_count,
            failedCount=failed_count,
            errors=errors
        )
    
    def _resolveConflict(self, target_folder: str, filename: str) -> str:
        """
        Resolve filename conflicts by adding numeric suffixes.
        
        Args:
            target_folder: Destination folder path
            filename: Original filename
            
        Returns:
            Full path to target file (possibly with numeric suffix)
            
        Example:
            If 'photo.jpg' exists, returns path to 'photo_1.jpg'
            If 'photo_1.jpg' also exists, returns path to 'photo_2.jpg'
        """
        # Build initial target path
        target_path = os.path.join(target_folder, filename)
        
        # If no conflict, return as-is
        if not os.path.exists(target_path):
            return target_path
        
        # Split filename into name and extension
        name, ext = os.path.splitext(filename)
        
        # Try adding numeric suffixes until we find an available name
        counter = 1
        while True:
            new_filename = f"{name}_{counter}{ext}"
            target_path = os.path.join(target_folder, new_filename)
            
            if not os.path.exists(target_path):
                return target_path
            
            counter += 1
            
            # Safety check to prevent infinite loop
            if counter > 10000:
                raise RuntimeError(f"Could not resolve filename conflict for {filename}")
