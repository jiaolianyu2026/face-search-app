"""
Flask application for face recognition search API.
Provides endpoints for image upload, face detection, search, and export.
"""

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid
import threading
from typing import Tuple, Dict

from config import (
    MAX_FILE_SIZE_BYTES,
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_EXTENSIONS,
    TEMP_UPLOAD_DIR
)
from models import UploadResult, DetectionResult, SearchTask, Progress, ExportResult
from face_detection import FaceDetectionModule
from face_search import FaceSearchModule
from image_export import ImageExportModule
from error_handlers import (
    ValidationError,
    NotFoundError,
    ServiceError,
    register_error_handlers
)
from logger import get_logger

# 初始化日志记录器
logger = get_logger('app')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_BYTES

# Register error handlers
register_error_handlers(app)

# 记录应用启动
logger.info("Flask 应用启动")

# Initialize modules
face_detector = FaceDetectionModule()
face_searcher = FaceSearchModule()
image_exporter = ImageExportModule()

# Store active search tasks in memory
search_tasks: Dict[str, SearchTask] = {}

# Store detection results cache (imageId -> DetectionResult)
detection_cache: Dict[str, DetectionResult] = {}


def validate_file_format(filename: str, content_type: str) -> Tuple[bool, str]:
    """
    Validate if file format is supported.
    
    Args:
        filename: Name of the file
        content_type: MIME type of the file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file extension
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file format. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
    
    # Check MIME type
    if content_type not in SUPPORTED_IMAGE_FORMATS:
        return False, f"Unsupported content type: {content_type}"
    
    # Verify extension matches content type
    expected_extensions = SUPPORTED_IMAGE_FORMATS.get(content_type, [])
    if file_ext not in expected_extensions:
        return False, f"File extension {file_ext} does not match content type {content_type}"
    
    return True, ""


@app.route('/api/upload', methods=['POST'])
def upload_image():
    """
    Upload an image file for face recognition.
    
    Request:
        - file: Image file (multipart/form-data)
        
    Response:
        - UploadResult with imageId and previewUrl on success
        - Error message on failure
        
    Validates:
        - File format (JPEG, PNG, WebP)
        - File size (<=10MB)
    """
    # Check if file is present in request
    if 'file' not in request.files:
        raise ValidationError("未提供文件", field="file")
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        raise ValidationError("未选择文件", field="file")
    
    # Validate file format
    is_valid, error_msg = validate_file_format(file.filename, file.content_type)
    if not is_valid:
        raise ValidationError(error_msg, field="file")
    
    # Generate unique imageId
    image_id = str(uuid.uuid4())
    
    # Get file extension and create secure filename
    file_ext = os.path.splitext(file.filename)[1].lower()
    secure_name = f"{image_id}{file_ext}"
    
    # Save file to temp directory
    file_path = os.path.join(TEMP_UPLOAD_DIR, secure_name)
    try:
        file.save(file_path)
        logger.info(f"图片上传成功: {image_id}, 文件名: {file.filename}")
    except Exception as e:
        logger.error(f"保存文件失败: {image_id}, 错误: {str(e)}", exc_info=True)
        raise ServiceError(
            f"保存文件失败: {str(e)}",
            service_name="file_system",
            original_error=e
        )
    
    # Generate preview URL
    preview_url = f"/api/preview/{image_id}"
    
    # Return success result
    result = UploadResult(
        success=True,
        imageId=image_id,
        previewUrl=preview_url
    )
    return jsonify(result.__dict__), 200


@app.route('/api/preview/<image_id>', methods=['GET'])
def preview_image(image_id: str):
    """
    Get preview of uploaded image.
    
    Args:
        image_id: Unique identifier of the uploaded image
        
    Returns:
        Image file
    """
    # Find file with matching imageId
    for filename in os.listdir(TEMP_UPLOAD_DIR):
        if filename.startswith(image_id):
            return send_from_directory(TEMP_UPLOAD_DIR, filename)
    
    logger.warning(f"预览请求失败，未找到图片: {image_id}")
    raise NotFoundError(
        f"未找到图片: {image_id}",
        resource_type="image",
        resource_id=image_id
    )


@app.route('/api/detect', methods=['POST'])
def detect_faces():
    """
    Detect faces in an uploaded image.
    
    Request:
        - imageId: Unique identifier of uploaded image (JSON body)
        
    Response:
        - DetectionResult with list of detected faces on success
        - Error message on failure
        
    Returns:
        - 200: Faces detected successfully
        - 400: Invalid request (missing imageId)
        - 404: Image not found
        - 422: No faces detected in image
        - 500: Internal error during face detection
    """
    # Get imageId from request body
    data = request.get_json()
    if not data or 'imageId' not in data:
        raise ValidationError("需要提供 imageId", field="imageId")
    
    image_id = data['imageId']
    
    # Find image file with matching imageId
    image_path = None
    for filename in os.listdir(TEMP_UPLOAD_DIR):
        if filename.startswith(image_id):
            image_path = os.path.join(TEMP_UPLOAD_DIR, filename)
            break
    
    if not image_path:
        raise NotFoundError(
            f"未找到图片: {image_id}",
            resource_type="image",
            resource_id=image_id
        )
    
    # 检查图片文件大小
    file_size = os.path.getsize(image_path)
    logger.info(f"开始检测人脸: {image_id}, 文件大小: {file_size / 1024:.2f} KB")
    
    # Detect faces using FaceDetectionModule
    try:
        detection_result = face_detector.detectFaces(image_path)
        
        # Cache detection result for later use in search
        detection_cache[image_id] = detection_result
        
        # Check if no faces were detected
        if len(detection_result.faces) == 0:
            logger.warning(f"图片中未检测到人脸: {image_id}")
            return jsonify({
                "faces": [],
                "error": detection_result.error or "图片中未检测到人脸"
            }), 422
        
        logger.info(f"人脸检测成功: {image_id}, 检测到 {len(detection_result.faces)} 个人脸")
        
        # Return successful detection result
        # Convert Face objects to dictionaries for JSON serialization
        faces_data = [
            {
                "faceId": face.faceId,
                "boundingBox": face.boundingBox,
                "features": face.features
            }
            for face in detection_result.faces
        ]
        
        return jsonify({
            "faces": faces_data,
            "error": None
        }), 200
        
    except Exception as e:
        logger.error(f"人脸检测过程中发生错误: {image_id}, 错误: {str(e)}", exc_info=True)
        raise ServiceError(
            f"人脸检测过程中发生错误: {str(e)}",
            service_name="face_detection",
            original_error=e
        )


@app.route('/api/search', methods=['POST'])
def search_faces():
    """
    Start a face search task.
    
    Request (JSON body):
        - imageId: Unique identifier of uploaded image (required)
        - faceId: Unique identifier of face to search (required)
        - searchFolder: Path to folder to search (required)
        - threshold: Similarity threshold 0-1 (optional, default 0.6)
        
    Response:
        - taskId: Unique identifier for the search task
        - status: Initial status of the task ('pending')
        
    Returns:
        - 200: Search task created successfully
        - 400: Invalid request (missing required parameters)
        - 404: Image or face not found
        - 500: Internal error
        
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    # Get request data
    data = request.get_json()
    if not data:
        raise ValidationError("需要提供请求体")
    
    # Validate required parameters
    image_id = data.get('imageId')
    face_id = data.get('faceId')
    search_folder = data.get('searchFolder')
    threshold = data.get('threshold', 0.6)
    
    if not image_id:
        raise ValidationError("需要提供 imageId", field="imageId")
    if not face_id:
        raise ValidationError("需要提供 faceId", field="faceId")
    if not search_folder:
        raise ValidationError("需要提供 searchFolder", field="searchFolder")
    
    # Validate threshold
    try:
        threshold = float(threshold)
        if not 0 <= threshold <= 1:
            raise ValidationError("threshold 必须在 0 到 1 之间", field="threshold")
    except (ValueError, TypeError):
        raise ValidationError("threshold 必须是数字", field="threshold")
    
    # Validate search folder exists (before processing image)
    if not os.path.exists(search_folder):
        logger.warning(f"搜索文件夹不存在: {search_folder}")
        raise ValidationError(f"搜索文件夹不存在: {search_folder}", field="searchFolder")
    if not os.path.isdir(search_folder):
        logger.warning(f"搜索路径不是文件夹: {search_folder}")
        raise ValidationError(f"搜索路径不是文件夹: {search_folder}", field="searchFolder")
    
    # Find image file with matching imageId
    image_path = None
    for filename in os.listdir(TEMP_UPLOAD_DIR):
        if filename.startswith(image_id):
            image_path = os.path.join(TEMP_UPLOAD_DIR, filename)
            break
    
    if not image_path:
        raise NotFoundError(
            f"未找到图片: {image_id}",
            resource_type="image",
            resource_id=image_id
        )
    
    # Detect faces to get the target face features
    try:
        # Try to use cached detection result first
        if image_id in detection_cache:
            logger.info(f"使用缓存的检测结果: {image_id}")
            detection_result = detection_cache[image_id]
        else:
            # If not cached, detect faces
            logger.info(f"缓存未命中，重新检测人脸: {image_id}")
            detection_result = face_detector.detectFaces(image_path)
            detection_cache[image_id] = detection_result
        
        if detection_result.error or len(detection_result.faces) == 0:
            logger.warning(f"搜索任务创建失败，图片中未检测到人脸: {image_id}")
            raise NotFoundError("图片中未检测到人脸", resource_type="face")
        
        # Find the specific face by faceId
        target_face = None
        for face in detection_result.faces:
            if face.faceId == face_id:
                target_face = face
                break
        
        if not target_face:
            logger.warning(f"搜索任务创建失败，未找到指定人脸: {face_id}")
            logger.debug(f"可用的 faceId: {[f.faceId for f in detection_result.faces]}")
            raise NotFoundError(
                f"未找到人脸: {face_id}",
                resource_type="face",
                resource_id=face_id
            )
        
        # Extract target features
        target_features = target_face.features
        
    except (NotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"提取人脸特征时发生错误: {image_id}, 错误: {str(e)}", exc_info=True)
        raise ServiceError(
            f"提取人脸特征时发生错误: {str(e)}",
            service_name="face_detection",
            original_error=e
        )
    
    # Create SearchTask
    search_task = SearchTask.create(
        targetFeatures=target_features,
        searchFolder=search_folder,
        threshold=threshold
    )
    
    # Store task in memory
    search_tasks[search_task.taskId] = search_task
    
    logger.info(f"创建搜索任务: {search_task.taskId}, 文件夹: {search_folder}, 阈值: {threshold}")
    
    # Define background search function
    def run_search():
        """Execute search in background thread."""
        try:
            # Update task status to running
            search_task.status = 'running'
            logger.info(f"开始执行搜索任务: {search_task.taskId}")
            
            # Define progress callback
            def progress_callback(progress: Progress):
                search_task.progress = progress
            
            # Execute search
            search_result = face_searcher.searchFaces(
                targetFeatures=target_features,
                searchFolder=search_folder,
                threshold=threshold,
                progressCallback=progress_callback
            )
            
            # Update task with results
            search_task.results = search_result.matches
            search_task.progress = Progress(
                current=search_result.totalProcessed,
                total=search_result.totalProcessed
            )
            
            # Update status based on cancellation
            if search_result.cancelled:
                search_task.status = 'cancelled'
                search_task.cancelled = True
                logger.info(f"搜索任务已取消: {search_task.taskId}, 已处理 {search_result.totalProcessed} 个文件")
            else:
                search_task.status = 'completed'
                logger.info(f"搜索任务完成: {search_task.taskId}, 找到 {len(search_result.matches)} 个匹配结果")
                
        except Exception as e:
            # Handle errors during search
            logger.error(f"搜索任务执行失败: {search_task.taskId}, 错误: {str(e)}", exc_info=True)
            search_task.status = 'completed'
            search_task.progress = Progress(current=0, total=0)
            # Store error in results (empty list indicates error)
    
    # Start search in background thread
    search_thread = threading.Thread(target=run_search, daemon=True)
    search_thread.start()
    
    # Return taskId to client
    return jsonify({
        "taskId": search_task.taskId,
        "status": search_task.status
    }), 200


