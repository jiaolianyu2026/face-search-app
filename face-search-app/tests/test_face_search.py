"""
Unit tests for FaceSearchModule.
Tests search functionality, progress tracking, and cancellation.
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from face_search import FaceSearchModule
from models import Progress


class TestFaceSearchModule:
    """Unit tests for FaceSearchModule."""
    
    @pytest.fixture
    def search_module(self):
        """Create a FaceSearchModule instance."""
        return FaceSearchModule()
    
    @pytest.fixture
    def temp_search_folder(self):
        """Create a temporary folder with test images."""
        temp_dir = tempfile.mkdtemp()
        
        # Create some test images
        for i in range(3):
            img = Image.new('RGB', (100, 100), color=(i*80, i*80, i*80))
            img.save(os.path.join(temp_dir, f'test_image_{i}.jpg'))
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def target_features(self):
        """Create a sample 128-dimensional feature vector."""
        return np.random.rand(128).tolist()
    
    def test_search_empty_folder(self, search_module, target_features):
        """Test searching in an empty folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=0.6
            )
            
            assert result.matches == []
            assert result.totalProcessed == 0
            assert result.cancelled is False
    
    def test_search_nonexistent_folder(self, search_module, target_features):
        """Test searching in a non-existent folder."""
        result = search_module.searchFaces(
            targetFeatures=target_features,
            searchFolder='/nonexistent/folder',
            threshold=0.6
        )
        
        # Should return empty result without crashing
        assert result.matches == []
        assert result.totalProcessed == 0
    
    def test_search_with_progress_callback(self, search_module, temp_search_folder, target_features):
        """Test that progress callback is called during search."""
        progress_updates = []
        
        def progress_callback(progress: Progress):
            progress_updates.append({
                'current': progress.current,
                'total': progress.total,
                'currentFile': progress.currentFile,
                'percentage': progress.percentage
            })
        
        result = search_module.searchFaces(
            targetFeatures=target_features,
            searchFolder=temp_search_folder,
            threshold=0.6,
            progressCallback=progress_callback
        )
        
        # Should have received progress updates
        assert len(progress_updates) > 0
        
        # Final update should show completion
        final_update = progress_updates[-1]
        assert final_update['current'] == final_update['total']
        assert final_update['percentage'] == 100.0
    
    def test_search_cancellation(self, search_module, temp_search_folder, target_features):
        """Test that search can be cancelled."""
        call_count = [0]
        
        def progress_callback(progress: Progress):
            call_count[0] += 1
            # Cancel after first progress update
            if call_count[0] == 1:
                search_module.cancelSearch()
        
        result = search_module.searchFaces(
            targetFeatures=target_features,
            searchFolder=temp_search_folder,
            threshold=0.6,
            progressCallback=progress_callback
        )
        
        # Search should be marked as cancelled
        assert result.cancelled is True
        
        # Should have processed fewer images than total
        # (or possibly 0 if cancelled immediately)
        assert result.totalProcessed < 3 or result.totalProcessed == 0
    
    def test_search_threshold_filtering(self, search_module, target_features):
        """Test that results are filtered by threshold."""
        # This is a basic test - actual threshold filtering
        # is tested more thoroughly in property tests
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test image
            img = Image.new('RGB', (100, 100), color=(128, 128, 128))
            img.save(os.path.join(temp_dir, 'test.jpg'))
            
            # Search with very high threshold (unlikely to match)
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=0.99
            )
            
            # All matches should have similarity >= 0.99
            for match in result.matches:
                assert match.similarity >= 0.99
    
    def test_search_results_sorted_descending(self, search_module, target_features):
        """Test that results are sorted by similarity in descending order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test images
            for i in range(3):
                img = Image.new('RGB', (100, 100), color=(i*80, i*80, i*80))
                img.save(os.path.join(temp_dir, f'test_{i}.jpg'))
            
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=0.0  # Accept all matches
            )
            
            # Check that results are sorted descending
            for i in range(len(result.matches) - 1):
                assert result.matches[i].similarity >= result.matches[i + 1].similarity
    
    def test_search_skips_corrupted_files(self, search_module, target_features):
        """Test that search continues when encountering corrupted files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a valid image
            img = Image.new('RGB', (100, 100), color=(128, 128, 128))
            img.save(os.path.join(temp_dir, 'valid.jpg'))
            
            # Create a corrupted "image" (just text)
            with open(os.path.join(temp_dir, 'corrupted.jpg'), 'w') as f:
                f.write('This is not an image')
            
            # Search should not crash
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=0.6
            )
            
            # Should have processed both files (even if one failed)
            assert result.totalProcessed >= 1
            assert result.cancelled is False
    
    def test_search_uses_cache(self, search_module, temp_search_folder, target_features):
        """Test that search uses cached features on second run."""
        # First search - will populate cache
        result1 = search_module.searchFaces(
            targetFeatures=target_features,
            searchFolder=temp_search_folder,
            threshold=0.6
        )
        
        # Second search - should use cache
        result2 = search_module.searchFaces(
            targetFeatures=target_features,
            searchFolder=temp_search_folder,
            threshold=0.6
        )
        
        # Both should process same number of files
        assert result1.totalProcessed == result2.totalProcessed
        
        # Results should be consistent (same matches)
        assert len(result1.matches) == len(result2.matches)
    
    def test_search_with_different_thresholds(self, search_module, temp_search_folder, target_features):
        """Test that different thresholds produce different result counts."""
        # Search with low threshold
        result_low = search_module.searchFaces(
            targetFeatures=target_features,
            searchFolder=temp_search_folder,
            threshold=0.3
        )
        
        # Search with high threshold
        result_high = search_module.searchFaces(
            targetFeatures=target_features,
            searchFolder=temp_search_folder,
            threshold=0.9
        )
        
        # Lower threshold should have >= matches than higher threshold
        assert len(result_low.matches) >= len(result_high.matches)
