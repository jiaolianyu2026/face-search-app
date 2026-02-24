# -*- coding: utf-8 -*-
"""
Property-based tests for FaceLibraryModule.
Uses hypothesis to generate random test cases and verify correctness properties.

**Feature: face-library-management**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.6, 3.7, 10.2**
"""

import pytest
import os
import sys
import uuid
import sqlite3
import tempfile
import time
import gc
from pathlib import Path
from datetime import datetime
from hypothesis import given, strategies as st, settings, assume

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from face_library import FaceLibraryModule
from models import LibraryFace


# Custom strategies for test data generation
def valid_names():
    """Generate valid names (1-100 characters)."""
    return st.text(min_size=1, max_size=100, alphabet=st.characters(
        blacklist_categories=('Cc', 'Cs'),
        blacklist_characters='\x00'
    ))


def valid_feature_vectors():
    """Generate valid 128-dimensional feature vectors."""
    return st.lists(
        st.floats(
            min_value=-10.0,
            max_value=10.0,
            allow_nan=False,
            allow_infinity=False
        ),
        min_size=128,
        max_size=128
    )


def valid_uuids():
    """Generate valid UUID strings."""
    return st.uuids().map(str)


def valid_iso_timestamps():
    """Generate valid ISO 8601 timestamp strings."""
    return st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ).map(lambda dt: dt.isoformat())



class TestProperty5_SaveFaceRoundTrip:
    """
    Property 5: 人像保存 Round-Trip
    
    对于任意有效的人像数据（名称、特征向量、缩略图），保存到人像库后立即查询应该返回包含相同数据的 LibraryFace 对象。
    
    **Validates: Requirements 2.1, 2.3**
    """
    
    @given(
        name=valid_names(),
        features=valid_feature_vectors(),
        uuid_str=valid_uuids(),
        timestamp=valid_iso_timestamps()
    )
    @settings(max_examples=10, deadline=2000)
    def test_save_and_retrieve_preserves_data(self, name, features, uuid_str, timestamp):
        """Property: Saving a face and immediately retrieving it should return the same data."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            thumbnail_path = os.path.join(tmp_dir, f"thumb_{uuid_str}.jpg")
            Path(thumbnail_path).touch()
            
            original_face = LibraryFace(
                id=uuid_str, name=name, feature_vector=features,
                thumbnail_path=thumbnail_path, created_at=timestamp,
                source_image_id=str(uuid.uuid4())
            )
            
            result = temp_db.saveFace(original_face)
            assert result is True
            
            retrieved_face = temp_db.getFace(uuid_str)
            assert retrieved_face is not None
            assert retrieved_face.id == original_face.id
            assert retrieved_face.name == original_face.name
            assert len(retrieved_face.feature_vector) == 128
            for i in range(128):
                assert abs(retrieved_face.feature_vector[i] - original_face.feature_vector[i]) < 1e-5


class TestProperty6_ThumbnailFileExistence:
    """Property 6: 缩略图文件存在性"""
    
    @given(name=valid_names(), features=valid_feature_vectors(), 
           uuid_str=valid_uuids(), timestamp=valid_iso_timestamps())
    @settings(max_examples=10, deadline=2000)
    def test_saved_face_has_existing_thumbnail(self, name, features, uuid_str, timestamp):
        """Property: After saving a face, its thumbnail file should exist and be readable."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            thumbnail_path = os.path.join(tmp_dir, f"thumb_{uuid_str}.jpg")
            with open(thumbnail_path, 'w') as f:
                f.write("fake thumbnail data")
            
            face = LibraryFace(id=uuid_str, name=name, feature_vector=features,
                             thumbnail_path=thumbnail_path, created_at=timestamp)
            
            result = temp_db.saveFace(face)
            assert result is True
            
            retrieved_face = temp_db.getFace(uuid_str)
            assert retrieved_face is not None
            assert os.path.exists(retrieved_face.thumbnail_path)
            assert os.path.isfile(retrieved_face.thumbnail_path)
            assert os.access(retrieved_face.thumbnail_path, os.R_OK)


