"""
Integration test for search API endpoint.
Tests the complete flow: upload -> detect -> search.
"""

import pytest
import os
import sys
import tempfile
import shutil
import json
import time
from PIL import Image, ImageDraw

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app


class TestSearchIntegration:
    """Integration tests for search functionality."""
    
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
        
        # Create some test images
        for i in range(3):
            img = Image.new('RGB', (200, 200), color=(i*80, i*80, i*80))
            img.save(os.path.join(temp_dir, f'search_image_{i}.jpg'))
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def create_image_with_face(self):
        """Create a simple test image that might contain a face-like pattern."""
        # Create a larger image with a simple face-like pattern
        img = Image.new('RGB', (400, 400), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw a simple face-like pattern
        # Face outline (circle)
        draw.ellipse([100, 100, 300, 300], fill=(255, 220, 180), outline=(0, 0, 0))
        # Eyes
        draw.ellipse([150, 150, 180, 180], fill=(0, 0, 0))
        draw.ellipse([220, 150, 250, 180], fill=(0, 0, 0))
        # Nose
        draw.polygon([(200, 180), (190, 220), (210, 220)], fill=(200, 180, 160))
        # Mouth
        draw.arc([160, 220, 240, 260], 0, 180, fill=(0, 0, 0), width=3)
        
        return img
    
    def test_complete_search_flow(self, client, temp_search_folder):
        """Test the complete flow: upload -> detect -> search."""
        # Step 1: Create and upload an image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = self.create_image_with_face()
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            # Upload the image
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test_face.jpg')},
                    content_type='multipart/form-data'
                )
            
            assert upload_response.status_code == 200
            upload_data = json.loads(upload_response.data)
            assert upload_data['success'] is True
            image_id = upload_data['imageId']
            
            # Step 2: Detect faces
            detect_response = client.post(
                '/api/detect',
                json={'imageId': image_id}
            )
            
            # If no faces detected, this is expected for simple test images
            if detect_response.status_code == 422:
                pytest.skip("No faces detected in test image - this is expected for simple test patterns")
            
            assert detect_response.status_code == 200
            detect_data = json.loads(detect_response.data)
            assert len(detect_data['faces']) > 0
            
            face_id = detect_data['faces'][0]['faceId']
            
            # Step 3: Start search
            search_response = client.post(
                '/api/search',
                json={
                    'imageId': image_id,
                    'faceId': face_id,
                    'searchFolder': temp_search_folder,
                    'threshold': 0.5
                }
            )
            
            assert search_response.status_code == 200
            search_data = json.loads(search_response.data)
            
            # Verify response structure
            assert 'taskId' in search_data
            assert 'status' in search_data
            assert isinstance(search_data['taskId'], str)
            assert len(search_data['taskId']) > 0
            assert search_data['status'] in ['pending', 'running']
            
            # The search runs in background, so we just verify it started successfully
            print(f"Search task created with ID: {search_data['taskId']}")
            
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_search_with_custom_threshold(self, client, temp_search_folder):
        """Test search with custom threshold value."""
        # Create and upload an image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = self.create_image_with_face()
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test_face.jpg')},
                    content_type='multipart/form-data'
                )
            
            upload_data = json.loads(upload_response.data)
            image_id = upload_data['imageId']
            
            # Detect faces
            detect_response = client.post(
                '/api/detect',
                json={'imageId': image_id}
            )
            
            if detect_response.status_code == 422:
                pytest.skip("No faces detected in test image")
            
            detect_data = json.loads(detect_response.data)
            if len(detect_data['faces']) == 0:
                pytest.skip("No faces detected in test image")
            
            face_id = detect_data['faces'][0]['faceId']
            
            # Test with different threshold values
            for threshold in [0.3, 0.6, 0.9]:
                search_response = client.post(
                    '/api/search',
                    json={
                        'imageId': image_id,
                        'faceId': face_id,
                        'searchFolder': temp_search_folder,
                        'threshold': threshold
                    }
                )
                
                assert search_response.status_code == 200
                search_data = json.loads(search_response.data)
                assert 'taskId' in search_data
                
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_search_validates_parameters_before_processing(self, client):
        """Test that parameter validation happens before expensive operations."""
        # This test verifies that we validate the search folder
        # before doing face detection (which is expensive)
        
        # Create a valid image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = Image.new('RGB', (200, 200), color=(128, 128, 128))
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test.jpg')},
                    content_type='multipart/form-data'
                )
            
            upload_data = json.loads(upload_response.data)
            image_id = upload_data['imageId']
            
            # Try to search with invalid folder (should fail fast)
            search_response = client.post(
                '/api/search',
                json={
                    'imageId': image_id,
                    'faceId': 'any-face-id',
                    'searchFolder': '/nonexistent/folder'
                }
            )
            
            # Should return 400 (validation error) not 404 (face not found)
            assert search_response.status_code == 400
            data = json.loads(search_response.data)
            assert 'error' in data
            assert data['error']['code'] == 'VALIDATION_ERROR'
            assert '不存在' in data['error']['message'] or 'does not exist' in data['error']['message']
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_search_progress_tracking(self, client, temp_search_folder):
        """Test that search progress can be tracked via GET /api/search/{taskId}."""
        # Create and upload an image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = self.create_image_with_face()
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test_face.jpg')},
                    content_type='multipart/form-data'
                )
            
            upload_data = json.loads(upload_response.data)
            image_id = upload_data['imageId']
            
            # Detect faces
            detect_response = client.post(
                '/api/detect',
                json={'imageId': image_id}
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
                    'imageId': image_id,
                    'faceId': face_id,
                    'searchFolder': temp_search_folder,
                    'threshold': 0.5
                }
            )
            
            assert search_response.status_code == 200
            search_data = json.loads(search_response.data)
            task_id = search_data['taskId']
            
            # Poll for progress updates
            max_polls = 20
            for i in range(max_polls):
                status_response = client.get(f'/api/search/{task_id}')
                assert status_response.status_code == 200
                
                status_data = json.loads(status_response.data)
                
                # Verify response structure
                assert 'taskId' in status_data
                assert 'status' in status_data
                assert 'progress' in status_data
                assert 'createdAt' in status_data
                
                # Verify progress structure
                progress = status_data['progress']
                assert 'current' in progress
                assert 'total' in progress
                assert 'percentage' in progress
                assert 'currentFile' in progress
                
                # Check if completed
                if status_data['status'] in ['completed', 'cancelled']:
                    # Should have results when completed
                    assert 'results' in status_data
                    assert isinstance(status_data['results'], list)
                    break
                
                time.sleep(0.1)
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_search_cancellation_flow(self, client, temp_search_folder):
        """Test the complete cancellation flow: start search -> cancel -> verify cancelled."""
        # Create and upload an image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = self.create_image_with_face()
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test_face.jpg')},
                    content_type='multipart/form-data'
                )
            
            upload_data = json.loads(upload_response.data)
            image_id = upload_data['imageId']
            
            # Detect faces
            detect_response = client.post(
                '/api/detect',
                json={'imageId': image_id}
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
                    'imageId': image_id,
                    'faceId': face_id,
                    'searchFolder': temp_search_folder,
                    'threshold': 0.5
                }
            )
            
            assert search_response.status_code == 200
            search_data = json.loads(search_response.data)
            task_id = search_data['taskId']
            
            # Cancel the search immediately
            cancel_response = client.post(f'/api/search/{task_id}/cancel')
            assert cancel_response.status_code == 200
            
            cancel_data = json.loads(cancel_response.data)
            assert cancel_data['taskId'] == task_id
            assert cancel_data['status'] == 'cancelled'
            assert 'cancelled' in cancel_data['message'].lower()
            
            # Verify the task status shows cancelled
            status_response = client.get(f'/api/search/{task_id}')
            assert status_response.status_code == 200
            
            status_data = json.loads(status_response.data)
            assert status_data['status'] == 'cancelled'
            
            # Should have results (partial results from before cancellation)
            assert 'results' in status_data
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_search_results_structure(self, client, temp_search_folder):
        """Test that completed search returns properly structured results."""
        # Create and upload an image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = self.create_image_with_face()
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                upload_response = client.post(
                    '/api/upload',
                    data={'file': (f, 'test_face.jpg')},
                    content_type='multipart/form-data'
                )
            
            upload_data = json.loads(upload_response.data)
            image_id = upload_data['imageId']
            
            # Detect faces
            detect_response = client.post(
                '/api/detect',
                json={'imageId': image_id}
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
                    'imageId': image_id,
                    'faceId': face_id,
                    'searchFolder': temp_search_folder,
                    'threshold': 0.5
                }
            )
            
            assert search_response.status_code == 200
            search_data = json.loads(search_response.data)
            task_id = search_data['taskId']
            
            # Wait for completion
            max_wait = 10  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = client.get(f'/api/search/{task_id}')
                status_data = json.loads(status_response.data)
                
                if status_data['status'] in ['completed', 'cancelled']:
                    # Verify results structure
                    assert 'results' in status_data
                    results = status_data['results']
                    assert isinstance(results, list)
                    
                    # If there are results, verify their structure
                    for result in results:
                        assert 'imagePath' in result
                        assert 'similarity' in result
                        assert 'faceLocation' in result
                        
                        # Verify similarity is in valid range
                        assert 0 <= result['similarity'] <= 1
                        
                        # Verify faceLocation structure
                        face_loc = result['faceLocation']
                        assert 'x' in face_loc or 'y' in face_loc
                    
                    break
                
                time.sleep(0.1)
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
