"""
Face Search Module for searching faces in a folder.
Integrates file scanning, face detection, caching, and similarity computation.
"""

import os
from typing import List, Optional, Callable
from models import Match, SearchResult, Progress
from file_scanner import FileSystemScannerModule
from face_detection import FaceDetectionModule
from cache_module import CacheModule
from similarity import SimilarityModule
from logger import get_logger

# 初始化日志记录器
logger = get_logger('face_search')


class FaceSearchModule:
    """
    Module for searching faces in a folder.
    
    Integrates multiple modules to:
    - Scan folders for images
    - Detect faces in images (with caching)
    - Compare faces using similarity computation
    - Track progress and support cancellation
    """
    
    def __init__(self):
        """Initialize the FaceSearchModule with required sub-modules."""
        self.scanner = FileSystemScannerModule()
        self.detector = FaceDetectionModule()
        self.cache = CacheModule()
        self.similarity = SimilarityModule()
        self.cancelled = False
    
    def searchFaces(
        self,
        targetFeatures: List[float],
        searchFolder: str,
        threshold: float = 0.6,
        progressCallback: Optional[Callable[[Progress], None]] = None
    ) -> SearchResult:
        """
        Search for faces matching target features in a folder.
        
        Args:
            targetFeatures: 128-dimensional feature vector of target face
            searchFolder: Path to folder to search
            threshold: Similarity threshold (0-1), default 0.6
            progressCallback: Optional callback for progress updates
            
        Returns:
            SearchResult containing matches, total processed, and cancelled flag
            
        Requirements:
            - Scans folder recursively (Requirement 4.1)
            - Detects faces in all images (Requirement 4.2)
            - Skips unreadable files (Requirement 4.3)
            - Compares all faces with target (Requirement 4.4)
            - Filters by threshold (Requirement 4.5)
            - Sorts by similarity descending (Requirement 5.3)
            - Reports progress (Requirement 6.2, 6.3)
            - Supports cancellation (Requirement 6.4, 6.5)
        """
        # Reset cancelled flag
        self.cancelled = False
        
        logger.info(f"开始搜索人脸: 文件夹={searchFolder}, 阈值={threshold}")
        
        # Step 1: Scan folder for images
        scan_result = self.scanner.scanFolder(searchFolder)
        
        if scan_result.error:
            logger.error(f"扫描文件夹失败: {searchFolder}, 错误: {scan_result.error}")
            # Return empty result if scan failed
            return SearchResult(matches=[], totalProcessed=0, cancelled=False)
        
        image_paths = scan_result.imagePaths
        total_images = len(image_paths)
        
        logger.info(f"扫描完成，找到 {total_images} 个图片文件")
        
        # Initialize results
        matches = []
        processed_count = 0
        skipped_count = 0
        
        # Step 2: Process each image
        for image_path in image_paths:
            # Check if search was cancelled
            if self.cancelled:
                logger.info(f"搜索已取消，已处理 {processed_count}/{total_images} 个文件")
                break
            
            # Update progress
            if progressCallback:
                progress = Progress(
                    current=processed_count,
                    total=total_images,
                    currentFile=image_path
                )
                progressCallback(progress)
            
            # Step 3: Try to get cached features
            cache_entry = self.cache.getCachedFeatures(image_path)
            
            if cache_entry:
                # Use cached features
                faces = cache_entry.features
                logger.debug(f"使用缓存的人脸特征: {image_path}")
            else:
                # Step 4: Detect faces in image
                try:
                    detection_result = self.detector.detectFaces(image_path)
                    
                    if detection_result.error:
                        # Skip this file and continue (Requirement 4.3)
                        logger.debug(f"跳过文件（检测失败）: {image_path}")
                        processed_count += 1
                        skipped_count += 1
                        continue
                    
                    faces = detection_result.faces
                    
                    # Cache the detected features
                    self.cache.setCachedFeatures(image_path, faces)
                    
                except Exception as e:
                    # Skip files that cause errors (Requirement 4.3)
                    logger.warning(f"跳过文件（异常）: {image_path}, 错误: {str(e)}")
                    processed_count += 1
                    skipped_count += 1
                    continue
            
            # Step 5: Compare each detected face with target
            for face in faces:
                try:
                    # Compute similarity
                    similarity_score = self.similarity.computeSimilarity(
                        targetFeatures,
                        face.features
                    )
                    
                    # Step 6: Filter by threshold (Requirement 4.5)
                    if similarity_score >= threshold:
                        # Create match object
                        match = Match(
                            imagePath=image_path,
                            similarity=similarity_score,
                            faceLocation=face.boundingBox
                        )
                        matches.append(match)
                
                except Exception:
                    # Skip if similarity computation fails
                    continue
            
            processed_count += 1
        
        # Final progress update
        if progressCallback:
            progress = Progress(
                current=processed_count,
                total=total_images,
                currentFile=None
            )
            progressCallback(progress)
        
        # Step 7: Sort matches by similarity descending (Requirement 5.3)
        matches.sort(key=lambda m: m.similarity, reverse=True)
        
        logger.info(
            f"搜索完成: 处理 {processed_count} 个文件, "
            f"跳过 {skipped_count} 个文件, "
            f"找到 {len(matches)} 个匹配结果, "
            f"已取消: {self.cancelled}"
        )
        
        # Return search result
        return SearchResult(
            matches=matches,
            totalProcessed=processed_count,
            cancelled=self.cancelled
        )
    
    def cancelSearch(self) -> bool:
        """
        Cancel the current search operation.
        
        Returns:
            True if cancellation was successful
        """
        logger.info("收到取消搜索请求")
        self.cancelled = True
        return True
