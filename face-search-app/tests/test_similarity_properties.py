# -*- coding: utf-8 -*-
"""
Property-based tests for similarity computation functionality.
Uses hypothesis to generate random test cases and verify universal properties.

**Feature: face-recognition-search, Property 19: 相似度计算对称�?*
**Feature: face-recognition-search, Property 20: 相似度范围约�?*
**Validates: Requirements 4.5 and implicit mathematical properties**
"""

import pytest
import os
import sys
import numpy as np
from hypothesis import given, strategies as st, settings, assume

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from similarity import SimilarityModule


# Strategy for generating valid 128-dimensional feature vectors
def feature_vector_strategy():
    """
    Generate random 128-dimensional feature vectors.
    
    Returns vectors with values in reasonable range for face features.
    """
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


class TestProperty19_SimilaritySymmetry:
    """
    Property 19: 相似度计算对称�?
    
    对于任何两个特征向量A和B，computeSimilarity(A, B)应当等于computeSimilarity(B, A)
    
    **Validates: Implicit mathematical property**
    """
    
    @given(
        features1=feature_vector_strategy(),
        features2=feature_vector_strategy()
    )
    @settings(max_examples=3, deadline=5000)
    def test_similarity_is_symmetric(self, features1, features2):
        """
        Property: Cosine similarity is symmetric.
        
        For any two feature vectors A and B:
            computeSimilarity(A, B) == computeSimilarity(B, A)
        
        This is a fundamental mathematical property of cosine similarity.
        
        **Validates: Implicit mathematical property**
        """
        # Skip if either vector is all zeros (undefined similarity)
        assume(not all(f == 0 for f in features1))
        assume(not all(f == 0 for f in features2))
        
        similarity_module = SimilarityModule()
        
        # Compute similarity in both directions
        similarity_ab = similarity_module.computeSimilarity(features1, features2)
        similarity_ba = similarity_module.computeSimilarity(features2, features1)
        
        # Should be equal (within floating point tolerance)
        assert abs(similarity_ab - similarity_ba) < 1e-10, \
            f"Similarity should be symmetric: " \
            f"computeSimilarity(A, B) = {similarity_ab}, " \
            f"computeSimilarity(B, A) = {similarity_ba}"
    
    @given(
        features=feature_vector_strategy()
    )
    @settings(max_examples=3, deadline=5000)
    def test_self_similarity_is_one_or_zero(self, features):
        """
        Property: A vector compared to itself has similarity 1.0 (or 0.0 if zero vector).
        
        For any feature vector A:
            computeSimilarity(A, A) == 1.0 (if A is non-zero)
            computeSimilarity(A, A) == 0.0 (if A is zero vector)
        
        **Validates: Implicit mathematical property**
        """
        similarity_module = SimilarityModule()
        
        # Compute self-similarity
        similarity = similarity_module.computeSimilarity(features, features)
        
        # Check if it's exactly a zero vector
        # Use numpy to compute norm for numerical stability
        norm = np.linalg.norm(features)
        is_zero_vector = (norm == 0.0)  # Exact zero check
        
        if is_zero_vector:
            # Zero vector should have similarity 0.0
            assert similarity == 0.0, \
                f"Zero vector (norm={norm}) should have self-similarity 0.0, got {similarity}"
        else:
            # Non-zero vector should have self-similarity 1.0
            # For very small but non-zero vectors, the result should still be 1.0
            # because mathematically a vector is always parallel to itself
            assert abs(similarity - 1.0) < 1e-6, \
                f"Non-zero vector (norm={norm}) should have self-similarity 1.0, got {similarity}"


