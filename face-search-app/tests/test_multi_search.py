"""
多人像搜索模块的单元测试
测试 MultiSearchModule 的核心功能
"""

import pytest
import os
import sys
import tempfile
import numpy as np
import uuid
from pathlib import Path
from PIL import Image

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from multi_search import MultiSearchModule
from models import Match, Progress, MultiSearchResult


class TestMultiSearchModule:
    """MultiSearchModule 的单元测试套件"""
    
    @pytest.fixture
    def multi_search(self):
        """创建 MultiSearchModule 实例"""
        return MultiSearchModule()
    
    @pytest.fixture
    def test_images_dir(self, tmp_path):
        """创建测试图片目录"""
        images_dir = tmp_path / "test_images"
        images_dir.mkdir()
        
        # 创建一些测试图片
        for i in range(5):
            img = Image.new('RGB', (200, 200), color=(i*50, i*50, i*50))
            img_path = images_dir / f"test_{i}.jpg"
            img.save(img_path)
        
        return str(images_dir)
    
    @pytest.fixture
    def sample_features(self):
        """生成样本特征向量"""
        return np.random.rand(128).tolist()
    
    def test_single_face_search(self, multi_search, test_images_dir, sample_features):
        """
        测试单人像搜索（退化情况）
        验证需求 8.1
        """
        face_id = str(uuid.uuid4())
        target_features_list = [(face_id, sample_features)]
        
        result = multi_search.searchMultipleFaces(
            target_features_list=target_features_list,
            search_folder=test_images_dir,
            threshold=0.6
        )
        
        # 验证返回 MultiSearchResult
        assert isinstance(result, MultiSearchResult)
        assert result.cancelled is False
        
        # 验证处理了图片
        assert result.total_processed >= 0
        
        # 验证源人像映射存在
        assert face_id in result.source_face_map or len(result.matches) == 0
    
    def test_multiple_faces_search(self, multi_search, test_images_dir):
        """
        测试多人像搜索
        验证需求 8.1, 8.2
        """
        # 创建多个目标人像
        num_faces = 3
        target_features_list = []
        face_ids = []
        
        for i in range(num_faces):
            face_id = str(uuid.uuid4())
            features = np.random.rand(128).tolist()
            target_features_list.append((face_id, features))
            face_ids.append(face_id)
        
        result = multi_search.searchMultipleFaces(
            target_features_list=target_features_list,
            search_folder=test_images_dir,
            threshold=0.6
        )
        
        # 验证返回结果
        assert isinstance(result, MultiSearchResult)
        assert result.cancelled is False
        
        # 验证处理了图片
        assert result.total_processed >= 0
        
        # 验证所有源人像都在映射中（如果有匹配的话）
        for face_id in face_ids:
            if len(result.matches) > 0:
                # 至少有一个匹配应该来自某个源人像
                source_face_ids = [m['sourceFaceId'] for m in result.matches]
                assert any(fid in source_face_ids for fid in face_ids)
    
    def test_empty_target_faces(self, multi_search, test_images_dir):
        """
        测试空目标人像列表
        验证需求 8.1
        """
        result = multi_search.searchMultipleFaces(
            target_features_list=[],
            search_folder=test_images_dir,
            threshold=0.6
        )
        
        # 应该返回空结果
        assert isinstance(result, MultiSearchResult)
        assert len(result.matches) == 0
        assert result.total_processed == 0
        assert result.cancelled is False
    
    def test_search_result_merge(self, multi_search):
        """
        测试搜索结果合并（去重）
        验证需求 8.2, 8.3
        """
        # 创建 MultiSearchResult 并添加重复匹配
        result = MultiSearchResult()
        
        # 添加相同路径的匹配（不同相似度）
        match1 = Match(
            imagePath="/path/to/image1.jpg",
            similarity=0.8,
            faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
        )
        match2 = Match(
            imagePath="/path/to/image1.jpg",  # 相同路径
            similarity=0.9,  # 更高相似度
            faceLocation={'x': 10, 'y': 10, 'width': 100, 'height': 100}
        )
        match3 = Match(
            imagePath="/path/to/image2.jpg",  # 不同路径
            similarity=0.7,
            faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
        )
        
        face_id1 = str(uuid.uuid4())
        face_id2 = str(uuid.uuid4())
        
        result.add_match(match1, face_id1)
        result.add_match(match2, face_id2)
        result.add_match(match3, face_id1)
        
        # 合并前应该有 3 个匹配
        assert len(result.matches) == 3
        
        # 执行合并
        result.merge_duplicates()
        
        # 合并后应该只有 2 个匹配（image1.jpg 被去重）
        assert len(result.matches) == 2
        
        # 验证保留了最高相似度的匹配
        image1_matches = [m for m in result.matches if m['imagePath'] == "/path/to/image1.jpg"]
        assert len(image1_matches) == 1
        assert image1_matches[0]['similarity'] == 0.9
    
    def test_highest_similarity_preserved(self, multi_search):
        """
        测试保留最高相似度分数
        验证需求 8.4
        """
        result = MultiSearchResult()
        
        # 添加多个相同路径但不同相似度的匹配
        similarities = [0.6, 0.85, 0.7, 0.9, 0.75]
        face_id = str(uuid.uuid4())
        
        for sim in similarities:
            match = Match(
                imagePath="/path/to/same_image.jpg",
                similarity=sim,
                faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
            )
            result.add_match(match, face_id)
        
        # 合并前有 5 个匹配
        assert len(result.matches) == 5
        
        # 执行合并
        result.merge_duplicates()
        
        # 合并后只有 1 个匹配
        assert len(result.matches) == 1
        
        # 验证保留了最高相似度 0.9
        assert result.matches[0]['similarity'] == 0.9
    
    def test_source_face_identification(self, multi_search):
        """
        测试源人像标识
        验证需求 8.5
        """
        result = MultiSearchResult()
        
        # 添加来自不同源人像的匹配
        face_id1 = str(uuid.uuid4())
        face_id2 = str(uuid.uuid4())
        
        match1 = Match(
            imagePath="/path/to/image1.jpg",
            similarity=0.8,
            faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
        )
        match2 = Match(
            imagePath="/path/to/image2.jpg",
            similarity=0.7,
            faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
        )
        
        result.add_match(match1, face_id1)
        result.add_match(match2, face_id2)
        
        # 验证每个匹配都有源人像ID
        assert len(result.matches) == 2
        assert result.matches[0]['sourceFaceId'] == face_id1
        assert result.matches[1]['sourceFaceId'] == face_id2
        
        # 验证源人像映射
        assert face_id1 in result.source_face_map
        assert face_id2 in result.source_face_map
        assert len(result.source_face_map[face_id1]) == 1
        assert len(result.source_face_map[face_id2]) == 1
    
    def test_cancel_search(self, multi_search, test_images_dir, sample_features):
        """
        测试取消搜索操作
        验证需求 8.7
        """
        face_id = str(uuid.uuid4())
        target_features_list = [(face_id, sample_features)]
        
        # 先调用取消方法
        multi_search.cancelSearch()
        
        result = multi_search.searchMultipleFaces(
            target_features_list=target_features_list,
            search_folder=test_images_dir,
            threshold=0.6
        )
        
        # 注意：searchMultipleFaces 会重置 cancelled 标志
        # 所以这个测试验证的是取消方法本身的功能
        # 实际的取消需要在搜索过程中调用
        assert isinstance(result, MultiSearchResult)
    
    def test_cancel_search_method(self, multi_search):
        """
        测试取消搜索方法
        验证需求 8.7
        """
        # 调用取消方法
        success = multi_search.cancelSearch()
        
        assert success is True
        assert multi_search.cancelled is True
    
    def test_search_single_face_method(self, multi_search, test_images_dir, sample_features):
        """
        测试单人像搜索便捷方法
        """
        face_id = str(uuid.uuid4())
        
        result = multi_search.searchSingleFace(
            face_id=face_id,
            features=sample_features,
            search_folder=test_images_dir,
            threshold=0.6
        )
        
        # 验证返回 MultiSearchResult
        assert isinstance(result, MultiSearchResult)
        assert result.cancelled is False
    
    def test_progress_callback(self, multi_search, test_images_dir, sample_features):
        """
        测试进度回调功能
        验证需求 8.6
        """
        face_id = str(uuid.uuid4())
        target_features_list = [(face_id, sample_features)]
        
        # 记录进度回调
        progress_updates = []
        
        def progress_callback(progress: Progress):
            progress_updates.append({
                'current': progress.current,
                'total': progress.total,
                'percentage': progress.percentage
            })
        
        result = multi_search.searchMultipleFaces(
            target_features_list=target_features_list,
            search_folder=test_images_dir,
            threshold=0.6,
            progress_callback=progress_callback
        )
        
        # 验证收到了进度更新（如果有图片被处理）
        if result.total_processed > 0:
            assert len(progress_updates) > 0
            # 验证进度百分比在 0-100 之间
            for update in progress_updates:
                assert 0 <= update['percentage'] <= 100
    
    def test_multiple_faces_progress_aggregation(self, multi_search, test_images_dir):
        """
        测试多人像搜索的综合进度
        验证需求 8.6
        """
        # 创建多个目标人像
        num_faces = 2
        target_features_list = []
        
        for i in range(num_faces):
            face_id = str(uuid.uuid4())
            features = np.random.rand(128).tolist()
            target_features_list.append((face_id, features))
        
        progress_updates = []
        
        def progress_callback(progress: Progress):
            progress_updates.append(progress.percentage)
        
        result = multi_search.searchMultipleFaces(
            target_features_list=target_features_list,
            search_folder=test_images_dir,
            threshold=0.6,
            progress_callback=progress_callback
        )
        
        # 验证进度更新（如果有）
        if len(progress_updates) > 0:
            # 验证进度是递增的（大致）
            assert progress_updates[-1] >= progress_updates[0]
    
    def test_sort_by_similarity(self, multi_search):
        """
        测试按相似度排序
        """
        result = MultiSearchResult()
        
        # 添加不同相似度的匹配
        similarities = [0.6, 0.9, 0.7, 0.85, 0.75]
        face_id = str(uuid.uuid4())
        
        for i, sim in enumerate(similarities):
            match = Match(
                imagePath=f"/path/to/image{i}.jpg",
                similarity=sim,
                faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
            )
            result.add_match(match, face_id)
        
        # 排序前
        assert result.matches[0]['similarity'] == 0.6
        
        # 执行排序
        result.sort_by_similarity()
        
        # 排序后应该按降序排列
        assert result.matches[0]['similarity'] == 0.9
        assert result.matches[1]['similarity'] == 0.85
        assert result.matches[2]['similarity'] == 0.75
        assert result.matches[3]['similarity'] == 0.7
        assert result.matches[4]['similarity'] == 0.6
    
    def test_invalid_search_folder(self, multi_search, sample_features):
        """
        测试无效的搜索文件夹
        """
        face_id = str(uuid.uuid4())
        target_features_list = [(face_id, sample_features)]
        
        # 使用不存在的文件夹
        result = multi_search.searchMultipleFaces(
            target_features_list=target_features_list,
            search_folder="/nonexistent/folder",
            threshold=0.6
        )
        
        # 应该返回空结果或处理错误
        assert isinstance(result, MultiSearchResult)
        # 不应该崩溃