class TestProperty7_CreatedTimestampValidity:
    """Property 7: 创建时间戳有效性"""
    
    @given(name=valid_names(), features=valid_feature_vectors(), uuid_str=valid_uuids())
    @settings(max_examples=10, deadline=2000)
    def test_created_timestamp_is_within_operation_time(self, name, features, uuid_str):
        """Property: The created timestamp should be between operation start and end time."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            thumbnail_path = os.path.join(tmp_dir, f"thumb_{uuid_str}.jpg")
            Path(thumbnail_path).touch()
            
            start_time = datetime.now()
            face = LibraryFace.create(name=name, feature_vector=features, thumbnail_path=thumbnail_path)
            result = temp_db.saveFace(face)
            end_time = datetime.now()
            
            assert result is True
            retrieved_face = temp_db.getFace(face.id)
            assert retrieved_face is not None
            
            created_dt = datetime.fromisoformat(retrieved_face.created_at.replace('Z', '+00:00'))
            if created_dt.tzinfo is not None:
                created_dt = created_dt.replace(tzinfo=None)
            
            assert start_time <= created_dt <= end_time


class TestProperty8_IDUniqueness:
    """Property 8: ID 唯一性"""
    
    @given(names=st.lists(valid_names(), min_size=2, max_size=10),
           features_list=st.lists(valid_feature_vectors(), min_size=2, max_size=10))
    @settings(max_examples=8, deadline=3000)
    def test_multiple_faces_have_unique_ids(self, names, features_list):
        """Property: 保存多个人像时，所有 ID 应该唯一。"""
        num_faces = min(len(names), len(features_list))
        assume(num_faces >= 2)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            saved_ids = []
            for i in range(num_faces):
                thumbnail_path = os.path.join(tmp_dir, f"thumb_{i}.jpg")
                Path(thumbnail_path).touch()
                
                face = LibraryFace.create(name=names[i], feature_vector=features_list[i],
                                        thumbnail_path=thumbnail_path)
                result = temp_db.saveFace(face)
                assert result is True
                saved_ids.append(face.id)
            
            unique_ids = set(saved_ids)
            assert len(unique_ids) == num_faces
            
            for face_id in saved_ids:
                retrieved = temp_db.getFace(face_id)
                assert retrieved is not None
                assert retrieved.id == face_id


class TestProperty9_PersistenceValidation:
    """Property 9: 持久化验证"""
    
    @given(names=st.lists(valid_names(), min_size=1, max_size=5),
           features_list=st.lists(valid_feature_vectors(), min_size=1, max_size=5))
    @settings(max_examples=8, deadline=3000)
    def test_faces_persist_after_database_reconnection(self, names, features_list):
        """Property: 关闭并重新打开数据库后，数据应该保持一致。"""
        num_faces = min(len(names), len(features_list))
        assume(num_faces >= 1)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            
            # 第一次连接：保存人像
            library1 = FaceLibraryModule(db_path=db_path)
            saved_faces = []
            
            for i in range(num_faces):
                thumbnail_path = os.path.join(tmp_dir, f"thumb_{i}.jpg")
                Path(thumbnail_path).touch()
                
                face = LibraryFace.create(name=names[i], feature_vector=features_list[i],
                                        thumbnail_path=thumbnail_path)
                result = library1.saveFace(face)
                assert result is True
                saved_faces.append(face)
            
            count_before = library1.count()
            assert count_before == num_faces
            del library1
            
            # 第二次连接：验证数据持久化
            library2 = FaceLibraryModule(db_path=db_path)
            count_after = library2.count()
            assert count_after == num_faces
            
            for original_face in saved_faces:
                retrieved_face = library2.getFace(original_face.id)
                assert retrieved_face is not None
                assert retrieved_face.id == original_face.id
                assert retrieved_face.name == original_face.name
                assert len(retrieved_face.feature_vector) == 128



class TestProperty10_ListQueryCompleteness:
    """Property 10: 列表查询完整性"""
    
    @given(names=st.lists(valid_names(), min_size=1, max_size=10),
           features_list=st.lists(valid_feature_vectors(), min_size=1, max_size=10))
    @settings(max_examples=8, deadline=3000)
    def test_get_all_faces_returns_complete_list(self, names, features_list):
        """Property: 查询所有人像应该返回完整列表，每个人像包含必需字段。"""
        num_faces = min(len(names), len(features_list))
        assume(num_faces >= 1)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            for i in range(num_faces):
                thumbnail_path = os.path.join(tmp_dir, f"thumb_{i}.jpg")
                Path(thumbnail_path).touch()
                
                face = LibraryFace.create(name=names[i], feature_vector=features_list[i],
                                        thumbnail_path=thumbnail_path)
                result = temp_db.saveFace(face)
                assert result is True
            
            all_faces = temp_db.getAllFaces()
            assert len(all_faces) == num_faces
            
            for face_dict in all_faces:
                assert 'id' in face_dict and face_dict['id']
                assert 'name' in face_dict and face_dict['name']
                assert 'thumbnail_path' in face_dict and face_dict['thumbnail_path']
                assert 'created_at' in face_dict and face_dict['created_at']
                assert 'feature_vector' not in face_dict


class TestProperty11_NameUpdateRoundTrip:
    """Property 11: 名称更新 Round-Trip"""
    
    @given(original_name=valid_names(), new_name=valid_names(), features=valid_feature_vectors(),
           uuid_str=valid_uuids(), timestamp=valid_iso_timestamps())
    @settings(max_examples=10, deadline=2000)
    def test_update_name_is_reflected_in_query(self, original_name, new_name, features, uuid_str, timestamp):
        """Property: 更新人像名称后，查询应该返回新名称。"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            thumbnail_path = os.path.join(tmp_dir, f"thumb_{uuid_str}.jpg")
            Path(thumbnail_path).touch()
            
            face = LibraryFace(id=uuid_str, name=original_name, feature_vector=features,
                             thumbnail_path=thumbnail_path, created_at=timestamp)
            result = temp_db.saveFace(face)
            assert result is True
            
            retrieved = temp_db.getFace(uuid_str)
            assert retrieved.name == original_name
            
            update_result = temp_db.updateFace(uuid_str, new_name)
            assert update_result is True
            
            updated_face = temp_db.getFace(uuid_str)
            assert updated_face is not None
            assert updated_face.name == new_name
            assert updated_face.id == uuid_str


