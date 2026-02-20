"""
Core data model classes for face recognition search application.
Defines Face, Match, Progress, and SearchTask data structures.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
from datetime import datetime
import uuid


@dataclass
class Face:
    """
    Represents a detected face in an image.
    
    Attributes:
        faceId: Unique identifier for the face
        boundingBox: Dictionary with x, y, width, height coordinates
        features: 128-dimensional feature vector as a list of floats
    """
    faceId: str
    boundingBox: dict  # {x: int, y: int, width: int, height: int}
    features: List[float]  # 128-dimensional vector
    
    def __post_init__(self):
        """Validate face data after initialization."""
        if len(self.features) != 128:
            raise ValueError(f"Face features must be 128-dimensional, got {len(self.features)}")
        if not all(isinstance(coord, (int, float)) for coord in 
                   [self.boundingBox.get('x'), self.boundingBox.get('y'), 
                    self.boundingBox.get('width'), self.boundingBox.get('height')]):
            raise ValueError("BoundingBox must contain numeric x, y, width, height values")


@dataclass
class Match:
    """
    Represents a matching face found during search.
    
    Attributes:
        imagePath: Full path to the image file
        similarity: Similarity score between 0 and 1
        faceLocation: Dictionary with x, y, width, height coordinates
        thumbnailUrl: Optional URL to thumbnail image
    """
    imagePath: str
    similarity: float
    faceLocation: dict  # {x: int, y: int, width: int, height: int}
    thumbnailUrl: Optional[str] = None
    
    def __post_init__(self):
        """Validate match data after initialization."""
        if not 0 <= self.similarity <= 1:
            raise ValueError(f"Similarity must be between 0 and 1, got {self.similarity}")


@dataclass
class Progress:
    """
    Represents progress information for a long-running operation.
    
    Attributes:
        current: Current number of items processed
        total: Total number of items to process
        currentFile: Optional path to the file currently being processed
        percentage: Progress percentage between 0 and 100
    """
    current: int
    total: int
    currentFile: Optional[str] = None
    percentage: float = field(init=False)
    
    def __post_init__(self):
        """Calculate percentage after initialization."""
        if self.total > 0:
            self.percentage = (self.current / self.total) * 100
        else:
            self.percentage = 0.0
        
        # Validate values
        if self.current < 0 or self.total < 0:
            raise ValueError("Current and total must be non-negative")
        if self.current > self.total:
            raise ValueError("Current cannot exceed total")


@dataclass
class SearchTask:
    """
    Represents a face search task.
    
    Attributes:
        taskId: Unique identifier for the task
        targetFeatures: 128-dimensional feature vector of target face
        searchFolder: Path to folder to search
        threshold: Similarity threshold for matches
        status: Current status of the task
        progress: Current progress information
        results: List of matching faces found
        createdAt: Timestamp when task was created
        cancelled: Flag indicating if task was cancelled
    """
    taskId: str
    targetFeatures: List[float]
    searchFolder: str
    threshold: float = 0.6
    status: Literal['pending', 'running', 'completed', 'cancelled'] = 'pending'
    progress: Progress = field(default_factory=lambda: Progress(current=0, total=0))
    results: List[Match] = field(default_factory=list)
    createdAt: float = field(default_factory=lambda: datetime.now().timestamp())
    cancelled: bool = False
    
    def __post_init__(self):
        """Validate search task data after initialization."""
        if len(self.targetFeatures) != 128:
            raise ValueError(f"Target features must be 128-dimensional, got {len(self.targetFeatures)}")
        if not 0 <= self.threshold <= 1:
            raise ValueError(f"Threshold must be between 0 and 1, got {self.threshold}")
    
    @staticmethod
    def create(targetFeatures: List[float], searchFolder: str, threshold: float = 0.6) -> 'SearchTask':
        """
        Factory method to create a new SearchTask with a generated UUID.
        
        Args:
            targetFeatures: 128-dimensional feature vector
            searchFolder: Path to search folder
            threshold: Similarity threshold (default 0.6)
            
        Returns:
            New SearchTask instance
        """
        return SearchTask(
            taskId=str(uuid.uuid4()),
            targetFeatures=targetFeatures,
            searchFolder=searchFolder,
            threshold=threshold
        )


@dataclass
class UploadResult:
    """
    Result of an image upload operation.
    
    Attributes:
        success: Whether upload was successful
        imageId: Unique identifier for uploaded image
        previewUrl: URL to preview the image
        error: Optional error message if upload failed
    """
    success: bool
    imageId: Optional[str] = None
    previewUrl: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DetectionResult:
    """
    Result of face detection operation.
    
    Attributes:
        faces: List of detected faces
        error: Optional error message if detection failed
    """
    faces: List[Face] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ScanResult:
    """
    Result of folder scanning operation.
    
    Attributes:
        imagePaths: List of image file paths found
        totalCount: Total number of images found
        error: Optional error message if scan failed
    """
    imagePaths: List[str] = field(default_factory=list)
    totalCount: int = 0
    error: Optional[str] = None


@dataclass
class SearchResult:
    """
    Result of face search operation.
    
    Attributes:
        matches: List of matching faces found
        totalProcessed: Total number of images processed
        cancelled: Whether search was cancelled
    """
    matches: List[Match] = field(default_factory=list)
    totalProcessed: int = 0
    cancelled: bool = False


@dataclass
class ExportResult:
    """
    Result of image export operation.
    
    Attributes:
        successCount: Number of successfully exported images
        failedCount: Number of failed exports
        errors: List of error details for failed exports
    """
    successCount: int = 0
    failedCount: int = 0
    errors: List[dict] = field(default_factory=list)  # [{path: str, error: str}]


@dataclass
class CacheEntry:
    """
    Cache entry for storing face features.
    
    Attributes:
        features: List of detected faces
        timestamp: When the cache entry was created
        fileHash: Hash of the file for validation
    """
    features: List[Face]
    timestamp: float
    fileHash: str
