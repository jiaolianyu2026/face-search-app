"""
统一错误处理模块
定义自定义异常类和标准化错误响应格式
"""

from typing import Optional, Dict, Any
from flask import jsonify
from logger import get_logger

# 初始化日志记录器
logger = get_logger('error_handlers')


class ValidationError(Exception):
    """
    输入验证错误
    用于无效的文件格式、文件大小超限、无效参数等情况
    """
    def __init__(self, message: str, field: Optional[str] = None):
        """
        初始化验证错误
        
        Args:
            message: 错误消息
            field: 可选的字段名称
        """
        self.message = message
        self.field = field
        super().__init__(self.message)


class NotFoundError(Exception):
    """
    资源未找到错误
    用于图片、人脸、任务等资源不存在的情况
    """
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        """
        初始化未找到错误
        
        Args:
            message: 错误消息
            resource_type: 资源类型（如 'image', 'face', 'task'）
            resource_id: 资源标识符
        """
        self.message = message
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(self.message)


class ServiceError(Exception):
    """
    服务错误
    用于人脸检测服务不可用、文件系统访问失败等系统级错误
    """
    def __init__(self, message: str, service_name: Optional[str] = None, original_error: Optional[Exception] = None):
        """
        初始化服务错误
        
        Args:
            message: 错误消息
            service_name: 服务名称（如 'face_detection', 'file_system'）
            original_error: 原始异常对象
        """
        self.message = message
        self.service_name = service_name
        self.original_error = original_error
        super().__init__(self.message)


def create_error_response(error_code: str, message: str, status_code: int, **kwargs) -> tuple:
    """
    创建标准化的错误响应
    
    Args:
        error_code: 错误代码（如 'VALIDATION_ERROR', 'NOT_FOUND'）
        message: 错误消息
        status_code: HTTP状态码
        **kwargs: 额外的错误信息字段
        
    Returns:
        (response, status_code) 元组
    """
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message
        }
    }
    
    # 添加额外的错误信息
    if kwargs:
        response["error"].update(kwargs)
    
    return jsonify(response), status_code


def register_error_handlers(app):
    """
    注册Flask错误处理器
    
    Args:
        app: Flask应用实例
    """
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        """处理验证错误"""
        logger.warning(f"验证错误: {error.message}, 字段: {error.field}")
        extra = {}
        if error.field:
            extra["field"] = error.field
        
        return create_error_response(
            error_code="VALIDATION_ERROR",
            message=error.message,
            status_code=400,
            **extra
        )
    
    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error: NotFoundError):
        """处理资源未找到错误"""
        logger.warning(f"资源未找到: {error.message}, 类型: {error.resource_type}, ID: {error.resource_id}")
        extra = {}
        if error.resource_type:
            extra["resourceType"] = error.resource_type
        if error.resource_id:
            extra["resourceId"] = error.resource_id
        
        return create_error_response(
            error_code="NOT_FOUND",
            message=error.message,
            status_code=404,
            **extra
        )
    
    @app.errorhandler(ServiceError)
    def handle_service_error(error: ServiceError):
        """处理服务错误"""
        logger.error(
            f"服务错误: {error.message}, 服务: {error.service_name}",
            exc_info=error.original_error
        )
        extra = {}
        if error.service_name:
            extra["service"] = error.service_name
        
        return create_error_response(
            error_code="SERVICE_ERROR",
            message=error.message,
            status_code=500,
            **extra
        )
    
    @app.errorhandler(413)
    def handle_file_too_large(e):
        """处理文件大小超限错误"""
        from config import MAX_FILE_SIZE_BYTES
        logger.warning(f"文件大小超限: {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB")
        return create_error_response(
            error_code="FILE_TOO_LARGE",
            message=f"文件大小超过最大限制 {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB",
            status_code=413
        )
    
    @app.errorhandler(500)
    def handle_internal_error(e):
        """处理内部服务器错误"""
        logger.error(f"内部服务器错误: {str(e)}", exc_info=True)
        return create_error_response(
            error_code="INTERNAL_ERROR",
            message="内部服务器错误，请稍后重试",
            status_code=500
        )
    
    @app.errorhandler(404)
    def handle_not_found(e):
        """处理路由未找到错误"""
        logger.warning(f"路由未找到: {str(e)}")
        return create_error_response(
            error_code="ROUTE_NOT_FOUND",
            message="请求的路由不存在",
            status_code=404
        )
    
    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        """处理HTTP方法不允许错误"""
        logger.warning(f"HTTP方法不允许: {str(e)}")
        return create_error_response(
            error_code="METHOD_NOT_ALLOWED",
            message="不支持的HTTP方法",
            status_code=405
        )
