"""
Unit tests for search API endpoint.
Tests POST /api/search endpoint functionality.
"""

import pytest
import os
import sys
import tempfile
import shutil
import json
from PIL import Image
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app


class TestSearchAPI:
    """Unit tests for search API endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def temp_search_folder(self):
        """Create a temporary folder with test images."""
        temp_dir = tempfile.mkdtemp()
        
        # Create some test images with faces
        for i in range(3):
            img = Image.new('RGB', (200, 200), color=(i*80, i*80, i*80))
            img.save(os.path.join(temp_dir, f'test_image_{i}.jpg'))
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def uploaded_image(self, client):
        """Upload a test image and return imageId."""
        # Create a test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = Image.new('RGB', (200, 200), color=(128, 128, 128))
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            # Upload the image
            with open(tmp_path, 'rb') as f:
                response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test.jpg')},
                    content_type='multipart/form-data'
                )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            yield data['imageId']
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_search_missing_body(self, client):
        """Test search endpoint with missing request body."""
        response = client.post('/api/search')
        # Flask returns 415 for missing content-type or 400 for missing body
        assert response.status_code in [400, 415]
    
    def test_search_missing_image_id(self, client, temp_search_folder):
        """Test search endpoint with missing imageId."""
        response = client.post(
            '/api/search',
            json={
                'faceId': 'test-face-id',
                'searchFolder': temp_search_folder
            }
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert 'imageId' in data['error']['message']
    
    def test_search_missing_face_id(self, client, uploaded_image, temp_search_folder):
        """Test search endpoint with missing faceId."""
        response = client.post(
            '/api/search',
            json={
                'imageId': uploaded_image,
                'searchFolder': temp_search_folder
            }
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert 'faceId' in data['error']['message']
    
    def test_search_missing_search_folder(self, client, uploaded_image):
        """Test search endpoint with missing searchFolder."""
        response = client.post(
            '/api/search',
            json={
                'imageId': uploaded_image,
                'faceId': 'test-face-id'
            }
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert 'searchFolder' in data['error']['message']
    
    def test_search_invalid_threshold(self, client, uploaded_image, temp_search_folder):
        """Test search endpoint with invalid threshold."""
        response = client.post(
            '/api/search',
            json={
                'imageId': uploaded_image,
                'faceId': 'test-face-id',
                'searchFolder': temp_search_folder,
                'threshold': 1.5  # Invalid: > 1
            }
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert 'threshold' in data['error']['message']
    
    def test_search_invalid_image_id(self, client, temp_search_folder):
        """Test search endpoint with non-existent imageId."""
        response = client.post(
            '/api/search',
            json={
                'imageId': 'nonexistent-id',
                'faceId': 'test-face-id',
                'searchFolder': temp_search_folder
            }
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['resourceType'] == 'image'
    
    def test_search_nonexistent_folder(self, client, uploaded_image):
        """Test search endpoint with non-existent search folder."""
        response = client.post(
            '/api/search',
            json={
                'imageId': uploaded_image,
                'faceId': 'test-face-id',
                'searchFolder': '/nonexistent/folder'
            }
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert '不存在' in data['error']['message'] or 'does not exist' in data['error']['message']
    
    def test_search_folder_is_file(self, client, uploaded_image):
        """Test search endpoint when searchFolder is a file, not a directory."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            response = client.post(
                '/api/search',
                json={
                    'imageId': uploaded_image,
                    'faceId': 'test-face-id',
                    'searchFolder': tmp_path
                }
            )
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
            assert data['error']['code'] == 'VALIDATION_ERROR'
            assert '文件夹' in data['error']['message'] or 'directory' in data['error']['message']
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_search_invalid_face_id(self, client, uploaded_image, temp_search_folder):
        """Test search endpoint with invalid faceId."""
        # First detect faces to get valid face structure
        detect_response = client.post(
            '/api/detect',
            json={'imageId': uploaded_image}
        )
        
        # If no faces detected, this test is not applicable
        if detect_response.status_code == 422:
            pytest.skip("No faces detected in test image")
        
        # Try to search with invalid faceId
        response = client.post(
            '/api/search',
            json={
                'imageId': uploaded_image,
                'faceId': 'invalid-face-id',
                'searchFolder': temp_search_folder
            }
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'Face not found' in data['error']
    
    def test_search_default_threshold(self, client, uploaded_image, temp_search_folder):
        """Test search endpoint uses default threshold when not specified."""
        # First detect faces
        detect_response = client.post(
            '/api/detect',
            json={'imageId': uploaded_image}
        )
        
        # If no faces detected, skip this test
        if detect_response.status_code == 422:
            pytest.skip("No faces detected in test image")
        
        detect_data = json.loads(detect_response.data)
        if len(detect_data['faces']) == 0:
            pytest.skip("No faces detected in test image")
        
        face_id = detect_data['faces'][0]['faceId']
        
        # Start search without threshold (should use default 0.6)
        response = client.post(
            '/api/search',
            json={
                'imageId': uploaded_image,
                'faceId': face_id,
                'searchFolder': temp_search_folder
            }
        )
        
        # Should succeed and return taskId
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'taskId' in data
        assert 'status' in data
        assert data['status'] in ['pending', 'running']
    
    def test_search_returns_task_id(self, client, uploaded_image, temp_search_folder):
        """Test that search endpoint returns a taskId."""
        # First detect faces
        detect_response = client.post(
            '/api/detect',
            json={'imageId': uploaded_image}
        )
        
        # If no faces detected, skip this test
        if detect_response.status_code == 422:
            pytest.skip("No faces detected in test image")
        
        detect_data = json.loads(detect_response.data)
        if len(detect_data['faces']) == 0:
            pytest.skip("No faces detected in test image")
        
        face_id = detect_data['faces'][0]['faceId']
        
        # Start search
        response = client.post(
            '/api/search',
            json={
                'imageId': uploaded_image,
                'faceId': face_id,
                'searchFolder': temp_search_folder,
                'threshold': 0.7
            }
        )
        
        # Should succeed
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have taskId and status
        assert 'taskId' in data
        assert 'status' in data
        assert isinstance(data['taskId'], str)
        assert len(data['taskId']) > 0
        assert data['status'] in ['pending', 'running']

    def test_get_search_status_not_found(self, client):
        """Test getting status of non-existent search task."""
        response = client.get('/api/search/nonexistent-task-id')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['resourceType'] == 'task'
    
    def test_get_search_status_pending(self, client, uploaded_image, temp_search_folder):
        """Test getting status of a pending/running search task."""
        # First detect faces
        detect_response = client.post(
            '/api/detect',
            json={'imageId': uploaded_image}
        )
        
        if detect_response.status_code == 422:
            pytest.skip("No faces detected in test image")
        
        detect_data = json.loads(detect_response.data)
        if len(detect_data['faces']) == 0:
            pytest.skip("No faces detected in test image")
        
        face_id = detect_data['faces'][0]['faceId']
        
        # Start search
        search_response = client.post(
            '/api/search',
            json={
                'imageId': uploaded_image,
                'faceId': face_id,
                'searchFolder': temp_search_folder,
                'threshold': 0.7
            }
        )
        
        assert search_response.status_code == 200
        search_data = json.loads(search_response.data)
        task_id = search_data['taskId']
        
        # Get status
        status_response = client.get(f'/api/search/{task_id}')
        assert status_response.status_code == 200
        
        status_data = json.loads(status_response.data)
        assert 'taskId' in status_data
        assert 'status' in status_data
        assert 'progress' in status_data
        assert 'createdAt' in status_data
        
        assert status_data['taskId'] == task_id
        assert status_data['status'] in ['pending', 'running', 'completed', 'cancelled']
        
        # Check progress structure
        progress = status_data['progress']
        assert 'current' in progress
        assert 'total' in progress
        assert 'percentage' in progress
        assert 'currentFile' in progress
    
    def test_get_search_status_completed(self, client, uploaded_image, temp_search_folder):
        """Test getting status of a completed search task includes results."""
        import time
        
        # First detect faces
        detect_response = client.post(
            '/api/detect',
            json={'imageId': uploaded_image}
        )
        
        if detect_response.status_code == 422:
            pytest.skip("No faces detected in test image")
        
        detect_data = json.loads(detect_response.data)
        if len(detect_data['faces']) == 0:
            pytest.skip("No faces detected in test image")
        
        face_id = detect_data['faces'][0]['faceId']
        
        # Start search
        search_response = client.post(
            '/api/search',
            json={
                'imageId': uploaded_image,
                'faceId': face_id,
                'searchFolder': temp_search_folder,
                'threshold': 0.7
            }
        )
        
        assert search_response.status_code == 200
        search_data = json.loads(search_response.data)
        task_id = search_data['taskId']
        
        # Wait for search to complete (with timeout)
        max_wait = 10  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = client.get(f'/api/search/{task_id}')
            status_data = json.loads(status_response.data)
            
            if status_data['status'] in ['completed', 'cancelled']:
                break
            
            time.sleep(0.1)
        
        # Get final status
        status_response = client.get(f'/api/search/{task_id}')
        assert status_response.status_code == 200
        
        status_data = json.loads(status_response.data)
        
        # Should have results when completed
        if status_data['status'] in ['completed', 'cancelled']:
            assert 'results' in status_data
            assert isinstance(status_data['results'], list)
    
    def test_cancel_search_not_found(self, client):
        """Test cancelling non-existent search task."""
        response = client.post('/api/search/nonexistent-task-id/cancel')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['resourceType'] == 'task'
    
    def test_cancel_search_success(self, client, uploaded_image, temp_search_folder):
        """Test successfully cancelling a running search task."""
        # First detect faces
        detect_response = client.post(
            '/api/detect',
            json={'imageId': uploaded_image}
        )
        
        if detect_response.status_code == 422:
            pytest.skip("No faces detected in test image")
        
        detect_data = json.loads(detect_response.data)
        if len(detect_data['faces']) == 0:
            pytest.skip("No faces detected in test image")
        
        face_id = detect_data['faces'][0]['faceId']
        
        # Start search
        search_response = client.post(
            '/api/search',
            json={
                'imageId': uploaded_image,
                'faceId': face_id,
                'searchFolder': temp_search_folder,
                'threshold': 0.7
            }
        )
        
        assert search_response.status_code == 200
        search_data = json.loads(search_response.data)
        task_id = search_data['taskId']
        
        # Cancel the search
        cancel_response = client.post(f'/api/search/{task_id}/cancel')
        assert cancel_response.status_code == 200
        
        cancel_data = json.loads(cancel_response.data)
        assert 'taskId' in cancel_data
        assert 'status' in cancel_data
        assert 'message' in cancel_data
        
        assert cancel_data['taskId'] == task_id
        assert cancel_data['status'] == 'cancelled'
        assert 'cancelled' in cancel_data['message'].lower()
    
    def test_cancel_search_already_completed(self, client, uploaded_image, temp_search_folder):
        """Test that cancelling a completed task returns an error."""
        import time
        
        # First detect faces
        detect_response = client.post(
            '/api/detect',
            json={'imageId': uploaded_image}
        )
        
        if detect_response.status_code == 422:
            pytest.skip("No faces detected in test image")
        
        detect_data = json.loads(detect_response.data)
        if len(detect_data['faces']) == 0:
            pytest.skip("No faces detected in test image")
        
        face_id = detect_data['faces'][0]['faceId']
        
        # Start search
        search_response = client.post(
            '/api/search',
            json={
                'imageId': uploaded_image,
                'faceId': face_id,
                'searchFolder': temp_search_folder,
                'threshold': 0.7
            }
        )
        
        assert search_response.status_code == 200
        search_data = json.loads(search_response.data)
        task_id = search_data['taskId']
        
        # Wait for search to complete
        max_wait = 10  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = client.get(f'/api/search/{task_id}')
            status_data = json.loads(status_response.data)
            
            if status_data['status'] == 'completed':
                break
            
            time.sleep(0.1)
        
        # Try to cancel completed task
        cancel_response = client.post(f'/api/search/{task_id}/cancel')
        assert cancel_response.status_code == 400
        
        cancel_data = json.loads(cancel_response.data)
        assert 'error' in cancel_data
        assert 'cannot cancel' in cancel_data['error'].lower()
