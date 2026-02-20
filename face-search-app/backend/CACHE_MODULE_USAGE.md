# Cache Module Usage Guide

## Overview

The `CacheModule` provides efficient caching of face detection features to avoid redundant computation. It uses SQLite for persistent storage and validates cache entries using file modification time and MD5 hash.

## Features

- **Persistent Storage**: Uses SQLite database for reliable caching
- **Cache Validation**: Validates cache using file modification time and MD5 hash
- **Automatic Invalidation**: Cache is automatically invalidated when files are modified
- **Thread-Safe**: SQLite provides thread-safe operations
- **Easy Integration**: Simple API with just two main methods

## Basic Usage

```python
from cache_module import CacheModule
from models import Face

# Initialize cache module
cache = CacheModule()

# Example: Detect faces and cache them
image_path = "/path/to/image.jpg"

# Check if features are cached
cache_entry = cache.getCachedFeatures(image_path)

if cache_entry is not None:
    # Use cached features
    faces = cache_entry.features
    print(f"Using cached features: {len(faces)} faces")
else:
    # Detect faces (expensive operation)
    faces = detect_faces_from_image(image_path)  # Your detection logic
    
    # Cache the results
    cache.setCachedFeatures(image_path, faces)
    print(f"Cached {len(faces)} faces")
```

## API Reference

### `getCachedFeatures(imagePath: str) -> Optional[CacheEntry]`

Retrieves cached face features for an image.

**Parameters:**
- `imagePath`: Path to the image file

**Returns:**
- `CacheEntry` if cache is valid and file hasn't been modified
- `None` if cache doesn't exist or file has been modified

**Cache Validation:**
1. Checks if file exists
2. Compares file modification time
3. Compares file MD5 hash
4. Returns cached features only if both match

### `setCachedFeatures(imagePath: str, faces: List[Face]) -> None`

Caches face features for an image.

**Parameters:**
- `imagePath`: Path to the image file
- `faces`: List of detected Face objects

**Behavior:**
- Computes file metadata (modification time, MD5 hash)
- Stores features in SQLite database
- Updates existing cache entry if it exists

### `clear_cache() -> None`

Clears all cached entries from the database.

### `get_cache_size() -> int`

Returns the number of cached entries.

## Integration Example

Here's how to integrate the cache module into the face detection workflow:

```python
from cache_module import CacheModule
from face_detection import FaceDetectionModule

cache = CacheModule()
detector = FaceDetectionModule()

def detect_faces_with_cache(image_path: str):
    """Detect faces with caching support."""
    
    # Try to get cached features
    cache_entry = cache.getCachedFeatures(image_path)
    
    if cache_entry is not None:
        # Cache hit - return cached features
        return cache_entry.features
    
    # Cache miss - detect faces
    detection_result = detector.detectFaces(image_path)
    
    if detection_result.error is None:
        # Cache the detected faces
        cache.setCachedFeatures(image_path, detection_result.faces)
        return detection_result.faces
    
    return []
```

## Performance Benefits

The cache module provides significant performance improvements:

1. **Avoids Redundant Computation**: Face detection is expensive (can take 1-2 seconds per image). Caching eliminates this cost for unchanged files.

2. **Batch Processing**: When processing large folders, many images may be processed multiple times. The cache ensures each image is only processed once.

3. **Incremental Updates**: When new images are added to a folder, only the new images need to be processed.

## Cache Invalidation

The cache is automatically invalidated when:

1. **File is Modified**: If the file content changes, the MD5 hash will differ
2. **File is Replaced**: If a file is deleted and recreated, the modification time will differ
3. **Manual Clearing**: Using `clear_cache()` method

## Storage Location

By default, the cache database is stored in:
```
backend/cache/face_cache.db
```

You can specify a custom cache directory:
```python
cache = CacheModule(cache_dir="/custom/cache/path")
```

## Testing

The cache module includes comprehensive tests:

- **Unit Tests** (`tests/test_cache.py`): Test specific scenarios and edge cases
- **Property Tests** (`tests/test_cache_properties.py`): Test general properties across many inputs

Run tests with:
```bash
pytest tests/test_cache.py tests/test_cache_properties.py -v
```

## Requirements Validation

This implementation satisfies **Requirement 9.4**:
> "系统应当缓存已处理图片的人脸特征以避免重复计算"

The cache module ensures that processed images are cached and reused, avoiding redundant face detection operations.
