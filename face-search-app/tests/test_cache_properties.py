# -*- coding: utf-8 -*-
"""
Property-based tests for CacheModule.
Tests cache consistency properties using hypothesis.

**Feature: face-recognition-search, Property 18: 缓存一致�?*
**Validates: Requirements 9.4**
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
from hypothesis import given, strategies as st, settings
from cache_module import CacheModule
from models import Face


# Strategy for generating valid bounding boxes
@st.composite
def bounding_box_strategy(draw):
    """Generate valid bounding box dictionaries."""
    return {
        'x': draw(st.integers(min_value=0, max_value=1000)),
        'y': draw(st.integers(min_value=0, max_value=1000)),
        'width': draw(st.integers(min_value=1, max_value=500)),
        'height': draw(st.integers(min_value=1, max_value=500))
    }


# Strategy for generating valid Face objects
@st.composite
def face_strategy(draw):
    """Generate valid Face objects."""
    face_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-')))
    bbox = draw(bounding_box_strategy())
    # Generate 128-dimensional feature vector
    features = draw(st.lists(
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=128,
        max_size=128
    ))
    return Face(faceId=face_id, boundingBox=bbox, features=features)


@settings(max_examples=3, deadline=None)
@given(faces=st.lists(face_strategy(), min_size=0, max_size=5))
def test_property_cache_consistency_unmodified_file(faces):
    """
    **Property 18: 缓存一致�?*
    **Validates: Requirements 9.4**
    
    Property: For any image file, if the file content is not modified 
    (based on file hash and modification time), the second processing 
    should use cached feature data instead of recomputing.
    
    This test verifies that:
    1. After caching features, they can be retrieved
    2. Retrieved features match the original features
    3. Cache is used for unmodified files (no recomputation needed)
    """
    # Create temporary cache directory and module
    temp_cache_dir = tempfile.mkdtemp()
    cache_module = CacheModule(cache_dir=temp_cache_dir)
    
    # Create temporary image file
    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False)
    temp_file.write(b'test image data for property testing')
    temp_file.close()
    temp_image_file = temp_file.name
    
    try:
        # Cache the features
        cache_module.setCachedFeatures(temp_image_file, faces)
        
        # Retrieve cached features
        cache_entry = cache_module.getCachedFeatures(temp_image_file)
        
        # Verify cache hit
        assert cache_entry is not None, "Cache should return entry for unmodified file"
        
        # Verify number of faces matches
        assert len(cache_entry.features) == len(faces), \
            f"Cached features count mismatch: expected {len(faces)}, got {len(cache_entry.features)}"
        
        # Verify each face is preserved correctly
        for i, (original_face, cached_face) in enumerate(zip(faces, cache_entry.features)):
            assert cached_face.faceId == original_face.faceId, \
                f"Face {i} ID mismatch: expected {original_face.faceId}, got {cached_face.faceId}"
            assert cached_face.boundingBox == original_face.boundingBox, \
                f"Face {i} bounding box mismatch"
            assert len(cached_face.features) == 128, \
                f"Face {i} features dimension mismatch"
            assert cached_face.features == original_face.features, \
                f"Face {i} features mismatch"
        
        # Verify file hash is stored
        assert cache_entry.fileHash != '', "Cache entry should have file hash"
        
        # Verify timestamp is reasonable
        assert cache_entry.timestamp > 0, "Cache entry should have valid timestamp"
    
    finally:
        # Cleanup
        if os.path.exists(temp_image_file):
            os.unlink(temp_image_file)
        shutil.rmtree(temp_cache_dir, ignore_errors=True)


@settings(max_examples=3, deadline=None)
@given(
    faces1=st.lists(face_strategy(), min_size=0, max_size=3),
    faces2=st.lists(face_strategy(), min_size=0, max_size=3),
    file_content1=st.binary(min_size=10, max_size=1000),
    file_content2=st.binary(min_size=10, max_size=1000)
)
def test_property_cache_invalidation_on_modification(faces1, faces2, file_content1, file_content2):
    """
    **Property 18: 缓存一致�?(Invalidation)**
    **Validates: Requirements 9.4**
    
    Property: For any image file, if the file content is modified,
    the cache should be invalidated and return None, forcing recomputation.
    
    This test verifies that:
    1. Cache works for original file
    2. After file modification, cache is invalidated
    3. New features can be cached after modification
    """
    # Skip if file contents are the same
    if file_content1 == file_content2:
        return
    
    # Create temporary cache directory and module
    temp_cache_dir = tempfile.mkdtemp()
    cache_module = CacheModule(cache_dir=temp_cache_dir)
    
    # Create temporary file with first content
    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False)
    temp_file.write(file_content1)
    temp_file.close()
    
    try:
        # Cache features for original file
        cache_module.setCachedFeatures(temp_file.name, faces1)
        
        # Verify cache hit
        cache_entry = cache_module.getCachedFeatures(temp_file.name)
        assert cache_entry is not None, "Cache should work for original file"
        assert len(cache_entry.features) == len(faces1)
        
        # Wait to ensure modification time changes
        time.sleep(0.1)
        
        # Modify the file
        with open(temp_file.name, 'wb') as f:
            f.write(file_content2)
        
        # Cache should be invalidated
        cache_entry = cache_module.getCachedFeatures(temp_file.name)
        assert cache_entry is None, \
            "Cache should be invalidated after file modification"
        
        # Should be able to cache new features
        cache_module.setCachedFeatures(temp_file.name, faces2)
        cache_entry = cache_module.getCachedFeatures(temp_file.name)
        assert cache_entry is not None, "Should be able to cache after modification"
        assert len(cache_entry.features) == len(faces2)
        
    finally:
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        shutil.rmtree(temp_cache_dir, ignore_errors=True)


@settings(max_examples=3, deadline=None)
@given(faces=st.lists(face_strategy(), min_size=1, max_size=3))
def test_property_cache_idempotency(faces):
    """
    **Property 18: 缓存一致�?(Idempotency)**
    **Validates: Requirements 9.4**
    
    Property: Caching the same features multiple times for an unmodified file
    should be idempotent - retrieving the cache should always return the same data.
    """
    # Create temporary cache directory and module
    temp_cache_dir = tempfile.mkdtemp()
    cache_module = CacheModule(cache_dir=temp_cache_dir)
    
    # Create temporary image file
    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False)
    temp_file.write(b'test image data for idempotency testing')
    temp_file.close()
    temp_image_file = temp_file.name
    
    try:
        # Cache features multiple times
        for _ in range(3):
            cache_module.setCachedFeatures(temp_image_file, faces)
        
        # Retrieve cache multiple times
        results = []
        for _ in range(3):
            cache_entry = cache_module.getCachedFeatures(temp_image_file)
            assert cache_entry is not None
            results.append(cache_entry)
        
        # All results should have the same number of faces
        for result in results:
            assert len(result.features) == len(faces)
        
        # All results should have the same file hash
        file_hashes = [result.fileHash for result in results]
        assert len(set(file_hashes)) == 1, "File hash should be consistent"
        
        # All results should have matching face data
        for result in results:
            for i, (original_face, cached_face) in enumerate(zip(faces, result.features)):
                assert cached_face.faceId == original_face.faceId
                assert cached_face.boundingBox == original_face.boundingBox
                assert cached_face.features == original_face.features
    
    finally:
        # Cleanup
        if os.path.exists(temp_image_file):
            os.unlink(temp_image_file)
        shutil.rmtree(temp_cache_dir, ignore_errors=True)


@settings(max_examples=3, deadline=None)
@given(
    faces_list=st.lists(
        st.lists(face_strategy(), min_size=0, max_size=3),
        min_size=2,
        max_size=5
    )
)
def test_property_cache_independence(faces_list):
    """
    **Property 18: 缓存一致�?(Independence)**
    **Validates: Requirements 9.4**
    
    Property: Caching features for different files should be independent.
    Caching or modifying one file should not affect the cache of other files.
    """
    # Create temporary cache directory and module
    temp_cache_dir = tempfile.mkdtemp()
    cache_module = CacheModule(cache_dir=temp_cache_dir)
    
    # Create multiple temporary files
    temp_files = []
    for i in range(len(faces_list)):
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False)
        temp_file.write(f'image data {i}'.encode())
        temp_file.close()
        temp_files.append(temp_file.name)
    
    try:
        # Cache features for each file
        for temp_file, faces in zip(temp_files, faces_list):
            cache_module.setCachedFeatures(temp_file, faces)
        
        # Verify all caches work
        for temp_file, faces in zip(temp_files, faces_list):
            cache_entry = cache_module.getCachedFeatures(temp_file)
            assert cache_entry is not None
            assert len(cache_entry.features) == len(faces)
        
        # Modify one file
        if len(temp_files) > 0:
            time.sleep(0.1)
            with open(temp_files[0], 'wb') as f:
                f.write(b'modified data')
            
            # First file cache should be invalidated
            cache_entry = cache_module.getCachedFeatures(temp_files[0])
            assert cache_entry is None, "Modified file cache should be invalidated"
            
            # Other files' caches should still work
            for temp_file, faces in zip(temp_files[1:], faces_list[1:]):
                cache_entry = cache_module.getCachedFeatures(temp_file)
                assert cache_entry is not None, \
                    "Other files' caches should not be affected"
                assert len(cache_entry.features) == len(faces)
    
    finally:
        # Cleanup
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        shutil.rmtree(temp_cache_dir, ignore_errors=True)

