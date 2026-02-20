# Project Structure Documentation

## Overview
This document describes the project structure for the Face Recognition Search Application.

## Directory Structure

```
face-search-app/
├── backend/                    # Python backend application
│   ├── venv/                  # Virtual environment (not in version control)
│   ├── temp_uploads/          # Temporary storage for uploaded images
│   ├── cache/                 # Cache for face features
│   ├── __init__.py            # Package initialization
│   ├── config.py              # Configuration constants
│   ├── models.py              # Core data models
│   ├── requirements.txt       # Python dependencies
│   ├── INSTALLATION.md        # Installation instructions
│   └── PROJECT_STRUCTURE.md   # This file
├── frontend/                   # Web frontend (to be implemented)
│   └── .gitkeep               # Placeholder
├── tests/                      # Test suite
│   ├── __init__.py            # Test package initialization
│   └── test_models.py         # Unit tests for data models
├── .kiro/                      # Kiro specs and configuration
│   └── specs/
│       └── face-recognition-search/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
└── README.md                   # Project documentation
```

## Core Components

### Configuration (config.py)
Defines application constants:
- **File Upload**: MAX_FILE_SIZE_MB (10MB), supported formats (JPEG, PNG, WebP)
- **Face Recognition**: DEFAULT_SIMILARITY_THRESHOLD (0.6), FACE_FEATURE_DIMENSION (128)
- **Storage Paths**: TEMP_UPLOAD_DIR, CACHE_DIR
- **Performance**: FACE_DETECTION_TIMEOUT_SECONDS (2s), BATCH_SIZE (100)
- **Logging**: LOG_FILE, LOG_LEVEL

### Data Models (models.py)
Core data structures with validation:

1. **Face**: Detected face with bounding box and 128-dimensional feature vector
2. **Match**: Matching face found during search with similarity score
3. **Progress**: Progress information for long-running operations
4. **SearchTask**: Face search task with status, progress, and results
5. **UploadResult**: Result of image upload operation
6. **DetectionResult**: Result of face detection operation
7. **ScanResult**: Result of folder scanning operation
8. **SearchResult**: Result of face search operation
9. **ExportResult**: Result of image export operation
10. **CacheEntry**: Cache entry for storing face features

All models include validation logic to ensure data integrity.

### Dependencies (requirements.txt)
Core Python packages:
- **face_recognition**: Face detection and feature extraction
- **opencv-python**: Image processing
- **numpy**: Numerical computations
- **Pillow**: Image manipulation
- **Flask**: Web framework
- **Flask-CORS**: Cross-origin resource sharing

### Tests (tests/test_models.py)
Unit tests for data models covering:
- Valid data creation
- Validation logic
- Edge cases and error conditions

## Setup Status

✅ Project directory structure created
✅ Configuration file with constants defined
✅ Core data models implemented with validation
✅ Requirements file created
✅ Unit tests for data models passing
✅ Installation documentation provided

⚠️ Dependencies require CMake installation (see INSTALLATION.md)

## Next Steps

Refer to `.kiro/specs/face-recognition-search/tasks.md` for the implementation plan.
The next task is to implement the image upload module (Task 2).
