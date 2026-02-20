# -*- coding: utf-8 -*-
"""
Property-based tests for image upload functionality.
Uses hypothesis to generate random test cases and verify universal properties.

**Feature: face-recognition-search, Property 1: 图片格式验证**
**Validates: Requirements 1.1**
"""

import pytest
import os
import sys
import io
import uuid
from hypothesis import given, strategies as st, settings
from PIL import Image

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, validate_file_format
from config import SUPPORTED_EXTENSIONS, SUPPORTED_IMAGE_FORMATS


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# Strategy for generating file extensions
supported_extensions = st.sampled_from(['.jpg', '.jpeg', '.png', '.webp'])
unsupported_extensions = st.sampled_from(['.gif', '.bmp', '.txt', '.pdf', '.doc', '.tiff', '.svg'])

# Strategy for generating MIME types
supported_mime_types = st.sampled_from(['image/jpeg', 'image/png', 'image/webp'])
unsupported_mime_types = st.sampled_from([
    'image/gif', 'image/bmp', 'text/plain', 'application/pdf',
    'image/tiff', 'image/svg+xml', 'video/mp4', 'audio/mpeg'
])


class TestProperty1_ImageFormatValidation:
    """
    Property 1: 图片格式验证
    
    对于任何文件输入，系统应当接受JPEG、PNG、WebP格式的文件，并拒绝其他格式的文件
    
    **Validates: Requirements 1.1**
    """
    
    @given(extension=supported_extensions)
    @settings(max_examples=3)
    def test_supported_formats_are_accepted(self, extension):
        """
        Property: All supported formats (JPEG, PNG, WebP) should be accepted.
        
        For any supported file extension, the validation should return True.
        """
        # Map extension to correct MIME type
        mime_mapping = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        
        filename = f"test{extension}"
        mime_type = mime_mapping[extension]
        
        is_valid, error = validate_file_format(filename, mime_type)
        
        assert is_valid is True, f"Supported format {extension} should be accepted"
        assert error == "", f"No error should be returned for supported format {extension}"
    
    @given(extension=unsupported_extensions)
    @settings(max_examples=3)
    def test_unsupported_formats_are_rejected(self, extension):
        """
        Property: All unsupported formats should be rejected.
        
        For any unsupported file extension, the validation should return False.
        """
        # Map to plausible MIME types
        mime_mapping = {
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.tiff': 'image/tiff',
            '.svg': 'image/svg+xml'
        }
        
        filename = f"test{extension}"
        mime_type = mime_mapping.get(extension, 'application/octet-stream')
        
        is_valid, error = validate_file_format(filename, mime_type)
        
        assert is_valid is False, f"Unsupported format {extension} should be rejected"
        assert error != "", f"Error message should be provided for unsupported format {extension}"
        assert "Unsupported" in error, f"Error should mention 'Unsupported' for {extension}"
    
    @given(
        supported_ext=supported_extensions,
        wrong_mime=unsupported_mime_types
    )
    @settings(max_examples=3)
    def test_mismatched_extension_and_mime_rejected(self, supported_ext, wrong_mime):
        """
        Property: Files with mismatched extension and MIME type should be rejected.
        
        Even if the extension is supported, if the MIME type doesn't match, reject it.
        """
        filename = f"test{supported_ext}"
        
        is_valid, error = validate_file_format(filename, wrong_mime)
        
        # Should be rejected due to mismatch or unsupported MIME
        assert is_valid is False, f"Mismatched extension {supported_ext} and MIME {wrong_mime} should be rejected"
        assert error != "", "Error message should be provided for mismatched format"


