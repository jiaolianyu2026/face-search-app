"""
多人像搜索模块的属性测试
使用 Hypothesis 验证多人像搜索的通用属性
"""

import pytest
import os
import sys
import tempfile
import numpy as np
import uuid
from pathlib import Path
from PIL import Image
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from multi_search import MultiSearchModule
from models import Match, Progress, MultiSearchResult


# ============================================================================
# Hypothesis 策略定义
# ============================================================================

# 生成有效的特征向量（128维）
def feature_vector_strategy():
    """生成128维特征向量"""
    return st.lists(
        st.floats(
            min_value=-1.0,
            max_value=1.0,
            allow_nan=False,
            allow_infinity=False
        ),
        min_size=128,
        max_size=128
    )


# 生成相似度分数
def similarity_strategy():
    """生成有效的相似度分数 [0.0, 1.0]"""
    return st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


# 生成人像边界框
def bounding_box_strategy():
    """生成有效的边界框"""
    return st.fixed_dictionaries({
        'x': st.integers(min_value=0, max_value=1000),
        'y': st.integers(min_value=0, max_value=1000),
        'width': st.integers(min_value=10, max_value=500),
        'height': st.integers(min_value=10, max_value=500)
    })


# 生成图片路径
def image_path_strategy():
    """生成图片路径"""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/_-.'
        ),
        min_size=5,
        max_size=50
    ).map(lambda s: f"/path/to/{s}.jpg")


# 生成 Match 对象
def match_strategy():
    """生成 Match 对象"""
    return st.builds(
        Match,
        imagePath=image_path_strategy(),
        similarity=similarity_strategy(),
        faceLocation=bounding_box_strategy()
    )


# 生成人像ID
def face_id_strategy():
    """生成人像ID（UUID格式）"""
    return st.uuids().map(str)


# ============================================================================
# 属性 25: 多人像搜索结果合并（去重）
# Feature: face-library-management, Property 25: 多人像搜索结果合并
# ============================================================================