@app.route('/api/search/<task_id>', methods=['GET'])
def get_search_status(task_id: str):
    """
    Get the status and progress of a search task.
    
    Args:
        task_id: Unique identifier of the search task
        
    Response:
        - taskId: Task identifier
        - status: Current status ('pending', 'running', 'completed', 'cancelled')
        - progress: Progress information (current, total, percentage, currentFile)
        - results: List of matches (only when completed or cancelled)
        - createdAt: Task creation timestamp
        
    Returns:
        - 200: Task status retrieved successfully
        - 404: Task not found
        
    Requirements: 6.2, 6.3
    """
    # Check if task exists
    if task_id not in search_tasks:
        raise NotFoundError(
            f"未找到搜索任务: {task_id}",
            resource_type="task",
            resource_id=task_id
        )
    
    task = search_tasks[task_id]
    
    # Build response with task information
    response = {
        "taskId": task.taskId,
        "status": task.status,
        "progress": {
            "current": task.progress.current,
            "total": task.progress.total,
            "percentage": task.progress.percentage,
            "currentFile": task.progress.currentFile
        },
        "createdAt": task.createdAt
    }
    
    # Include results if task is completed or cancelled
    if task.status in ['completed', 'cancelled']:
        response["results"] = [
            {
                "imagePath": match.imagePath,
                "similarity": match.similarity,
                "faceLocation": match.faceLocation,
                "thumbnailUrl": match.thumbnailUrl
            }
            for match in task.results
        ]
    
    return jsonify(response), 200