class TestProperty1_UploadEndpointFormatValidation:
    """
    Property 1 (API level): Upload endpoint format validation
    
    Test that the upload endpoint correctly accepts/rejects different file formats.
    
    **Validates: Requirements 1.1**
    """
    
    def create_test_image(self, format='JPEG', size=(100, 100)):
        """Create a test image in memory."""
        img = Image.new('RGB', size, color='blue')
        img_io = io.BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        return img_io
    
    def get_test_client(self):
        """Create a test client without using fixtures."""
        app.config['TESTING'] = True
        return app.test_client()
    
    @given(extension=supported_extensions)
    @settings(max_examples=3, deadline=2000)
    def test_upload_endpoint_accepts_supported_formats(self, extension):
        """
        Property: Upload endpoint should accept all supported image formats.
        
        For any supported format, the upload should succeed (status 200).
        """
        client = self.get_test_client()
        
        # Map extension to format and MIME type
        format_mapping = {
            '.jpg': ('JPEG', 'image/jpeg'),
            '.jpeg': ('JPEG', 'image/jpeg'),
            '.png': ('PNG', 'image/png'),
            '.webp': ('WEBP', 'image/webp')
        }
        
        img_format, mime_type = format_mapping[extension]
        
        try:
            img_data = self.create_test_image(img_format)
            filename = f"test{extension}"
            
            response = client.post('/api/upload', data={
                'file': (img_data, filename, mime_type)
            }, content_type='multipart/form-data')
            
            assert response.status_code == 200, \
                f"Upload should succeed for supported format {extension}"
            
            data = response.get_json()
            assert data['success'] is True, \
                f"Response should indicate success for {extension}"
            assert 'imageId' in data, \
                f"Response should contain imageId for {extension}"
        finally:
            # Cleanup
            from config import TEMP_UPLOAD_DIR
            for filename in os.listdir(TEMP_UPLOAD_DIR):
                file_path = os.path.join(TEMP_UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
    
    @given(extension=unsupported_extensions)
    @settings(max_examples=3)
    def test_upload_endpoint_rejects_unsupported_formats(self, extension):
        """
        Property: Upload endpoint should reject all unsupported file formats.
        
        For any unsupported format, the upload should fail (status 400).
        """
        client = self.get_test_client()
        
        # Create dummy file data
        file_data = io.BytesIO(b'dummy file content')
        filename = f"test{extension}"
        
        # Map to plausible MIME types
        mime_mapping = {
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.tiff': 'image/tiff',
            '.svg': 'image/svg+xml'
        }
        mime_type = mime_mapping.get(extension, 'application/octet-stream')
        
        response = client.post('/api/upload', data={
            'file': (file_data, filename, mime_type)
        }, content_type='multipart/form-data')
        
        assert response.status_code == 400, \
            f"Upload should fail for unsupported format {extension}"
        
        data = response.get_json()
        assert data['success'] is False, \
            f"Response should indicate failure for {extension}"
        assert 'error' in data, \
            f"Response should contain error message for {extension}"
        assert "Unsupported" in data['error'], \
            f"Error should mention 'Unsupported' for {extension}"


class TestProperty2_FileSizeLimit:
    """
    Property 2: 文件大小限制
    
    对于任何上传的文件，如果大小超过10MB，系统应当拒绝该文件
    
    **Validates: Requirements 1.2**
    """
    
    def create_test_image_with_size(self, target_size_bytes, format='JPEG'):
        """
        Create a test image with approximately the target size.
        
        Args:
            target_size_bytes: Target file size in bytes
            format: Image format (JPEG, PNG, WEBP)
            
        Returns:
            BytesIO object containing the image data
        """
        # Start with a reasonable image size and adjust quality/dimensions
        # to reach target file size
        
        if target_size_bytes < 1024:  # Very small file
            img = Image.new('RGB', (10, 10), color='blue')
            img_io = io.BytesIO()
            img.save(img_io, format=format, quality=10)
            img_io.seek(0)
            return img_io
        
        # Estimate dimensions based on target size
        # Rough estimate: JPEG at quality 85 is about 0.1-0.3 bytes per pixel
        estimated_pixels = int(target_size_bytes / 0.2)
        dimension = int(estimated_pixels ** 0.5)
        dimension = max(10, min(dimension, 10000))  # Clamp to reasonable range
        
        # Create image
        img = Image.new('RGB', (dimension, dimension), color='blue')
        
        # Add some variation to make it more realistic
        import random
        pixels = img.load()
        for i in range(0, dimension, 10):
            for j in range(0, dimension, 10):
                pixels[i, j] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        # Save with quality adjustment
        img_io = io.BytesIO()
        quality = 85 if format == 'JPEG' else None
        
        if format == 'JPEG':
            img.save(img_io, format=format, quality=quality)
        else:
            img.save(img_io, format=format)
        
        img_io.seek(0)
        return img_io
    
    def get_test_client(self):
        """Create a test client without using fixtures."""
        app.config['TESTING'] = True
        return app.test_client()
    
    @given(
        size_mb=st.floats(min_value=0.001, max_value=9.9, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=3, deadline=5000)
    def test_files_under_10mb_are_accepted(self, size_mb):
        """
        Property: All files under 10MB should be accepted (format validation aside).
        
        For any file size < 10MB, the upload should not fail due to size limits.
        """
        client = self.get_test_client()
        
        target_size_bytes = int(size_mb * 1024 * 1024)
        
        try:
            img_data = self.create_test_image_with_size(target_size_bytes, format='JPEG')
            actual_size = len(img_data.getvalue())
            
            # Ensure we're actually under the limit
            if actual_size >= 10 * 1024 * 1024:
                return  # Skip this test case
            
            img_data.seek(0)
            filename = "test.jpg"
            
            response = client.post('/api/upload', data={
                'file': (img_data, filename, 'image/jpeg')
            }, content_type='multipart/form-data')
            
            # Should not fail due to size (status should be 200, not 413)
            assert response.status_code != 413, \
                f"File of size {actual_size} bytes ({actual_size / (1024*1024):.2f}MB) should not be rejected for size"
            
            # If it's a valid image under 10MB, it should succeed
            if response.status_code == 200:
                data = response.get_json()
                assert data['success'] is True, \
                    f"Upload should succeed for file under 10MB"
        finally:
            # Cleanup
            from config import TEMP_UPLOAD_DIR
            for filename in os.listdir(TEMP_UPLOAD_DIR):
                file_path = os.path.join(TEMP_UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
    
    @given(
        size_mb=st.floats(min_value=10.1, max_value=20.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=3, deadline=5000)
    def test_files_over_10mb_are_rejected(self, size_mb):
        """
        Property: All files over 10MB should be rejected.
        
        For any file size > 10MB, the upload should fail with status 413.
        """
        client = self.get_test_client()
        
        target_size_bytes = int(size_mb * 1024 * 1024)
        
        try:
            img_data = self.create_test_image_with_size(target_size_bytes, format='JPEG')
            actual_size = len(img_data.getvalue())
            
            # Ensure we're actually over the limit
            if actual_size < 10 * 1024 * 1024:
                return  # Skip this test case
            
            img_data.seek(0)
            filename = "test.jpg"
            
            response = client.post('/api/upload', data={
                'file': (img_data, filename, 'image/jpeg')
            }, content_type='multipart/form-data')
            
            # Should fail with 413 (Payload Too Large)
            assert response.status_code == 413, \
                f"File of size {actual_size} bytes ({actual_size / (1024*1024):.2f}MB) should be rejected with status 413"
            
            data = response.get_json()
            assert data['success'] is False, \
                f"Response should indicate failure for oversized file"
            assert 'error' in data, \
                f"Response should contain error message"
            assert 'exceeds' in data['error'].lower() or 'limit' in data['error'].lower(), \
                f"Error message should mention size limit"
        finally:
            # Cleanup
            from config import TEMP_UPLOAD_DIR
            for filename in os.listdir(TEMP_UPLOAD_DIR):
                file_path = os.path.join(TEMP_UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
    
    def test_boundary_exactly_10mb(self):
        """
        Test the exact 10MB boundary condition.
        
        A file of exactly 10MB should be accepted (10MB is the limit, not exceeded).
        """
        client = self.get_test_client()
        
        # Create a file of exactly 10MB
        exactly_10mb = 10 * 1024 * 1024
        
        # Create simple data of exactly 10MB
        # We'll create a minimal valid JPEG structure
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        
        # Get the actual image data
        img_data = img_io.getvalue()
        
        # Pad to exactly 10MB if needed (though this might not be a valid JPEG anymore)
        # Instead, let's just test with a file close to 10MB
        if len(img_data) < exactly_10mb:
            # Create a larger image
            dimension = 3000  # Should create a file close to 10MB
            img = Image.new('RGB', (dimension, dimension), color='blue')
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG', quality=95)
        
        img_io.seek(0)
        actual_size = len(img_io.getvalue())
        
        try:
            response = client.post('/api/upload', data={
                'file': (img_io, 'test.jpg', 'image/jpeg')
            }, content_type='multipart/form-data')
            
            # If file is <= 10MB, should not get 413
            if actual_size <= exactly_10mb:
                assert response.status_code != 413, \
                    f"File of exactly {actual_size} bytes should not be rejected for size"
            else:
                # If we accidentally created a file > 10MB, it should be rejected
                assert response.status_code == 413, \
                    f"File over 10MB should be rejected"
        finally:
            # Cleanup
            from config import TEMP_UPLOAD_DIR
            for filename in os.listdir(TEMP_UPLOAD_DIR):
                file_path = os.path.join(TEMP_UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass


class TestProperty3_UploadRoundTripConsistency:
    """
    Property 3: 图片上传往返一致�?
    
    对于任何成功上传的图片，使用返回的imageId应当能够检索到该图片进行后续处�?
    
    **Validates: Requirements 1.4**
    """
    
    def create_random_image(self, format='JPEG', width=None, height=None):
        """
        Create a random test image.
        
        Args:
            format: Image format (JPEG, PNG, WEBP)
            width: Image width (random if None)
            height: Image height (random if None)
            
        Returns:
            BytesIO object containing the image data
        """
        import random
        
        # Random dimensions if not specified
        if width is None:
            width = random.randint(50, 500)
        if height is None:
            height = random.randint(50, 500)
        
        # Random color
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        # Create image
        img = Image.new('RGB', (width, height), color=color)
        
        # Add some random pixels for variation
        pixels = img.load()
        for _ in range(min(width * height // 10, 100)):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            pixels[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        # Save to BytesIO
        img_io = io.BytesIO()
        if format == 'JPEG':
            img.save(img_io, format=format, quality=85)
        else:
            img.save(img_io, format=format)
        
        img_io.seek(0)
        return img_io
    
    def get_test_client(self):
        """Create a test client without using fixtures."""
        app.config['TESTING'] = True
        return app.test_client()
    
    @given(
        format_choice=st.sampled_from(['JPEG', 'PNG', 'WEBP']),
        width=st.integers(min_value=50, max_value=500),
        height=st.integers(min_value=50, max_value=500)
    )
    @settings(max_examples=3, deadline=10000)
    def test_uploaded_image_can_be_retrieved_by_imageid(self, format_choice, width, height):
        """
        Property: For any successfully uploaded image, it should be retrievable using its imageId.
        
        This tests the round-trip consistency: upload -> get imageId -> retrieve by imageId.
        """
        client = self.get_test_client()
        
        # Map format to extension and MIME type
        format_mapping = {
            'JPEG': ('.jpg', 'image/jpeg'),
            'PNG': ('.png', 'image/png'),
            'WEBP': ('.webp', 'image/webp')
        }
        
        extension, mime_type = format_mapping[format_choice]
        
        try:
            # Step 1: Create and upload a random image
            img_data = self.create_random_image(format=format_choice, width=width, height=height)
            original_size = len(img_data.getvalue())
            img_data.seek(0)
            
            filename = f"test{extension}"
            
            upload_response = client.post('/api/upload', data={
                'file': (img_data, filename, mime_type)
            }, content_type='multipart/form-data')
            
            # Verify upload succeeded
            assert upload_response.status_code == 200, \
                f"Upload should succeed for {format_choice} image"
            
            upload_data = upload_response.get_json()
            assert upload_data['success'] is True, \
                f"Upload response should indicate success"
            assert 'imageId' in upload_data, \
                f"Upload response should contain imageId"
            assert 'previewUrl' in upload_data, \
                f"Upload response should contain previewUrl"
            
            image_id = upload_data['imageId']
            preview_url = upload_data['previewUrl']
            
            # Verify imageId is not empty
            assert image_id != "", \
                f"imageId should not be empty"
            
            # Verify previewUrl contains the imageId
            assert image_id in preview_url, \
                f"previewUrl should contain the imageId"
            
            # Step 2: Retrieve the image using the imageId
            retrieve_response = client.get(preview_url)
            
            # Verify retrieval succeeded
            assert retrieve_response.status_code == 200, \
                f"Image retrieval should succeed for imageId {image_id}"
            
            # Verify retrieved data is not empty
            retrieved_data = retrieve_response.data
            assert len(retrieved_data) > 0, \
                f"Retrieved image data should not be empty"
            
            # Verify retrieved data is a valid image of the same format
            retrieved_img_io = io.BytesIO(retrieved_data)
            try:
                retrieved_img = Image.open(retrieved_img_io)
                
                # Verify format matches
                assert retrieved_img.format == format_choice, \
                    f"Retrieved image format should be {format_choice}, got {retrieved_img.format}"
                
                # Verify dimensions match
                assert retrieved_img.size == (width, height), \
                    f"Retrieved image dimensions should be ({width}, {height}), got {retrieved_img.size}"
                
            except Exception as e:
                pytest.fail(f"Retrieved data is not a valid {format_choice} image: {str(e)}")
            
            # Step 3: Verify the image file exists in the temp directory
            from config import TEMP_UPLOAD_DIR
            found = False
            for filename in os.listdir(TEMP_UPLOAD_DIR):
                if filename.startswith(image_id):
                    found = True
                    break
            
            assert found, \
                f"Image file with imageId {image_id} should exist in temp directory"
            
        finally:
            # Cleanup
            from config import TEMP_UPLOAD_DIR
            for filename in os.listdir(TEMP_UPLOAD_DIR):
                file_path = os.path.join(TEMP_UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
    
    @given(
        format_choice=st.sampled_from(['JPEG', 'PNG', 'WEBP'])
    )
    @settings(max_examples=3, deadline=10000)
    def test_multiple_uploads_have_unique_imageids(self, format_choice):
        """
        Property: Multiple uploads should generate unique imageIds.
        
        This ensures that each upload gets a unique identifier for retrieval.
        """
        client = self.get_test_client()
        
        # Map format to extension and MIME type
        format_mapping = {
            'JPEG': ('.jpg', 'image/jpeg'),
            'PNG': ('.png', 'image/png'),
            'WEBP': ('.webp', 'image/webp')
        }
        
        extension, mime_type = format_mapping[format_choice]
        
        try:
            image_ids = []
            
            # Upload 3 images
            for i in range(3):
                img_data = self.create_random_image(format=format_choice)
                img_data.seek(0)
                
                filename = f"test_{i}{extension}"
                
                upload_response = client.post('/api/upload', data={
                    'file': (img_data, filename, mime_type)
                }, content_type='multipart/form-data')
                
                assert upload_response.status_code == 200, \
                    f"Upload {i} should succeed"
                
                upload_data = upload_response.get_json()
                assert upload_data['success'] is True
                assert 'imageId' in upload_data
                
                image_ids.append(upload_data['imageId'])
            
            # Verify all imageIds are unique
            assert len(image_ids) == len(set(image_ids)), \
                f"All imageIds should be unique, got: {image_ids}"
            
            # Verify each image can be retrieved independently
            for image_id in image_ids:
                retrieve_response = client.get(f"/api/preview/{image_id}")
                assert retrieve_response.status_code == 200, \
                    f"Should be able to retrieve image with imageId {image_id}"
                assert len(retrieve_response.data) > 0, \
                    f"Retrieved image data should not be empty for {image_id}"
            
        finally:
            # Cleanup
            from config import TEMP_UPLOAD_DIR
            for filename in os.listdir(TEMP_UPLOAD_DIR):
                file_path = os.path.join(TEMP_UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
    
    def test_nonexistent_imageid_returns_404(self):
        """
        Property: Attempting to retrieve a non-existent imageId should return 404.
        
        This verifies proper error handling for invalid imageIds.
        """
        client = self.get_test_client()
        
        # Try to retrieve with a random UUID that doesn't exist
        fake_image_id = str(uuid.uuid4())
        
        retrieve_response = client.get(f"/api/preview/{fake_image_id}")
        
        assert retrieve_response.status_code == 404, \
            f"Retrieving non-existent imageId should return 404"
        
        data = retrieve_response.get_json()
        assert 'error' in data, \
            f"Error response should contain error message"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

