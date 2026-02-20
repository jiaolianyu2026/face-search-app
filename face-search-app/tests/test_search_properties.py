# -*- coding: utf-8 -*-
"""
Property-based tests for face search functionality.
Uses hypothesis to generate random test cases and verify universal properties.

**Feature: face-recognition-search, Property 7: 搜索错误恢复**
**Feature: face-recognition-search, Property 8: 人脸比对完整�?*
**Feature: face-recognition-search, Property 9: 相似度阈值匹�?*
**Feature: face-recognition-search, Property 11: 结果排序不变�?*
**Feature: face-recognition-search, Property 12: 搜索进度信息完整�?*
**Feature: face-recognition-search, Property 13: 搜索取消有效�?*
**Validates: Requirements 4.2, 4.3, 4.4, 4.5, 5.1, 5.3, 6.2, 6.3, 6.4, 6.5**
"""

import pytest
import os
import sys
import tempfile
import shutil
import numpy as np
from pathlib import Path
from PIL import Image
from hypothesis import given, strategies as st, settings, assume

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from face_search import FaceSearchModule
from models import Progress


# Strategy for generating valid 128-dimensional feature vectors
def feature_vector_strategy():
    """Generate random 128-dimensional feature vectors."""
    return st.lists(
        st.floats(
            min_value=-10.0,
            max_value=10.0,
            allow_nan=False,
            allow_infinity=False
        ),
        min_size=128,
        max_size=128
    )


# Strategy for generating valid threshold values
def threshold_strategy():
    """Generate valid threshold values in [0, 1] range."""
    return st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


class TestProperty7_SearchErrorRecovery:
    """
    Property 7: 搜索错误恢复
    
    对于任何包含部分损坏或无法读取文件的文件夹，搜索应当跳过这些文件并继续处理其他有效文�?
    
    **Validates: Requirement 4.3**
    """
    
    @given(
        num_valid=st.integers(min_value=1, max_value=5),
        num_corrupted=st.integers(min_value=1, max_value=5),
        target_features=feature_vector_strategy(),
        threshold=threshold_strategy()
    )
    @settings(max_examples=3, deadline=10000)
    def test_search_continues_with_corrupted_files(self, num_valid, num_corrupted, target_features, threshold):
        """
        Property: Search continues processing when encountering corrupted files.
        
        For any folder containing both valid and corrupted image files:
            - Search should not crash
            - Search should process all valid files
            - totalProcessed should reflect files that were attempted
            - cancelled flag should be False
        
        **Validates: Requirement 4.3**
        """
        search_module = FaceSearchModule()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create valid images
            for i in range(num_valid):
                img = Image.new('RGB', (100, 100), color=(i*50, i*50, i*50))
                img.save(os.path.join(temp_dir, f'valid_{i}.jpg'))
            
            # Create corrupted "images" (text files with image extensions)
            for i in range(num_corrupted):
                with open(os.path.join(temp_dir, f'corrupted_{i}.jpg'), 'w') as f:
                    f.write(f'This is not an image file {i}')
            
            # Search should not crash
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=threshold
            )
            
            # Verify search completed without crashing
            assert result is not None, "Search should return a result even with corrupted files"
            
            # Verify search was not cancelled
            assert result.cancelled is False, "Search should not be marked as cancelled"
            
            # Verify some files were processed (at least attempted)
            total_files = num_valid + num_corrupted
            assert result.totalProcessed >= 0, "totalProcessed should be non-negative"
            assert result.totalProcessed <= total_files, \
                f"totalProcessed ({result.totalProcessed}) should not exceed total files ({total_files})"
            
            # Verify matches are valid (if any)
            for match in result.matches:
                assert match.similarity >= threshold, \
                    f"All matches should meet threshold: {match.similarity} >= {threshold}"
                assert os.path.exists(match.imagePath), \
                    f"Match path should exist: {match.imagePath}"
    
    @given(
        target_features=feature_vector_strategy(),
        threshold=threshold_strategy()
    )
    @settings(max_examples=3, deadline=10000)
    def test_search_handles_all_corrupted_files(self, target_features, threshold):
        """
        Property: Search handles folder with only corrupted files gracefully.
        
        For any folder containing only corrupted files:
            - Search should not crash
            - Search should return empty matches
            - cancelled flag should be False
        
        **Validates: Requirement 4.3**
        """
        search_module = FaceSearchModule()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create only corrupted files
            for i in range(3):
                with open(os.path.join(temp_dir, f'corrupted_{i}.png'), 'w') as f:
                    f.write(f'Corrupted data {i}')
            
            # Search should not crash
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=threshold
            )
            
            # Verify search completed
            assert result is not None
            assert result.cancelled is False
            
            # Should have no matches (all files corrupted)
            assert len(result.matches) == 0, "Should have no matches when all files are corrupted"


