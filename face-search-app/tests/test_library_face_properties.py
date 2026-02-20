# -*- coding: utf-8 -*-
"""
Property-based tests for LibraryFace data model.
Uses hypothesis to generate random test cases and verify validation properties.

**Feature: face-library-management**
**Validates: Requirements 7.3, 7.4, 7.5**
"""

import pytest
import os
import sys
import uuid
from datetime import datetime
from hypothesis import given, strategies as st, settings, assume

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models import LibraryFace


# Custom strategies for test data generation
def valid_names():
    """Generate valid names (1-100 characters)."""
    return st.text(min_size=1, max_size=100, alphabet=st.characters(
        blacklist_categories=('Cc', 'Cs'),  # Exclude control characters
        blacklist_characters='\x00'
    ))


def invalid_empty_names():
    """Generate invalid empty names."""
    return st.just("")


def invalid_long_names():
    """Generate invalid names (>100 characters)."""
    return st.text(min_size=101, max_size=200)


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


def invalid_feature_vectors():
    """Generate invalid feature vectors (not 128-dimensional)."""
    return st.one_of(
        st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=0, max_size=127),
        st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=129, max_size=256)
    )


def valid_uuids():
    """Generate valid UUID strings."""
    return st.uuids().map(str)


def invalid_uuids():
    """Generate invalid UUID strings."""
    return st.one_of(
        st.text(min_size=1, max_size=20),  # Random text
        st.just("not-a-uuid"),
        st.just("12345"),
        st.just(""),
    )


def valid_iso_timestamps():
    """Generate valid ISO 8601 timestamp strings."""
    return st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ).map(lambda dt: dt.isoformat())


class TestProperty22_NameFieldValidation:
    """
    Property 22: 名称字段验证
    
    对于任意空字符串或长度超过 100 字符的名称，创建 LibraryFace 应该抛出 ValueError 异常。
    
    **Validates: Requirements 7.3**
    """
    
    @given(
        name=valid_names(),
        features=valid_feature_vectors(),
        uuid_str=valid_uuids(),
        timestamp=valid_iso_timestamps()
    )
    @settings(max_examples=5, deadline=1000)
    def test_valid_names_are_accepted(self, name, features, uuid_str, timestamp):
        """
        Property: Valid names (1-100 characters) should be accepted.
        
        **Validates: Requirements 7.3**
        """
        # Attempt to create LibraryFace with valid name
        try:
            face = LibraryFace(
                id=uuid_str,
                name=name,
                feature_vector=features,
                thumbnail_path="/path/to/thumbnail.jpg",
                created_at=timestamp
            )
            
            # Verify the face was created successfully
            assert face.name == name, "Name should be stored correctly"
            assert len(face.name) >= 1, "Name should have at least 1 character"
            assert len(face.name) <= 100, "Name should have at most 100 characters"
            
        except ValueError as e:
            # If a ValueError is raised, it should not be about the name
            # (it might be about other fields if the generated data is edge-case)
            error_msg = str(e).lower()
            assert "name" not in error_msg, \
                f"Valid name '{name}' (length {len(name)}) should not raise name-related error: {e}"
    
    @given(
        features=valid_feature_vectors(),
        uuid_str=valid_uuids(),
        timestamp=valid_iso_timestamps()
    )
    @settings(max_examples=5, deadline=1000)
    def test_empty_names_are_rejected(self, features, uuid_str, timestamp):
        """
        Property: Empty names should be rejected with ValueError.
        
        **Validates: Requirements 7.3**
        """
        # Attempt to create LibraryFace with empty name
        with pytest.raises(ValueError) as exc_info:
            LibraryFace(
                id=uuid_str,
                name="",
                feature_vector=features,
                thumbnail_path="/path/to/thumbnail.jpg",
                created_at=timestamp
            )
        
        # Verify the error message mentions name
        error_msg = str(exc_info.value).lower()
        assert "name" in error_msg, \
            f"Error message should mention 'name', got: {exc_info.value}"
        assert "empty" in error_msg or "cannot" in error_msg, \
            f"Error message should indicate name cannot be empty, got: {exc_info.value}"
    
    @given(
        name=invalid_long_names(),
        features=valid_feature_vectors(),
        uuid_str=valid_uuids(),
        timestamp=valid_iso_timestamps()
    )
    @settings(max_examples=5, deadline=1000)
    def test_long_names_are_rejected(self, name, features, uuid_str, timestamp):
        """
        Property: Names longer than 100 characters should be rejected with ValueError.
        
        **Validates: Requirements 7.3**
        """
        # Ensure name is actually longer than 100 characters
        assume(len(name) > 100)
        
        # Attempt to create LibraryFace with long name
        with pytest.raises(ValueError) as exc_info:
            LibraryFace(
                id=uuid_str,
                name=name,
                feature_vector=features,
                thumbnail_path="/path/to/thumbnail.jpg",
                created_at=timestamp
            )
        
        # Verify the error message mentions name and length
        error_msg = str(exc_info.value).lower()
        assert "name" in error_msg, \
            f"Error message should mention 'name', got: {exc_info.value}"
        assert ("100" in str(exc_info.value) or "exceed" in error_msg or "length" in error_msg), \
            f"Error message should mention length limit, got: {exc_info.value}"


