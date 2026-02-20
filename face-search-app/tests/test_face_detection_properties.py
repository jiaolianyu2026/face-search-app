# -*- coding: utf-8 -*-
"""
Property-based tests for face detection functionality.
Uses hypothesis to generate random test cases and verify universal properties.

**Feature: face-recognition-search, Property 4: 人脸检测结果完整�?*
**Validates: Requirements 2.3, 2.5**
"""

import pytest
import os
import sys
import io
import numpy as np
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from PIL import Image, ImageDraw

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from face_detection import FaceDetectionModule
from models import Face, DetectionResult


class TestProperty4_FaceDetectionResultCompleteness:
    """
    Property 4: 人脸检测结果完整�?
    
    对于任何检测到的人脸，结果应当包含边界框位置信息和128维特征向�?
    
    **Validates: Requirements 2.3, 2.5**
    """
    
    def create_test_image_with_pattern(self, width, height, num_patterns, tmp_path):
        """
        Create a test image with face-like patterns.
        
        Args:
            width: Image width
            height: Image height
            num_patterns: Number of face-like patterns to draw
            tmp_path: Temporary directory path
            
        Returns:
            Path to the created image file
        """
        # Create base image
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw face-like patterns
        for i in range(num_patterns):
            # Calculate position for this pattern
            pattern_size = min(width, height) // (num_patterns + 1)
            x_offset = (i + 1) * (width // (num_patterns + 2))
            y_offset = height // 2 - pattern_size // 2
            
            # Draw a simple face-like pattern
            # Face outline (ellipse)
            draw.ellipse(
                [x_offset, y_offset, x_offset + pattern_size, y_offset + pattern_size],
                fill='peachpuff',
                outline='black'
            )
            
            # Eyes
            eye_y = y_offset + pattern_size // 3
            left_eye_x = x_offset + pattern_size // 3
            right_eye_x = x_offset + 2 * pattern_size // 3
            eye_size = pattern_size // 10
            
            draw.ellipse(
                [left_eye_x - eye_size, eye_y - eye_size, 
                 left_eye_x + eye_size, eye_y + eye_size],
                fill='black'
            )
            draw.ellipse(
                [right_eye_x - eye_size, eye_y - eye_size,
                 right_eye_x + eye_size, eye_y + eye_size],
                fill='black'
            )
            
            # Mouth
            mouth_y = y_offset + 2 * pattern_size // 3
            draw.arc(
                [x_offset + pattern_size // 4, mouth_y - pattern_size // 8,
                 x_offset + 3 * pattern_size // 4, mouth_y + pattern_size // 8],
                0, 180, fill='black', width=2
            )
        
        # Save image
        img_path = tmp_path / f"test_pattern_{width}x{height}_{num_patterns}.jpg"
        img.save(img_path)
        return str(img_path)
    
    @given(
        width=st.integers(min_value=200, max_value=800),
        height=st.integers(min_value=200, max_value=800),
        num_patterns=st.integers(min_value=1, max_value=3)
    )
    @settings(
        max_examples=3, 
        deadline=10000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_all_detected_faces_have_complete_structure(
        self, tmp_path, width, height, num_patterns
    ):
        """
        Property: For any detection result, all detected faces must have complete data.
        
        This property verifies that every face in the detection result contains:
        1. A unique faceId (non-empty string)
        2. A bounding box with x, y, width, height (all non-negative)
        3. A 128-dimensional feature vector (all floats)
        
        **Validates: Requirements 2.3, 2.5**
        """
        # Create face detector instance
        face_detector = FaceDetectionModule()
        
        # Create test image with patterns
        img_path = self.create_test_image_with_pattern(width, height, num_patterns, tmp_path)
        
        # Detect faces
        result = face_detector.detectFaces(img_path)
        
        # Verify result is a DetectionResult
        assert isinstance(result, DetectionResult), \
            "detectFaces should return a DetectionResult object"
        
        # Verify faces is a list
        assert isinstance(result.faces, list), \
            "DetectionResult.faces should be a list"
        
        # For each detected face, verify completeness
        for i, face in enumerate(result.faces):
            # Verify face is a Face object
            assert isinstance(face, Face), \
                f"Face {i} should be a Face object, got {type(face)}"
            
            # Property 1: Face has a unique, non-empty faceId
            assert hasattr(face, 'faceId'), \
                f"Face {i} should have a faceId attribute"
            assert face.faceId is not None, \
                f"Face {i} faceId should not be None"
            assert isinstance(face.faceId, str), \
                f"Face {i} faceId should be a string, got {type(face.faceId)}"
            assert len(face.faceId) > 0, \
                f"Face {i} faceId should not be empty"
            
            # Property 2: Face has a complete bounding box
            assert hasattr(face, 'boundingBox'), \
                f"Face {i} should have a boundingBox attribute"
            assert face.boundingBox is not None, \
                f"Face {i} boundingBox should not be None"
            assert isinstance(face.boundingBox, dict), \
                f"Face {i} boundingBox should be a dict, got {type(face.boundingBox)}"
            
            # Verify all required bounding box fields
            required_bbox_fields = ['x', 'y', 'width', 'height']
            for field in required_bbox_fields:
                assert field in face.boundingBox, \
                    f"Face {i} boundingBox should have '{field}' field"
                assert isinstance(face.boundingBox[field], (int, float)), \
                    f"Face {i} boundingBox['{field}'] should be numeric, got {type(face.boundingBox[field])}"
                
                # Verify non-negative values
                if field in ['width', 'height']:
                    assert face.boundingBox[field] > 0, \
                        f"Face {i} boundingBox['{field}'] should be positive, got {face.boundingBox[field]}"
                else:  # x, y can be 0 or positive
                    assert face.boundingBox[field] >= 0, \
                        f"Face {i} boundingBox['{field}'] should be non-negative, got {face.boundingBox[field]}"
            
            # Verify bounding box is within image bounds
            assert face.boundingBox['x'] + face.boundingBox['width'] <= width, \
                f"Face {i} bounding box extends beyond image width"
            assert face.boundingBox['y'] + face.boundingBox['height'] <= height, \
                f"Face {i} bounding box extends beyond image height"
            
            # Property 3: Face has a 128-dimensional feature vector
            assert hasattr(face, 'features'), \
                f"Face {i} should have a features attribute"
            assert face.features is not None, \
                f"Face {i} features should not be None"
            assert isinstance(face.features, (list, np.ndarray)), \
                f"Face {i} features should be a list or numpy array, got {type(face.features)}"
            
            # Verify exactly 128 dimensions
            assert len(face.features) == 128, \
                f"Face {i} features should be 128-dimensional, got {len(face.features)} dimensions"
            
            # Verify all features are floats
            for j, feature_value in enumerate(face.features):
                assert isinstance(feature_value, (float, np.floating)), \
                    f"Face {i} feature[{j}] should be a float, got {type(feature_value)}"
                
                # Verify feature values are finite (not NaN or Inf)
                assert np.isfinite(feature_value), \
                    f"Face {i} feature[{j}] should be finite, got {feature_value}"
        
        # If multiple faces detected, verify all faceIds are unique
        if len(result.faces) > 1:
            face_ids = [face.faceId for face in result.faces]
            assert len(face_ids) == len(set(face_ids)), \
                f"All faceIds should be unique, got duplicates: {face_ids}"
    
    @given(
        location_top=st.integers(min_value=10, max_value=100),
        location_left=st.integers(min_value=10, max_value=100),
        face_size=st.integers(min_value=50, max_value=200)
    )
    @settings(max_examples=3, deadline=5000)
    def test_face_creation_always_produces_complete_structure(
        self, location_top, location_left, face_size
    ):
        """
        Property: The internal face creation method always produces complete Face objects.
        
        This tests the _create_face_from_detection method directly to ensure
        it always creates faces with complete data structures.
        
        **Validates: Requirements 2.3, 2.5**
        """
        # Create face detector instance
        face_detector = FaceDetectionModule()
        
        # Create synthetic face location and encoding
        location = (
            location_top,  # top
            location_left + face_size,  # right
            location_top + face_size,  # bottom
            location_left  # left
        )
        
        # Create random 128-dimensional encoding
        encoding = np.random.rand(128).astype(np.float64)
        
        # Create face using internal method
        face = face_detector._create_face_from_detection(location, encoding)
        
        # Verify face is a Face object
        assert isinstance(face, Face), \
            "Created object should be a Face instance"
        
        # Verify faceId completeness
        assert face.faceId is not None, "faceId should not be None"
        assert isinstance(face.faceId, str), "faceId should be a string"
        assert len(face.faceId) > 0, "faceId should not be empty"
        
        # Verify bounding box completeness
        assert face.boundingBox is not None, "boundingBox should not be None"
        assert isinstance(face.boundingBox, dict), "boundingBox should be a dict"
        
        required_fields = ['x', 'y', 'width', 'height']
        for field in required_fields:
            assert field in face.boundingBox, \
                f"boundingBox should have '{field}' field"
            assert isinstance(face.boundingBox[field], (int, float)), \
                f"boundingBox['{field}'] should be numeric"
        
        # Verify bounding box values match location
        assert face.boundingBox['x'] == location_left, \
            "boundingBox x should equal left coordinate"
        assert face.boundingBox['y'] == location_top, \
            "boundingBox y should equal top coordinate"
        assert face.boundingBox['width'] == face_size, \
            "boundingBox width should equal face size"
        assert face.boundingBox['height'] == face_size, \
            "boundingBox height should equal face size"
        
        # Verify features completeness
        assert face.features is not None, "features should not be None"
        assert isinstance(face.features, list), "features should be a list"
        assert len(face.features) == 128, \
            f"features should be 128-dimensional, got {len(face.features)}"
        
        # Verify all features are floats and finite
        for i, feature_value in enumerate(face.features):
            assert isinstance(feature_value, float), \
                f"feature[{i}] should be a float, got {type(feature_value)}"
            assert np.isfinite(feature_value), \
                f"feature[{i}] should be finite, got {feature_value}"
    
    def test_empty_detection_result_has_valid_structure(self, tmp_path):
        """
        Property: Even when no faces are detected, the result structure should be valid.
        
        This verifies that DetectionResult is always well-formed, even with no faces.
        
        **Validates: Requirements 2.3**
        """
        # Create face detector instance
        face_detector = FaceDetectionModule()
        
        # Create a blank image with no faces
        img = Image.new('RGB', (200, 200), color='blue')
        img_path = tmp_path / "no_faces.jpg"
        img.save(img_path)
        
        # Detect faces
        result = face_detector.detectFaces(str(img_path))
        
        # Verify result structure
        assert isinstance(result, DetectionResult), \
            "Result should be a DetectionResult object"
        assert isinstance(result.faces, list), \
            "faces should be a list"
        assert len(result.faces) == 0, \
            "faces list should be empty when no faces detected"
        
        # Error message should be present
        assert result.error is not None, \
            "error should be set when no faces detected"
        assert isinstance(result.error, str), \
            "error should be a string"
        assert len(result.error) > 0, \
            "error message should not be empty"
    
    @given(
        num_faces=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=3, deadline=5000)
    def test_multiple_faces_all_have_unique_ids_and_complete_data(
        self, num_faces
    ):
        """
        Property: When multiple faces are created, each has unique ID and complete data.
        
        This tests that the face creation process maintains data integrity
        when processing multiple faces.
        
        **Validates: Requirements 2.3, 2.5**
        """
        # Create face detector instance
        face_detector = FaceDetectionModule()
        
        faces = []
        
        # Create multiple faces
        for i in range(num_faces):
            location = (
                10 + i * 50,  # top
                110 + i * 50,  # right
                110 + i * 50,  # bottom
                10 + i * 50   # left
            )
            encoding = np.random.rand(128).astype(np.float64)
            
            face = face_detector._create_face_from_detection(location, encoding)
            faces.append(face)
        
        # Verify all faces have unique IDs
        face_ids = [face.faceId for face in faces]
        assert len(face_ids) == len(set(face_ids)), \
            "All faceIds should be unique"
        
        # Verify each face has complete structure
        for i, face in enumerate(faces):
            assert isinstance(face, Face), \
                f"Face {i} should be a Face object"
            assert face.faceId is not None and len(face.faceId) > 0, \
                f"Face {i} should have non-empty faceId"
            assert 'x' in face.boundingBox and 'y' in face.boundingBox, \
                f"Face {i} should have complete bounding box"
            assert 'width' in face.boundingBox and 'height' in face.boundingBox, \
                f"Face {i} should have width and height in bounding box"
            assert len(face.features) == 128, \
                f"Face {i} should have 128-dimensional features"
            assert all(isinstance(f, float) for f in face.features), \
                f"Face {i} features should all be floats"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