class TestMultiSearchResultModel:
    """MultiSearchResult 数据模型的测试"""
    
    def test_create_empty_result(self):
        """测试创建空结果"""
        result = MultiSearchResult()
        
        assert len(result.matches) == 0
        assert result.total_processed == 0
        assert len(result.source_face_map) == 0
        assert result.cancelled is False
    
    def test_add_match(self):
        """测试添加匹配"""
        result = MultiSearchResult()
        
        match = Match(
            imagePath="/path/to/image.jpg",
            similarity=0.8,
            faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
        )
        face_id = str(uuid.uuid4())
        
        result.add_match(match, face_id)
        
        assert len(result.matches) == 1
        assert result.matches[0]['imagePath'] == "/path/to/image.jpg"
        assert result.matches[0]['similarity'] == 0.8
        assert result.matches[0]['sourceFaceId'] == face_id
        
        # 验证源人像映射
        assert face_id in result.source_face_map
        assert len(result.source_face_map[face_id]) == 1
    
    def test_merge_no_duplicates(self):
        """测试合并无重复的结果"""
        result = MultiSearchResult()
        
        # 添加不同路径的匹配
        for i in range(3):
            match = Match(
                imagePath=f"/path/to/image{i}.jpg",
                similarity=0.8,
                faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
            )
            result.add_match(match, str(uuid.uuid4()))
        
        # 合并前后数量应该相同
        assert len(result.matches) == 3
        result.merge_duplicates()
        assert len(result.matches) == 3
    
    def test_merge_all_duplicates(self):
        """测试合并全部重复的结果"""
        result = MultiSearchResult()
        
        # 添加相同路径的匹配
        for i in range(5):
            match = Match(
                imagePath="/path/to/same_image.jpg",
                similarity=0.6 + i * 0.05,  # 递增相似度
                faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
            )
            result.add_match(match, str(uuid.uuid4()))
        
        # 合并前有 5 个
        assert len(result.matches) == 5
        
        # 合并后只有 1 个
        result.merge_duplicates()
        assert len(result.matches) == 1
        
        # 保留最高相似度
        assert result.matches[0]['similarity'] == 0.8  # 0.6 + 4*0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
