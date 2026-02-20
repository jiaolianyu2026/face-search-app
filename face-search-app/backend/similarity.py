"""
Similarity Module for computing similarity between face feature vectors.
Uses cosine similarity to compare 128-dimensional face feature vectors.
"""

import numpy as np
from typing import List


class SimilarityModule:
    """
    Module for computing similarity between face feature vectors.
    
    Uses cosine similarity to measure how similar two face feature vectors are.
    Cosine similarity ranges from 0 (completely different) to 1 (identical).
    """
    
    def __init__(self):
        """Initialize the SimilarityModule."""
        pass
    
    def computeSimilarity(self, features1: List[float], features2: List[float]) -> float:
        """
        Compute cosine similarity between two face feature vectors.
        
        The cosine similarity is calculated as:
            similarity = dot(v1, v2) / (norm(v1) * norm(v2))
        
        Args:
            features1: First 128-dimensional feature vector
            features2: Second 128-dimensional feature vector
            
        Returns:
            Similarity score between 0 and 1, where:
            - 1.0 means identical faces
            - 0.0 means completely different faces
            - Higher values indicate more similar faces
            
        Raises:
            ValueError: If feature vectors have different lengths or are invalid
        """
        # Validate input
        if len(features1) != len(features2):
            raise ValueError(
                f"Feature vectors must have the same length. "
                f"Got {len(features1)} and {len(features2)}"
            )
        
        if len(features1) == 0:
            raise ValueError("Feature vectors cannot be empty")
        
        # Convert to numpy arrays for efficient computation
        v1 = np.array(features1)
        v2 = np.array(features2)
        
        # Compute norms
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        # Handle zero vectors (avoid division by zero)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Compute cosine similarity
        dot_product = np.dot(v1, v2)
        similarity = dot_product / (norm1 * norm2)
        
        # Ensure result is in [0, 1] range
        # Cosine similarity can be negative for opposite vectors,
        # but for face features we clamp to [0, 1]
        similarity = float(np.clip(similarity, 0.0, 1.0))
        
        return similarity
