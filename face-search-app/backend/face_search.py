"""
Face Search Module for searching faces in a folder.
Integrates file scanning, face detection, caching, and similarity computation.
Supports parallel processing for improved performance.
"""

import os
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Match, SearchResult, Progress
from file_scanner import FileSystemScannerModule
from face_detection import FaceDetectionModule
from cache_module import CacheModule
from similarity import SimilarityModule
from logger import get_logger
from config import MAX_WORKER_THREADS, ENABLE_PARALLEL_PROCESSING, BATCH_SIZE

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
        self.enable_parallel = ENABLE_PARALLEL_PROCESSING
        self.max_workers = MAX_WORKER_THREADS
    
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
            - Parallel processing for performance (Requirement 9.2)
            - Batch processing for large folders (Requirement 9.3)
        """
        # Reset cancelled flag
        self.cancelled = False
        
        logger.info(f"开始搜索人脸: 文件夹={searchFolder}, 阈值={threshold}, 并行处理={self.enable_parallel}")
        
        # Step 1: Scan folder for images
        scan_result = self.scanner.scanFolder(searchFolder)
        
        if scan_result.error:
            logger.error(f"扫描文件夹失败: {searchFolder}, 错误: {scan_result.error}")
            # Return empty result if scan failed
            return SearchResult(matches=[], totalProcessed=0, cancelled=False)
        
        image_paths = scan_result.imagePaths
        total_images = len(image_paths)
        
        logger.info(f"扫描完成，找到 {total_images} 个图片文件")
        
        # Choose processing method based on configuration and folder size
        if self.enable_parallel and total_images > 10:
            logger.info(f"使用并行处理模式，工作线程数: {self.max_workers}")
            return self._searchFacesParallel(
                targetFeatures, image_paths, threshold, progressCallback
            )
        else:
            logger.info("使用串行处理模式")
            return self._searchFacesSequential(
                targetFeatures, image_paths, threshold, progressCallback
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
    
    def _processImage(
        self,
        image_path: str,
        targetFeatures: List[float],
        threshold: float
    ) -> tuple[List[Match], bool]:
        """
        Process a single image: detect faces and find matches.
        
        Args:
            image_path: Path to image file
            targetFeatures: Target face features to match
            threshold: Similarity threshold
            
        Returns:
            Tuple of (matches_list, success_flag)
        """
        matches = []
        
        try:
            # Try to get cached features
            cache_entry = self.cache.getCachedFeatures(image_path)
            
            if cache_entry:
                faces = cache_entry.features
                logger.debug(f"使用缓存的人脸特征: {image_path}")
            else:
                # Detect faces in image
                detection_result = self.detector.detectFaces(image_path)
                
                if detection_result.error:
                    logger.debug(f"跳过文件（检测失败）: {image_path}")
                    return matches, False
                
                faces = detection_result.faces
                
                # Cache the detected features
                self.cache.setCachedFeatures(image_path, faces)
            
            # Compare each detected face with target
            for face in faces:
                try:
                    similarity_score = self.similarity.computeSimilarity(
                        targetFeatures,
                        face.features
                    )
                    
                    if similarity_score >= threshold:
                        match = Match(
                            imagePath=image_path,
                            similarity=similarity_score,
                            faceLocation=face.boundingBox
                        )
                        matches.append(match)
                
                except Exception:
                    continue
            
            return matches, True
            
        except Exception as e:
            logger.warning(f"跳过文件（异常）: {image_path}, 错误: {str(e)}")
            return matches, False
    
    def _searchFacesSequential(
        self,
        targetFeatures: List[float],
        image_paths: List[str],
        threshold: float,
        progressCallback: Optional[Callable[[Progress], None]]
    ) -> SearchResult:
        """
        Sequential (single-threaded) face search implementation.
        
        Args:
            targetFeatures: Target face features
            image_paths: List of image paths to process
            threshold: Similarity threshold
            progressCallback: Progress callback function
            
        Returns:
            SearchResult with matches and statistics
        """
        matches = []
        processed_count = 0
        skipped_count = 0
        total_images = len(image_paths)
        
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
            
            # Process image
            image_matches, success = self._processImage(image_path, targetFeatures, threshold)
            matches.extend(image_matches)
            
            processed_count += 1
            if not success:
                skipped_count += 1
        
        # Final progress update
        if progressCallback:
            progress = Progress(
                current=processed_count,
                total=total_images,
                currentFile=None
            )
            progressCallback(progress)
        
        # Sort matches by similarity descending
        matches.sort(key=lambda m: m.similarity, reverse=True)
        
        logger.info(
            f"串行搜索完成: 处理 {processed_count} 个文件, "
            f"跳过 {skipped_count} 个文件, "
            f"找到 {len(matches)} 个匹配结果"
        )
        
        return SearchResult(
            matches=matches,
            totalProcessed=processed_count,
            cancelled=self.cancelled
        )
    
    def _searchFacesParallel(
        self,
        targetFeatures: List[float],
        image_paths: List[str],
        threshold: float,
        progressCallback: Optional[Callable[[Progress], None]]
    ) -> SearchResult:
        """
        Parallel (multi-threaded) face search implementation with batch processing.
        
        Args:
            targetFeatures: Target face features
            image_paths: List of image paths to process
            threshold: Similarity threshold
            progressCallback: Progress callback function
            
        Returns:
            SearchResult with matches and statistics
            
        Requirements:
            - Parallel processing (Requirement 9.2)
            - Batch processing for large folders (Requirement 9.3)
        """
        matches = []
        processed_count = 0
        skipped_count = 0
        total_images = len(image_paths)
        
        # Process images in batches to avoid memory issues
        batch_size = BATCH_SIZE
        num_batches = (total_images + batch_size - 1) // batch_size
        
        logger.info(f"使用批处理: {num_batches} 批，每批 {batch_size} 个文件")
        
        for batch_idx in range(num_batches):
            # Check if search was cancelled
            if self.cancelled:
                logger.info(f"搜索已取消，已处理 {processed_count}/{total_images} 个文件")
                break
            
            # Get current batch
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_images)
            batch_paths = image_paths[start_idx:end_idx]
            
            logger.debug(f"处理批次 {batch_idx + 1}/{num_batches}: {len(batch_paths)} 个文件")
            
            # Process batch in parallel using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_path = {
                    executor.submit(self._processImage, path, targetFeatures, threshold): path
                    for path in batch_paths
                }
                
                # Process completed tasks
                for future in as_completed(future_to_path):
                    # Check if search was cancelled
                    if self.cancelled:
                        # Cancel remaining futures
                        for f in future_to_path:
                            f.cancel()
                        break
                    
                    image_path = future_to_path[future]
                    
                    try:
                        image_matches, success = future.result()
                        matches.extend(image_matches)
                        
                        if not success:
                            skipped_count += 1
                    
                    except Exception as e:
                        logger.warning(f"处理文件时发生异常: {image_path}, 错误: {str(e)}")
                        skipped_count += 1
                    
                    processed_count += 1
                    
                    # Update progress
                    if progressCallback:
                        progress = Progress(
                            current=processed_count,
                            total=total_images,
                            currentFile=image_path
                        )
                        progressCallback(progress)
        
        # Final progress update
        if progressCallback:
            progress = Progress(
                current=processed_count,
                total=total_images,
                currentFile=None
            )
            progressCallback(progress)
        
        # Sort matches by similarity descending
        matches.sort(key=lambda m: m.similarity, reverse=True)
        
        logger.info(
            f"并行搜索完成: 处理 {processed_count} 个文件, "
            f"跳过 {skipped_count} 个文件, "
            f"找到 {len(matches)} 个匹配结果"
        )
        
        return SearchResult(
            matches=matches,
            totalProcessed=processed_count,
            cancelled=self.cancelled
        )
