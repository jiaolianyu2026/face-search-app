"""
Unit tests for ImageExportModule.
Tests specific examples, edge cases, and error conditions.
"""

import os
import sys
import tempfile
import shutil
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from image_export import ImageExportModule
from models import ExportResult, Progress


class TestImageExportModule:
    """Unit tests for ImageExportModule."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        self.export_module = ImageExportModule()
        
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
    
    def test_export_single_image(self):
        """Test exporting a single image successfully."""
        # Create test file
        source_file = self._create_test_file('test.jpg', 'image data')
        
        # Export the file
        result = self.export_module.exportImages([source_file], self.target_dir)
        
        # Verify result
        assert result.successCount == 1
        assert result.failedCount == 0
        assert len(result.errors) == 0
        
        # Verify file was copied
        target_file = os.path.join(self.target_dir, 'test.jpg')
        assert os.path.exists(target_file)
        
        # Verify content
        with open(target_file, 'r') as f:
            assert f.read() == 'image data'
    
    def test_export_multiple_images(self):
        """Test exporting multiple images."""
        # Create test files
        source_files = [
            self._create_test_file('image1.jpg', 'data1'),
            self._create_test_file('image2.png', 'data2'),
            self._create_test_file('image3.webp', 'data3')
        ]
        
        # Export the files
        result = self.export_module.exportImages(source_files, self.target_dir)
        
        # Verify result
        assert result.successCount == 3
        assert result.failedCount == 0
        assert len(result.errors) == 0
        
        # Verify all files were copied
        assert os.path.exists(os.path.join(self.target_dir, 'image1.jpg'))
        assert os.path.exists(os.path.join(self.target_dir, 'image2.png'))
        assert os.path.exists(os.path.join(self.target_dir, 'image3.webp'))
    
    def test_filename_conflict_resolution(self):
        """Test automatic renaming when filename conflicts occur."""
        # Create source file
        source_file = self._create_test_file('photo.jpg', 'original')
        
        # Create existing file in target with same name
        existing_file = os.path.join(self.target_dir, 'photo.jpg')
        with open(existing_file, 'w') as f:
            f.write('existing')
        
        # Export the file
        result = self.export_module.exportImages([source_file], self.target_dir)
        
        # Verify result
        assert result.successCount == 1
        assert result.failedCount == 0
        
        # Verify original file unchanged
        with open(existing_file, 'r') as f:
            assert f.read() == 'existing'
        
        # Verify new file created with suffix
        renamed_file = os.path.join(self.target_dir, 'photo_1.jpg')
        assert os.path.exists(renamed_file)
        with open(renamed_file, 'r') as f:
            assert f.read() == 'original'
    
    def test_multiple_filename_conflicts(self):
        """Test renaming with multiple conflicts (photo.jpg, photo_1.jpg, photo_2.jpg)."""
        # Create source file
        source_file = self._create_test_file('image.png', 'new')
        
        # Create existing files with same base name
        with open(os.path.join(self.target_dir, 'image.png'), 'w') as f:
            f.write('existing1')
        with open(os.path.join(self.target_dir, 'image_1.png'), 'w') as f:
            f.write('existing2')
        
        # Export the file
        result = self.export_module.exportImages([source_file], self.target_dir)
        
        # Verify result
        assert result.successCount == 1
        assert result.failedCount == 0
        
        # Verify new file created with _2 suffix
        renamed_file = os.path.join(self.target_dir, 'image_2.png')
        assert os.path.exists(renamed_file)
        with open(renamed_file, 'r') as f:
            assert f.read() == 'new'
    
    def test_export_nonexistent_source_file(self):
        """Test handling of nonexistent source file."""
        # Try to export nonexistent file
        nonexistent_file = os.path.join(self.source_dir, 'missing.jpg')
        result = self.export_module.exportImages([nonexistent_file], self.target_dir)
        
        # Verify result
        assert result.successCount == 0
        assert result.failedCount == 1
        assert len(result.errors) == 1
        assert result.errors[0]['path'] == nonexistent_file
        assert 'does not exist' in result.errors[0]['error']
    
    def test_export_to_nonexistent_target_folder(self):
        """Test handling of nonexistent target folder."""
        # Create source file
        source_file = self._create_test_file('test.jpg')
        
        # Try to export to nonexistent folder
        nonexistent_folder = os.path.join(self.temp_dir, 'nonexistent')
        result = self.export_module.exportImages([source_file], nonexistent_folder)
        
        # Verify result
        assert result.successCount == 0
        assert result.failedCount == 1
        assert len(result.errors) == 1
        assert 'does not exist' in result.errors[0]['error']
    
    def test_export_mixed_success_and_failure(self):
        """Test exporting with some successes and some failures."""
        # Create valid source file
        valid_file = self._create_test_file('valid.jpg', 'valid')
        
        # Create list with valid and invalid files
        invalid_file = os.path.join(self.source_dir, 'invalid.jpg')
        files = [valid_file, invalid_file]
        
        # Export the files
        result = self.export_module.exportImages(files, self.target_dir)
        
        # Verify result
        assert result.successCount == 1
        assert result.failedCount == 1
        assert len(result.errors) == 1
        
        # Verify valid file was copied
        assert os.path.exists(os.path.join(self.target_dir, 'valid.jpg'))
    
    def test_export_empty_list(self):
        """Test exporting empty list of images."""
        result = self.export_module.exportImages([], self.target_dir)
        
        # Verify result
        assert result.successCount == 0
        assert result.failedCount == 0
        assert len(result.errors) == 0
    
    def test_export_preserves_metadata(self):
        """Test that file metadata (timestamps) are preserved."""
        # Create source file
        source_file = self._create_test_file('test.jpg', 'data')
        
        # Set specific modification time
        old_time = 1000000000.0  # Some timestamp in the past
        os.utime(source_file, (old_time, old_time))
        
        # Export the file
        result = self.export_module.exportImages([source_file], self.target_dir)
        
        # Verify success
        assert result.successCount == 1
        
        # Verify metadata preserved
        target_file = os.path.join(self.target_dir, 'test.jpg')
        target_mtime = os.path.getmtime(target_file)
        assert abs(target_mtime - old_time) < 1.0  # Allow small difference
    
    def test_progress_callback(self):
        """Test that progress callback is called during export."""
        # Create test files
        source_files = [
            self._create_test_file('img1.jpg'),
            self._create_test_file('img2.jpg'),
            self._create_test_file('img3.jpg')
        ]
        
        # Track progress updates
        progress_updates = []
        
        def callback(progress: Progress):
            progress_updates.append({
                'current': progress.current,
                'total': progress.total,
                'percentage': progress.percentage
            })
        
        # Export with callback
        result = self.export_module.exportImages(source_files, self.target_dir, callback)
        
        # Verify result
        assert result.successCount == 3
        
        # Verify progress updates were called
        assert len(progress_updates) > 0
        
        # Verify final progress
        final_progress = progress_updates[-1]
        assert final_progress['current'] == 3
        assert final_progress['total'] == 3
        assert final_progress['percentage'] == 100.0
    
    def test_statistics_accuracy(self):
        """Test that successCount + failedCount equals total images."""
        # Create mix of valid and invalid files
        valid1 = self._create_test_file('valid1.jpg')
        valid2 = self._create_test_file('valid2.jpg')
        invalid1 = os.path.join(self.source_dir, 'invalid1.jpg')
        invalid2 = os.path.join(self.source_dir, 'invalid2.jpg')
        
        files = [valid1, invalid1, valid2, invalid2]
        
        # Export the files
        result = self.export_module.exportImages(files, self.target_dir)
        
        # Verify statistics accuracy (Requirement 8.6, 8.7)
        assert result.successCount + result.failedCount == len(files)
        assert result.successCount == 2
        assert result.failedCount == 2
        assert len(result.errors) == 2