class TestProperty12_DeleteOperationValidity:
    """Property 12: 删除操作有效性"""
    
    @given(name=valid_names(), features=valid_feature_vectors(),
           uuid_str=valid_uuids(), timestamp=valid_iso_timestamps())
    @settings(max_examples=10, deadline=2000)
    def test_deleted_face_cannot_be_retrieved(self, name, features, uuid_str, timestamp):
        """Property: 删除人像后，查询应该返回 None。"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            thumbnail_path = os.path.join(tmp_dir, f"thumb_{uuid_str}.jpg")
            with open(thumbnail_path, 'w') as f:
                f.write("fake thumbnail")
            
            face = LibraryFace(id=uuid_str, name=name, feature_vector=features,
                             thumbnail_path=thumbnail_path, created_at=timestamp)
            result = temp_db.saveFace(face)
            assert result is True
            
            retrieved = temp_db.getFace(uuid_str)
            assert retrieved is not None
            
            count_before = temp_db.count()
            delete_result = temp_db.deleteFace(uuid_str)
            assert delete_result is True
            
            deleted_face = temp_db.getFace(uuid_str)
            assert deleted_face is None
            
            count_after = temp_db.count()
            assert count_after == count_before - 1
            assert not os.path.exists(thumbnail_path)


class TestProperty13_NameSearchFiltering:
    """Property 13: 名称搜索过滤"""
    
    @given(search_keyword=st.text(min_size=1, max_size=5, alphabet=st.characters(
               whitelist_categories=('Lu', 'Ll'), min_codepoint=65, max_codepoint=122)),
           matching_names=st.lists(st.text(min_size=3, max_size=20), min_size=1, max_size=3),
           non_matching_names=st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(
               blacklist_categories=('Cc', 'Cs'), blacklist_characters='\x00')), min_size=1, max_size=3),
           features_list=st.lists(valid_feature_vectors(), min_size=2, max_size=6))
    @settings(max_examples=5, deadline=5000)
    def test_search_returns_only_matching_names(self, search_keyword, matching_names, 
                                               non_matching_names, features_list):
        """Property: 按名称搜索应该只返回包含搜索关键词的人像。"""
        matching_names = [name + search_keyword + "suffix" for name in matching_names[:3]]
        non_matching_names = [name for name in non_matching_names[:3] if search_keyword not in name]
        assume(len(non_matching_names) >= 1)
        
        all_names = matching_names + non_matching_names
        num_faces = len(all_names)
        assume(num_faces <= len(features_list))
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            for i, name in enumerate(all_names):
                thumbnail_path = os.path.join(tmp_dir, f"thumb_{i}.jpg")
                Path(thumbnail_path).touch()
                
                face = LibraryFace.create(name=name, feature_vector=features_list[i],
                                        thumbnail_path=thumbnail_path)
                result = temp_db.saveFace(face)
                assert result is True
            
            search_results = temp_db.getAllFaces(search_name=search_keyword)
            
            # 验证所有返回的结果都包含搜索关键词
            for face_dict in search_results:
                assert search_keyword in face_dict['name'], \
                    f"搜索结果 '{face_dict['name']}' 应该包含关键词 '{search_keyword}'"
            
            # 重新计算实际包含 search_keyword 的名称数量（基础名称也可能包含关键词）
            actual_matching_count = sum(1 for name in all_names if search_keyword in name)
            assert len(search_results) <= actual_matching_count, \
                f"搜索结果数量 {len(search_results)} 不应超过实际匹配数量 {actual_matching_count}"
            
            # 验证至少返回了一些结果（如果有匹配的名称）
            if actual_matching_count > 0:
                assert len(search_results) > 0, "应该至少返回一个匹配结果"


class TestProperty14_TimeSortingCorrectness:
    """Property 14: 时间排序正确性"""
    
    @given(names=st.lists(valid_names(), min_size=3, max_size=6),
           features_list=st.lists(valid_feature_vectors(), min_size=3, max_size=6))
    @settings(max_examples=8, deadline=5000)
    def test_faces_sorted_by_created_time(self, names, features_list):
        """Property: 按创建时间排序应该返回单调排列的列表。"""
        num_faces = min(len(names), len(features_list))
        assume(num_faces >= 3)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            for i in range(num_faces):
                thumbnail_path = os.path.join(tmp_dir, f"thumb_{i}.jpg")
                Path(thumbnail_path).touch()
                
                face = LibraryFace.create(name=names[i], feature_vector=features_list[i],
                                        thumbnail_path=thumbnail_path)
                result = temp_db.saveFace(face)
                assert result is True
                time.sleep(0.01)
            
            sorted_faces = temp_db.getAllFaces(sort_by='created_at')
            assert len(sorted_faces) == num_faces
            
            for i in range(len(sorted_faces) - 1):
                current_time = datetime.fromisoformat(sorted_faces[i]['created_at'].replace('Z', '+00:00'))
                next_time = datetime.fromisoformat(sorted_faces[i + 1]['created_at'].replace('Z', '+00:00'))
                
                if current_time.tzinfo is not None:
                    current_time = current_time.replace(tzinfo=None)
                if next_time.tzinfo is not None:
                    next_time = next_time.replace(tzinfo=None)
                
                assert current_time >= next_time
    
    @given(names=st.lists(valid_names(), min_size=3, max_size=6),
           features_list=st.lists(valid_feature_vectors(), min_size=3, max_size=6))
    @settings(max_examples=8, deadline=5000)
    def test_faces_sorted_by_name(self, names, features_list):
        """Property: 按名称排序应该返回字母顺序排列的列表。"""
        num_faces = min(len(names), len(features_list))
        assume(num_faces >= 3)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            for i in range(num_faces):
                thumbnail_path = os.path.join(tmp_dir, f"thumb_{i}.jpg")
                Path(thumbnail_path).touch()
                
                face = LibraryFace.create(name=names[i], feature_vector=features_list[i],
                                        thumbnail_path=thumbnail_path)
                result = temp_db.saveFace(face)
                assert result is True
            
            sorted_faces = temp_db.getAllFaces(sort_by='name')
            assert len(sorted_faces) == num_faces
            
            sorted_names = [face['name'] for face in sorted_faces]
            expected_sorted = sorted(names[:num_faces])
            assert sorted_names == expected_sorted


class TestProperty29_PrimaryKeyUniquenessConstraint:
    """Property 29: 主键唯一性约束"""
    
    @given(name1=valid_names(), name2=valid_names(), features1=valid_feature_vectors(),
           features2=valid_feature_vectors(), uuid_str=valid_uuids(),
           timestamp1=valid_iso_timestamps(), timestamp2=valid_iso_timestamps())
    @settings(max_examples=8, deadline=2000)
    def test_duplicate_id_insertion_fails(self, name1, name2, features1, features2, 
                                         uuid_str, timestamp1, timestamp2):
        """Property: 尝试插入相同 ID 的人像应该失败。"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            thumbnail_path1 = os.path.join(tmp_dir, f"thumb1_{uuid_str}.jpg")
            Path(thumbnail_path1).touch()
            
            face1 = LibraryFace(id=uuid_str, name=name1, feature_vector=features1,
                              thumbnail_path=thumbnail_path1, created_at=timestamp1)
            result1 = temp_db.saveFace(face1)
            assert result1 is True
            
            thumbnail_path2 = os.path.join(tmp_dir, f"thumb2_{uuid_str}.jpg")
            Path(thumbnail_path2).touch()
            
            face2 = LibraryFace(id=uuid_str, name=name2, feature_vector=features2,
                              thumbnail_path=thumbnail_path2, created_at=timestamp2)
            result2 = temp_db.saveFace(face2)
            assert result2 is False
            
            count = temp_db.count()
            assert count == 1
            
            retrieved = temp_db.getFace(uuid_str)
            assert retrieved is not None
            assert retrieved.name == name1
            
            # 显式删除对象并强制垃圾回收以关闭数据库连接
            del temp_db
            gc.collect()
            time.sleep(0.1)  # 给 Windows 一点时间释放文件锁