class TestProperty23_FeatureVectorDimensionValidation:
    """
    Property 23: 特征向量维度验证
    
    对于任意非 128 维的特征向量，创建 LibraryFace 应该抛出 ValueError 异常。
    
    **Validates: Requirements 7.4**
    """
    
    @given(
        name=valid_names(),
        features=valid_feature_vectors(),
        uuid_str=valid_uuids(),
        timestamp=valid_iso_timestamps()
    )
    @settings(max_examples=5, deadline=1000)
    def test_128_dimensional_vectors_are_accepted(self, name, features, uuid_str, timestamp):
        """
        Property: 128-dimensional feature vectors should be accepted.
        
        **Validates: Requirements 7.4**
        """
        # Verify the generated features are exactly 128-dimensional
        assert len(features) == 128, "Test data should be 128-dimensional"
        
        # Attempt to create LibraryFace with valid feature vector
        try:
            face = LibraryFace(
                id=uuid_str,
                name=name,
                feature_vector=features,
                thumbnail_path="/path/to/thumbnail.jpg",
                created_at=timestamp
            )
            
            # Verify the feature vector was stored correctly
            assert len(face.feature_vector) == 128, \
                "Feature vector should be 128-dimensional"
            assert face.feature_vector == features, \
                "Feature vector should be stored correctly"
            
        except ValueError as e:
            # If a ValueError is raised, it should not be about feature vector dimension
            error_msg = str(e).lower()
            assert "feature" not in error_msg and "128" not in error_msg, \
                f"Valid 128-dimensional feature vector should not raise error: {e}"
    
    @given(
        name=valid_names(),
        features=invalid_feature_vectors(),
        uuid_str=valid_uuids(),
        timestamp=valid_iso_timestamps()
    )
    @settings(max_examples=5, deadline=1000)
    def test_non_128_dimensional_vectors_are_rejected(self, name, features, uuid_str, timestamp):
        """
        Property: Non-128-dimensional feature vectors should be rejected with ValueError.
        
        **Validates: Requirements 7.4**
        """
        # Ensure features are not 128-dimensional
        assume(len(features) != 128)
        
        # Attempt to create LibraryFace with invalid feature vector
        with pytest.raises(ValueError) as exc_info:
            LibraryFace(
                id=uuid_str,
                name=name,
                feature_vector=features,
                thumbnail_path="/path/to/thumbnail.jpg",
                created_at=timestamp
            )
        
        # Verify the error message mentions feature vector and dimension
        error_msg = str(exc_info.value).lower()
        assert ("feature" in error_msg or "vector" in error_msg), \
            f"Error message should mention 'feature' or 'vector', got: {exc_info.value}"
        assert "128" in str(exc_info.value), \
            f"Error message should mention '128', got: {exc_info.value}"
        assert str(len(features)) in str(exc_info.value), \
            f"Error message should mention actual dimension {len(features)}, got: {exc_info.value}"
    
    @given(
        name=valid_names(),
        uuid_str=valid_uuids(),
        timestamp=valid_iso_timestamps(),
        dimension=st.integers(min_value=0, max_value=256)
    )
    @settings(max_examples=5, deadline=1000)
    def test_various_wrong_dimensions_are_rejected(self, name, uuid_str, timestamp, dimension):
        """
        Property: Any dimension other than 128 should be rejected.
        
        **Validates: Requirements 7.4**
        """
        # Skip if dimension is 128 (valid case)
        assume(dimension != 128)
        
        # Create feature vector with wrong dimension
        features = [0.5] * dimension
        
        # Attempt to create LibraryFace
        with pytest.raises(ValueError) as exc_info:
            LibraryFace(
                id=uuid_str,
                name=name,
                feature_vector=features,
                thumbnail_path="/path/to/thumbnail.jpg",
                created_at=timestamp
            )
        
        # Verify error message
        assert "128" in str(exc_info.value), \
            f"Error should mention required dimension 128, got: {exc_info.value}"