class TestProperty8_FaceComparisonCompleteness:
    """
    Property 8: 人脸比对完整�?
    
    对于任何搜索任务，搜索文件夹中所有检测到的人脸都应当与目标人脸特征进行相似度计算
    
    **Validates: Requirements 4.2, 4.4**
    """
    
    @given(
        num_images=st.integers(min_value=1, max_value=5),
        target_features=feature_vector_strategy(),
        threshold=threshold_strategy()
    )
    @settings(max_examples=3, deadline=10000)
    def test_all_detected_faces_are_compared(self, num_images, target_features, threshold):
        """
        Property: All detected faces in search folder are compared with target.
        
        For any search operation:
            - Every image in the folder should be processed
            - Every face detected should be compared
            - No faces should be skipped (unless file is corrupted)
        
        This property is verified indirectly by ensuring:
            1. totalProcessed matches the number of valid image files
            2. Search completes without errors
            3. Results are consistent across multiple runs
        
        **Validates: Requirements 4.2, 4.4**
        """
        search_module = FaceSearchModule()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test images
            for i in range(num_images):
                img = Image.new('RGB', (100, 100), color=(i*50, i*50, i*50))
                img.save(os.path.join(temp_dir, f'image_{i}.jpg'))
            
            # Perform search
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=threshold
            )
            
            # Verify all images were processed
            assert result.totalProcessed == num_images, \
                f"All {num_images} images should be processed, got {result.totalProcessed}"
            
            # Verify search completed
            assert result.cancelled is False
            
            # Verify all matches meet threshold
            for match in result.matches:
                assert match.similarity >= threshold
            
            # Run search again - should get consistent results (due to caching)
            result2 = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=threshold
            )
            
            # Results should be consistent
            assert result2.totalProcessed == result.totalProcessed, \
                "Repeated search should process same number of files"
            assert len(result2.matches) == len(result.matches), \
                "Repeated search should find same number of matches"


class TestProperty9_SimilarityThresholdMatching:
    """
    Property 9: 相似度阈值匹�?
    
    对于任何搜索结果，所有返回的匹配图片的相似度分数都应当大于或等于设定的阈�?
    
    **Validates: Requirements 4.5, 5.1**
    """
    
    @given(
        num_images=st.integers(min_value=1, max_value=10),
        target_features=feature_vector_strategy(),
        threshold=threshold_strategy()
    )
    @settings(max_examples=3, deadline=10000)
    def test_all_matches_meet_threshold(self, num_images, target_features, threshold):
        """
        Property: All search results have similarity >= threshold.
        
        For any search with threshold T:
            For all matches M in results:
                M.similarity >= T
        
        This is a critical correctness property ensuring the threshold filter works.
        
        **Validates: Requirements 4.5, 5.1**
        """
        search_module = FaceSearchModule()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test images
            for i in range(num_images):
                img = Image.new('RGB', (100, 100), color=(i*25, i*25, i*25))
                img.save(os.path.join(temp_dir, f'test_{i}.jpg'))
            
            # Perform search
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=threshold
            )
            
            # Verify ALL matches meet threshold
            for match in result.matches:
                assert match.similarity >= threshold, \
                    f"Match similarity {match.similarity} must be >= threshold {threshold}"
                
                # Also verify similarity is in valid range
                assert 0.0 <= match.similarity <= 1.0, \
                    f"Match similarity {match.similarity} must be in [0, 1] range"
    
    @given(
        target_features=feature_vector_strategy()
    )
    @settings(max_examples=3, deadline=10000)
    def test_higher_threshold_produces_fewer_or_equal_matches(self, target_features):
        """
        Property: Higher threshold produces fewer or equal matches.
        
        For any search folder and target features:
            matches(threshold=0.3) >= matches(threshold=0.7)
        
        This verifies the threshold filtering is monotonic.
        
        **Validates: Requirement 4.5**
        """
        search_module = FaceSearchModule()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test images
            for i in range(5):
                img = Image.new('RGB', (100, 100), color=(i*50, i*50, i*50))
                img.save(os.path.join(temp_dir, f'test_{i}.jpg'))
            
            # Search with low threshold
            result_low = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=0.3
            )
            
            # Search with high threshold
            result_high = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=0.7
            )
            
            # Lower threshold should have >= matches
            assert len(result_low.matches) >= len(result_high.matches), \
                f"Lower threshold (0.3) should have >= matches than higher threshold (0.7): " \
                f"{len(result_low.matches)} >= {len(result_high.matches)}"


