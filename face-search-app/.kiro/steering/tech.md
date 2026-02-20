---
inclusion: always
---

# Technology Stack

## Backend

- Python 3.14+
- Flask 3.0+ (REST API)
- face_recognition (dlib-based face detection and encoding)
- OpenCV (image processing)
- NumPy (numerical operations)
- Pillow (image manipulation)

## Testing

- pytest (unit tests)
- hypothesis (property-based tests)

## Key Libraries

- `face_recognition`: Face detection and 128D feature extraction
- `dlib-bin`: Precompiled dlib for easier Windows installation
- `Flask-CORS`: Cross-origin resource sharing

## Common Commands

### Environment Setup
```bash
# Windows
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application
```bash
cd backend
python app.py
# Server runs on http://localhost:5000
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_face_detection.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run property-based tests (may take longer)
pytest tests/test_face_detection_properties.py -v
```

### Dependency Verification
```bash
cd backend
python check_dependencies.py
```

## Configuration

All configuration constants in `backend/config.py`:
- File size limits: 10MB max
- Supported formats: JPEG, PNG, WebP
- Similarity threshold: 0.6 default
- Face feature dimension: 128
- Batch size: 100 images
- Detection timeout: 2 seconds
