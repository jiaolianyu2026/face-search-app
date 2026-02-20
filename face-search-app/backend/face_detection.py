"""
Face Detection Module for detecting faces and extracting features.
Uses face_recognition library for face detection and feature extraction.
Supports multiple detection models (HOG for speed, CNN for accuracy).
"""

import face_recognition
import numpy as np
import uuid
from typing import List, Tuple
from PIL import Image
from models import Face, DetectionResult
from logger import get_logger
from config import FACE_DETECTION_MODEL

# 初始化日志记录器
logger = get_logger('face_detection')


class FaceDetectionModule:
    """
    Module for detecting faces in images and extracting facial features.
    
    Uses face_recognition library (based on dlib) to:
    - Detect face locations in images
    - Extract 128-dimensional feature vectors for each face
    """
    
    def __init__(self, model: str = FACE_DETECTION_MODEL):
        """
        Initialize the FaceDetectionModule.
        
        Args:
            model: Detection model to use ('hog' for speed, 'cnn' for accuracy)
        """
        self.model = model
        logger.info(f"人脸检测模块初始化，模型: {model}")
    
    def detectFaces(self, image_path: str) -> DetectionResult:
        """
        Detect all faces in an image and extract their features.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            DetectionResult containing list of detected faces with locations and features
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image cannot be loaded
        """
        try:
            logger.debug(f"开始检测人脸: {image_path}")
            
            # 检查文件是否存在
            import os
            if not os.path.exists(image_path):
                logger.error(f"图片文件未找到: {image_path}")
                return DetectionResult(faces=[], error=f"Image file not found: {image_path}")
            
            # 获取文件大小
            file_size = os.path.getsize(image_path)
            logger.debug(f"图片文件大小: {file_size / 1024:.2f} KB")
            
            # Load image using face_recognition
            logger.debug("加载图片...")
            image = face_recognition.load_image_file(image_path)
            logger.debug(f"图片加载成功，尺寸: {image.shape}")
            
            # Detect face locations using specified model
            # 'hog' is faster but less accurate, 'cnn' is more accurate but slower
            # Returns list of tuples: (top, right, bottom, left)
            logger.debug(f"开始检测人脸位置（模型: {self.model}）...")
            face_locations = face_recognition.face_locations(image, model=self.model)
            logger.debug(f"人脸位置检测完成，找到 {len(face_locations)} 个人脸")
            
            # Check if any faces were detected
            if len(face_locations) == 0:
                logger.info(f"图片中未检测到人脸: {image_path}")
                return DetectionResult(faces=[], error="No faces detected in image")
            
            # Extract 128-dimensional feature encodings for all detected faces
            logger.debug("开始提取人脸特征...")
            face_encodings = face_recognition.face_encodings(image, face_locations)
            logger.debug(f"人脸特征提取完成，特征数量: {len(face_encodings)}")
            
            # Build Face objects for each detected face
            faces = []
            for location, encoding in zip(face_locations, face_encodings):
                face = self._create_face_from_detection(location, encoding)
                faces.append(face)
            
            logger.info(f"人脸检测完成: {image_path}, 检测到 {len(faces)} 个人脸")
            return DetectionResult(faces=faces)
            
        except FileNotFoundError:
            logger.error(f"图片文件未找到: {image_path}")
            return DetectionResult(faces=[], error=f"Image file not found: {image_path}")
        except MemoryError as e:
            logger.error(f"内存不足: {image_path}, 错误: {str(e)}", exc_info=True)
            return DetectionResult(faces=[], error=f"Memory error: Image too large")
        except Exception as e:
            logger.error(f"处理图片时发生错误: {image_path}, 错误: {str(e)}", exc_info=True)
            return DetectionResult(faces=[], error=f"Error processing image: {str(e)}")
    
    def extractFeatures(self, image_path: str, face_location: Tuple[int, int, int, int]) -> List[float]:
        """
        Extract 128-dimensional feature vector for a specific face in an image.
        
        Args:
            image_path: Path to the image file
            face_location: Tuple of (top, right, bottom, left) coordinates
            
        Returns:
            128-dimensional feature vector as list of floats
            
        Raises:
            ValueError: If face cannot be encoded
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Extract encoding for the specific face location
            face_encodings = face_recognition.face_encodings(image, [face_location])
            
            if len(face_encodings) == 0:
                raise ValueError("Could not extract features for specified face location")
            
            # Convert numpy array to list of floats
            return face_encodings[0].tolist()
            
        except Exception as e:
            raise ValueError(f"Error extracting features: {str(e)}")
    
    def _create_face_from_detection(
        self, 
        location: Tuple[int, int, int, int], 
        encoding: np.ndarray
    ) -> Face:
        """
        Create a Face object from detection results.
        
        Args:
            location: Tuple of (top, right, bottom, left) coordinates
            encoding: 128-dimensional numpy array of face features
            
        Returns:
            Face object with unique ID, bounding box, and features
        """
        # Generate unique face ID
        face_id = str(uuid.uuid4())
        
        # Convert face_recognition location format (top, right, bottom, left)
        # to bounding box format (x, y, width, height)
        top, right, bottom, left = location
        bounding_box = {
            'x': left,
            'y': top,
            'width': right - left,
            'height': bottom - top
        }
        
        # Convert numpy array to list of floats
        features = encoding.tolist()
        
        return Face(
            faceId=face_id,
            boundingBox=bounding_box,
            features=features
        )