class TestProperty11_ResultSortingInvariance:
    """
    Property 11: 结果排序不变�?
    
    对于任何搜索结果列表，匹配图片应当按相似度分数从高到低排�?
    
    **Validates: Requirement 5.3**
    """
    
    @given(
        num_images=st.integers(min_value=2, max_value=10),
        target_features=feature_vector_strategy(),
        threshold=st.floats(min_value=0.0, max_value=0.5)  # Low threshold to get more matches
    )
    @settings(max_examples=3, deadline=10000)
    def test_results_sorted_descending_by_similarity(self, num_images, target_features, threshold):
        """
        Property: Search results are always sorted by similarity in descending order.
        
        For any search results:
            For all i < j:
                results[i].similarity >= results[j].similarity
        
        This ensures users see the best matches first.
        
        **Validates: Requirement 5.3**
        """
        search_module = FaceSearchModule()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test images
            for i in range(num_images):
                img = Image.new('RGB', (100, 100), color=(i*25, i*25, i*25))
                img.save(os.path.join(temp_dir, f'test_{i}.jpg'))
            
            # Perform search
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=threshold
            )
            
            # Verify sorting (descending order)
            matches = result.matches
            
            for i in range(len(matches) - 1):
                current_similarity = matches[i].similarity
                next_similarity = matches[i + 1].similarity
                
                assert current_similarity >= next_similarity, \
                    f"Results must be sorted descending: " \
                    f"matches[{i}].similarity ({current_similarity}) >= " \
                    f"matches[{i+1}].similarity ({next_similarity})"
    
    @given(
        num_images=st.integers(min_value=1, max_value=8),
        target_features=feature_vector_strategy(),
        threshold=threshold_strategy()
    )
    @settings(max_examples=3, deadline=10000)
    def test_sorting_is_stable_across_runs(self, num_images, target_features, threshold):
        """
        Property: Sorting is consistent across multiple runs.
        
        For the same search parameters, results should be sorted the same way.
        
        **Validates: Requirement 5.3**
        """
        search_module = FaceSearchModule()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test images
            for i in range(num_images):
                img = Image.new('RGB', (100, 100), color=(i*30, i*30, i*30))
                img.save(os.path.join(temp_dir, f'test_{i}.jpg'))
            
            # Perform search twice
            result1 = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=threshold
            )
            
            result2 = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=threshold
            )
            
            # Both should have same number of matches
            assert len(result1.matches) == len(result2.matches)
            
            # Both should be sorted descending
            for i in range(len(result1.matches) - 1):
                assert result1.matches[i].similarity >= result1.matches[i + 1].similarity
            
            for i in range(len(result2.matches) - 1):
                assert result2.matches[i].similarity >= result2.matches[i + 1].similarity


