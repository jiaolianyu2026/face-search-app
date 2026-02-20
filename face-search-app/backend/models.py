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


@dataclass
class LibraryFace:
    """
    表示保存在人像库中的人像。
    
    Attributes:
        id: 唯一标识符（UUID格式）
        name: 人像名称（1-100字符）
        feature_vector: 128维特征向量
        thumbnail_path: 缩略图文件路径
        created_at: 创建时间戳（ISO 8601格式）
        source_image_id: 源图片ID（可选）
    """
    id: str
    name: str
    feature_vector: List[float]
    thumbnail_path: str
    created_at: str
    source_image_id: Optional[str] = None
    
    def __post_init__(self):
        """验证库人像数据。"""
        # 验证 UUID 格式
        try:
            uuid.UUID(self.id)
        except ValueError:
            raise ValueError(f"ID must be a valid UUID, got {self.id}")
        
        # 验证名称长度
        if not self.name or len(self.name) == 0:
            raise ValueError("Name cannot be empty")
        if len(self.name) > 100:
            raise ValueError(f"Name must not exceed 100 characters, got {len(self.name)}")
        
        # 验证特征向量维度
        if len(self.feature_vector) != 128:
            raise ValueError(f"Feature vector must be 128-dimensional, got {len(self.feature_vector)}")
        
        # 验证 ISO 8601 时间戳格式
        try:
            datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValueError(f"created_at must be in ISO 8601 format, got {self.created_at}")
    
    @staticmethod
    def create(name: str, feature_vector: List[float], thumbnail_path: str, 
               source_image_id: Optional[str] = None) -> 'LibraryFace':
        """
        工厂方法：创建新的 LibraryFace 实例。
        
        Args:
            name: 人像名称
            feature_vector: 128维特征向量
            thumbnail_path: 缩略图路径
            source_image_id: 源图片ID（可选）
            
        Returns:
            新的 LibraryFace 实例
        """
        return LibraryFace(
            id=str(uuid.uuid4()),
            name=name,
            feature_vector=feature_vector,
            thumbnail_path=thumbnail_path,
            created_at=datetime.now().isoformat(),
            source_image_id=source_image_id
        )


@dataclass
class FaceSelection:
    """
    表示用户选择的人像集合。
    
    Attributes:
        uploaded_faces: 从上传图片中选择的人像列表
        library_faces: 从人像库中选择的人像ID列表
    """
    uploaded_faces: List[dict] = field(default_factory=list)  # [{imageId: str, faceId: str}]
    library_faces: List[str] = field(default_factory=list)  # [libraryFaceId: str]
    
    def get_all_face_ids(self) -> List[str]:
        """
        获取所有选中的人像ID。
        
        Returns:
            包含所有人像ID的列表
        """
        uploaded_ids = [f"{face['imageId']}:{face['faceId']}" for face in self.uploaded_faces]
        return uploaded_ids + self.library_faces
    
    def is_empty(self) -> bool:
        """
        检查是否没有选择任何人像。
        
        Returns:
            如果没有选择任何人像返回 True
        """
        return len(self.uploaded_faces) == 0 and len(self.library_faces) == 0
    
    def count(self) -> int:
        """
        获取选中人像的总数。
        
        Returns:
            选中人像的数量
        """
        return len(self.uploaded_faces) + len(self.library_faces)


@dataclass
class MultiSearchResult:
    """
    多人像搜索的结果。
    
    Attributes:
        matches: 匹配结果列表，每个匹配包含源人像ID
        total_processed: 处理的图片总数
        source_face_map: 源人像ID到匹配结果的映射
        cancelled: 搜索是否被取消
    """
    matches: List[dict] = field(default_factory=list)  # [{...Match, sourceFaceId: str}]
    total_processed: int = 0
    source_face_map: dict = field(default_factory=dict)  # {sourceFaceId: [Match]}
    cancelled: bool = False
    
    def add_match(self, match: Match, source_face_id: str):
        """
        添加一个匹配结果。
        
        Args:
            match: 匹配对象
            source_face_id: 源人像ID
        """
        match_dict = {
            'imagePath': match.imagePath,
            'similarity': match.similarity,
            'faceLocation': match.faceLocation,
            'thumbnailUrl': match.thumbnailUrl,
            'sourceFaceId': source_face_id
        }
        self.matches.append(match_dict)
        
        # 更新源人像映射
        if source_face_id not in self.source_face_map:
            self.source_face_map[source_face_id] = []
        self.source_face_map[source_face_id].append(match)
    
    def merge_duplicates(self):
        """
        合并重复的图片路径，保留最高相似度分数。
        """
        # 按图片路径分组
        path_groups = {}
        for match in self.matches:
            path = match['imagePath']
            if path not in path_groups:
                path_groups[path] = []
            path_groups[path].append(match)
        
        # 对每个路径保留最高相似度的匹配
        merged_matches = []
        for path, matches in path_groups.items():
            best_match = max(matches, key=lambda m: m['similarity'])
            merged_matches.append(best_match)
        
        self.matches = merged_matches
    
    def sort_by_similarity(self):
        """
        按相似度降序排序匹配结果。
        """
        self.matches.sort(key=lambda m: m['similarity'], reverse=True)
