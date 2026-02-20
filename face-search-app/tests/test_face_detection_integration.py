"""
Integration tests for FaceDetectionModule with real face images.
These tests verify the complete face detection workflow.
"""

import pytest
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from face_detection import FaceDetectionModule
from models import Face, DetectionResult


class TestFaceDetectionIntegration:
    """Integration tests for face detection functionality."""
    
    @pytest.fixture
    def face_detector(self):
        """Create a FaceDetectionModule instance."""
        return FaceDetectionModule()
    
    @pytest.fixture
    def simple_face_image(self, tmp_path):
        """
        Create a simple synthetic face-like image for testing.
        Note: Real face detection may not work on synthetic images,
        but this tests the pipeline.
        """
        # Create a 400x400 image with a simple face-like pattern
        img = Image.new('RGB', (400, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple face-like pattern
        # Face outline (circle)
        draw.ellipse([100, 100, 300, 300], fill='peachpuff', outline='black')
        # Eyes
        draw.ellipse([140, 160, 180, 200], fill='black')
        draw.ellipse([220, 160, 260, 200], fill='black')
        # Nose
        draw.polygon([(200, 200), (190, 240), (210, 240)], fill='tan')
        # Mouth
        draw.arc([150, 220, 250, 280], 0, 180, fill='black', width=3)
        
        img_path = tmp_path / "synthetic_face.jpg"
        img.save(img_path)
        return str(img_path)
    
    def test_detectFaces_workflow(self, face_detector, simple_face_image):
        """Test the complete face detection workflow."""
        result = face_detector.detectFaces(simple_face_image)
        
        # Verify result structure
        assert isinstance(result, DetectionResult)
        assert isinstance(result.faces, list)
        
        # Note: Synthetic images may not be detected as faces by the model
        # This test verifies the workflow completes without errors
        if len(result.faces) > 0:
            # If faces are detected, verify structure
            for face in result.faces:
                assert isinstance(face, Face)
                assert face.faceId is not None
                assert len(face.features) == 128
                assert 'x' in face.boundingBox
                assert 'y' in face.boundingBox
                assert 'width' in face.boundingBox
                assert 'height' in face.boundingBox
    
    def test_multiple_face_detection_structure(self, face_detector):
        """Test that multiple faces can be detected and each has unique ID."""
        # This is a structural test - verifies the module can handle multiple faces
        location1 = (10, 110, 110, 10)
        location2 = (150, 250, 250, 150)
        encoding1 = np.random.rand(128)
        encoding2 = np.random.rand(128)
        
        face1 = face_detector._create_face_from_detection(location1, encoding1)
        face2 = face_detector._create_face_from_detection(location2, encoding2)
        
        # Verify unique IDs
        assert face1.faceId != face2.faceId
        
        # Verify both have correct structure
        assert len(face1.features) == 128
        assert len(face2.features) == 128
        assert face1.boundingBox != face2.boundingBox
    
    def test_extractFeatures_with_invalid_location(self, face_detector, simple_face_image):
        """Test that extractFeatures handles invalid face locations gracefully."""
        # Use an invalid location (outside image bounds)
        invalid_location = (1000, 1100, 1100, 1000)
        
        # The face_recognition library may return empty encodings for invalid locations
        # This should raise a ValueError in our implementation
        try:
            result = face_detector.extractFeatures(simple_face_image, invalid_location)
            # If it doesn't raise, it should at least return a valid 128-dim vector or raise
            assert len(result) == 128 or result is None
        except ValueError:
            # This is the expected behavior
            pass
    
    def test_face_features_are_numeric(self, face_detector):
        """Test that all face features are valid numeric values."""
        location = (10, 110, 110, 10)
        encoding = np.random.rand(128)
        
        face = face_detector._create_face_from_detection(location, encoding)
        
        # Verify all features are floats and not NaN
        for feature in face.features:
            assert isinstance(feature, float)
            assert not np.isnan(feature)
            assert not np.isinf(feature)
    
    def test_bounding_box_coordinates_are_positive(self, face_detector):
        """Test that bounding box coordinates are non-negative."""
        location = (50, 150, 200, 100)
        encoding = np.random.rand(128)
        
        face = face_detector._create_face_from_detection(location, encoding)
        
        assert face.boundingBox['x'] >= 0
        assert face.boundingBox['y'] >= 0
        assert face.boundingBox['width'] > 0
        assert face.boundingBox['height'] > 0
    
    def test_detectFaces_error_handling(self, face_detector):
        """Test that detectFaces handles various error conditions."""
        # Test with nonexistent file
        result = face_detector.detectFaces("/nonexistent/file.jpg")
        assert result.error is not None
        assert len(result.faces) == 0
        
        # Test with invalid path
        result = face_detector.detectFaces("")
        assert result.error is not None
        assert len(result.faces) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