class TestProperty12_SearchProgressCompleteness:
    """
    Property 12: 搜索进度信息完整�?
    
    对于任何搜索进度更新，Progress对象应当包含当前处理数量、总数量、当前文件路径和百分比信�?
    
    **Validates: Requirements 6.2, 6.3**
    """
    
    @given(
        num_images=st.integers(min_value=1, max_value=10),
        target_features=feature_vector_strategy(),
        threshold=threshold_strategy()
    )
    @settings(max_examples=3, deadline=10000)
    def test_progress_updates_contain_all_required_fields(self, num_images, target_features, threshold):
        """
        Property: All progress updates contain required fields.
        
        For any progress update during search:
            - progress.current is defined and >= 0
            - progress.total is defined and > 0
            - progress.percentage is defined and in [0, 100]
            - progress.currentFile is defined (may be None at end)
        
        **Validates: Requirements 6.2, 6.3**
        """
        search_module = FaceSearchModule()
        progress_updates = []
        
        def progress_callback(progress: Progress):
            progress_updates.append({
                'current': progress.current,
                'total': progress.total,
                'percentage': progress.percentage,
                'currentFile': progress.currentFile
            })
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test images
            for i in range(num_images):
                img = Image.new('RGB', (100, 100), color=(i*25, i*25, i*25))
                img.save(os.path.join(temp_dir, f'test_{i}.jpg'))
            
            # Perform search with progress callback
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=threshold,
                progressCallback=progress_callback
            )
            
            # Verify we received progress updates
            assert len(progress_updates) > 0, "Should receive at least one progress update"
            
            # Verify each progress update has all required fields
            for i, update in enumerate(progress_updates):
                # Check all fields exist
                assert 'current' in update, f"Update {i} missing 'current' field"
                assert 'total' in update, f"Update {i} missing 'total' field"
                assert 'percentage' in update, f"Update {i} missing 'percentage' field"
                assert 'currentFile' in update, f"Update {i} missing 'currentFile' field"
                
                # Verify field values
                assert update['current'] >= 0, \
                    f"Update {i}: current ({update['current']}) should be >= 0"
                assert update['total'] > 0, \
                    f"Update {i}: total ({update['total']}) should be > 0"
                assert update['current'] <= update['total'], \
                    f"Update {i}: current ({update['current']}) should be <= total ({update['total']})"
                assert 0.0 <= update['percentage'] <= 100.0, \
                    f"Update {i}: percentage ({update['percentage']}) should be in [0, 100]"
                
                # currentFile can be None (at the end) or a string
                assert update['currentFile'] is None or isinstance(update['currentFile'], str), \
                    f"Update {i}: currentFile should be None or string"
            
            # Final update should show completion
            final_update = progress_updates[-1]
            assert final_update['current'] == final_update['total'], \
                "Final progress update should show completion"
            assert final_update['percentage'] == 100.0, \
                "Final progress update should show 100%"
    
    @given(
        num_images=st.integers(min_value=2, max_value=8),
        target_features=feature_vector_strategy(),
        threshold=threshold_strategy()
    )
    @settings(max_examples=5, deadline=10000)
    def test_progress_updates_are_monotonic(self, num_images, target_features, threshold):
        """
        Property: Progress updates are monotonically increasing.
        
        For any sequence of progress updates:
            progress[i].current <= progress[i+1].current
            progress[i].percentage <= progress[i+1].percentage
        
        **Validates: Requirement 6.2**
        """
        search_module = FaceSearchModule()
        progress_updates = []
        
        def progress_callback(progress: Progress):
            progress_updates.append({
                'current': progress.current,
                'percentage': progress.percentage
            })
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test images
            for i in range(num_images):
                img = Image.new('RGB', (100, 100), color=(i*30, i*30, i*30))
                img.save(os.path.join(temp_dir, f'test_{i}.jpg'))
            
            # Perform search
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=threshold,
                progressCallback=progress_callback
            )
            
            # Verify progress is monotonic
            for i in range(len(progress_updates) - 1):
                current_progress = progress_updates[i]['current']
                next_progress = progress_updates[i + 1]['current']
                
                assert current_progress <= next_progress, \
                    f"Progress should be monotonic: " \
                    f"update[{i}].current ({current_progress}) <= " \
                    f"update[{i+1}].current ({next_progress})"
                
                current_percentage = progress_updates[i]['percentage']
                next_percentage = progress_updates[i + 1]['percentage']
                
                assert current_percentage <= next_percentage, \
                    f"Percentage should be monotonic: " \
                    f"update[{i}].percentage ({current_percentage}) <= " \
                    f"update[{i+1}].percentage ({next_percentage})"


