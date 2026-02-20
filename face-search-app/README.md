# Face Recognition Search Application

A web application that allows users to upload images containing faces, identify face features, and search for all images containing the same face in a specified folder.

## Project Structure

```
.
├── backend/           # Python backend application
│   ├── venv/         # Virtual environment (not in version control)
│   ├── temp_uploads/ # Temporary storage for uploaded images
│   ├── cache/        # Cache for face features
│   ├── __init__.py   # Package initialization
│   ├── config.py     # Configuration constants
│   ├── models.py     # Core data models
│   └── requirements.txt  # Python dependencies
├── frontend/         # Web frontend (to be implemented)
├── tests/            # Test suite
└── .kiro/            # Kiro specs and configuration
```

## Setup

### Backend Setup

1. Create and activate virtual environment:
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Core Data Models

- **Face**: Represents a detected face with bounding box and 128-dimensional feature vector
- **Match**: Represents a matching face found during search
- **Progress**: Progress information for long-running operations
- **SearchTask**: Represents a face search task with status and results
- **UploadResult**: Result of image upload operation
- **DetectionResult**: Result of face detection operation
- **ScanResult**: Result of folder scanning operation
- **SearchResult**: Result of face search operation
- **ExportResult**: Result of image export operation
- **CacheEntry**: Cache entry for storing face features

## Configuration

See `backend/config.py` for configuration options including:
- File size limits (10MB default)
- Supported image formats (JPEG, PNG, WebP)
- Similarity threshold (0.6 default)
- Performance settings

## Development Status

This project is under active development. See `.kiro/specs/face-recognition-search/tasks.md` for implementation progress.