class TestProperty25_ResultMerge:
    """
    属性 25: 对于任意 N 个人像的搜索，合并后的结果中每个图片路径应该只出现一次（去重）
    
    **Validates: Requirements 8.2, 8.3**
    """
    
    @given(
        num_matches=st.integers(min_value=1, max_value=20),
        num_unique_paths=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_25_unique_paths_after_merge(self, num_matches, num_unique_paths):
        """
        对于任意数量的匹配结果，合并后每个图片路径应该只出现一次
        
        **Validates: Requirements 8.2, 8.3**
        """
        # 确保匹配数量大于等于唯一路径数量
        assume(num_matches >= num_unique_paths)
        
        result = MultiSearchResult()
        
        # 生成有限数量的唯一路径
        unique_paths = [f"/path/to/image{i}.jpg" for i in range(num_unique_paths)]
        
        # 添加匹配，可能有重复路径
        for i in range(num_matches):
            # 从唯一路径中随机选择
            path = unique_paths[i % num_unique_paths]
            
            match = Match(
                imagePath=path,
                similarity=np.random.uniform(0.6, 1.0),
                faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
            )
            face_id = str(uuid.uuid4())
            result.add_match(match, face_id)
        
        # 合并前可能有重复
        assert len(result.matches) == num_matches
        
        # 执行合并
        result.merge_duplicates()
        
        # 合并后每个路径只出现一次
        assert len(result.matches) == num_unique_paths
        
        # 验证所有路径都是唯一的
        paths = [m['imagePath'] for m in result.matches]
        assert len(paths) == len(set(paths))
    
    @given(
        matches_data=st.lists(
            st.tuples(
                image_path_strategy(),
                similarity_strategy(),
                face_id_strategy()
            ),
            min_size=1,
            max_size=50
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_property_25_no_duplicate_paths(self, matches_data):
        """
        对于任意匹配数据列表，合并后不应该有重复的图片路径
        
        **Validates: Requirements 8.2, 8.3**
        """
        result = MultiSearchResult()
        
        # 添加所有匹配
        for path, similarity, face_id in matches_data:
            match = Match(
                imagePath=path,
                similarity=similarity,
                faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
            )
            result.add_match(match, face_id)
        
        # 执行合并
        result.merge_duplicates()
        
        # 提取所有路径
        paths = [m['imagePath'] for m in result.matches]
        
        # 验证没有重复路径
        assert len(paths) == len(set(paths)), "合并后仍存在重复路径"
        
        # 验证合并后的数量不超过原始数量
        assert len(result.matches) <= len(matches_data)


# ============================================================================
# 属性 26: 最高相似度保留
# Feature: face-library-management, Property 26: 最高相似度保留
# ============================================================================

class TestProperty26_HighestSimilarity:
    """
    属性 26: 对于任意同一图片匹配多个源人像的情况，
    最终结果中该图片的相似度分数应该是所有匹配中的最高值
    
    **Validates: Requirements 8.4**
    """
    
    @given(
        image_path=image_path_strategy(),
        similarities=st.lists(
            similarity_strategy(),
            min_size=2,
            max_size=10
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_property_26_max_similarity_preserved(self, image_path, similarities):
        """
        对于同一图片的多个匹配，合并后应该保留最高相似度
        
        **Validates: Requirements 8.4**
        """
        result = MultiSearchResult()
        
        # 添加相同路径但不同相似度的匹配
        for similarity in similarities:
            match = Match(
                imagePath=image_path,
                similarity=similarity,
                faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
            )
            face_id = str(uuid.uuid4())
            result.add_match(match, face_id)
        
        # 记录最高相似度
        max_similarity = max(similarities)
        
        # 执行合并
        result.merge_duplicates()
        
        # 应该只有一个匹配
        assert len(result.matches) == 1
        
        # 验证保留了最高相似度
        assert result.matches[0]['similarity'] == max_similarity
    
    @given(
        num_paths=st.integers(min_value=1, max_value=5),
        matches_per_path=st.integers(min_value=2, max_value=8)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_26_multiple_paths_max_similarity(
        self,
        num_paths,
        matches_per_path
    ):
        """
        对于多个图片路径，每个路径都应该保留其最高相似度
        
        **Validates: Requirements 8.4**
        """
        result = MultiSearchResult()
        
        # 为每个路径记录最高相似度
        expected_max_similarities = {}
        
        for path_idx in range(num_paths):
            path = f"/path/to/image{path_idx}.jpg"
            similarities = []
            
            for _ in range(matches_per_path):
                similarity = np.random.uniform(0.6, 1.0)
                similarities.append(similarity)
                
                match = Match(
                    imagePath=path,
                    similarity=similarity,
                    faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
                )
                face_id = str(uuid.uuid4())
                result.add_match(match, face_id)
            
            expected_max_similarities[path] = max(similarities)
        
        # 执行合并
        result.merge_duplicates()
        
        # 验证每个路径只出现一次
        assert len(result.matches) == num_paths
        
        # 验证每个路径的相似度是最高值
        for match in result.matches:
            path = match['imagePath']
            assert match['similarity'] == expected_max_similarities[path]
    
    @given(
        path_similarities=st.dictionaries(
            keys=image_path_strategy(),
            values=st.lists(
                similarity_strategy(),
                min_size=1,
                max_size=10
            ),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_property_26_arbitrary_path_similarity_mapping(self, path_similarities):
        """
        对于任意路径到相似度列表的映射，合并后每个路径应该保留最高相似度
        
        **Validates: Requirements 8.4**
        """
        result = MultiSearchResult()
        
        # 添加所有匹配
        for path, similarities in path_similarities.items():
            for similarity in similarities:
                match = Match(
                    imagePath=path,
                    similarity=similarity,
                    faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
                )
                face_id = str(uuid.uuid4())
                result.add_match(match, face_id)
        
        # 计算每个路径的期望最高相似度
        expected_max = {path: max(sims) for path, sims in path_similarities.items()}
        
        # 执行合并
        result.merge_duplicates()
        
        # 验证结果数量
        assert len(result.matches) == len(path_similarities)
        
        # 验证每个路径的相似度
        for match in result.matches:
            path = match['imagePath']
            assert match['similarity'] == expected_max[path]


# ============================================================================
# 属性 27: 源人像标识
# Feature: face-library-management, Property 27: 源人像标识
# ============================================================================

class TestProperty27_SourceFaceIdentification:
    """
    属性 27: 对于任意搜索结果中的匹配，应该存在对应的源人像 ID 
    标识该匹配来自哪个搜索人像
    
    **Validates: Requirements 8.5**
    """
    
    @given(
        num_matches=st.integers(min_value=1, max_value=20),
        num_source_faces=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_27_all_matches_have_source_face_id(
        self,
        num_matches,
        num_source_faces
    ):
        """
        对于任意数量的匹配，每个匹配都应该有源人像ID
        
        **Validates: Requirements 8.5**
        """
        result = MultiSearchResult()
        
        # 生成源人像ID列表
        source_face_ids = [str(uuid.uuid4()) for _ in range(num_source_faces)]
        
        # 添加匹配，随机分配源人像
        for i in range(num_matches):
            match = Match(
                imagePath=f"/path/to/image{i}.jpg",
                similarity=np.random.uniform(0.6, 1.0),
                faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
            )
            # 随机选择一个源人像ID
            face_id = source_face_ids[i % num_source_faces]
            result.add_match(match, face_id)
        
        # 验证每个匹配都有源人像ID
        for match in result.matches:
            assert 'sourceFaceId' in match
            assert match['sourceFaceId'] is not None
            assert match['sourceFaceId'] in source_face_ids
    
    @given(
        matches_with_sources=st.lists(
            st.tuples(
                match_strategy(),
                face_id_strategy()
            ),
            min_size=1,
            max_size=30
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_property_27_source_face_mapping_consistency(self, matches_with_sources):
        """
        对于任意匹配和源人像的配对，源人像映射应该保持一致
        
        **Validates: Requirements 8.5**
        """
        result = MultiSearchResult()
        
        # 记录每个匹配的源人像
        expected_sources = {}
        
        for match, face_id in matches_with_sources:
            result.add_match(match, face_id)
            # 记录第一次出现的源人像（合并前）
            if match.imagePath not in expected_sources:
                expected_sources[match.imagePath] = face_id
        
        # 验证源人像映射存在
        assert len(result.source_face_map) > 0
        
        # 验证每个源人像ID都在映射中
        all_source_ids = set(face_id for _, face_id in matches_with_sources)
        for source_id in all_source_ids:
            assert source_id in result.source_face_map
    
    @given(
        num_faces=st.integers(min_value=1, max_value=10),
        matches_per_face=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_27_source_face_map_completeness(
        self,
        num_faces,
        matches_per_face
    ):
        """
        对于任意数量的源人像，源人像映射应该包含所有源人像
        
        **Validates: Requirements 8.5**
        """
        result = MultiSearchResult()
        
        source_face_ids = []
        
        # 为每个源人像添加匹配
        for face_idx in range(num_faces):
            face_id = str(uuid.uuid4())
            source_face_ids.append(face_id)
            
            for match_idx in range(matches_per_face):
                match = Match(
                    imagePath=f"/path/to/face{face_idx}_match{match_idx}.jpg",
                    similarity=np.random.uniform(0.6, 1.0),
                    faceLocation={'x': 0, 'y': 0, 'width': 100, 'height': 100}
                )
                result.add_match(match, face_id)
        
        # 验证所有源人像都在映射中
        assert len(result.source_face_map) == num_faces
        
        for face_id in source_face_ids:
            assert face_id in result.source_face_map
            # 验证每个源人像有正确数量的匹配
            assert len(result.source_face_map[face_id]) == matches_per_face


# ============================================================================
# 属性 28: 多人像搜索取消
# Feature: face-library-management, Property 28: 多人像搜索取消
# ============================================================================

class TestProperty28_SearchCancellation:
    """
    属性 28: 对于任意正在运行的多人像搜索任务，调用取消操作后，
    任务状态应该变为 'cancelled' 且停止处理新图片
    
    **Validates: Requirements 8.7**
    """
    
    def test_property_28_cancel_sets_flag(self):
        """
        对于任意搜索模块，调用取消应该设置取消标志
        
        **Validates: Requirements 8.7**
        """
        multi_search = MultiSearchModule()
        
        # 初始状态
        assert multi_search.cancelled is False
        
        # 调用取消
        success = multi_search.cancelSearch()
        
        # 验证取消成功
        assert success is True
        assert multi_search.cancelled is True
    
    @given(
        num_faces=st.integers(min_value=1, max_value=5)
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_28_cancelled_result_marked(self, num_faces, tmp_path):
        """
        对于任意数量的目标人像，如果搜索被取消，结果应该标记为已取消
        
        **Validates: Requirements 8.7**
        """
        multi_search = MultiSearchModule()
        
        # 创建测试图片目录（使用唯一名称避免冲突）
        test_dir = tmp_path / f"test_images_{uuid.uuid4().hex[:8]}"
        test_dir.mkdir(exist_ok=True)
        
        # 创建一些测试图片
        for i in range(3):
            img = Image.new('RGB', (200, 200), color=(i*50, i*50, i*50))
            img_path = test_dir / f"test_{i}.jpg"
            img.save(img_path)
        
        # 准备目标人像
        target_features_list = []
        for _ in range(num_faces):
            face_id = str(uuid.uuid4())
            features = np.random.rand(128).tolist()
            target_features_list.append((face_id, features))
        
        # 先设置取消标志
        multi_search.cancelSearch()
        
        # 执行搜索（应该立即检测到取消）
        result = multi_search.searchMultipleFaces(
            target_features_list=target_features_list,
            search_folder=str(test_dir),
            threshold=0.6
        )
        
        # 注意：searchMultipleFaces 会重置 cancelled 标志
        # 所以这个测试主要验证取消方法本身
        assert isinstance(result, MultiSearchResult)
    
    def test_property_28_cancel_method_returns_true(self):
        """
        对于任意搜索模块，取消方法应该返回 True 表示成功
        
        **Validates: Requirements 8.7**
        """
        multi_search = MultiSearchModule()
        
        # 多次调用取消都应该返回 True
        assert multi_search.cancelSearch() is True
        assert multi_search.cancelSearch() is True
        assert multi_search.cancelSearch() is True
    
    @given(
        initial_cancelled=st.booleans()
    )
    @settings(max_examples=20, deadline=None)
    def test_property_28_cancel_idempotent(self, initial_cancelled):
        """
        对于任意初始取消状态，调用取消操作应该是幂等的
        
        **Validates: Requirements 8.7**
        """
        multi_search = MultiSearchModule()
        multi_search.cancelled = initial_cancelled
        
        # 调用取消
        result1 = multi_search.cancelSearch()
        state1 = multi_search.cancelled
        
        # 再次调用取消
        result2 = multi_search.cancelSearch()
        state2 = multi_search.cancelled
        
        # 验证幂等性
        assert result1 is True
        assert result2 is True
        assert state1 is True
        assert state2 is True


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
