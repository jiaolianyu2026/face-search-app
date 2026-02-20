# -*- coding: utf-8 -*-
"""
Property-based tests for file system scanner functionality.
Uses hypothesis to generate random test cases and verify universal properties.

**Feature: face-recognition-search, Property 5: 文件夹路径验�?*
**Validates: Requirements 3.2, 3.3**
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from file_scanner import FileSystemScannerModule
from models import ScanResult


class TestProperty5_FolderPathValidation:
    """
    Property 5: 文件夹路径验�?
    
    对于任何文件夹路径输入，系统应当验证路径是否存在且可访问，无效路径应当返回错�?
    
    **Validates: Requirements 3.2, 3.3**
    """
    
    # Strategy for generating invalid path components
    invalid_path_components = st.sampled_from([
        'nonexistent',
        'does_not_exist',
        'invalid_folder',
        'missing_directory',
        'fake_path',
        '___invalid___',
        'no_such_folder'
    ])
    
    # Strategy for generating path depths
    path_depth = st.integers(min_value=1, max_value=5)
    
    @given(
        depth=st.integers(min_value=1, max_value=4),
        component=invalid_path_components
    )
    @settings(max_examples=3)
    def test_nonexistent_paths_return_error(self, depth, component):
        """
        Property: For any non-existent folder path, the system should return an error.
        
        This validates Requirement 3.2: System should validate that folder exists.
        """
        scanner = FileSystemScannerModule()
        
        # Build a path that definitely doesn't exist
        # Use a base that's unlikely to exist
        base_path = os.path.join(tempfile.gettempdir(), 'nonexistent_base_' + component)
        
        # Add depth to the path
        path_parts = [base_path]
        for i in range(depth):
            path_parts.append(f'level_{i}_{component}')
        
        nonexistent_path = os.path.join(*path_parts)
        
        # Ensure the path really doesn't exist
        assume(not os.path.exists(nonexistent_path))
        
        # Scan the non-existent path
        result = scanner.scanFolder(nonexistent_path)
        
        # Verify result is a ScanResult
        assert isinstance(result, ScanResult), \
            "Result should be a ScanResult object"
        
        # Verify error is returned
        assert result.error is not None, \
            f"Non-existent path '{nonexistent_path}' should return an error"
        
        assert "does not exist" in result.error.lower() or "not found" in result.error.lower(), \
            f"Error message should indicate path doesn't exist, got: {result.error}"
        
        # Verify no images are returned
        assert len(result.imagePaths) == 0, \
            "Non-existent path should return empty image list"
        
        assert result.totalCount == 0, \
            "Non-existent path should return totalCount of 0"
    
    @given(
        filename=st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=5,
            max_size=20
        ).filter(lambda x: '/' not in x and '\\' not in x)
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_file_paths_instead_of_directories_return_error(self, filename, tmp_path):
        """
        Property: For any file path (not a directory), the system should return an error.
        
        This validates Requirement 3.2: System should validate that path is a directory.
        """
        scanner = FileSystemScannerModule()
        
        # Create a file (not a directory)
        file_path = tmp_path / f"{filename}.txt"
        file_path.touch()
        
        # Verify it's a file
        assert os.path.isfile(str(file_path))
        
        # Try to scan the file path
        result = scanner.scanFolder(str(file_path))
        
        # Verify result is a ScanResult
        assert isinstance(result, ScanResult), \
            "Result should be a ScanResult object"
        
        # Verify error is returned
        assert result.error is not None, \
            f"File path '{file_path}' should return an error"
        
        assert "not a directory" in result.error.lower(), \
            f"Error message should indicate path is not a directory, got: {result.error}"
        
        # Verify no images are returned
        assert len(result.imagePaths) == 0, \
            "File path should return empty image list"
        
        assert result.totalCount == 0, \
            "File path should return totalCount of 0"
    
    @given(
        folder_name=st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=5,
            max_size=20
        ).filter(lambda x: '/' not in x and '\\' not in x)
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_valid_accessible_paths_return_no_error(self, folder_name, tmp_path):
        """
        Property: For any valid and accessible folder path, the system should not return an error.
        
        This validates Requirements 3.2 and 3.3: System should accept valid, accessible paths.
        """
        scanner = FileSystemScannerModule()
        
        # Create a valid directory
        valid_folder = tmp_path / folder_name
        valid_folder.mkdir()
        
        # Verify it exists and is a directory
        assert os.path.exists(str(valid_folder))
        assert os.path.isdir(str(valid_folder))
        
        # Scan the valid folder
        result = scanner.scanFolder(str(valid_folder))
        
        # Verify result is a ScanResult
        assert isinstance(result, ScanResult), \
            "Result should be a ScanResult object"
        
        # Verify no error is returned
        assert result.error is None, \
            f"Valid accessible path '{valid_folder}' should not return an error, got: {result.error}"
        
        # Verify result structure is valid
        assert isinstance(result.imagePaths, list), \
            "imagePaths should be a list"
        
        assert isinstance(result.totalCount, int), \
            "totalCount should be an integer"
        
        assert result.totalCount >= 0, \
            "totalCount should be non-negative"
        
        # For empty folder, should return empty list
        assert len(result.imagePaths) == 0, \
            "Empty folder should return empty image list"
        
        assert result.totalCount == 0, \
            "Empty folder should return totalCount of 0"
    
    @given(
        num_images=st.integers(min_value=1, max_value=10),
        extension=st.sampled_from(['.jpg', '.jpeg', '.png', '.webp'])
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_valid_paths_with_images_return_correct_count(self, num_images, extension, tmp_path):
        """
        Property: For any valid folder with images, the system should return correct count.
        
        This validates that valid paths are processed correctly without errors.
        """
        scanner = FileSystemScannerModule()
        
        # Create a unique subdirectory for this test iteration
        import uuid
        test_dir = tmp_path / str(uuid.uuid4())
        test_dir.mkdir()
        
        # Create images in the folder
        for i in range(num_images):
            image_file = test_dir / f"image_{i}{extension}"
            image_file.touch()
        
        # Scan the folder
        result = scanner.scanFolder(str(test_dir))
        
        # Verify no error
        assert result.error is None, \
            f"Valid folder with images should not return error, got: {result.error}"
        
        # Verify correct count
        assert result.totalCount == num_images, \
            f"Should find {num_images} images, found {result.totalCount}"
        
        assert len(result.imagePaths) == num_images, \
            f"Should return {num_images} image paths, got {len(result.imagePaths)}"
    
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        depth=st.integers(min_value=1, max_value=3),
        images_per_level=st.integers(min_value=0, max_value=3)
    )
    def test_nested_valid_paths_return_no_error(self, depth, images_per_level, tmp_path):
        """
        Property: For any valid nested folder structure, the system should not return an error.
        
        This validates that complex valid paths are handled correctly.
        """
        scanner = FileSystemScannerModule()
        
        # Create a unique subdirectory for this test iteration
        import uuid
        test_root = tmp_path / str(uuid.uuid4())
        test_root.mkdir()
        
        # Create nested folder structure
        current_path = test_root
        total_images = 0
        
        for level in range(depth):
            # Create images at current level
            for i in range(images_per_level):
                image_file = current_path / f"image_level{level}_{i}.jpg"
                image_file.touch()
                total_images += 1
            
            # Create subfolder for next level
            if level < depth - 1:
                current_path = current_path / f"subfolder_{level}"
                current_path.mkdir()
        
        # Scan from the root
        result = scanner.scanFolder(str(test_root))
        
        # Verify no error
        assert result.error is None, \
            f"Valid nested folder structure should not return error, got: {result.error}"
        
        # Verify all images are found
        assert result.totalCount == total_images, \
            f"Should find all {total_images} images in nested structure, found {result.totalCount}"
        
        assert len(result.imagePaths) == total_images, \
            f"Should return {total_images} image paths, got {len(result.imagePaths)}"
    
    def test_permission_denied_paths_return_error(self, tmp_path):
        """
        Property: For any folder without read permissions, the system should return an error.
        
        This validates Requirement 3.3: System should validate folder is accessible.
        
        Note: This test is platform-dependent and may be skipped on Windows.
        """
        scanner = FileSystemScannerModule()
        import platform
        
        # Skip on Windows as chmod doesn't work the same way
        if platform.system() == 'Windows':
            pytest.skip("Permission testing not reliable on Windows")
        
        # Create a folder
        restricted_folder = tmp_path / "restricted"
        restricted_folder.mkdir()
        
        # Add a test image
        (restricted_folder / "test.jpg").touch()
        
        try:
            # Remove read permissions (Unix-like systems)
            os.chmod(restricted_folder, 0o000)
            
            # Try to scan the restricted folder
            result = scanner.scanFolder(str(restricted_folder))
            
            # Should return error about access
            assert result.error is not None, \
                "Folder without read permissions should return an error"
            
            assert "not accessible" in result.error.lower() or "permission" in result.error.lower(), \
                f"Error should mention access/permission issue, got: {result.error}"
            
            # Should return empty results
            assert len(result.imagePaths) == 0, \
                "Inaccessible folder should return empty image list"
            
            assert result.totalCount == 0, \
                "Inaccessible folder should return totalCount of 0"
            
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(restricted_folder, 0o755)
            except:
                pass
    
    @given(
        special_chars=st.sampled_from([
            'folder with spaces',
            'folder-with-dashes',
            'folder_with_underscores',
            'folder.with.dots',
            'folder(with)parens'
        ])
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_paths_with_special_characters_are_handled(self, special_chars, tmp_path):
        """
        Property: For any valid folder path with special characters, the system should handle it correctly.
        
        This validates that the path validation is robust to various valid path formats.
        """
        scanner = FileSystemScannerModule()
        
        # Create folder with special characters
        special_folder = tmp_path / special_chars
        special_folder.mkdir()
        
        # Add a test image
        (special_folder / "test.jpg").touch()
        
        # Scan the folder
        result = scanner.scanFolder(str(special_folder))
        
        # Should not return error for valid path with special chars
        assert result.error is None, \
            f"Valid path with special characters should not return error, got: {result.error}"
        
        # Should find the image
        assert result.totalCount == 1, \
            f"Should find 1 image in folder with special characters"
        
        assert len(result.imagePaths) == 1, \
            f"Should return 1 image path"
    
    def test_empty_string_path_returns_error(self):
        """
        Property: An empty string path should return an error.
        
        This validates edge case handling for invalid input.
        """
        scanner = FileSystemScannerModule()
        result = scanner.scanFolder("")
        
        assert result.error is not None, \
            "Empty string path should return an error"
        
        assert len(result.imagePaths) == 0, \
            "Empty string path should return empty image list"
        
        assert result.totalCount == 0, \
            "Empty string path should return totalCount of 0"
    
    @given(
        whitespace=st.sampled_from(['   ', '\t', '\n', '  \t  '])
    )
    @settings(max_examples=3)
    def test_whitespace_only_paths_return_error(self, whitespace):
        """
        Property: Paths containing only whitespace should return an error.
        
        This validates edge case handling for invalid input.
        """
        scanner = FileSystemScannerModule()
        result = scanner.scanFolder(whitespace)
        
        assert result.error is not None, \
            f"Whitespace-only path '{repr(whitespace)}' should return an error"
        
        assert len(result.imagePaths) == 0, \
            "Whitespace-only path should return empty image list"
        
        assert result.totalCount == 0, \
            "Whitespace-only path should return totalCount of 0"
    
    def test_relative_paths_are_handled(self, tmp_path):
        """
        Property: Relative paths should be handled correctly if they resolve to valid folders.
        
        This validates that the system can handle both absolute and relative paths.
        """
        scanner = FileSystemScannerModule()
        
        # Create a test folder
        test_folder = tmp_path / "test_relative"
        test_folder.mkdir()
        (test_folder / "image.jpg").touch()
        
        # Change to parent directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Use relative path
            result = scanner.scanFolder("test_relative")
            
            # Should work with relative path
            assert result.error is None, \
                f"Valid relative path should not return error, got: {result.error}"
            
            assert result.totalCount == 1, \
                "Should find 1 image using relative path"
            
        finally:
            # Restore original directory
            os.chdir(original_cwd)
    
    def test_absolute_paths_are_handled(self, tmp_path):
        """
        Property: Absolute paths should be handled correctly.
        
        This validates that the system properly handles absolute paths.
        """
        scanner = FileSystemScannerModule()
        
        # Create a test folder
        test_folder = tmp_path / "test_absolute"
        test_folder.mkdir()
        (test_folder / "image.jpg").touch()
        
        # Use absolute path
        absolute_path = str(test_folder.resolve())
        result = scanner.scanFolder(absolute_path)
        
        # Should work with absolute path
        assert result.error is None, \
            f"Valid absolute path should not return error, got: {result.error}"
        
        assert result.totalCount == 1, \
            "Should find 1 image using absolute path"
        
        # Returned paths should be absolute
        assert os.path.isabs(result.imagePaths[0]), \
            "Returned image paths should be absolute"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


class TestProperty6_RecursiveScanCompleteness:
    """
    Property 6: 递归扫描完整�?
    
    对于任何有效的文件夹路径，扫描结果应当包含该文件夹及所有子文件夹中的所有支持格式的图片文件
    
    **Validates: Requirements 3.4**
    """
    
    @given(
        num_levels=st.integers(min_value=1, max_value=4),
        images_per_level=st.integers(min_value=1, max_value=5),
        extension=st.sampled_from(['.jpg', '.jpeg', '.png', '.webp'])
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_images_in_nested_structure_are_found(self, num_levels, images_per_level, extension, tmp_path):
        """
        Property: For any valid folder with nested subfolders, all images should be found.
        
        This validates Requirement 3.4: System should recursively scan all subfolders.
        """
        scanner = FileSystemScannerModule()
        
        # Create a unique test directory
        import uuid
        test_root = tmp_path / str(uuid.uuid4())
        test_root.mkdir()
        
        # Track all created image paths
        expected_images = []
        
        # Create nested folder structure with images at each level
        def create_nested_structure(parent_path, current_level, max_level):
            # Create images at current level
            for i in range(images_per_level):
                image_file = parent_path / f"image_L{current_level}_N{i}{extension}"
                image_file.touch()
                expected_images.append(str(image_file))
            
            # Create subfolder and recurse if not at max depth
            if current_level < max_level:
                subfolder = parent_path / f"subfolder_{current_level}"
                subfolder.mkdir()
                create_nested_structure(subfolder, current_level + 1, max_level)
        
        # Build the nested structure
        create_nested_structure(test_root, 1, num_levels)
        
        # Scan the root folder
        result = scanner.scanFolder(str(test_root))
        
        # Verify no error
        assert result.error is None, \
            f"Valid nested folder should not return error, got: {result.error}"
        
        # Calculate expected total
        expected_total = num_levels * images_per_level
        
        # Verify all images are found
        assert result.totalCount == expected_total, \
            f"Should find all {expected_total} images across {num_levels} levels, found {result.totalCount}"
        
        assert len(result.imagePaths) == expected_total, \
            f"Should return {expected_total} image paths, got {len(result.imagePaths)}"
        
        # Verify all expected images are in the result
        result_paths_set = set(result.imagePaths)
        expected_paths_set = set(expected_images)
        
        assert result_paths_set == expected_paths_set, \
            f"Result should contain exactly the expected images. Missing: {expected_paths_set - result_paths_set}, Extra: {result_paths_set - expected_paths_set}"
    
    @given(
        num_subfolders=st.integers(min_value=2, max_value=5),
        images_per_folder=st.integers(min_value=1, max_value=4)
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_images_in_sibling_folders_are_found(self, num_subfolders, images_per_folder, tmp_path):
        """
        Property: For any folder with multiple sibling subfolders, all images should be found.
        
        This validates that recursive scanning covers all branches, not just one path.
        """
        scanner = FileSystemScannerModule()
        
        # Create a unique test directory
        import uuid
        test_root = tmp_path / str(uuid.uuid4())
        test_root.mkdir()
        
        # Track all created image paths
        expected_images = []
        
        # Create multiple sibling subfolders with images
        for folder_idx in range(num_subfolders):
            subfolder = test_root / f"folder_{folder_idx}"
            subfolder.mkdir()
            
            for img_idx in range(images_per_folder):
                image_file = subfolder / f"image_{img_idx}.jpg"
                image_file.touch()
                expected_images.append(str(image_file))
        
        # Scan the root folder
        result = scanner.scanFolder(str(test_root))
        
        # Verify no error
        assert result.error is None, \
            f"Valid folder structure should not return error, got: {result.error}"
        
        # Calculate expected total
        expected_total = num_subfolders * images_per_folder
        
        # Verify all images are found
        assert result.totalCount == expected_total, \
            f"Should find all {expected_total} images across {num_subfolders} sibling folders, found {result.totalCount}"
        
        assert len(result.imagePaths) == expected_total, \
            f"Should return {expected_total} image paths, got {len(result.imagePaths)}"
        
        # Verify all expected images are in the result
        result_paths_set = set(result.imagePaths)
        expected_paths_set = set(expected_images)
        
        assert result_paths_set == expected_paths_set, \
            f"Result should contain exactly the expected images"
    
    @given(
        extensions=st.lists(
            st.sampled_from(['.jpg', '.jpeg', '.png', '.webp']),
            min_size=2,
            max_size=4,
            unique=True
        ),
        images_per_extension=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_supported_formats_are_found(self, extensions, images_per_extension, tmp_path):
        """
        Property: For any folder with images of different supported formats, all should be found.
        
        This validates that the scanner correctly identifies all supported image formats.
        """
        scanner = FileSystemScannerModule()
        
        # Create a unique test directory
        import uuid
        test_root = tmp_path / str(uuid.uuid4())
        test_root.mkdir()
        
        # Track all created image paths
        expected_images = []
        
        # Create images with different extensions
        for ext in extensions:
            for i in range(images_per_extension):
                image_file = test_root / f"image_{ext.replace('.', '')}_{i}{ext}"
                image_file.touch()
                expected_images.append(str(image_file))
        
        # Scan the folder
        result = scanner.scanFolder(str(test_root))
        
        # Verify no error
        assert result.error is None, \
            f"Valid folder should not return error, got: {result.error}"
        
        # Calculate expected total
        expected_total = len(extensions) * images_per_extension
        
        # Verify all images are found
        assert result.totalCount == expected_total, \
            f"Should find all {expected_total} images of various formats, found {result.totalCount}"
        
        assert len(result.imagePaths) == expected_total, \
            f"Should return {expected_total} image paths, got {len(result.imagePaths)}"
        
        # Verify all expected images are in the result
        result_paths_set = set(result.imagePaths)
        expected_paths_set = set(expected_images)
        
        assert result_paths_set == expected_paths_set, \
            f"Result should contain exactly the expected images of all formats"
    
    @given(
        num_images=st.integers(min_value=1, max_value=5),
        num_non_images=st.integers(min_value=1, max_value=5),
        non_image_ext=st.sampled_from(['.txt', '.pdf', '.doc', '.gif', '.bmp', '.mp4', '.zip'])
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_only_supported_formats_are_included(self, num_images, num_non_images, non_image_ext, tmp_path):
        """
        Property: For any folder with mixed file types, only supported image formats should be found.
        
        This validates that the scanner filters correctly and doesn't include unsupported files.
        """
        scanner = FileSystemScannerModule()
        
        # Create a unique test directory
        import uuid
        test_root = tmp_path / str(uuid.uuid4())
        test_root.mkdir()
        
        # Create supported image files
        expected_images = []
        for i in range(num_images):
            image_file = test_root / f"image_{i}.jpg"
            image_file.touch()
            expected_images.append(str(image_file))
        
        # Create non-image files (should be ignored)
        for i in range(num_non_images):
            non_image_file = test_root / f"file_{i}{non_image_ext}"
            non_image_file.touch()
        
        # Scan the folder
        result = scanner.scanFolder(str(test_root))
        
        # Verify no error
        assert result.error is None, \
            f"Valid folder should not return error, got: {result.error}"
        
        # Verify only image files are found
        assert result.totalCount == num_images, \
            f"Should find only {num_images} image files, ignoring {num_non_images} non-image files, found {result.totalCount}"
        
        assert len(result.imagePaths) == num_images, \
            f"Should return only {num_images} image paths, got {len(result.imagePaths)}"
        
        # Verify all returned paths are the expected images
        result_paths_set = set(result.imagePaths)
        expected_paths_set = set(expected_images)
        
        assert result_paths_set == expected_paths_set, \
            f"Result should contain only supported image files"
        
        # Verify no non-image files are included
        for path in result.imagePaths:
            ext = os.path.splitext(path)[1].lower()
            assert ext in ['.jpg', '.jpeg', '.png', '.webp'], \
                f"Found unsupported file type: {path}"
    
    @given(
        depth=st.integers(min_value=2, max_value=5),
        images_at_root=st.integers(min_value=0, max_value=3),
        images_at_leaf=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_images_at_all_depths_are_found(self, depth, images_at_root, images_at_leaf, tmp_path):
        """
        Property: For any nested structure, images at all depths (root and leaf) should be found.
        
        This validates that scanning doesn't miss images at any level of the hierarchy.
        """
        scanner = FileSystemScannerModule()
        
        # Create a unique test directory
        import uuid
        test_root = tmp_path / str(uuid.uuid4())
        test_root.mkdir()
        
        # Track all created image paths
        expected_images = []
        
        # Create images at root level
        for i in range(images_at_root):
            image_file = test_root / f"root_image_{i}.jpg"
            image_file.touch()
            expected_images.append(str(image_file))
        
        # Create deep nested structure
        current_path = test_root
        for level in range(depth):
            current_path = current_path / f"level_{level}"
            current_path.mkdir()
        
        # Create images at the deepest level
        for i in range(images_at_leaf):
            image_file = current_path / f"leaf_image_{i}.jpg"
            image_file.touch()
            expected_images.append(str(image_file))
        
        # Scan from root
        result = scanner.scanFolder(str(test_root))
        
        # Verify no error
        assert result.error is None, \
            f"Valid nested structure should not return error, got: {result.error}"
        
        # Calculate expected total
        expected_total = images_at_root + images_at_leaf
        
        # Verify all images are found
        assert result.totalCount == expected_total, \
            f"Should find all {expected_total} images (root and leaf), found {result.totalCount}"
        
        assert len(result.imagePaths) == expected_total, \
            f"Should return {expected_total} image paths, got {len(result.imagePaths)}"
        
        # Verify all expected images are in the result
        result_paths_set = set(result.imagePaths)
        expected_paths_set = set(expected_images)
        
        assert result_paths_set == expected_paths_set, \
            f"Result should contain images from all depths"
    
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        case_variant=st.sampled_from([
            ('image.JPG', True),
            ('image.Jpg', True),
            ('image.jPg', True),
            ('image.JPEG', True),
            ('image.PNG', True),
            ('image.WEBP', True),
            ('image.jpg', True),
            ('image.GIF', False),
            ('image.BMP', False)
        ])
    )
    def test_case_insensitive_extension_matching(self, case_variant, tmp_path):
        """
        Property: For any image file with extension in any case, supported formats should be found.
        
        This validates that extension matching is case-insensitive.
        """
        scanner = FileSystemScannerModule()
        filename, should_be_found = case_variant
        
        # Create a unique test directory
        import uuid
        test_root = tmp_path / str(uuid.uuid4())
        test_root.mkdir()
        
        # Create file with the specified case
        image_file = test_root / filename
        image_file.touch()
        
        # Scan the folder
        result = scanner.scanFolder(str(test_root))
        
        # Verify no error
        assert result.error is None, \
            f"Valid folder should not return error, got: {result.error}"
        
        # Verify correct behavior based on whether it should be found
        if should_be_found:
            assert result.totalCount == 1, \
                f"File '{filename}' with supported extension should be found"
            assert len(result.imagePaths) == 1, \
                f"Should return 1 image path for '{filename}'"
        else:
            assert result.totalCount == 0, \
                f"File '{filename}' with unsupported extension should not be found"
            assert len(result.imagePaths) == 0, \
                f"Should return 0 image paths for '{filename}'"
    
    def test_empty_nested_folders_return_zero_images(self, tmp_path):
        """
        Property: For any nested folder structure with no images, scan should return zero images.
        
        This validates that empty nested structures are handled correctly.
        """
        scanner = FileSystemScannerModule()
        
        # Create a unique test directory
        import uuid
        test_root = tmp_path / str(uuid.uuid4())
        test_root.mkdir()
        
        # Create nested empty folders
        current_path = test_root
        for i in range(3):
            current_path = current_path / f"empty_{i}"
            current_path.mkdir()
        
        # Scan the root
        result = scanner.scanFolder(str(test_root))
        
        # Verify no error
        assert result.error is None, \
            f"Valid empty nested structure should not return error, got: {result.error}"
        
        # Verify no images found
        assert result.totalCount == 0, \
            "Empty nested structure should return 0 images"
        
        assert len(result.imagePaths) == 0, \
            "Empty nested structure should return empty image list"
    
    @given(
        num_branches=st.integers(min_value=2, max_value=4),
        depth_per_branch=st.integers(min_value=2, max_value=3),
        images_per_branch=st.integers(min_value=1, max_value=2)
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_complex_tree_structure_completeness(self, num_branches, depth_per_branch, images_per_branch, tmp_path):
        """
        Property: For any complex tree structure with multiple branches, all images should be found.
        
        This validates that recursive scanning handles complex directory trees correctly.
        """
        scanner = FileSystemScannerModule()
        
        # Create a unique test directory
        import uuid
        test_root = tmp_path / str(uuid.uuid4())
        test_root.mkdir()
        
        # Track all created image paths
        expected_images = []
        
        # Create multiple branches, each with its own depth
        for branch_idx in range(num_branches):
            branch_root = test_root / f"branch_{branch_idx}"
            branch_root.mkdir()
            
            # Create nested structure in this branch
            current_path = branch_root
            for depth_idx in range(depth_per_branch):
                # Add images at this level
                for img_idx in range(images_per_branch):
                    image_file = current_path / f"img_b{branch_idx}_d{depth_idx}_n{img_idx}.png"
                    image_file.touch()
                    expected_images.append(str(image_file))
                
                # Create next level
                if depth_idx < depth_per_branch - 1:
                    current_path = current_path / f"depth_{depth_idx}"
                    current_path.mkdir()
        
        # Scan the root
        result = scanner.scanFolder(str(test_root))
        
        # Verify no error
        assert result.error is None, \
            f"Valid complex tree should not return error, got: {result.error}"
        
        # Calculate expected total
        expected_total = num_branches * depth_per_branch * images_per_branch
        
        # Verify all images are found
        assert result.totalCount == expected_total, \
            f"Should find all {expected_total} images in complex tree, found {result.totalCount}"
        
        assert len(result.imagePaths) == expected_total, \
            f"Should return {expected_total} image paths, got {len(result.imagePaths)}"
        
        # Verify all expected images are in the result
        result_paths_set = set(result.imagePaths)
        expected_paths_set = set(expected_images)
        
        assert result_paths_set == expected_paths_set, \
            f"Result should contain all images from complex tree structure"