class TestProperty22_DeleteOperationDataConsistency:
    """
    Property 22: 删除操作的数据一致性
    
    对于任意历史人像，删除操作应该同时从数据库和文件系统中移除数据，确保不留下孤立的文件或记录。
    
    **Validates: Requirements 9.2**
    **Feature: unified-face-selector, Property 22: 删除操作的数据一致性**
    """
    
    @given(
        name=valid_names(),
        features=valid_feature_vectors(),
        uuid_str=valid_uuids(),
        timestamp=valid_iso_timestamps()
    )
    @settings(max_examples=100, deadline=2000)
    def test_delete_removes_both_database_and_file(self, name, features, uuid_str, timestamp):
        """
        属性测试：删除操作应该同时从数据库和文件系统中移除数据
        
        验证：
        1. 删除前，数据库记录存在
        2. 删除前，缩略图文件存在
        3. 删除后，数据库记录不存在
        4. 删除后，缩略图文件不存在
        5. 删除后，人像库计数减少
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            # 创建真实的缩略图文件
            thumbnail_path = os.path.join(tmp_dir, f"thumb_{uuid_str}.jpg")
            with open(thumbnail_path, 'w') as f:
                f.write("fake thumbnail data")
            
            # 创建并保存人像
            face = LibraryFace(
                id=uuid_str,
                name=name,
                feature_vector=features,
                thumbnail_path=thumbnail_path,
                created_at=timestamp,
                source_image_id=str(uuid.uuid4())
            )
            
            save_result = temp_db.saveFace(face)
            assert save_result is True, "保存人像应该成功"
            
            # 验证删除前的状态
            # 1. 数据库记录存在
            retrieved_before = temp_db.getFace(uuid_str)
            assert retrieved_before is not None, "删除前，数据库记录应该存在"
            assert retrieved_before.id == uuid_str
            assert retrieved_before.name == name
            
            # 2. 缩略图文件存在
            assert os.path.exists(thumbnail_path), "删除前，缩略图文件应该存在"
            assert os.path.isfile(thumbnail_path), "缩略图路径应该是文件"
            
            # 3. 记录删除前的人像库计数
            count_before = temp_db.count()
            assert count_before >= 1, "删除前，人像库应该至少有一个人像"
            
            # 执行删除操作
            delete_result = temp_db.deleteFace(uuid_str)
            assert delete_result is True, "删除操作应该成功"
            
            # 验证删除后的状态
            # 4. 数据库记录不存在
            retrieved_after = temp_db.getFace(uuid_str)
            assert retrieved_after is None, "删除后，数据库记录应该不存在"
            
            # 5. 缩略图文件不存在
            assert not os.path.exists(thumbnail_path), "删除后，缩略图文件应该不存在"
            
            # 6. 人像库计数减少
            count_after = temp_db.count()
            assert count_after == count_before - 1, "删除后，人像库计数应该减少 1"
            
            # 7. 验证不能再次删除同一个人像
            delete_again_result = temp_db.deleteFace(uuid_str)
            assert delete_again_result is False, "删除不存在的人像应该返回 False"
    
    @given(
        names=st.lists(valid_names(), min_size=2, max_size=5),
        features_list=st.lists(valid_feature_vectors(), min_size=2, max_size=5)
    )
    @settings(max_examples=100, deadline=3000)
    def test_delete_one_does_not_affect_others(self, names, features_list):
        """
        属性测试：删除一个人像不应该影响其他人像
        
        验证：
        1. 保存多个人像
        2. 删除其中一个
        3. 其他人像的数据库记录仍然存在
        4. 其他人像的缩略图文件仍然存在
        5. 只有被删除的人像的数据被移除
        """
        num_faces = min(len(names), len(features_list))
        assume(num_faces >= 2)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            # 创建并保存多个人像
            saved_faces = []
            thumbnail_paths = []
            
            for i in range(num_faces):
                face_id = str(uuid.uuid4())
                thumbnail_path = os.path.join(tmp_dir, f"thumb_{face_id}.jpg")
                
                # 创建真实的缩略图文件
                with open(thumbnail_path, 'w') as f:
                    f.write(f"fake thumbnail data {i}")
                
                face = LibraryFace(
                    id=face_id,
                    name=names[i],
                    feature_vector=features_list[i],
                    thumbnail_path=thumbnail_path,
                    created_at=datetime.now().isoformat(),
                    source_image_id=str(uuid.uuid4())
                )
                
                save_result = temp_db.saveFace(face)
                assert save_result is True
                
                saved_faces.append(face)
                thumbnail_paths.append(thumbnail_path)
            
            # 验证所有人像都已保存
            initial_count = temp_db.count()
            assert initial_count == num_faces
            
            # 删除第一个人像
            face_to_delete = saved_faces[0]
            thumbnail_to_delete = thumbnail_paths[0]
            
            delete_result = temp_db.deleteFace(face_to_delete.id)
            assert delete_result is True, "删除操作应该成功"
            
            # 验证被删除的人像不存在
            deleted_face = temp_db.getFace(face_to_delete.id)
            assert deleted_face is None, "被删除的人像不应该在数据库中"
            assert not os.path.exists(thumbnail_to_delete), "被删除的人像的缩略图不应该存在"
            
            # 验证其他人像仍然存在
            for i in range(1, num_faces):
                other_face = saved_faces[i]
                other_thumbnail = thumbnail_paths[i]
                
                # 数据库记录仍然存在
                retrieved = temp_db.getFace(other_face.id)
                assert retrieved is not None, f"其他人像 {i} 应该仍然在数据库中"
                assert retrieved.id == other_face.id
                assert retrieved.name == other_face.name
                
                # 缩略图文件仍然存在
                assert os.path.exists(other_thumbnail), f"其他人像 {i} 的缩略图应该仍然存在"
            
            # 验证人像库计数正确
            final_count = temp_db.count()
            assert final_count == num_faces - 1, "人像库计数应该减少 1"
    
    @given(
        name=valid_names(),
        features=valid_feature_vectors(),
        uuid_str=valid_uuids(),
        timestamp=valid_iso_timestamps()
    )
    @settings(max_examples=100, deadline=2000)
    def test_delete_without_thumbnail_file(self, name, features, uuid_str, timestamp):
        """
        属性测试：删除操作在缩略图文件不存在时仍然应该成功
        
        验证：
        1. 保存人像后删除缩略图文件（模拟文件丢失）
        2. 删除操作仍然应该成功
        3. 数据库记录应该被移除
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            # 创建缩略图文件
            thumbnail_path = os.path.join(tmp_dir, f"thumb_{uuid_str}.jpg")
            with open(thumbnail_path, 'w') as f:
                f.write("fake thumbnail data")
            
            # 创建并保存人像
            face = LibraryFace(
                id=uuid_str,
                name=name,
                feature_vector=features,
                thumbnail_path=thumbnail_path,
                created_at=timestamp,
                source_image_id=str(uuid.uuid4())
            )
            
            save_result = temp_db.saveFace(face)
            assert save_result is True
            
            # 手动删除缩略图文件（模拟文件丢失）
            os.remove(thumbnail_path)
            assert not os.path.exists(thumbnail_path), "缩略图文件应该已被删除"
            
            # 验证数据库记录仍然存在
            retrieved_before = temp_db.getFace(uuid_str)
            assert retrieved_before is not None, "数据库记录应该仍然存在"
            
            # 执行删除操作（即使缩略图文件不存在）
            delete_result = temp_db.deleteFace(uuid_str)
            assert delete_result is True, "删除操作应该成功，即使缩略图文件不存在"
            
            # 验证数据库记录已被移除
            retrieved_after = temp_db.getFace(uuid_str)
            assert retrieved_after is None, "删除后，数据库记录应该不存在"
            
            # 验证人像库计数正确
            count_after = temp_db.count()
            assert count_after == 0, "人像库应该为空"
    
    @given(
        names=st.lists(valid_names(), min_size=3, max_size=5),
        features_list=st.lists(valid_feature_vectors(), min_size=3, max_size=5)
    )
    @settings(max_examples=100, deadline=3000)
    def test_delete_all_leaves_empty_database(self, names, features_list):
        """
        属性测试：删除所有人像后，数据库应该为空
        
        验证：
        1. 保存多个人像
        2. 逐个删除所有人像
        3. 所有数据库记录都被移除
        4. 所有缩略图文件都被移除
        5. 人像库计数为 0
        """
        num_faces = min(len(names), len(features_list))
        assume(num_faces >= 3)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            temp_db = FaceLibraryModule(db_path=db_path)
            
            # 创建并保存多个人像
            saved_faces = []
            thumbnail_paths = []
            
            for i in range(num_faces):
                face_id = str(uuid.uuid4())
                thumbnail_path = os.path.join(tmp_dir, f"thumb_{face_id}.jpg")
                
                with open(thumbnail_path, 'w') as f:
                    f.write(f"fake thumbnail data {i}")
                
                face = LibraryFace(
                    id=face_id,
                    name=names[i],
                    feature_vector=features_list[i],
                    thumbnail_path=thumbnail_path,
                    created_at=datetime.now().isoformat(),
                    source_image_id=str(uuid.uuid4())
                )
                
                save_result = temp_db.saveFace(face)
                assert save_result is True
                
                saved_faces.append(face)
                thumbnail_paths.append(thumbnail_path)
            
            # 验证所有人像都已保存
            initial_count = temp_db.count()
            assert initial_count == num_faces
            
            # 逐个删除所有人像
            for i, face in enumerate(saved_faces):
                delete_result = temp_db.deleteFace(face.id)
                assert delete_result is True, f"删除人像 {i} 应该成功"
                
                # 验证当前人像已被删除
                retrieved = temp_db.getFace(face.id)
                assert retrieved is None, f"人像 {i} 应该已从数据库中移除"
                
                # 验证缩略图文件已被删除
                assert not os.path.exists(thumbnail_paths[i]), f"人像 {i} 的缩略图应该已被删除"
                
                # 验证人像库计数正确
                expected_count = num_faces - (i + 1)
                current_count = temp_db.count()
                assert current_count == expected_count, f"删除 {i+1} 个人像后，计数应该为 {expected_count}"
            
            # 验证最终状态
            final_count = temp_db.count()
            assert final_count == 0, "删除所有人像后，人像库应该为空"
            
            all_faces = temp_db.getAllFaces()
            assert len(all_faces) == 0, "getAllFaces 应该返回空列表"
            
            # 验证所有缩略图文件都已被删除
            for thumbnail_path in thumbnail_paths:
                assert not os.path.exists(thumbnail_path), "所有缩略图文件都应该已被删除"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
