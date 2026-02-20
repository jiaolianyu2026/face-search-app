"""
Unit tests for image upload API endpoint.
Tests file format validation, size limits, and upload functionality.
"""

import pytest
import os
import io
from PIL import Image

# Add backend to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, validate_file_format
from config import MAX_FILE_SIZE_BYTES, TEMP_UPLOAD_DIR


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def cleanup_uploads():
    """Clean up uploaded files after tests."""
    yield
    # Clean up temp uploads directory
    for filename in os.listdir(TEMP_UPLOAD_DIR):
        file_path = os.path.join(TEMP_UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


def create_test_image(format='JPEG', size=(100, 100)):
    """
    Create a test image in memory.
    
    Args:
        format: Image format (JPEG, PNG, WEBP)
        size: Image dimensions (width, height)
        
    Returns:
        BytesIO object containing image data
    """
    img = Image.new('RGB', size, color='red')
    img_io = io.BytesIO()
    img.save(img_io, format=format)
    img_io.seek(0)
    return img_io


class TestFileFormatValidation:
    """Test file format validation logic."""
    
    def test_valid_jpeg_format(self):
        """Test that JPEG files are accepted."""
        is_valid, error = validate_file_format('test.jpg', 'image/jpeg')
        assert is_valid is True
        assert error == ""
    
    def test_valid_png_format(self):
        """Test that PNG files are accepted."""
        is_valid, error = validate_file_format('test.png', 'image/png')
        assert is_valid is True
        assert error == ""
    
    def test_valid_webp_format(self):
        """Test that WebP files are accepted."""
        is_valid, error = validate_file_format('test.webp', 'image/webp')
        assert is_valid is True
        assert error == ""
    
    def test_invalid_gif_format(self):
        """Test that GIF files are rejected."""
        is_valid, error = validate_file_format('test.gif', 'image/gif')
        assert is_valid is False
        assert "Unsupported" in error
    
    def test_invalid_extension(self):
        """Test that files with unsupported extensions are rejected."""
        is_valid, error = validate_file_format('test.txt', 'text/plain')
        assert is_valid is False
        assert "Unsupported" in error
    
    def test_mismatched_extension_and_content_type(self):
        """Test that mismatched extension and content type are rejected."""
        is_valid, error = validate_file_format('test.jpg', 'image/png')
        assert is_valid is False
        assert "does not match" in error


class TestUploadEndpoint:
    """Test image upload API endpoint."""
    
    def test_upload_valid_jpeg(self, client, cleanup_uploads):
        """Test uploading a valid JPEG image."""
        img_data = create_test_image('JPEG')
        
        response = client.post('/api/upload', data={
            'file': (img_data, 'test.jpg', 'image/jpeg')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'imageId' in data
        assert data['imageId'] is not None
        assert 'previewUrl' in data
        assert data['previewUrl'].startswith('/api/preview/')
    
    def test_upload_valid_png(self, client, cleanup_uploads):
        """Test uploading a valid PNG image."""
        img_data = create_test_image('PNG')
        
        response = client.post('/api/upload', data={
            'file': (img_data, 'test.png', 'image/png')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'imageId' in data
    
    def test_upload_no_file(self, client):
        """Test upload request without file."""
        response = client.post('/api/upload', data={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert '文件' in data['error']['message']
    
    def test_upload_empty_filename(self, client):
        """Test upload with empty filename."""
        response = client.post('/api/upload', data={
            'file': (io.BytesIO(b''), '', 'image/jpeg')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert '文件' in data['error']['message']
    
    def test_upload_invalid_format(self, client):
        """Test uploading an unsupported file format."""
        response = client.post('/api/upload', data={
            'file': (io.BytesIO(b'test data'), 'test.txt', 'text/plain')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
    
    def test_upload_file_saved_to_disk(self, client, cleanup_uploads):
        """Test that uploaded file is actually saved to disk."""
        img_data = create_test_image('JPEG')
        
        response = client.post('/api/upload', data={
            'file': (img_data, 'test.jpg', 'image/jpeg')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = response.get_json()
        image_id = data['imageId']
        
        # Check that file exists in temp directory
        files = os.listdir(TEMP_UPLOAD_DIR)
        matching_files = [f for f in files if f.startswith(image_id)]
        assert len(matching_files) == 1
    
    def test_preview_endpoint(self, client, cleanup_uploads):
        """Test that preview endpoint returns uploaded image."""
        img_data = create_test_image('JPEG')
        
        # Upload image
        response = client.post('/api/upload', data={
            'file': (img_data, 'test.jpg', 'image/jpeg')
        }, content_type='multipart/form-data')
        
        data = response.get_json()
        image_id = data['imageId']
        
        # Get preview
        preview_response = client.get(f'/api/preview/{image_id}')
        assert preview_response.status_code == 200
        assert preview_response.content_type.startswith('image/')
    
    def test_preview_nonexistent_image(self, client):
        """Test preview endpoint with non-existent imageId."""
        response = client.get('/api/preview/nonexistent-id')
        assert response.status_code == 404


class TestFileSizeLimit:
    """Test file size validation."""
    
    def test_file_size_within_limit(self, client, cleanup_uploads):
        """Test uploading a file within size limit."""
        # Create a small image (well under 10MB)
        img_data = create_test_image('JPEG', size=(500, 500))
        
        response = client.post('/api/upload', data={
            'file': (img_data, 'test.jpg', 'image/jpeg')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_file_size_exceeds_limit(self, client):
        """Test uploading a file that exceeds size limit."""
        # Create a large file (over 10MB)
        large_data = io.BytesIO(b'x' * (MAX_FILE_SIZE_BYTES + 1))
        
        response = client.post('/api/upload', data={
            'file': (large_data, 'large.jpg', 'image/jpeg')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 413
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'FILE_TOO_LARGE'



if __name__ == '__main__':
    pytest.main([__file__, '-v'])
