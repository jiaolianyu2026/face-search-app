"""
Unit tests for /api/detect endpoint.
Tests the face detection API endpoint functionality.
"""

import pytest
import os
import sys
import json
from PIL import Image, ImageDraw

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app
from config import TEMP_UPLOAD_DIR


class TestDetectAPI:
    """Test suite for /api/detect endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def uploaded_image_id(self, client, tmp_path):
        """Upload a test image and return its imageId."""
        # Create a simple test image
        img = Image.new('RGB', (400, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple face-like pattern
        draw.ellipse([100, 100, 300, 300], fill='peachpuff', outline='black')
        draw.ellipse([140, 160, 180, 200], fill='black')  # Left eye
        draw.ellipse([220, 160, 260, 200], fill='black')  # Right eye
        draw.arc([150, 220, 250, 280], 0, 180, fill='black', width=3)  # Mouth
        
        img_path = tmp_path / "test_face.jpg"
        img.save(img_path)
        
        # Upload the image
        with open(img_path, 'rb') as f:
            response = client.post(
                '/api/upload',
                data={'file': (f, 'test_face.jpg')},
                content_type='multipart/form-data'
            )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        return data['imageId']
    
    def test_detect_requires_imageId(self, client):
        """Test that /api/detect requires imageId parameter."""
        response = client.post(
            '/api/detect',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert 'imageId' in data['error']['message']
    
    def test_detect_with_missing_image(self, client):
        """Test that /api/detect returns 404 for non-existent imageId."""
        response = client.post(
            '/api/detect',
            data=json.dumps({'imageId': 'nonexistent-id'}),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['resourceType'] == 'image'
    
    def test_detect_returns_detection_result(self, client, uploaded_image_id):
        """Test that /api/detect returns a properly structured DetectionResult."""
        response = client.post(
            '/api/detect',
            data=json.dumps({'imageId': uploaded_image_id}),
            content_type='application/json'
        )
        
        # Should return either 200 (faces found) or 422 (no faces)
        assert response.status_code in [200, 422]
        data = json.loads(response.data)
        
        # Verify response structure
        assert 'faces' in data
        assert isinstance(data['faces'], list)
        
        if response.status_code == 200:
            # If faces detected, verify structure
            assert len(data['faces']) > 0
            for face in data['faces']:
                assert 'faceId' in face
                assert 'boundingBox' in face
                assert 'features' in face
                
                # Verify bounding box structure
                bbox = face['boundingBox']
                assert 'x' in bbox
                assert 'y' in bbox
                assert 'width' in bbox
                assert 'height' in bbox
                
                # Verify features are 128-dimensional
                assert len(face['features']) == 128
                assert all(isinstance(f, (int, float)) for f in face['features'])
        else:
            # If no faces detected, should have error message
            assert 'error' in data
            assert data['error'] is not None
    
    def test_detect_with_no_faces_returns_422(self, client, tmp_path):
        """Test that /api/detect returns 422 when no faces are detected."""
        # Create a blank image with no faces
        img = Image.new('RGB', (100, 100), color='blue')
        img_path = tmp_path / "no_face.jpg"
        img.save(img_path)
        
        # Upload the image
        with open(img_path, 'rb') as f:
            response = client.post(
                '/api/upload',
                data={'file': (f, 'no_face.jpg')},
                content_type='multipart/form-data'
            )
        
        assert response.status_code == 200
        upload_data = json.loads(response.data)
        image_id = upload_data['imageId']
        
        # Try to detect faces
        response = client.post(
            '/api/detect',
            data=json.dumps({'imageId': image_id}),
            content_type='application/json'
        )
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert len(data['faces']) == 0
        assert 'error' in data
        assert 'no faces' in data['error'].lower()
    
    def test_detect_face_ids_are_unique(self, client, uploaded_image_id):
        """Test that each detected face has a unique faceId."""
        response = client.post(
            '/api/detect',
            data=json.dumps({'imageId': uploaded_image_id}),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = json.loads(response.data)
            if len(data['faces']) > 1:
                face_ids = [face['faceId'] for face in data['faces']]
                # All face IDs should be unique
                assert len(face_ids) == len(set(face_ids))
    
    def test_detect_bounding_boxes_are_valid(self, client, uploaded_image_id):
        """Test that bounding boxes have valid coordinates."""
        response = client.post(
            '/api/detect',
            data=json.dumps({'imageId': uploaded_image_id}),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = json.loads(response.data)
            for face in data['faces']:
                bbox = face['boundingBox']
                # Coordinates should be non-negative
                assert bbox['x'] >= 0
                assert bbox['y'] >= 0
                # Dimensions should be positive
                assert bbox['width'] > 0
                assert bbox['height'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
