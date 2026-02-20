"""
Configuration file for face recognition search application.
Stores constants for file size limits, supported formats, similarity thresholds, etc.
"""

import os

# File upload configuration
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/webp': ['.webp']
}

SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']

# Face recognition configuration
DEFAULT_SIMILARITY_THRESHOLD = 0.6
FACE_FEATURE_DIMENSION = 128

# Storage paths
TEMP_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'temp_uploads')
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')

# Performance configuration
FACE_DETECTION_TIMEOUT_SECONDS = 2
BATCH_SIZE = 100  # For processing large folders
MAX_CONCURRENT_TASKS = 5
MAX_WORKER_THREADS = 4  # Number of threads for parallel image processing
THUMBNAIL_SIZE = (200, 200)  # Thumbnail dimensions for preview
ENABLE_PARALLEL_PROCESSING = True  # Enable/disable parallel processing
FACE_DETECTION_MODEL = 'hog'  # 'hog' for speed, 'cnn' for accuracy

# Logging configuration
LOG_FILE = os.path.join(os.path.dirname(__file__), 'app.log')
LOG_LEVEL = 'INFO'

# Ensure directories exist
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
