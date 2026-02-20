---
inclusion: always
---

# Project Structure

## Directory Layout

```
.
├── backend/              # Python backend application
│   ├── venv/            # Virtual environment (not in VCS)
│   ├── temp_uploads/    # Temporary uploaded images
│   ├── cache/           # Face feature cache (SQLite)
│   ├── app.py           # Flask application and API endpoints
│   ├── config.py        # Configuration constants
│   ├── models.py        # Core data models with validation
│   ├── face_detection.py    # Face detection module
│   ├── face_search.py       # Face search module
│   ├── file_scanner.py      # File system scanning
│   ├── similarity.py        # Similarity calculation
│   ├── cache_module.py      # Caching layer
│   └── requirements.txt     # Python dependencies
├── tests/               # Test suite (unit + property-based)
│   ├── test_*.py        # Unit tests
│   └── test_*_properties.py  # Property-based tests
├── frontend/            # Web frontend (to be implemented)
├── .kiro/
│   ├── specs/           # Feature specifications
│   └── steering/        # Project steering documents
└── README.md
```

## Module Organization

### Core Modules (backend/)

- `app.py`: Flask REST API with endpoints for upload, detect, search, cancel
- `models.py`: Pydantic-style data models (Face, Match, SearchTask, Progress, etc.)
- `face_detection.py`: FaceDetectionModule - detect faces and extract features
- `face_search.py`: FaceSearchModule - search folders for matching faces
- `file_scanner.py`: FileScannerModule - scan directories for image files
- `similarity.py`: SimilarityModule - calculate face similarity scores
- `cache_module.py`: CacheModule - SQLite-based feature caching

### Test Organization (tests/)

- Unit tests: `test_<module>.py` - specific examples and edge cases
- Property tests: `test_<module>_properties.py` - universal properties with hypothesis
- Integration tests: `test_<feature>_integration.py` - end-to-end workflows
- API tests: `test_<endpoint>_api.py` - HTTP endpoint testing

## Naming Conventions

- Files: snake_case (e.g., `face_detection.py`)
- Classes: PascalCase with Module suffix (e.g., `FaceDetectionModule`)
- Functions/methods: camelCase (e.g., `detectFaces`, `searchFaces`)
- Constants: UPPER_SNAKE_CASE (e.g., `MAX_FILE_SIZE_MB`)
- Test classes: `Test<FeatureName>` or `TestProperty<N>_<Description>`

## API Endpoints

- `POST /api/upload` - Upload image file
- `GET /api/preview/{imageId}` - Get uploaded image
- `POST /api/detect` - Detect faces in uploaded image
- `POST /api/search` - Start face search task
- `GET /api/search/{taskId}` - Get search status/results
- `POST /api/search/{taskId}/cancel` - Cancel search task

## Storage

- Uploaded images: `backend/temp_uploads/` (UUID-based filenames)
- Face cache: `backend/cache/face_cache.db` (SQLite)
- Logs: `backend/app.log`

## Spec-Driven Development

Feature specs in `.kiro/specs/<feature-name>/`:
- `requirements.md` - User stories and acceptance criteria
- `design.md` - Technical design and correctness properties
- `tasks.md` - Implementation task list with status tracking
