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
            
            # 验证返回的数量不超过匹配的数量
            expected_count = len(matching_names)
            assert len(search_results) <= expected_count, \
                f"搜索结果数量 {len(search_results)} 不应超过匹配数量 {expected_count}"
            
            # 验证至少返回了一些结果（如果有匹配的名称）
            if expected_count > 0:
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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
