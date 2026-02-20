"""
人像库管理模块的单元测试
测试 FaceLibraryModule 的核心功能
"""

import pytest
import os
import sys
import sqlite3
import tempfile
import numpy as np
import uuid
from pathlib import Path
from datetime import datetime

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from face_library import FaceLibraryModule
from models import LibraryFace


class TestFaceLibraryModule:
    """FaceLibraryModule 的单元测试套件"""
    
    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """创建临时数据库路径"""
        db_path = str(tmp_path / "test_face_library.db")
        return db_path
    
    @pytest.fixture
    def face_library(self, temp_db_path):
        """创建 FaceLibraryModule 实例"""
        return FaceLibraryModule(db_path=temp_db_path)
    
    @pytest.fixture
    def sample_face(self, tmp_path):
        """创建样本人像数据"""
        # 创建临时缩略图文件
        thumbnail_path = str(tmp_path / "thumbnail.jpg")
        Path(thumbnail_path).touch()
        
        # 生成 128 维特征向量
        features = np.random.rand(128).tolist()
        
        return LibraryFace(
            id=str(uuid.uuid4()),
            name="张三",
            feature_vector=features,
            thumbnail_path=thumbnail_path,
            created_at=datetime.now().isoformat(),
            source_image_id=str(uuid.uuid4())
        )
    
    def test_database_initialization(self, face_library, temp_db_path):
        """
        测试数据库初始化和表创建
        验证需求 10.1, 10.6
        """
        # 验证数据库文件已创建
        assert os.path.exists(temp_db_path)
        
        # 验证表结构
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # 检查 library_faces 表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='library_faces'
        """)
        assert cursor.fetchone() is not None
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(library_faces)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        assert 'id' in column_names
        assert 'name' in column_names
        assert 'feature_vector' in column_names
        assert 'thumbnail_path' in column_names
        assert 'created_at' in column_names
        assert 'source_image_id' in column_names
        
        conn.close()
    
    def test_database_indexes(self, face_library, temp_db_path):
        """
        测试数据库索引创建
        验证需求 10.3, 10.4
        """
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # 检查索引是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        assert 'idx_name' in indexes
        assert 'idx_created_at' in indexes
        
        conn.close()
    
    def test_save_face_success(self, face_library, sample_face):
        """
        测试保存人像成功
        验证需求 2.1, 2.2, 2.3, 2.4, 2.5
        """
        result = face_library.saveFace(sample_face)
        
        assert result is True
        
        # 验证人像已保存
        saved_face = face_library.getFace(sample_face.id)
        assert saved_face is not None
        assert saved_face.id == sample_face.id
        assert saved_face.name == sample_face.name
        assert len(saved_face.feature_vector) == 128
        assert saved_face.thumbnail_path == sample_face.thumbnail_path
        assert saved_face.created_at == sample_face.created_at
        assert saved_face.source_image_id == sample_face.source_image_id
    
    def test_save_face_duplicate_id(self, face_library, sample_face):
        """
        测试主键约束（重复 ID）
        验证需求 10.2
        """
        # 第一次保存成功
        result1 = face_library.saveFace(sample_face)
        assert result1 is True
        
        # 第二次保存相同 ID 应该失败
        result2 = face_library.saveFace(sample_face)
        assert result2 is False
    
    def test_get_face_exists(self, face_library, sample_face):
        """
        测试查询存在的人像
        验证需求 3.2
        """
        # 先保存
        face_library.saveFace(sample_face)
        
        # 查询
        retrieved_face = face_library.getFace(sample_face.id)
        
        assert retrieved_face is not None
        assert retrieved_face.id == sample_face.id
        assert retrieved_face.name == sample_face.name
        assert len(retrieved_face.feature_vector) == 128
    
    def test_get_face_not_exists(self, face_library):
        """
        测试查询不存在的人像
        验证需求 3.2
        """
        result = face_library.getFace("nonexistent-id")
        assert result is None
    
    def test_get_all_faces_empty(self, face_library):
        """
        测试查询空人像库
        验证需求 3.1
        """
        faces = face_library.getAllFaces()
        assert faces == []
    
    def test_get_all_faces_multiple(self, face_library, tmp_path):
        """
        测试查询多个人像
        验证需求 3.1
        """
        # 创建多个人像
        faces_data = []
        for i in range(3):
            thumbnail_path = str(tmp_path / f"thumbnail_{i}.jpg")
            Path(thumbnail_path).touch()
            
            face = LibraryFace(
                id=str(uuid.uuid4()),
                name=f"人像{i}",
                feature_vector=np.random.rand(128).tolist(),
                thumbnail_path=thumbnail_path,
                created_at=datetime.now().isoformat(),
                source_image_id=str(uuid.uuid4())
            )
            faces_data.append(face)
            face_library.saveFace(face)
        
        # 查询所有人像
        all_faces = face_library.getAllFaces()
        
        assert len(all_faces) == 3
        # 验证返回的是字典格式（不含特征向量）
        for face_dict in all_faces:
            assert 'id' in face_dict
            assert 'name' in face_dict
            assert 'thumbnail_path' in face_dict
            assert 'created_at' in face_dict
            assert 'source_image_id' in face_dict
            # 不应该包含特征向量
            assert 'feature_vector' not in face_dict
    
    def test_get_all_faces_sort_by_created_at(self, face_library, tmp_path):
        """
        测试按创建时间排序
        验证需求 3.7
        """
        import time
        
        # 创建多个人像，间隔时间
        face_ids = []
        for i in range(3):
            thumbnail_path = str(tmp_path / f"thumbnail_{i}.jpg")
            Path(thumbnail_path).touch()
            
            face_id = str(uuid.uuid4())
            face = LibraryFace(
                id=face_id,
                name=f"人像{i}",
                feature_vector=np.random.rand(128).tolist(),
                thumbnail_path=thumbnail_path,
                created_at=datetime.now().isoformat(),
                source_image_id=str(uuid.uuid4())
            )
            face_ids.append(face_id)
            face_library.saveFace(face)
            time.sleep(0.01)  # 确保时间戳不同
        
        # 按创建时间排序（默认降序）
        faces = face_library.getAllFaces(sort_by='created_at')
        
        # 验证顺序（最新的在前）
        assert len(faces) == 3
        # 最后创建的应该在第一个
        assert faces[0]['id'] == face_ids[-1]
    
    def test_get_all_faces_sort_by_name(self, face_library, tmp_path):
        """
        测试按名称排序
        验证需求 3.7
        """
        # 创建多个人像，名称不同
        names = ["张三", "李四", "王五"]
        for i, name in enumerate(names):
            thumbnail_path = str(tmp_path / f"thumbnail_{i}.jpg")
            Path(thumbnail_path).touch()
            
            face = LibraryFace(
                id=str(uuid.uuid4()),
                name=name,
                feature_vector=np.random.rand(128).tolist(),
                thumbnail_path=thumbnail_path,
                created_at=datetime.now().isoformat(),
                source_image_id=str(uuid.uuid4())
            )
            face_library.saveFace(face)
        
        # 按名称排序（升序）
        faces = face_library.getAllFaces(sort_by='name')
        
        assert len(faces) == 3
        # 验证按字母顺序排列
        face_names = [f['name'] for f in faces]
        assert face_names == sorted(names)
    
    def test_search_faces_by_name(self, face_library, tmp_path):
        """
        测试按名称搜索
        验证需求 3.6
        """
        # 创建多个人像
        names = ["张三", "张四", "李四", "王五"]
        for i, name in enumerate(names):
            thumbnail_path = str(tmp_path / f"thumbnail_{i}.jpg")
            Path(thumbnail_path).touch()
            
            face = LibraryFace(
                id=str(uuid.uuid4()),
                name=name,
                feature_vector=np.random.rand(128).tolist(),
                thumbnail_path=thumbnail_path,
                created_at=datetime.now().isoformat(),
                source_image_id=str(uuid.uuid4())
            )
            face_library.saveFace(face)
        
        # 搜索包含"张"的人像
        results = face_library.getAllFaces(search_name="张")
        
        assert len(results) == 2
        for face in results:
            assert "张" in face['name']
    
    def test_search_faces_no_match(self, face_library, tmp_path):
        """
        测试搜索无匹配结果
        验证需求 3.6
        """
        # 创建一个人像
        thumbnail_path = str(tmp_path / "thumbnail.jpg")
        Path(thumbnail_path).touch()
        
        face = LibraryFace(
            id=str(uuid.uuid4()),
            name="张三",
            feature_vector=np.random.rand(128).tolist(),
            thumbnail_path=thumbnail_path,
            created_at=datetime.now().isoformat(),
            source_image_id=str(uuid.uuid4())
        )
        face_library.saveFace(face)
        
        # 搜索不存在的名称
        results = face_library.getAllFaces(search_name="赵六")
        
        assert len(results) == 0
    
    def test_update_face_success(self, face_library, sample_face):
        """
        测试更新人像名称成功
        验证需求 3.3
        """
        # 先保存
        face_library.saveFace(sample_face)
        
        # 更新名称
        new_name = "李四"
        result = face_library.updateFace(sample_face.id, new_name)
        
        assert result is True
        
        # 验证更新成功
        updated_face = face_library.getFace(sample_face.id)
        assert updated_face.name == new_name
    
    def test_update_face_not_exists(self, face_library):
        """
        测试更新不存在的人像
        验证需求 3.3
        """
        result = face_library.updateFace("nonexistent-id", "新名称")
        assert result is False
    
    def test_update_face_empty_name(self, face_library, sample_face):
        """
        测试更新为空名称
        验证需求 3.3
        """
        face_library.saveFace(sample_face)
        
        # 尝试更新为空名称
        result = face_library.updateFace(sample_face.id, "")
        assert result is False
    
    def test_update_face_long_name(self, face_library, sample_face):
        """
        测试更新为超长名称
        验证需求 3.3
        """
        face_library.saveFace(sample_face)
        
        # 尝试更新为超过 100 字符的名称
        long_name = "a" * 101
        result = face_library.updateFace(sample_face.id, long_name)
        assert result is False
    
    def test_delete_face_success(self, face_library, sample_face):
        """
        测试删除人像成功
        验证需求 3.4
        """
        # 先保存
        face_library.saveFace(sample_face)
        
        # 验证存在
        assert face_library.getFace(sample_face.id) is not None
        
        # 删除
        result = face_library.deleteFace(sample_face.id)
        
        assert result is True
        
        # 验证已删除
        assert face_library.getFace(sample_face.id) is None
    
    def test_delete_face_not_exists(self, face_library):
        """
        测试删除不存在的人像
        验证需求 3.4
        """
        result = face_library.deleteFace("nonexistent-id")
        assert result is False
    
    def test_delete_face_with_thumbnail(self, face_library, tmp_path):
        """
        测试删除人像时同时删除缩略图
        验证需求 3.4
        """
        # 创建真实的缩略图文件
        thumbnail_path = str(tmp_path / "thumbnail_to_delete.jpg")
        with open(thumbnail_path, 'w') as f:
            f.write("fake image")
        
        face = LibraryFace(
            id=str(uuid.uuid4()),
            name="待删除",
            feature_vector=np.random.rand(128).tolist(),
            thumbnail_path=thumbnail_path,
            created_at=datetime.now().isoformat(),
            source_image_id=str(uuid.uuid4())
        )
        
        face_library.saveFace(face)
        
        # 验证缩略图存在
        assert os.path.exists(thumbnail_path)
        
        # 删除人像
        result = face_library.deleteFace(face.id)
        
        assert result is True
        # 验证缩略图也被删除
        assert not os.path.exists(thumbnail_path)
    
    def test_count_faces(self, face_library, tmp_path):
        """
        测试统计人像数量
        验证需求 3.1
        """
        # 初始为 0
        assert face_library.count() == 0
        
        # 添加人像
        for i in range(5):
            thumbnail_path = str(tmp_path / f"thumbnail_{i}.jpg")
            Path(thumbnail_path).touch()
            
            face = LibraryFace(
                id=str(uuid.uuid4()),
                name=f"人像{i}",
                feature_vector=np.random.rand(128).tolist(),
                thumbnail_path=thumbnail_path,
                created_at=datetime.now().isoformat(),
                source_image_id=str(uuid.uuid4())
            )
            face_library.saveFace(face)
        
        # 验证数量
        assert face_library.count() == 5
    
    def test_feature_vector_serialization(self, face_library, sample_face):
        """
        测试特征向量的序列化和反序列化
        验证需求 10.5
        """
        # 保存人像
        face_library.saveFace(sample_face)
        
        # 查询人像
        retrieved_face = face_library.getFace(sample_face.id)
        
        # 验证特征向量正确反序列化
        assert len(retrieved_face.feature_vector) == 128
        assert isinstance(retrieved_face.feature_vector, list)
        
        # 验证数值接近（浮点数精度）
        for i in range(128):
            assert abs(retrieved_face.feature_vector[i] - sample_face.feature_vector[i]) < 1e-6


class TestFaceLibraryEdgeCases:
    """人像库模块的边缘情况测试"""
    
    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """创建临时数据库路径"""
        db_path = str(tmp_path / "test_edge_cases.db")
        return db_path
    
    @pytest.fixture
    def face_library(self, temp_db_path):
        """创建 FaceLibraryModule 实例"""
        return FaceLibraryModule(db_path=temp_db_path)
    
    def test_database_directory_auto_creation(self, tmp_path):
        """
        测试数据库目录自动创建
        验证需求 10.6
        """
        # 使用不存在的目录路径
        db_path = str(tmp_path / "new_dir" / "subdir" / "face_library.db")
        
        # 创建模块应该自动创建目录
        library = FaceLibraryModule(db_path=db_path)
        
        assert os.path.exists(db_path)
        assert os.path.isfile(db_path)
    
    def test_concurrent_access(self, face_library, tmp_path):
        """
        测试并发访问（SQLite 的并发处理）
        """
        # 创建多个人像并保存
        faces = []
        for i in range(10):
            thumbnail_path = str(tmp_path / f"thumbnail_{i}.jpg")
            Path(thumbnail_path).touch()
            
            face = LibraryFace(
                id=str(uuid.uuid4()),
                name=f"人像{i}",
                feature_vector=np.random.rand(128).tolist(),
                thumbnail_path=thumbnail_path,
                created_at=datetime.now().isoformat(),
                source_image_id=str(uuid.uuid4())
            )
            faces.append(face)
        
        # 批量保存
        for face in faces:
            result = face_library.saveFace(face)
            assert result is True
        
        # 验证所有人像都已保存
        assert face_library.count() == 10
    
    def test_special_characters_in_name(self, face_library, tmp_path):
        """
        测试名称中包含特殊字符
        """
        thumbnail_path = str(tmp_path / "thumbnail.jpg")
        Path(thumbnail_path).touch()
        
        # 包含特殊字符的名称
        special_names = [
            "张三's Face",
            "李四 (测试)",
            "王五@公司",
            "赵六#123",
            "孙七&陈八"
        ]
        
        for i, name in enumerate(special_names):
            face = LibraryFace(
                id=str(uuid.uuid4()),
                name=name,
                feature_vector=np.random.rand(128).tolist(),
                thumbnail_path=thumbnail_path,
                created_at=datetime.now().isoformat(),
                source_image_id=str(uuid.uuid4())
            )
            
            result = face_library.saveFace(face)
            assert result is True
            
            # 验证可以正确查询
            retrieved = face_library.getFace(face.id)
            assert retrieved.name == name
    
    def test_unicode_names(self, face_library, tmp_path):
        """
        测试 Unicode 字符名称
        """
        thumbnail_path = str(tmp_path / "thumbnail.jpg")
        Path(thumbnail_path).touch()
        
        # 各种语言的名称
        unicode_names = [
            "张三",      # 中文
            "John Doe",  # 英文
            "山田太郎",  # 日文
            "김철수",    # 韩文
            "Müller",    # 德文
            "José",      # 西班牙文
        ]
        
        for i, name in enumerate(unicode_names):
            face = LibraryFace(
                id=str(uuid.uuid4()),
                name=name,
                feature_vector=np.random.rand(128).tolist(),
                thumbnail_path=thumbnail_path,
                created_at=datetime.now().isoformat(),
                source_image_id=str(uuid.uuid4())
            )
            
            result = face_library.saveFace(face)
            assert result is True
            
            # 验证可以正确查询
            retrieved = face_library.getFace(face.id)
            assert retrieved.name == name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
