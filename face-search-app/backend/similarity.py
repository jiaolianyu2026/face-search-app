"""
Similarity Module for computing similarity between face feature vectors.
Uses Euclidean distance to compare 128-dimensional face feature vectors,
consistent with the face_recognition library's design.

face_recognition 库使用 128 维欧氏距离编码：
- 欧氏距离 < 0.6 通常认为是同一个人（官方推荐阈值）
- 距离越小，相似度越高
- 本模块将欧氏距离转换为 [0, 1] 的相似度分数，方便与阈值比较
"""

import numpy as np
from typing import List


class SimilarityModule:
    """
    Module for computing similarity between face feature vectors.
    
    Uses Euclidean distance to measure how similar two face feature vectors are,
    consistent with the face_recognition library's encoding design.
    
    转换公式：similarity = 1 - (distance / max_distance)
    其中 max_distance = 1.0（经验值，face_recognition 编码的典型最大距离）
    
    这样：
    - 欧氏距离 0.0 → 相似度 1.0（完全相同）
    - 欧氏距离 0.6 → 相似度 0.4（官方阈值边界）
    - 欧氏距离 1.0 → 相似度 0.0（完全不同）
    
    注意：默认阈值应设为 0.4（对应欧氏距离 0.6），而不是 0.6。
    但为了向后兼容，保持阈值参数语义不变，在此模块内部处理转换。
    """
    
    # face_recognition 编码的典型最大欧氏距离
    # 超过此距离的人脸被认为完全不同
    MAX_DISTANCE = 1.0
    
    def __init__(self):
        """Initialize the SimilarityModule."""
        pass
    
    def computeSimilarity(self, features1: List[float], features2: List[float]) -> float:
        """
        Compute similarity between two face feature vectors using Euclidean distance.
        
        face_recognition 库的编码基于欧氏距离：距离越小，越相似。
        本方法将欧氏距离转换为相似度分数（0-1），距离越小，分数越高。
        
        转换公式：similarity = max(0, 1 - distance / MAX_DISTANCE)
        
        Args:
            features1: First 128-dimensional feature vector
            features2: Second 128-dimensional feature vector
            
        Returns:
            Similarity score between 0 and 1, where:
            - 1.0 means identical faces (distance = 0)
            - 0.4 means borderline match (distance ≈ 0.6, face_recognition 官方阈值)
            - 0.0 means completely different faces (distance >= 1.0)
            
        Raises:
            ValueError: If feature vectors have different lengths or are invalid
        """
        # 验证输入
        if len(features1) != len(features2):
            raise ValueError(
                f"Feature vectors must have the same length. "
                f"Got {len(features1)} and {len(features2)}"
            )
        
        if len(features1) == 0:
            raise ValueError("Feature vectors cannot be empty")
        
        # 转换为 numpy 数组
        v1 = np.array(features1, dtype=np.float64)
        v2 = np.array(features2, dtype=np.float64)
        
        # 计算欧氏距离
        distance = float(np.linalg.norm(v1 - v2))
        
        # 将距离转换为相似度分数 [0, 1]
        # distance=0 → similarity=1.0
        # distance=MAX_DISTANCE → similarity=0.0
        similarity = max(0.0, 1.0 - distance / self.MAX_DISTANCE)
        
        return similarity
    
    def computeDistance(self, features1: List[float], features2: List[float]) -> float:
        """
        直接计算两个特征向量的欧氏距离。
        
        Args:
            features1: 第一个 128 维特征向量
            features2: 第二个 128 维特征向量
            
        Returns:
            欧氏距离，值越小表示越相似
            face_recognition 官方推荐阈值：< 0.6 认为是同一个人
        """
        if len(features1) != len(features2):
            raise ValueError(
                f"Feature vectors must have the same length. "
                f"Got {len(features1)} and {len(features2)}"
            )
        
        v1 = np.array(features1, dtype=np.float64)
        v2 = np.array(features2, dtype=np.float64)
        
        return float(np.linalg.norm(v1 - v2))