@app.route('/api/search/<task_id>/cancel', methods=['POST'])
def cancel_search(task_id: str):
    """
    Cancel a running search task.
    
    Args:
        task_id: Unique identifier of the search task
        
    Response:
        - taskId: Task identifier
        - status: Updated status ('cancelled')
        - message: Confirmation message
        
    Returns:
        - 200: Task cancelled successfully
        - 404: Task not found
        - 400: Task cannot be cancelled (already completed)
        
    Requirements: 6.4, 6.5
    """
    # Check if task exists
    if task_id not in search_tasks:
        raise NotFoundError(
            f"未找到搜索任务: {task_id}",
            resource_type="task",
            resource_id=task_id
        )
    
    task = search_tasks[task_id]
    
    # Check if task can be cancelled
    if task.status in ['completed', 'cancelled']:
        logger.warning(f"尝试取消已完成的任务: {task_id}, 状态: {task.status}")
        raise ValidationError(
            f"无法取消状态为 {task.status} 的任务",
            field="status"
        )
    
    # Cancel the search by setting the cancelled flag on the searcher
    # Note: We need to mark the task as cancelled
    task.cancelled = True
    face_searcher.cancelSearch()
    
    # Update task status
    task.status = 'cancelled'
    
    logger.info(f"搜索任务已取消: {task_id}")
    
    return jsonify({
        "taskId": task.taskId,
        "status": task.status,
        "message": "搜索任务已成功取消"
    }), 200


