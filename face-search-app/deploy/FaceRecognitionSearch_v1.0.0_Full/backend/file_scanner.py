"""
File System Scanner Module for scanning folders and finding image files.
Recursively scans directories to find all supported image formats.
"""

import os
from typing import List
from models import ScanResult
from config import SUPPORTED_EXTENSIONS


class FileSystemScannerModule:
    """
    Module for scanning file system folders to find image files.
    
    Recursively traverses directories and filters for supported image formats.
    Validates folder paths and access permissions.
    """
    
    def __init__(self):
        """Initialize the FileSystemScannerModule."""
        pass
    
    def scanFolder(self, folder_path: str) -> ScanResult:
        """
        Scan a folder recursively to find all supported image files.
        
        Args:
            folder_path: Path to the folder to scan
            
        Returns:
            ScanResult containing list of image paths and total count
            
        Requirements:
            - Validates folder path exists (Requirement 3.2)
            - Validates folder is accessible (Requirement 3.3)
            - Recursively scans all subfolders (Requirement 3.4)
            - Filters for supported formats: .jpg, .jpeg, .png, .webp (Requirement 3.4)
        """
        # Validate folder path exists
        if not os.path.exists(folder_path):
            return ScanResult(
                imagePaths=[],
                totalCount=0,
                error=f"Folder path does not exist: {folder_path}"
            )
        
        # Validate it's a directory
        if not os.path.isdir(folder_path):
            return ScanResult(
                imagePaths=[],
                totalCount=0,
                error=f"Path is not a directory: {folder_path}"
            )
        
        # Validate folder is accessible (check read permission)
        if not os.access(folder_path, os.R_OK):
            return ScanResult(
                imagePaths=[],
                totalCount=0,
                error=f"Folder is not accessible (no read permission): {folder_path}"
            )
        
        # Scan folder recursively for image files
        image_paths = []
        
        try:
            # Use os.walk() to recursively traverse the directory tree
            for root, dirs, files in os.walk(folder_path):
                # Filter files by supported image extensions
                for file in files:
                    # Get file extension (lowercase for case-insensitive comparison)
                    _, ext = os.path.splitext(file)
                    ext_lower = ext.lower()
                    
                    # Check if extension is supported
                    if ext_lower in SUPPORTED_EXTENSIONS:
                        # Build full path to the image file
                        full_path = os.path.join(root, file)
                        image_paths.append(full_path)
            
            return ScanResult(
                imagePaths=image_paths,
                totalCount=len(image_paths),
                error=None
            )
            
        except PermissionError as e:
            return ScanResult(
                imagePaths=[],
                totalCount=0,
                error=f"Permission denied while scanning folder: {str(e)}"
            )
        except Exception as e:
            return ScanResult(
                imagePaths=[],
                totalCount=0,
                error=f"Error scanning folder: {str(e)}"
            )
