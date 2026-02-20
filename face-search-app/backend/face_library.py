"""
人像库管理模块
负责人像的持久化存储和CRUD操作
"""

import sqlite3
import logging
import os
import numpy as np
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path
from models import LibraryFace

# 配置日志
logger = logging.getLogger(__name__)


class FaceLibraryModule:
    """
    人像库管理类
    使用 SQLite 数据库存储人像特征和元数据
    """
    
    def __init__(self, db_path: str = 'backend/cache/face_library.db'):
        """
        初始化人像库模块
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_database()
    
    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        Path(db_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"数据库目录已准备: {db_dir}")
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建 library_faces 表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS library_faces (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    feature_vector BLOB NOT NULL,
                    thumbnail_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    source_image_id TEXT
                )
            ''')
            
            # 创建索引以优化查询
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_name 
                ON library_faces(name)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON library_faces(created_at)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("数据库表结构已初始化")
            
        except Exception as e:
            logger.error(f"初始化数据库失败: {str(e)}")
            raise
    
    def saveFace(self, library_face: LibraryFace) -> bool:
        """
        保存人像到数据库
        
        Args:
            library_face: LibraryFace 对象
            
        Returns:
            保存成功返回 True
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 序列化特征向量为 BLOB
            feature_blob = np.array(library_face.feature_vector, dtype=np.float32).tobytes()
            
            cursor.execute('''
                INSERT INTO library_faces 
                (id, name, feature_vector, thumbnail_path, created_at, source_image_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                library_face.id,
                library_face.name,
                feature_blob,
                library_face.thumbnail_path,
                library_face.created_at,
                library_face.source_image_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"人像已保存: {library_face.id} - {library_face.name}")
            return True
            
        except sqlite3.IntegrityError as e:
            logger.error(f"保存人像失败（ID重复）: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"保存人像失败: {str(e)}")
            return False
    
    def getFace(self, face_id: str) -> Optional[LibraryFace]:
        """
        根据ID查询单个人像
        
        Args:
            face_id: 人像ID
            
        Returns:
            LibraryFace 对象，不存在返回 None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, feature_vector, thumbnail_path, created_at, source_image_id
                FROM library_faces
                WHERE id = ?
            ''', (face_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # 反序列化特征向量
                feature_vector = np.frombuffer(row[2], dtype=np.float32).tolist()
                
                return LibraryFace(
                    id=row[0],
                    name=row[1],
                    feature_vector=feature_vector,
                    thumbnail_path=row[3],
                    created_at=row[4],
                    source_image_id=row[5]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"查询人像失败: {str(e)}")
            return None
    
    def getAllFaces(self, sort_by: str = 'created_at', 
                    search_name: Optional[str] = None) -> List[Dict]:
        """
        查询所有人像（不包含特征向量）
        
        Args:
            sort_by: 排序字段 ('created_at' 或 'name')
            search_name: 名称搜索关键词（可选）
            
        Returns:
            人像信息列表（字典格式，不含特征向量）
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 构建查询语句
            query = '''
                SELECT id, name, thumbnail_path, created_at, source_image_id
                FROM library_faces
            '''
            params = []
            
            # 添加名称搜索条件
            if search_name:
                query += ' WHERE name LIKE ?'
                params.append(f'%{search_name}%')
            
            # 添加排序
            if sort_by == 'name':
                query += ' ORDER BY name ASC'
            else:  # 默认按创建时间降序
                query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            # 转换为字典列表
            faces = []
            for row in rows:
                faces.append({
                    'id': row[0],
                    'name': row[1],
                    'thumbnail_path': row[2],
                    'created_at': row[3],
                    'source_image_id': row[4]
                })
            
            logger.info(f"查询到 {len(faces)} 个人像")
            return faces
            
        except Exception as e:
            logger.error(f"查询所有人像失败: {str(e)}")
            return []
    
    def updateFace(self, face_id: str, new_name: str) -> bool:
        """
        更新人像名称
        
        Args:
            face_id: 人像ID
            new_name: 新名称
            
        Returns:
            更新成功返回 True
        """
        try:
            # 验证新名称
            if not new_name or len(new_name) == 0:
                raise ValueError("名称不能为空")
            if len(new_name) > 100:
                raise ValueError("名称长度不能超过100字符")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE library_faces
                SET name = ?
                WHERE id = ?
            ''', (new_name, face_id))
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_affected > 0:
                logger.info(f"人像名称已更新: {face_id} -> {new_name}")
                return True
            else:
                logger.warning(f"人像不存在: {face_id}")
                return False
            
        except Exception as e:
            logger.error(f"更新人像失败: {str(e)}")
            return False
    
    def deleteFace(self, face_id: str, thumbnail_path: Optional[str] = None) -> bool:
        """
        删除人像及其缩略图
        
        Args:
            face_id: 人像ID
            thumbnail_path: 缩略图路径（可选，如果不提供则从数据库查询）
            
        Returns:
            删除成功返回 True
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 如果没有提供缩略图路径，先查询
            if not thumbnail_path:
                cursor.execute('''
                    SELECT thumbnail_path FROM library_faces WHERE id = ?
                ''', (face_id,))
                row = cursor.fetchone()
                if row:
                    thumbnail_path = row[0]
            
            # 删除数据库记录
            cursor.execute('''
                DELETE FROM library_faces WHERE id = ?
            ''', (face_id,))
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            # 删除缩略图文件
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    os.remove(thumbnail_path)
                    logger.info(f"缩略图已删除: {thumbnail_path}")
                except Exception as e:
                    logger.warning(f"删除缩略图失败: {str(e)}")
            
            if rows_affected > 0:
                logger.info(f"人像已删除: {face_id}")
                return True
            else:
                logger.warning(f"人像不存在: {face_id}")
                return False
            
        except Exception as e:
            logger.error(f"删除人像失败: {str(e)}")
            return False
    
    def count(self) -> int:
        """
        获取人像库中的人像总数
        
        Returns:
            人像数量
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM library_faces')
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"统计人像数量失败: {str(e)}")
            return 0