@app.route('/api/export', methods=['POST'])
def export_images():
    """
    Export (copy) matched images to a target directory.
    
    Request (JSON body):
        - imagePaths: List of image file paths to export (required)
        - targetFolder: Destination folder path (required)
        - createIfNotExists: Whether to create folder if it doesn't exist (optional, default false)
        
    Response:
        - successCount: Number of successfully exported images
        - failedCount: Number of failed exports
        - errors: List of error details for failed exports
        - folderCreated: Whether the folder was created (optional)
        
    Returns:
        - 200: Export completed (check successCount/failedCount for details)
        - 400: Invalid request (missing required parameters)
        - 404: Target folder does not exist (and createIfNotExists is false)
        - 403: Target folder is not writable or cannot be created
        
    Requirements: 8.4, 8.5, 8.6, 8.7
    """
    # Get request data
    data = request.get_json()
    if not data:
        raise ValidationError("需要提供请求体")
    
    # Validate required parameters
    image_paths = data.get('imagePaths')
    target_folder = data.get('targetFolder')
    create_if_not_exists = data.get('createIfNotExists', False)
    
    if image_paths is None:
        raise ValidationError("需要提供 imagePaths", field="imagePaths")
    if not isinstance(image_paths, list):
        raise ValidationError("imagePaths 必须是数组", field="imagePaths")
    if len(image_paths) == 0:
        raise ValidationError("imagePaths 不能为空", field="imagePaths")
    if not target_folder:
        raise ValidationError("需要提供 targetFolder", field="targetFolder")
    
    folder_created = False
    
    # Check if target folder exists
    if not os.path.exists(target_folder):
        if create_if_not_exists:
            # Try to create the folder
            try:
                os.makedirs(target_folder, exist_ok=True)
                folder_created = True
                logger.info(f"创建目标文件夹: {target_folder}")
            except Exception as e:
                logger.error(f"创建文件夹失败: {target_folder}, 错误: {str(e)}")
                raise ValidationError(
                    f"无法创建文件夹: {target_folder}",
                    field="targetFolder"
                )
        else:
            # Return special error indicating folder doesn't exist
            raise NotFoundError(
                f"目标文件夹不存在: {target_folder}",
                resource_type="folder",
                resource_id=target_folder
            )
    
    # Validate it's a directory
    if not os.path.isdir(target_folder):
        raise ValidationError(
            f"目标路径不是文件夹: {target_folder}",
            field="targetFolder"
        )
    
    # Validate target folder is writable
    if not os.access(target_folder, os.W_OK):
        raise ValidationError(
            f"目标文件夹不可写: {target_folder}",
            field="targetFolder"
        )
    
    # Execute export operation
    try:
        logger.info(f"开始转存图片: {len(image_paths)} 个文件到 {target_folder}")
        export_result = image_exporter.exportImages(
            imagePaths=image_paths,
            targetFolder=target_folder
        )
        
        logger.info(f"转存完成: 成功 {export_result.successCount}, 失败 {export_result.failedCount}")
        
        # Return export result
        response = {
            "successCount": export_result.successCount,
            "failedCount": export_result.failedCount,
            "errors": export_result.errors
        }
        
        if folder_created:
            response["folderCreated"] = True
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"转存过程中发生错误: {str(e)}", exc_info=True)
        raise ServiceError(
            f"转存过程中发生错误: {str(e)}",
            service_name="image_export",
            original_error=e
        )

if __name__ == '__main__':
    logger.info("启动 Flask 开发服务器: http://0.0.0.0:5000")
    # 使用生产模式，避免 debug 模式的问题
    # 禁用自动重载和调试器
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
