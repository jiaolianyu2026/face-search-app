"""
Unit tests for CacheModule.
Tests caching functionality including cache hits, misses, and invalidation.
"""

import os
import sys
import tempfile
import shutil
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from cache_module import CacheModule
from models import Face


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def cache_module(temp_cache_dir):
    """Create a CacheModule instance with temporary cache directory."""
    return CacheModule(cache_dir=temp_cache_dir)


@pytest.fixture
def temp_image_file():
    """Create a temporary image file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False)
    temp_file.write(b'fake image data')
    temp_file.close()
    yield temp_file.name
    # Cleanup
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


@pytest.fixture
def sample_faces():
    """Create sample Face objects for testing."""
    return [
        Face(
            faceId='face1',
            boundingBox={'x': 10, 'y': 20, 'width': 100, 'height': 100},
            features=[0.1] * 128
        ),
        Face(
            faceId='face2',
            boundingBox={'x': 150, 'y': 50, 'width': 80, 'height': 80},
            features=[0.2] * 128
        )
    ]


def test_cache_initialization(cache_module, temp_cache_dir):
    """Test that cache module initializes correctly."""
    assert os.path.exists(temp_cache_dir)
    assert os.path.exists(cache_module.db_path)
    assert cache_module.get_cache_size() == 0


def test_set_and_get_cached_features(cache_module, temp_image_file, sample_faces):
    """Test caching and retrieving face features."""
    # Cache features
    cache_module.setCachedFeatures(temp_image_file, sample_faces)
    
    # Retrieve cached features
    cache_entry = cache_module.getCachedFeatures(temp_image_file)
    
    assert cache_entry is not None
    assert len(cache_entry.features) == 2
    assert cache_entry.features[0].faceId == 'face1'
    assert cache_entry.features[1].faceId == 'face2'
    assert cache_entry.fileHash != ''


def test_cache_miss_for_nonexistent_file(cache_module):
    """Test that cache returns None for non-existent files."""
    result = cache_module.getCachedFeatures('/nonexistent/file.jpg')
    assert result is None


def test_cache_miss_for_uncached_file(cache_module, temp_image_file):
    """Test that cache returns None for files that haven't been cached."""
    result = cache_module.getCachedFeatures(temp_image_file)
    assert result is None


def test_cache_invalidation_on_file_modification(cache_module, temp_image_file, sample_faces):
    """Test that cache is invalidated when file is modified."""
    # Cache features
    cache_module.setCachedFeatures(temp_image_file, sample_faces)
    
    # Verify cache hit
    cache_entry = cache_module.getCachedFeatures(temp_image_file)
    assert cache_entry is not None
    
    # Wait a bit to ensure modification time changes
    time.sleep(0.1)
    
    # Modify the file
    with open(temp_image_file, 'wb') as f:
        f.write(b'modified image data')
    
    # Cache should be invalidated
    cache_entry = cache_module.getCachedFeatures(temp_image_file)
    assert cache_entry is None


def test_cache_update_on_recache(cache_module, temp_image_file, sample_faces):
    """Test that caching the same file again updates the cache."""
    # Cache features
    cache_module.setCachedFeatures(temp_image_file, sample_faces)
    assert cache_module.get_cache_size() == 1
    
    # Cache again with different features
    new_faces = [
        Face(
            faceId='face3',
            boundingBox={'x': 0, 'y': 0, 'width': 50, 'height': 50},
            features=[0.3] * 128
        )
    ]
    cache_module.setCachedFeatures(temp_image_file, new_faces)
    
    # Should still have only one entry
    assert cache_module.get_cache_size() == 1
    
    # Should retrieve updated features
    cache_entry = cache_module.getCachedFeatures(temp_image_file)
    assert cache_entry is not None
    assert len(cache_entry.features) == 1
    assert cache_entry.features[0].faceId == 'face3'


def test_cache_multiple_files(cache_module, sample_faces):
    """Test caching features for multiple files."""
    # Create multiple temp files
    temp_files = []
    for i in range(3):
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False)
        temp_file.write(f'image data {i}'.encode())
        temp_file.close()
        temp_files.append(temp_file.name)
    
    try:
        # Cache features for each file
        for temp_file in temp_files:
            cache_module.setCachedFeatures(temp_file, sample_faces)
        
        # Verify cache size
        assert cache_module.get_cache_size() == 3
        
        # Verify each file can be retrieved
        for temp_file in temp_files:
            cache_entry = cache_module.getCachedFeatures(temp_file)
            assert cache_entry is not None
            assert len(cache_entry.features) == 2
    finally:
        # Cleanup
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


def test_clear_cache(cache_module, temp_image_file, sample_faces):
    """Test clearing all cached entries."""
    # Cache some features
    cache_module.setCachedFeatures(temp_image_file, sample_faces)
    assert cache_module.get_cache_size() == 1
    
    # Clear cache
    cache_module.clearCache()
    assert cache_module.get_cache_size() == 0
    
    # Verify cache miss
    cache_entry = cache_module.getCachedFeatures(temp_image_file)
    assert cache_entry is None


def test_cache_with_empty_faces_list(cache_module, temp_image_file):
    """Test caching with empty faces list."""
    cache_module.setCachedFeatures(temp_image_file, [])
    
    cache_entry = cache_module.getCachedFeatures(temp_image_file)
    assert cache_entry is not None
    assert len(cache_entry.features) == 0


def test_cache_preserves_face_data(cache_module, temp_image_file):
    """Test that all face data is preserved in cache."""
    faces = [
        Face(
            faceId='test_face',
            boundingBox={'x': 123, 'y': 456, 'width': 789, 'height': 101},
            features=[float(i) / 128 for i in range(128)]
        )
    ]
    
    cache_module.setCachedFeatures(temp_image_file, faces)
    cache_entry = cache_module.getCachedFeatures(temp_image_file)
    
    assert cache_entry is not None
    assert len(cache_entry.features) == 1
    
    cached_face = cache_entry.features[0]
    assert cached_face.faceId == 'test_face'
    assert cached_face.boundingBox == {'x': 123, 'y': 456, 'width': 789, 'height': 101}
    assert len(cached_face.features) == 128
    assert cached_face.features[0] == 0.0
    assert cached_face.features[127] == 127 / 128