class TestProperty24_UUIDFormatValidation:
    """
    Property 24: UUID 格式验证
    
    对于任意生成的人像 ID，ID 应该符合标准 UUID 格式（8-4-4-4-12 十六进制字符）。
    
    **Validates: Requirements 7.5**
    """
    
    @given(
        name=valid_names(),
        features=valid_feature_vectors(),
        uuid_str=valid_uuids(),
        timestamp=valid_iso_timestamps()
    )
    @settings(max_examples=5, deadline=1000)
    def test_valid_uuids_are_accepted(self, name, features, uuid_str, timestamp):
        """
        Property: Valid UUID strings should be accepted.
        
        **Validates: Requirements 7.5**
        """
        # Attempt to create LibraryFace with valid UUID
        try:
            face = LibraryFace(
                id=uuid_str,
                name=name,
                feature_vector=features,
                thumbnail_path="/path/to/thumbnail.jpg",
                created_at=timestamp
            )
            
            # Verify the UUID was stored correctly
            assert face.id == uuid_str, "UUID should be stored correctly"
            
            # Verify the UUID can be parsed
            parsed_uuid = uuid.UUID(face.id)
            assert str(parsed_uuid) == uuid_str, "UUID should be valid and parseable"
            
        except ValueError as e:
            # If a ValueError is raised, it should not be about the UUID
            error_msg = str(e).lower()
            assert "uuid" not in error_msg and "id" not in error_msg, \
                f"Valid UUID '{uuid_str}' should not raise UUID-related error: {e}"
    
    @given(
        name=valid_names(),
        features=valid_feature_vectors(),
        invalid_id=invalid_uuids(),
        timestamp=valid_iso_timestamps()
    )
    @settings(max_examples=5, deadline=1000)
    def test_invalid_uuids_are_rejected(self, name, features, invalid_id, timestamp):
        """
        Property: Invalid UUID strings should be rejected with ValueError.
        
        **Validates: Requirements 7.5**
        """
        # Verify the ID is actually invalid
        try:
            uuid.UUID(invalid_id)
            assume(False)  # Skip if it's actually a valid UUID
        except (ValueError, AttributeError):
            pass  # Good, it's invalid
        
        # Attempt to create LibraryFace with invalid UUID
        with pytest.raises(ValueError) as exc_info:
            LibraryFace(
                id=invalid_id,
                name=name,
                feature_vector=features,
                thumbnail_path="/path/to/thumbnail.jpg",
                created_at=timestamp
            )
        
        # Verify the error message mentions UUID or ID
        error_msg = str(exc_info.value).lower()
        assert ("uuid" in error_msg or "id" in error_msg), \
            f"Error message should mention 'UUID' or 'ID', got: {exc_info.value}"
    
    @given(
        name=valid_names(),
        features=valid_feature_vectors(),
        timestamp=valid_iso_timestamps()
    )
    @settings(max_examples=5, deadline=1000)
    def test_factory_method_generates_valid_uuids(self, name, features, timestamp):
        """
        Property: The factory method should always generate valid UUIDs.
        
        **Validates: Requirements 7.5**
        """
        # Create LibraryFace using factory method
        face = LibraryFace.create(
            name=name,
            feature_vector=features,
            thumbnail_path="/path/to/thumbnail.jpg"
        )
        
        # Verify the ID is a valid UUID
        assert face.id is not None, "ID should not be None"
        assert isinstance(face.id, str), "ID should be a string"
        
        # Verify UUID format by parsing it
        try:
            parsed_uuid = uuid.UUID(face.id)
            assert str(parsed_uuid) == face.id, "ID should be a valid UUID string"
        except ValueError as e:
            pytest.fail(f"Factory method generated invalid UUID '{face.id}': {e}")
        
        # Verify UUID format pattern (8-4-4-4-12)
        parts = face.id.split('-')
        assert len(parts) == 5, \
            f"UUID should have 5 parts separated by hyphens, got {len(parts)}"
        assert len(parts[0]) == 8, f"First part should be 8 chars, got {len(parts[0])}"
        assert len(parts[1]) == 4, f"Second part should be 4 chars, got {len(parts[1])}"
        assert len(parts[2]) == 4, f"Third part should be 4 chars, got {len(parts[2])}"
        assert len(parts[3]) == 4, f"Fourth part should be 4 chars, got {len(parts[3])}"
        assert len(parts[4]) == 12, f"Fifth part should be 12 chars, got {len(parts[4])}"
        
        # Verify all parts are hexadecimal
        for i, part in enumerate(parts):
            try:
                int(part, 16)
            except ValueError:
                pytest.fail(f"UUID part {i} '{part}' is not hexadecimal")
    
    @given(
        name=valid_names(),
        features=valid_feature_vectors()
    )
    @settings(max_examples=5, deadline=1000)
    def test_multiple_factory_calls_generate_unique_uuids(self, name, features):
        """
        Property: Multiple factory method calls should generate unique UUIDs.
        
        **Validates: Requirements 7.5**
        """
        # Create multiple LibraryFace instances
        faces = []
        num_faces = 10
        
        for _ in range(num_faces):
            face = LibraryFace.create(
                name=name,
                feature_vector=features,
                thumbnail_path="/path/to/thumbnail.jpg"
            )
            faces.append(face)
        
        # Verify all UUIDs are unique
        face_ids = [face.id for face in faces]
        unique_ids = set(face_ids)
        
        assert len(unique_ids) == num_faces, \
            f"All {num_faces} UUIDs should be unique, got {len(unique_ids)} unique IDs"
        
        # Verify all are valid UUIDs
        for face_id in face_ids:
            try:
                uuid.UUID(face_id)
            except ValueError as e:
                pytest.fail(f"Generated ID '{face_id}' is not a valid UUID: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