class TestProperty20_SimilarityRangeConstraint:
    """
    Property 20: 相似度范围约�?
    
    对于任何两个有效的特征向量，计算得到的相似度分数应当在[0, 1]范围�?
    
    **Validates: Implicit mathematical property**
    """
    
    @given(
        features1=feature_vector_strategy(),
        features2=feature_vector_strategy()
    )
    @settings(max_examples=3, deadline=5000)
    def test_similarity_always_in_zero_to_one_range(self, features1, features2):
        """
        Property: Similarity score is always in [0, 1] range.
        
        For any two valid feature vectors A and B:
            0.0 <= computeSimilarity(A, B) <= 1.0
        
        This ensures the similarity score is always a valid probability-like value.
        
        **Validates: Implicit mathematical property, Requirement 4.5**
        """
        similarity_module = SimilarityModule()
        
        # Compute similarity
        similarity = similarity_module.computeSimilarity(features1, features2)
        
        # Verify range constraint
        assert 0.0 <= similarity <= 1.0, \
            f"Similarity must be in [0, 1] range, got {similarity}"
    
    @given(
        features1=feature_vector_strategy(),
        features2=feature_vector_strategy()
    )
    @settings(max_examples=3, deadline=5000)
    def test_similarity_is_finite(self, features1, features2):
        """
        Property: Similarity score is always a finite number.
        
        For any two valid feature vectors, the similarity should never be NaN or Inf.
        
        **Validates: Implicit mathematical property**
        """
        similarity_module = SimilarityModule()
        
        # Compute similarity
        similarity = similarity_module.computeSimilarity(features1, features2)
        
        # Verify it's finite
        assert np.isfinite(similarity), \
            f"Similarity must be finite, got {similarity}"
    
    @given(
        features1=feature_vector_strategy(),
        features2=feature_vector_strategy()
    )
    @settings(max_examples=3, deadline=5000)
    def test_similarity_is_python_float(self, features1, features2):
        """
        Property: Similarity score is always returned as a Python float.
        
        This ensures consistent type handling across the application.
        
        **Validates: Implementation requirement**
        """
        similarity_module = SimilarityModule()
        
        # Compute similarity
        similarity = similarity_module.computeSimilarity(features1, features2)
        
        # Verify it's a Python float (not numpy float)
        assert isinstance(similarity, float), \
            f"Similarity must be a Python float, got {type(similarity)}"
    
    @given(
        scale=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=3, deadline=5000)
    def test_similarity_invariant_to_scaling(self, scale):
        """
        Property: Cosine similarity is invariant to vector scaling.
        
        For any vectors A and B and positive scalar k:
            computeSimilarity(A, B) == computeSimilarity(k*A, B)
            computeSimilarity(A, B) == computeSimilarity(A, k*B)
            computeSimilarity(A, B) == computeSimilarity(k*A, k*B)
        
        This is because cosine similarity measures angle, not magnitude.
        
        **Validates: Implicit mathematical property**
        """
        similarity_module = SimilarityModule()
        
        # Create base vectors
        np.random.seed(42)
        features1 = np.random.rand(128).tolist()
        features2 = np.random.rand(128).tolist()
        
        # Compute base similarity
        base_similarity = similarity_module.computeSimilarity(features1, features2)
        
        # Scale first vector
        scaled_features1 = (np.array(features1) * scale).tolist()
        similarity_scaled_1 = similarity_module.computeSimilarity(scaled_features1, features2)
        
        # Scale second vector
        scaled_features2 = (np.array(features2) * scale).tolist()
        similarity_scaled_2 = similarity_module.computeSimilarity(features1, scaled_features2)
        
        # Scale both vectors
        similarity_scaled_both = similarity_module.computeSimilarity(scaled_features1, scaled_features2)
        
        # All should be equal (within floating point tolerance)
        tolerance = 1e-6
        assert abs(base_similarity - similarity_scaled_1) < tolerance, \
            f"Similarity should be invariant to scaling first vector: " \
            f"base={base_similarity}, scaled_1={similarity_scaled_1}"
        
        assert abs(base_similarity - similarity_scaled_2) < tolerance, \
            f"Similarity should be invariant to scaling second vector: " \
            f"base={base_similarity}, scaled_2={similarity_scaled_2}"
        
        assert abs(base_similarity - similarity_scaled_both) < tolerance, \
            f"Similarity should be invariant to scaling both vectors: " \
            f"base={base_similarity}, scaled_both={similarity_scaled_both}"
    
    @given(
        features1=feature_vector_strategy(),
        features2=feature_vector_strategy(),
        features3=feature_vector_strategy()
    )
    @settings(max_examples=3, deadline=5000)
    def test_triangle_inequality_property(self, features1, features2, features3):
        """
        Property: Similarity satisfies a form of triangle inequality.
        
        While cosine similarity doesn't satisfy the traditional triangle inequality,
        it does satisfy: if A is similar to B and B is similar to C,
        then A should have some similarity to C (transitivity of similarity).
        
        This is a weaker property but useful for face matching.
        
        **Validates: Implicit mathematical property**
        """
        # Skip zero vectors
        assume(not all(f == 0 for f in features1))
        assume(not all(f == 0 for f in features2))
        assume(not all(f == 0 for f in features3))
        
        similarity_module = SimilarityModule()
        
        # Compute pairwise similarities
        sim_ab = similarity_module.computeSimilarity(features1, features2)
        sim_bc = similarity_module.computeSimilarity(features2, features3)
        sim_ac = similarity_module.computeSimilarity(features1, features3)
        
        # All similarities should be in valid range
        assert 0.0 <= sim_ab <= 1.0, f"sim(A,B) out of range: {sim_ab}"
        assert 0.0 <= sim_bc <= 1.0, f"sim(B,C) out of range: {sim_bc}"
        assert 0.0 <= sim_ac <= 1.0, f"sim(A,C) out of range: {sim_ac}"
        
        # If A and B are very similar (>0.95) and B and C are very similar (>0.95),
        # then A and C should have reasonable similarity (not 0)
        if sim_ab > 0.95 and sim_bc > 0.95:
            # A and C should have some similarity (this is a weak constraint)
            # We don't enforce a specific value, just that it's not completely dissimilar
            assert sim_ac > 0.0, \
                f"If A≈B and B≈C, then A and C should have some similarity. " \
                f"Got sim(A,B)={sim_ab}, sim(B,C)={sim_bc}, sim(A,C)={sim_ac}"


class TestSimilarityEdgeCases:
    """
    Additional property tests for edge cases and error conditions.
    """
    
    @given(
        length=st.integers(min_value=1, max_value=256)
    )
    @settings(max_examples=3, deadline=5000)
    def test_different_length_vectors_raise_error(self, length):
        """
        Property: Vectors of different lengths always raise ValueError.
        
        **Validates: Input validation requirement**
        """
        assume(length != 128)  # Skip the valid length
        
        similarity_module = SimilarityModule()
        
        features1 = [1.0] * 128
        features2 = [1.0] * length
        
        with pytest.raises(ValueError, match="same length"):
            similarity_module.computeSimilarity(features1, features2)
    
    @given(
        features=feature_vector_strategy()
    )
    @settings(max_examples=3, deadline=5000)
    def test_zero_vector_always_returns_zero_similarity(self, features):
        """
        Property: Any vector compared to zero vector has similarity 0.0.
        
        **Validates: Edge case handling**
        """
        similarity_module = SimilarityModule()
        
        zero_vector = [0.0] * 128
        
        # Compute similarity with zero vector
        similarity = similarity_module.computeSimilarity(features, zero_vector)
        
        # Should always be 0.0
        assert similarity == 0.0, \
            f"Similarity with zero vector should be 0.0, got {similarity}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