class TestProperty13_SearchCancellationEffectiveness:
    """
    Property 13: 搜索取消有效�?
    
    对于任何正在运行的搜索任务，调用取消操作后，系统应当停止处理新文件，并保留已找到的结�?
    
    **Validates: Requirements 6.4, 6.5**
    """
    
    @given(
        num_images=st.integers(min_value=5, max_value=15),
        target_features=feature_vector_strategy(),
        threshold=threshold_strategy()
    )
    @settings(max_examples=3, deadline=10000)
    def test_cancellation_stops_processing(self, num_images, target_features, threshold):
        """
        Property: Cancelling search stops processing new files.
        
        For any search that is cancelled:
            - result.cancelled should be True
            - result.totalProcessed should be < total files (or 0-1 if cancelled early)
            - Partial results should be preserved
        
        **Validates: Requirements 6.4, 6.5**
        """
        search_module = FaceSearchModule()
        call_count = [0]
        
        def progress_callback(progress: Progress):
            call_count[0] += 1
            # Cancel after first progress update
            if call_count[0] == 1:
                search_module.cancelSearch()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test images
            for i in range(num_images):
                img = Image.new('RGB', (100, 100), color=(i*20, i*20, i*20))
                img.save(os.path.join(temp_dir, f'test_{i}.jpg'))
            
            # Perform search with cancellation
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=threshold,
                progressCallback=progress_callback
            )
            
            # Verify search was cancelled
            assert result.cancelled is True, "Search should be marked as cancelled"
            
            # Verify processing stopped early (or at least didn't process all)
            # Allow for 0-1 files processed if cancelled immediately
            assert result.totalProcessed < num_images or result.totalProcessed <= 1, \
                f"Cancelled search should process fewer files: " \
                f"{result.totalProcessed} < {num_images}"
            
            # Verify results are still valid (if any)
            for match in result.matches:
                assert match.similarity >= threshold
                assert os.path.exists(match.imagePath)
    
    @given(
        num_images=st.integers(min_value=3, max_value=10),
        target_features=feature_vector_strategy(),
        threshold=threshold_strategy()
    )
    @settings(max_examples=5, deadline=10000)
    def test_cancellation_preserves_partial_results(self, num_images, target_features, threshold):
        """
        Property: Cancelled search preserves results found before cancellation.
        
        For any cancelled search:
            - All matches in results should be valid
            - All matches should meet threshold
            - Results should be sorted descending
        
        **Validates: Requirement 6.5**
        """
        search_module = FaceSearchModule()
        call_count = [0]
        
        def progress_callback(progress: Progress):
            call_count[0] += 1
            # Cancel after processing a few files
            if progress.current >= 2:
                search_module.cancelSearch()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test images
            for i in range(num_images):
                img = Image.new('RGB', (100, 100), color=(i*25, i*25, i*25))
                img.save(os.path.join(temp_dir, f'test_{i}.jpg'))
            
            # Perform search with cancellation
            result = search_module.searchFaces(
                targetFeatures=target_features,
                searchFolder=temp_dir,
                threshold=threshold,
                progressCallback=progress_callback
            )
            
            # Verify cancellation
            assert result.cancelled is True
            
            # Verify all partial results are valid
            for match in result.matches:
                # Check threshold
                assert match.similarity >= threshold, \
                    f"Partial result should meet threshold: {match.similarity} >= {threshold}"
                
                # Check file exists
                assert os.path.exists(match.imagePath), \
                    f"Partial result path should exist: {match.imagePath}"
                
                # Check similarity range
                assert 0.0 <= match.similarity <= 1.0, \
                    f"Partial result similarity should be in [0, 1]: {match.similarity}"
            
            # Verify results are sorted
            for i in range(len(result.matches) - 1):
                assert result.matches[i].similarity >= result.matches[i + 1].similarity, \
                    "Partial results should still be sorted descending"
    
    @given(
        target_features=feature_vector_strategy(),
        threshold=threshold_strategy()
    )
    @settings(max_examples=3, deadline=10000)
    def test_cancel_search_returns_true(self, target_features, threshold):
        """
        Property: cancelSearch() always returns True.
        
        The cancelSearch method should always succeed and return True.
        
        **Validates: Requirement 6.4**
        """
        search_module = FaceSearchModule()
        
        # Cancel should always return True
        result = search_module.cancelSearch()
        assert result is True, "cancelSearch() should return True"
        
        # Verify cancelled flag is set
        assert search_module.cancelled is True, "cancelled flag should be set"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

