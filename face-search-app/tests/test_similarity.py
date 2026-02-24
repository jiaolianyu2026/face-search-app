"""
Unit tests for similarity computation functionality.
Tests specific examples and edge cases for cosine similarity calculation.
"""

import pytest
import os
import sys
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from similarity import SimilarityModule


class TestSimilarityModule:
    """Unit tests for SimilarityModule class."""
    
    def test_identical_vectors_have_similarity_one(self):
        """
        Test that identical feature vectors have similarity score of 1.0.
        
        This verifies the basic property that a face compared to itself
        should have perfect similarity.
        """
        similarity_module = SimilarityModule()
        
        # Create a random 128-dimensional vector
        features = np.random.rand(128).tolist()
        
        # Compute similarity with itself
        similarity = similarity_module.computeSimilarity(features, features)
        
        # Should be exactly 1.0 (or very close due to floating point)
        assert abs(similarity - 1.0) < 1e-6, \
            f"Identical vectors should have similarity 1.0, got {similarity}"
    
    def test_orthogonal_vectors_have_low_similarity(self):
        """
        Test that orthogonal (perpendicular) vectors have similarity close to 0.
        
        Orthogonal vectors have dot product of 0, so cosine similarity should be 0.
        """
        similarity_module = SimilarityModule()
        
        # Create two orthogonal vectors in 128 dimensions
        # Simple approach: first half of v1 is 1, second half is 0
        #                  first half of v2 is 0, second half is 1
        features1 = [1.0] * 64 + [0.0] * 64
        features2 = [0.0] * 64 + [1.0] * 64
        
        # Compute similarity
        similarity = similarity_module.computeSimilarity(features1, features2)
        
        # Should be 0.0 (or very close)
        assert abs(similarity) < 1e-6, \
            f"Orthogonal vectors should have similarity ~0, got {similarity}"
    
    def test_opposite_vectors_clamped_to_zero(self):
        """
        Test that opposite vectors (negative correlation) are clamped to 0.
        
        Cosine similarity can be negative for opposite vectors, but we clamp to [0, 1].
        """
        similarity_module = SimilarityModule()
        
        # Create opposite vectors
        features1 = [1.0] * 128
        features2 = [-1.0] * 128
        
        # Compute similarity
        similarity = similarity_module.computeSimilarity(features1, features2)
        
        # Should be clamped to 0.0
        assert similarity == 0.0, \
            f"Opposite vectors should be clamped to 0.0, got {similarity}"
    
    def test_similar_vectors_have_high_similarity(self):
        """
        Test that similar vectors have high similarity score.
        
        Vectors that differ slightly should have similarity close to 1.
        """
        similarity_module = SimilarityModule()
        
        # Create two similar vectors (second is first with small noise)
        np.random.seed(42)
        features1 = np.random.rand(128).tolist()
        features2 = (np.array(features1) + np.random.rand(128) * 0.01).tolist()
        
        # Compute similarity
        similarity = similarity_module.computeSimilarity(features1, features2)
        
        # Should be high (> 0.9)
        assert similarity > 0.9, \
            f"Similar vectors should have high similarity, got {similarity}"
    
    def test_different_vectors_have_lower_similarity(self):
        """
        Test that different random vectors have lower similarity.
        
        Random vectors should typically have moderate to low similarity.
        """
        similarity_module = SimilarityModule()
        
        # Create two different random vectors
        np.random.seed(42)
        features1 = np.random.rand(128).tolist()
        np.random.seed(123)
        features2 = np.random.rand(128).tolist()
        
        # Compute similarity
        similarity = similarity_module.computeSimilarity(features1, features2)
        
        # Should be less than 1.0 (not identical)
        assert similarity < 1.0, \
            f"Different vectors should have similarity < 1.0, got {similarity}"
        
        # Should be in valid range [0, 1]
        assert 0.0 <= similarity <= 1.0, \
            f"Similarity should be in [0, 1], got {similarity}"
    
    def test_zero_vector_returns_zero_similarity(self):
        """
        Test that zero vectors return 0 similarity (avoid division by zero).
        
        Zero vectors have no direction, so similarity is undefined.
        We return 0.0 to handle this gracefully.
        """
        similarity_module = SimilarityModule()
        
        # Create zero vector and normal vector
        features1 = [0.0] * 128
        features2 = [1.0] * 128
        
        # Compute similarity
        similarity = similarity_module.computeSimilarity(features1, features2)
        
        # Should be 0.0 (not undefined or error)
        assert similarity == 0.0, \
            f"Zero vector should have similarity 0.0, got {similarity}"
    
    def test_both_zero_vectors_return_zero_similarity(self):
        """
        Test that two zero vectors return 1.0 similarity.
        
        欧氏距离实现：两个零向量的欧氏距离 = 0，
        similarity = max(0, 1 - 0/1.0) = 1.0
        """
        similarity_module = SimilarityModule()
        
        # Create two zero vectors
        features1 = [0.0] * 128
        features2 = [0.0] * 128
        
        # Compute similarity
        similarity = similarity_module.computeSimilarity(features1, features2)
        
        # 欧氏距离为 0，相似度应为 1.0
        assert similarity == 1.0, \
            f"Two zero vectors (euclidean distance=0) should have similarity 1.0, got {similarity}"
    
    def test_normalized_vectors_similarity(self):
        """
        Test similarity computation with pre-normalized vectors.
        
        Face recognition libraries often return normalized feature vectors.
        """
        similarity_module = SimilarityModule()
        
        # Create normalized vectors (unit length)
        np.random.seed(42)
        v1 = np.random.rand(128)
        v1 = v1 / np.linalg.norm(v1)
        features1 = v1.tolist()
        
        v2 = np.random.rand(128)
        v2 = v2 / np.linalg.norm(v2)
        features2 = v2.tolist()
        
        # Compute similarity
        similarity = similarity_module.computeSimilarity(features1, features2)
        
        # Should be in valid range
        assert 0.0 <= similarity <= 1.0, \
            f"Similarity should be in [0, 1], got {similarity}"
    
    def test_invalid_different_length_vectors_raises_error(self):
        """
        Test that vectors of different lengths raise ValueError.
        """
        similarity_module = SimilarityModule()
        
        features1 = [1.0] * 128
        features2 = [1.0] * 64  # Wrong length
        
        with pytest.raises(ValueError, match="same length"):
            similarity_module.computeSimilarity(features1, features2)
    
    def test_empty_vectors_raise_error(self):
        """
        Test that empty vectors raise ValueError.
        """
        similarity_module = SimilarityModule()
        
        features1 = []
        features2 = []
        
        with pytest.raises(ValueError, match="cannot be empty"):
            similarity_module.computeSimilarity(features1, features2)
    
    def test_similarity_result_is_float(self):
        """
        Test that similarity result is always a Python float.
        """
        similarity_module = SimilarityModule()
        
        features1 = [1.0] * 128
        features2 = [1.0] * 128
        
        similarity = similarity_module.computeSimilarity(features1, features2)
        
        assert isinstance(similarity, float), \
            f"Similarity should be a float, got {type(similarity)}"
    
    def test_known_similarity_value(self):
        """
        Test with vectors that have a known euclidean distance similarity.
        
        对于向量 [1, 0, 0, ...] 和 [1, 1, 0, 0, ...]：
        欧氏距离 = sqrt((1-1)^2 + (0-1)^2) = sqrt(1) = 1.0
        similarity = max(0, 1 - 1.0/1.0) = 0.0
        """
        similarity_module = SimilarityModule()
        
        # Create vectors with known similarity
        # v1 = [1, 0, 0, ...] and v2 = [1, 1, 0, 0, ...]
        features1 = [1.0] + [0.0] * 127
        features2 = [1.0, 1.0] + [0.0] * 126
        
        # Compute similarity
        similarity = similarity_module.computeSimilarity(features1, features2)
        
        # 欧氏距离计算：
        # distance = sqrt((1-1)^2 + (0-1)^2) = 1.0
        # similarity = max(0, 1 - 1.0/1.0) = 0.0
        expected = 0.0
        
        assert abs(similarity - expected) < 1e-6, \
            f"Expected similarity {expected} (euclidean), got {similarity}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
