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
# 相似度阈值（基于欧氏距离转换：similarity = 1 - distance）
# face_recognition 官方推荐欧氏距离阈值 0.6（相似度 0.4）是宽松阈值
# 实际使用中距离 0.45~0.55 的人脸已是明显不同的人，建议用 0.5（欧氏距离 0.5）
DEFAULT_SIMILARITY_THRESHOLD = 0.5
FACE_FEATURE_DIMENSION = 128

# Storage paths
TEMP_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'temp_uploads')
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')

# Performance configuration
FACE_DETECTION_TIMEOUT_SECONDS = 2
BATCH_SIZE = 100  # For processing large folders
MAX_CONCURRENT_TASKS = 5
MAX_WORKER_THREADS = 2  # 减少线程数，避免dlib多线程问题
THUMBNAIL_SIZE = (200, 200)  # Thumbnail dimensions for preview
ENABLE_PARALLEL_PROCESSING = False  # 临时禁用并行处理以调试问题
FACE_DETECTION_MODEL = 'hog'  # 'hog' for speed, 'cnn' for accuracy

# Logging configuration
LOG_FILE = os.path.join(os.path.dirname(__file__), 'app.log')
LOG_LEVEL = 'INFO'  # 恢复为INFO级别

# Ensure directories exist
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
