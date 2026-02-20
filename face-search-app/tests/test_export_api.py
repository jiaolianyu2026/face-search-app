"""
API tests for /api/export endpoint.
Tests HTTP endpoint behavior, request validation, and response format.
"""

import os
import sys
import tempfile
import shutil
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app


class TestExportAPI:
    """API tests for image export endpoint."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        self.client = app.test_client()
        
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.source_dir = os.path.join(self.temp_dir, 'source')
        self.target_dir = os.path.join(self.temp_dir, 'target')
        os.makedirs(self.source_dir)
        os.makedirs(self.target_dir)
    
    def teardown_method(self):
        """Clean up test fixtures after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_file(self, filename: str, content: str = "test content") -> str:
        """Helper to create a test file in source directory."""
        filepath = os.path.join(self.source_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def test_export_success(self):
        """Test successful export operation."""
        # Create test files
        file1 = self._create_test_file('image1.jpg', 'data1')
        file2 = self._create_test_file('image2.png', 'data2')
        
        # Make API request
        response = self.client.post('/api/export', json={
            'imagePaths': [file1, file2],
            'targetFolder': self.target_dir
        })
        
        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['successCount'] == 2
        assert data['failedCount'] == 0
        assert len(data['errors']) == 0
        
        # Verify files were copied
        assert os.path.exists(os.path.join(self.target_dir, 'image1.jpg'))
        assert os.path.exists(os.path.join(self.target_dir, 'image2.png'))
    
    def test_export_missing_request_body(self):
        """Test error when request body is missing."""
        response = self.client.post('/api/export')
        
        # Flask returns 415 for missing content-type/body
        assert response.status_code == 415
    
    def test_export_missing_image_paths(self):
        """Test error when imagePaths parameter is missing."""
        response = self.client.post('/api/export', json={
            'targetFolder': self.target_dir
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert 'imagePaths' in data['error']['message']
    
    def test_export_missing_target_folder(self):
        """Test error when targetFolder parameter is missing."""
        file1 = self._create_test_file('test.jpg')
        
        response = self.client.post('/api/export', json={
            'imagePaths': [file1]
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert 'targetFolder' in data['error']['message']
    
    def test_export_image_paths_not_array(self):
        """Test error when imagePaths is not an array."""
        response = self.client.post('/api/export', json={
            'imagePaths': 'not-an-array',
            'targetFolder': self.target_dir
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert '数组' in data['error']['message'] or 'array' in data['error']['message']
    
    def test_export_empty_image_paths(self):
        """Test error when imagePaths is empty."""
        response = self.client.post('/api/export', json={
            'imagePaths': [],
            'targetFolder': self.target_dir
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert '空' in data['error']['message'] or 'empty' in data['error']['message']
    
    def test_export_nonexistent_target_folder(self):
        """Test error when target folder does not exist."""
        file1 = self._create_test_file('test.jpg')
        nonexistent_folder = os.path.join(self.temp_dir, 'nonexistent')
        
        response = self.client.post('/api/export', json={
            'imagePaths': [file1],
            'targetFolder': nonexistent_folder
        })
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['resourceType'] == 'folder'
    
    def test_export_target_not_directory(self):
        """Test error when target folder is not a directory."""
        file1 = self._create_test_file('test.jpg')
        file_not_dir = self._create_test_file('notadir.txt')
        
        response = self.client.post('/api/export', json={
            'imagePaths': [file1],
            'targetFolder': file_not_dir
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert '文件夹' in data['error']['message'] or 'directory' in data['error']['message']
    
    def test_export_target_not_writable(self):
        """Test error when target folder is not writable."""
        file1 = self._create_test_file('test.jpg')
        
        # Create read-only directory
        readonly_dir = os.path.join(self.temp_dir, 'readonly')
        os.makedirs(readonly_dir)
        
        # On Windows, os.chmod doesn't work the same way as Unix
        # Skip this test on Windows or use a different approach
        import platform
        if platform.system() == 'Windows':
            pytest.skip("Read-only directory test not reliable on Windows")
        
        os.chmod(readonly_dir, 0o444)  # Read-only
        
        try:
            response = self.client.post('/api/export', json={
                'imagePaths': [file1],
                'targetFolder': readonly_dir
            })
            
            assert response.status_code == 403
            data = response.get_json()
            assert 'error' in data
            assert 'not writable' in data['error']
        finally:
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)
    
    def test_export_partial_success(self):
        """Test export with some successes and some failures."""
        # Create one valid file
        valid_file = self._create_test_file('valid.jpg', 'valid')
        
        # Create list with valid and invalid files
        invalid_file = os.path.join(self.source_dir, 'invalid.jpg')
        
        response = self.client.post('/api/export', json={
            'imagePaths': [valid_file, invalid_file],
            'targetFolder': self.target_dir
        })
        
        # Should return 200 even with partial failure
        assert response.status_code == 200
        data = response.get_json()
        assert data['successCount'] == 1
        assert data['failedCount'] == 1
        assert len(data['errors']) == 1
        
        # Verify valid file was copied
        assert os.path.exists(os.path.join(self.target_dir, 'valid.jpg'))
    
    def test_export_response_format(self):
        """Test that response contains all required fields."""
        file1 = self._create_test_file('test.jpg')
        
        response = self.client.post('/api/export', json={
            'imagePaths': [file1],
            'targetFolder': self.target_dir
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify all required fields are present
        assert 'successCount' in data
        assert 'failedCount' in data
        assert 'errors' in data
        
        # Verify field types
        assert isinstance(data['successCount'], int)
        assert isinstance(data['failedCount'], int)
        assert isinstance(data['errors'], list)
    
    def test_export_error_details_format(self):
        """Test that error details contain path and error message."""
        # Try to export nonexistent file
        invalid_file = os.path.join(self.source_dir, 'missing.jpg')
        
        response = self.client.post('/api/export', json={
            'imagePaths': [invalid_file],
            'targetFolder': self.target_dir
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['failedCount'] == 1
        assert len(data['errors']) == 1
        
        # Verify error format
        error = data['errors'][0]
        assert 'path' in error
        assert 'error' in error
        assert error['path'] == invalid_file
