"""
Unit tests for core data models.
Tests validation logic and data structure integrity.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from models import Face, Match, Progress, SearchTask, UploadResult, DetectionResult


def test_face_creation():
    """Test Face model creation with valid data."""
    features = [0.1] * 128
    face = Face(
        faceId="face-123",
        boundingBox={"x": 10, "y": 20, "width": 100, "height": 120},
        features=features
    )
    assert face.faceId == "face-123"
    assert len(face.features) == 128
    assert face.boundingBox["x"] == 10


def test_face_invalid_features_dimension():
    """Test Face model rejects invalid feature dimensions."""
    features = [0.1] * 64  # Wrong dimension
    with pytest.raises(ValueError, match="128-dimensional"):
        Face(
            faceId="face-123",
            boundingBox={"x": 10, "y": 20, "width": 100, "height": 120},
            features=features
        )


def test_match_creation():
    """Test Match model creation with valid data."""
    match = Match(
        imagePath="/path/to/image.jpg",
        similarity=0.85,
        faceLocation={"x": 10, "y": 20, "width": 100, "height": 120}
    )
    assert match.imagePath == "/path/to/image.jpg"
    assert match.similarity == 0.85


def test_match_invalid_similarity():
    """Test Match model rejects invalid similarity values."""
    with pytest.raises(ValueError, match="between 0 and 1"):
        Match(
            imagePath="/path/to/image.jpg",
            similarity=1.5,  # Invalid
            faceLocation={"x": 10, "y": 20, "width": 100, "height": 120}
        )


def test_progress_calculation():
    """Test Progress model calculates percentage correctly."""
    progress = Progress(current=50, total=100)
    assert progress.percentage == 50.0
    
    progress2 = Progress(current=0, total=100)
    assert progress2.percentage == 0.0
    
    progress3 = Progress(current=100, total=100)
    assert progress3.percentage == 100.0


def test_progress_validation():
    """Test Progress model validates values."""
    with pytest.raises(ValueError, match="cannot exceed total"):
        Progress(current=150, total=100)
    
    with pytest.raises(ValueError, match="non-negative"):
        Progress(current=-1, total=100)


def test_search_task_creation():
    """Test SearchTask creation with factory method."""
    features = [0.1] * 128
    task = SearchTask.create(
        targetFeatures=features,
        searchFolder="/path/to/folder",
        threshold=0.7
    )
    assert task.taskId is not None
    assert len(task.taskId) > 0
    assert task.threshold == 0.7
    assert task.status == 'pending'
    assert len(task.results) == 0


def test_search_task_invalid_threshold():
    """Test SearchTask rejects invalid threshold values."""
    features = [0.1] * 128
    with pytest.raises(ValueError, match="between 0 and 1"):
        SearchTask(
            taskId="task-123",
            targetFeatures=features,
            searchFolder="/path/to/folder",
            threshold=1.5  # Invalid
        )


if __name__ == "__main__":
    # Run tests without pytest
    print("Running model tests...")
    
    try:
        test_face_creation()
        print("✓ test_face_creation passed")
    except Exception as e:
        print(f"✗ test_face_creation failed: {e}")
    
    try:
        test_face_invalid_features_dimension()
        print("✓ test_face_invalid_features_dimension passed")
    except Exception as e:
        print(f"✗ test_face_invalid_features_dimension failed: {e}")
    
    try:
        test_match_creation()
        print("✓ test_match_creation passed")
    except Exception as e:
        print(f"✗ test_match_creation failed: {e}")
    
    try:
        test_match_invalid_similarity()
        print("✓ test_match_invalid_similarity passed")
    except Exception as e:
        print(f"✗ test_match_invalid_similarity failed: {e}")
    
    try:
        test_progress_calculation()
        print("✓ test_progress_calculation passed")
    except Exception as e:
        print(f"✗ test_progress_calculation failed: {e}")
    
    try:
        test_progress_validation()
        print("✓ test_progress_validation passed")
    except Exception as e:
        print(f"✗ test_progress_validation failed: {e}")
    
    try:
        test_search_task_creation()
        print("✓ test_search_task_creation passed")
    except Exception as e:
        print(f"✗ test_search_task_creation failed: {e}")
    
    try:
        test_search_task_invalid_threshold()
        print("✓ test_search_task_invalid_threshold passed")
    except Exception as e:
        print(f"✗ test_search_task_invalid_threshold failed: {e}")
    
    print("\nAll tests completed!")
