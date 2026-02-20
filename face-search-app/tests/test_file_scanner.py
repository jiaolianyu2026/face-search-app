"""
Unit tests for FileSystemScannerModule.
Tests folder scanning and image file discovery functionality.
"""

import pytest
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from file_scanner import FileSystemScannerModule
from models import ScanResult


class TestFileSystemScannerModule:
    """Test suite for FileSystemScannerModule."""
    
    @pytest.fixture
    def scanner(self):
        """Create a FileSystemScannerModule instance."""
        return FileSystemScannerModule()
    
    @pytest.fixture
    def test_folder_structure(self, tmp_path):
        """
        Create a test folder structure with various files.
        
        Structure:
        tmp_path/
        ├── image1.jpg
        ├── image2.png
        ├── image3.webp
        ├── document.txt
        ├── subfolder1/
        │   ├── image4.jpeg
        │   └── image5.jpg
        └── subfolder2/
            ├── nested/
            │   └── image6.png
            └── video.mp4
        """
        # Create root level files
        (tmp_path / "image1.jpg").touch()
        (tmp_path / "image2.png").touch()
        (tmp_path / "image3.webp").touch()
        (tmp_path / "document.txt").touch()
        
        # Create subfolder1 with images
        subfolder1 = tmp_path / "subfolder1"
        subfolder1.mkdir()
        (subfolder1 / "image4.jpeg").touch()
        (subfolder1 / "image5.jpg").touch()
        
        # Create subfolder2 with nested folder
        subfolder2 = tmp_path / "subfolder2"
        subfolder2.mkdir()
        (subfolder2 / "video.mp4").touch()
        
        nested = subfolder2 / "nested"
        nested.mkdir()
        (nested / "image6.png").touch()
        
        return tmp_path
    
    def test_scanFolder_returns_scan_result(self, scanner, test_folder_structure):
        """Test that scanFolder returns a ScanResult object."""
        result = scanner.scanFolder(str(test_folder_structure))
        assert isinstance(result, ScanResult)
    
    def test_scanFolder_nonexistent_path(self, scanner):
        """Test that scanFolder handles nonexistent paths gracefully."""
        result = scanner.scanFolder("/nonexistent/path/to/folder")
        
        assert isinstance(result, ScanResult)
        assert result.error is not None
        assert "does not exist" in result.error.lower()
        assert len(result.imagePaths) == 0
        assert result.totalCount == 0
    
    def test_scanFolder_file_instead_of_directory(self, scanner, tmp_path):
        """Test that scanFolder handles file paths (not directories) gracefully."""
        # Create a file
        file_path = tmp_path / "test.txt"
        file_path.touch()
        
        result = scanner.scanFolder(str(file_path))
        
        assert isinstance(result, ScanResult)
        assert result.error is not None
        assert "not a directory" in result.error.lower()
        assert len(result.imagePaths) == 0
    
    def test_scanFolder_empty_folder(self, scanner, tmp_path):
        """Test scanning an empty folder."""
        empty_folder = tmp_path / "empty"
        empty_folder.mkdir()
        
        result = scanner.scanFolder(str(empty_folder))
        
        assert isinstance(result, ScanResult)
        assert result.error is None
        assert len(result.imagePaths) == 0
        assert result.totalCount == 0
    
    def test_scanFolder_finds_all_supported_formats(self, scanner, test_folder_structure):
        """Test that scanFolder finds all supported image formats."""
        result = scanner.scanFolder(str(test_folder_structure))
        
        assert result.error is None
        assert len(result.imagePaths) == 6  # Should find 6 image files
        assert result.totalCount == 6
        
        # Verify all paths are absolute
        for path in result.imagePaths:
            assert os.path.isabs(path)
        
        # Verify all supported formats are found
        extensions = [os.path.splitext(path)[1].lower() for path in result.imagePaths]
        assert '.jpg' in extensions or '.jpeg' in extensions
        assert '.png' in extensions
        assert '.webp' in extensions
    
    def test_scanFolder_filters_unsupported_formats(self, scanner, test_folder_structure):
        """Test that scanFolder filters out unsupported file formats."""
        result = scanner.scanFolder(str(test_folder_structure))
        
        # Should not include .txt or .mp4 files
        for path in result.imagePaths:
            ext = os.path.splitext(path)[1].lower()
            assert ext in ['.jpg', '.jpeg', '.png', '.webp']
            assert ext not in ['.txt', '.mp4', '.gif', '.bmp']
    
    def test_scanFolder_recursive_traversal(self, scanner, test_folder_structure):
        """Test that scanFolder recursively scans all subfolders."""
        result = scanner.scanFolder(str(test_folder_structure))
        
        # Should find images in root, subfolder1, and subfolder2/nested
        assert result.error is None
        assert len(result.imagePaths) == 6
        
        # Verify images from different levels are found
        paths_str = '\n'.join(result.imagePaths)
        assert 'image1.jpg' in paths_str  # Root level
        assert 'image4.jpeg' in paths_str or 'image5.jpg' in paths_str  # subfolder1
        assert 'image6.png' in paths_str  # subfolder2/nested
    
    def test_scanFolder_case_insensitive_extensions(self, scanner, tmp_path):
        """Test that scanFolder handles case-insensitive file extensions."""
        # Create files with various case extensions
        (tmp_path / "image1.JPG").touch()
        (tmp_path / "image2.Png").touch()
        (tmp_path / "image3.WEBP").touch()
        (tmp_path / "image4.JpEg").touch()
        
        result = scanner.scanFolder(str(tmp_path))
        
        assert result.error is None
        assert len(result.imagePaths) == 4
        assert result.totalCount == 4
    
    def test_scanFolder_mixed_content(self, scanner, tmp_path):
        """Test scanning folder with mixed image and non-image files."""
        # Create various files
        (tmp_path / "photo.jpg").touch()
        (tmp_path / "document.pdf").touch()
        (tmp_path / "picture.png").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "image.webp").touch()
        (tmp_path / "video.avi").touch()
        
        result = scanner.scanFolder(str(tmp_path))
        
        assert result.error is None
        assert len(result.imagePaths) == 3  # Only jpg, png, webp
        assert result.totalCount == 3
    
    def test_scanFolder_returns_full_paths(self, scanner, test_folder_structure):
        """Test that scanFolder returns complete absolute paths."""
        result = scanner.scanFolder(str(test_folder_structure))
        
        for path in result.imagePaths:
            # Verify path is absolute
            assert os.path.isabs(path)
            # Verify path starts with the test folder
            assert path.startswith(str(test_folder_structure))
            # Verify file exists
            assert os.path.exists(path)
    
    def test_scanFolder_handles_special_characters_in_filenames(self, scanner, tmp_path):
        """Test that scanFolder handles filenames with special characters."""
        # Create files with special characters
        (tmp_path / "image with spaces.jpg").touch()
        (tmp_path / "image-with-dashes.png").touch()
        (tmp_path / "image_with_underscores.webp").touch()
        (tmp_path / "image(1).jpeg").touch()
        
        result = scanner.scanFolder(str(tmp_path))
        
        assert result.error is None
        assert len(result.imagePaths) == 4
        assert result.totalCount == 4
    
    def test_scanFolder_deeply_nested_structure(self, scanner, tmp_path):
        """Test scanning deeply nested folder structures."""
        # Create a deeply nested structure
        current = tmp_path
        for i in range(5):
            current = current / f"level{i}"
            current.mkdir()
            (current / f"image{i}.jpg").touch()
        
        result = scanner.scanFolder(str(tmp_path))
        
        assert result.error is None
        assert len(result.imagePaths) == 5
        assert result.totalCount == 5


