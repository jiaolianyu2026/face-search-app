"""
Cache Module for storing and retrieving face features.
Caches face detection results to avoid redundant computation.
Uses file path + modification time as cache key and MD5 hash for validation.
"""

import os
import hashlib
import json
import sqlite3
from typing import List, Optional
from pathlib import Path

from models import Face, CacheEntry
from config import CACHE_DIR


class CacheModule:
    """
    Module for caching face detection features.
    
    Uses SQLite database to store cached face features with file metadata.
    Cache key is based on file path + modification time.
    File hash (MD5) is used to verify file hasn't been modified.
    """
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        """
        Initialize the CacheModule.
        
        Args:
            cache_dir: Directory to store cache database
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # SQLite database path
        self.db_path = os.path.join(cache_dir, 'face_cache.db')
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with cache table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_cache (
                file_path TEXT PRIMARY KEY,
                file_hash TEXT NOT NULL,
                modification_time REAL NOT NULL,
                features_json TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _compute_file_hash(self, file_path: str) -> str:
        """
        Compute MD5 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MD5 hash as hexadecimal string
        """
        md5_hash = hashlib.md5()
        
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            # If we can't read the file, return empty hash
            return ''
    
    def _get_file_mtime(self, file_path: str) -> float:
        """
        Get file modification time.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Modification time as timestamp
        """
        try:
            return os.path.getmtime(file_path)
        except Exception:
            return 0.0
    
    def _serialize_faces(self, faces: List[Face]) -> str:
        """
        Serialize list of Face objects to JSON string.
        
        Args:
            faces: List of Face objects
            
        Returns:
            JSON string representation
        """
        faces_data = []
        for face in faces:
            faces_data.append({
                'faceId': face.faceId,
                'boundingBox': face.boundingBox,
                'features': face.features
            })
        return json.dumps(faces_data)
    
    def _deserialize_faces(self, faces_json: str) -> List[Face]:
        """
        Deserialize JSON string to list of Face objects.
        
        Args:
            faces_json: JSON string representation
            
        Returns:
            List of Face objects
        """
        faces_data = json.loads(faces_json)
        faces = []
        for face_data in faces_data:
            faces.append(Face(
                faceId=face_data['faceId'],
                boundingBox=face_data['boundingBox'],
                features=face_data['features']
            ))
        return faces
    
    def getCachedFeatures(self, imagePath: str) -> Optional[CacheEntry]:
        """
        Get cached face features for an image.
        
        Validates that the file hasn't been modified by checking:
        1. File modification time matches cached value
        2. File hash (MD5) matches cached value
        
        Args:
            imagePath: Path to the image file
            
        Returns:
            CacheEntry if cache is valid and file hasn't been modified,
            None otherwise
        """
        # Check if file exists
        if not os.path.exists(imagePath):
            return None
        
        # Get current file metadata
        current_mtime = self._get_file_mtime(imagePath)
        current_hash = self._compute_file_hash(imagePath)
        
        if not current_hash:
            return None
        
        # Query database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_hash, modification_time, features_json, timestamp
            FROM face_cache
            WHERE file_path = ?
        ''', (imagePath,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        cached_hash, cached_mtime, features_json, timestamp = row
        
        # Validate cache: check if file has been modified
        if cached_hash != current_hash or cached_mtime != current_mtime:
            # File has been modified, cache is invalid
            return None
        
        # Deserialize faces
        try:
            faces = self._deserialize_faces(features_json)
            return CacheEntry(
                features=faces,
                timestamp=timestamp,
                fileHash=cached_hash
            )
        except Exception:
            # If deserialization fails, cache is invalid
            return None
    
    def setCachedFeatures(self, imagePath: str, faces: List[Face]) -> None:
        """
        Cache face features for an image.
        
        Stores the features along with file metadata (path, modification time, hash).
        If cache entry already exists for this path, it will be updated.
        
        Args:
            imagePath: Path to the image file
            faces: List of detected Face objects
        """
        # Check if file exists
        if not os.path.exists(imagePath):
            return
        
        # Get file metadata
        mtime = self._get_file_mtime(imagePath)
        file_hash = self._compute_file_hash(imagePath)
        
        if not file_hash:
            return
        
        # Serialize faces
        features_json = self._serialize_faces(faces)
        
        # Get current timestamp
        import time
        timestamp = time.time()
        
        # Insert or update cache entry
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO face_cache
            (file_path, file_hash, modification_time, features_json, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (imagePath, file_hash, mtime, features_json, timestamp))
        
        conn.commit()
        conn.close()
    
    def clearCache(self) -> int:
        """
        Clear all cached entries.
        
        Returns:
            Number of entries cleared
        """
        # Get count before clearing
        count = self.get_cache_size()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM face_cache')
        conn.commit()
        conn.close()
        
        return count
    
    def get_cache_size(self) -> int:
        """
        Get number of cached entries.
        
        Returns:
            Number of entries in cache
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM face_cache')
        count = cursor.fetchone()[0]
        conn.close()
        return count
