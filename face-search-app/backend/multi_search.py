"""
多人像搜索模块
支持同时搜索多个目标人像
"""

import logging
from typing import List, Dict, Optional, Callable
from models import Match, Progress, MultiSearchResult
from face_search import FaceSearchModule

# 配置日志
logger = logging.getLogger(__name__)


class MultiSearchModule:
    """
    多人像搜索类
    对多个目标人像执行搜索并合并结果
    """
    
    def __init__(self):
        """初始化多人像搜索模块"""
        self.search_module = FaceSearchModule()
        self.cancelled = False
    
    def searchMultipleFaces(
        self,
        target_features_list: List[tuple[str, List[float]]],  # [(faceId, features)]
        search_folder: str,
        threshold: float = 0.6,
        progress_callback: Optional[Callable[[Progress], None]] = None
    ) -> MultiSearchResult:
        """
        搜索多个目标人像
        
        Args:
            target_features_list: 目标人像列表，每项为 (faceId, features) 元组
            search_folder: 搜索文件夹路径
            threshold: 相似度阈值
            progress_callback: 进度回调函数
            
        Returns:
            MultiSearchResult 包含合并后的搜索结果
            
        需求:
            - 对每个人像执行独立搜索 (需求 8.1)
            - 合并所有搜索结果 (需求 8.2)
            - 去除重复的匹配图片 (需求 8.3)
            - 保留最高相似度分数 (需求 8.4)
            - 标识源人像 (需求 8.5)
            - 综合进度显示 (需求 8.6)
            - 支持取消操作 (需求 8.7)
        """
        # 重置取消标志
        self.cancelled = False
        
        num_faces = len(target_features_list)
        logger.info(f"开始多人像搜索: {num_faces} 个目标人像, 文件夹={search_folder}")
        
        # 创建结果对象
        result = MultiSearchResult()
        
        # 如果没有目标人像，返回空结果
        if num_faces == 0:
            logger.warning("没有提供目标人像")
            return result
        
        # 对每个目标人像执行搜索
        for face_idx, (face_id, features) in enumerate(target_features_list):
            # 检查是否取消
            if self.cancelled:
                logger.info(f"搜索已取消，已完成 {face_idx}/{num_faces} 个人像")
                result.cancelled = True
                break
            
            logger.info(f"搜索人像 {face_idx + 1}/{num_faces}: {face_id}")
            
            # 创建进度回调包装器（综合多个人像的进度）
            # 使用默认参数捕获当前的 face_idx 值，避免闭包问题
            def wrapped_progress_callback(progress: Progress, current_face_idx=face_idx):
                if progress_callback:
                    try:
                        # 计算综合进度
                        # 每个人像占总进度的 1/num_faces
                        base_progress = current_face_idx / num_faces
                        face_progress = (progress.current / progress.total if progress.total > 0 else 0) / num_faces
                        total_progress_ratio = base_progress + face_progress
                        
                        # 创建综合进度对象
                        # 使用虚拟的 current/total 来表示综合进度
                        virtual_total = 1000  # 使用较大的数字以提高精度
                        virtual_current = int(total_progress_ratio * virtual_total)
                        
                        combined_progress = Progress(
                            current=virtual_current,
                            total=virtual_total,
                            currentFile=progress.currentFile
                        )
                        progress_callback(combined_progress)
                    except Exception as e:
                        logger.error(f"进度回调发生错误: {str(e)}", exc_info=True)
            
            # 执行单个人像搜索
            try:
                search_result = self.search_module.searchFaces(
                    targetFeatures=features,
                    searchFolder=search_folder,
                    threshold=threshold,
                    progressCallback=wrapped_progress_callback
                )
                
                # 更新处理总数（使用最大值）
                result.total_processed = max(
                    result.total_processed,
                    search_result.totalProcessed
                )
                
                # 添加匹配结果（标记源人像ID）
                for match in search_result.matches:
                    result.add_match(match, face_id)
                
                logger.info(
                    f"人像 {face_id} 搜索完成: "
                    f"找到 {len(search_result.matches)} 个匹配"
                )
                
            except Exception as e:
                logger.error(f"搜索人像 {face_id} 时发生错误: {str(e)}")
                continue
        
        # 合并重复的图片路径（保留最高相似度）
        logger.info(f"合并前: {len(result.matches)} 个匹配结果")
        result.merge_duplicates()
        logger.info(f"合并后: {len(result.matches)} 个匹配结果")
        
        # 按相似度降序排序
        result.sort_by_similarity()
        
        logger.info(
            f"多人像搜索完成: "
            f"处理 {result.total_processed} 个文件, "
            f"找到 {len(result.matches)} 个唯一匹配"
        )
        
        return result
    
    def cancelSearch(self) -> bool:
        """
        取消当前搜索操作
        
        Returns:
            取消成功返回 True
        """
        logger.info("收到取消多人像搜索请求")
        self.cancelled = True
        # 同时取消底层的单人像搜索
        self.search_module.cancelSearch()
        return True
    
    def searchSingleFace(
        self,
        face_id: str,
        features: List[float],
        search_folder: str,
        threshold: float = 0.6,
        progress_callback: Optional[Callable[[Progress], None]] = None
    ) -> MultiSearchResult:
        """
        搜索单个人像（退化情况）
        
        Args:
            face_id: 人像ID
            features: 特征向量
            search_folder: 搜索文件夹
            threshold: 相似度阈值
            progress_callback: 进度回调
            
        Returns:
            MultiSearchResult 格式的搜索结果
        """
        logger.info(f"单人像搜索模式: {face_id}")
        
        # 调用多人像搜索（只有一个人像）
        return self.searchMultipleFaces(
            target_features_list=[(face_id, features)],
            search_folder=search_folder,
            threshold=threshold,
            progress_callback=progress_callback
        )