class TestFileSystemScannerRequirements:
    """
    Test suite validating specific requirements for file system scanning.
    Tests Requirements 3.2, 3.3, 3.4
    """
    
    @pytest.fixture
    def scanner(self):
        """Create a FileSystemScannerModule instance."""
        return FileSystemScannerModule()
    
    def test_requirement_3_2_folder_existence_validation(self, scanner):
        """
        Test Requirement 3.2: Validate folder path exists.
        
        When user selects a folder, system should validate that the folder exists.
        """
        # Test with nonexistent path
        result = scanner.scanFolder("/this/path/does/not/exist")
        
        assert result.error is not None, "Should return error for nonexistent path"
        assert "does not exist" in result.error.lower()
        assert len(result.imagePaths) == 0
        assert result.totalCount == 0
    
    def test_requirement_3_3_folder_access_validation(self, scanner, tmp_path):
        """
        Test Requirement 3.3: Validate folder access permissions.
        
        When user selects a folder without access permissions,
        system should display error message.
        
        Note: This test is platform-dependent and may be skipped on Windows
        where permission handling differs from Unix-like systems.
        """
        import platform
        
        # Skip on Windows as chmod doesn't work the same way
        if platform.system() == 'Windows':
            pytest.skip("Permission testing not reliable on Windows")
        
        # Create a folder
        restricted_folder = tmp_path / "restricted"
        restricted_folder.mkdir()
        
        # Add a test image
        (restricted_folder / "test.jpg").touch()
        
        # Try to remove read permissions (Unix-like systems)
        try:
            os.chmod(restricted_folder, 0o000)
            
            result = scanner.scanFolder(str(restricted_folder))
            
            # Should return error about access
            assert result.error is not None
            assert "not accessible" in result.error.lower() or "permission" in result.error.lower()
            
            # Restore permissions for cleanup
            os.chmod(restricted_folder, 0o755)
        except (OSError, PermissionError):
            # Permission changes may not work on all systems
            # Skip this test on systems where we can't modify permissions
            pytest.skip("Cannot modify folder permissions on this system")
    
    def test_requirement_3_4_recursive_scan_all_subfolders(self, scanner, tmp_path):
        """
        Test Requirement 3.4: Recursively scan folder and all subfolders.
        
        When user selects a valid folder, system should recursively scan
        that folder and all subfolders for image files.
        """
        # Create a complex folder structure
        # root/
        #   ├── root_image.jpg
        #   ├── level1_a/
        #   │   ├── image_1a.png
        #   │   └── level2_a/
        #   │       └── image_2a.webp
        #   └── level1_b/
        #       ├── image_1b.jpeg
        #       └── document.txt
        
        root = tmp_path / "root"
        root.mkdir()
        (root / "root_image.jpg").touch()
        
        level1_a = root / "level1_a"
        level1_a.mkdir()
        (level1_a / "image_1a.png").touch()
        
        level2_a = level1_a / "level2_a"
        level2_a.mkdir()
        (level2_a / "image_2a.webp").touch()
        
        level1_b = root / "level1_b"
        level1_b.mkdir()
        (level1_b / "image_1b.jpeg").touch()
        (level1_b / "document.txt").touch()
        
        # Scan the root folder
        result = scanner.scanFolder(str(root))
        
        # Should find all 4 image files across all levels
        assert result.error is None, "Should scan successfully"
        assert len(result.imagePaths) == 4, "Should find all 4 images"
        assert result.totalCount == 4
        
        # Verify images from all levels are found
        paths_str = '\n'.join(result.imagePaths)
        assert 'root_image.jpg' in paths_str, "Should find root level image"
        assert 'image_1a.png' in paths_str, "Should find level 1 image"
        assert 'image_2a.webp' in paths_str, "Should find level 2 image"
        assert 'image_1b.jpeg' in paths_str, "Should find another level 1 image"
        
        # Verify non-image file is not included
        assert 'document.txt' not in paths_str, "Should not include non-image files"
    
    def test_requirement_3_4_supported_formats_filter(self, scanner, tmp_path):
        """
        Test Requirement 3.4: Filter for supported image formats.
        
        System should only include files with supported formats:
        .jpg, .jpeg, .png, .webp
        """
        # Create files with various formats
        supported_files = [
            "image1.jpg",
            "image2.jpeg",
            "image3.png",
            "image4.webp",
            "IMAGE5.JPG",  # Test case insensitivity
        ]
        
        unsupported_files = [
            "image.gif",
            "image.bmp",
            "image.tiff",
            "image.svg",
            "document.pdf",
            "video.mp4",
            "audio.mp3",
        ]
        
        for filename in supported_files:
            (tmp_path / filename).touch()
        
        for filename in unsupported_files:
            (tmp_path / filename).touch()
        
        result = scanner.scanFolder(str(tmp_path))
        
        # Should find only supported formats
        assert result.error is None
        assert len(result.imagePaths) == len(supported_files)
        assert result.totalCount == len(supported_files)
        
        # Verify only supported extensions are in results
        for path in result.imagePaths:
            ext = os.path.splitext(path)[1].lower()
            assert ext in ['.jpg', '.jpeg', '.png', '.webp']
        
        # Verify unsupported formats are not included
        paths_str = '\n'.join(result.imagePaths)
        for unsupported in unsupported_files:
            assert unsupported not in paths_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
