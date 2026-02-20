"""
错误处理模块的单元测试
测试自定义异常类和错误响应格式
"""

import pytest
import json
import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from error_handlers import (
    ValidationError,
    NotFoundError,
    ServiceError,
    create_error_response
)
from app import app


@pytest.fixture
def app_context():
    """创建 Flask 应用上下文"""
    with app.app_context():
        yield


class TestValidationError:
    """测试 ValidationError 异常类"""
    
    def test_validation_error_with_message_only(self):
        """测试只包含消息的验证错误"""
        error = ValidationError("无效的输入")
        assert error.message == "无效的输入"
        assert error.field is None
        assert str(error) == "无效的输入"
    
    def test_validation_error_with_field(self):
        """测试包含字段名的验证错误"""
        error = ValidationError("文件格式不支持", field="file")
        assert error.message == "文件格式不支持"
        assert error.field == "file"
    
    def test_validation_error_inheritance(self):
        """测试 ValidationError 继承自 Exception"""
        error = ValidationError("测试错误")
        assert isinstance(error, Exception)


class TestNotFoundError:
    """测试 NotFoundError 异常类"""
    
    def test_not_found_error_with_message_only(self):
        """测试只包含消息的未找到错误"""
        error = NotFoundError("资源未找到")
        assert error.message == "资源未找到"
        assert error.resource_type is None
        assert error.resource_id is None
    
    def test_not_found_error_with_resource_info(self):
        """测试包含资源信息的未找到错误"""
        error = NotFoundError(
            "图片未找到",
            resource_type="image",
            resource_id="abc123"
        )
        assert error.message == "图片未找到"
        assert error.resource_type == "image"
        assert error.resource_id == "abc123"
    
    def test_not_found_error_inheritance(self):
        """测试 NotFoundError 继承自 Exception"""
        error = NotFoundError("测试错误")
        assert isinstance(error, Exception)


class TestServiceError:
    """测试 ServiceError 异常类"""
    
    def test_service_error_with_message_only(self):
        """测试只包含消息的服务错误"""
        error = ServiceError("服务不可用")
        assert error.message == "服务不可用"
        assert error.service_name is None
        assert error.original_error is None
    
    def test_service_error_with_service_name(self):
        """测试包含服务名的服务错误"""
        error = ServiceError(
            "人脸检测失败",
            service_name="face_detection"
        )
        assert error.message == "人脸检测失败"
        assert error.service_name == "face_detection"
    
    def test_service_error_with_original_error(self):
        """测试包含原始异常的服务错误"""
        original = ValueError("原始错误")
        error = ServiceError(
            "处理失败",
            service_name="processor",
            original_error=original
        )
        assert error.message == "处理失败"
        assert error.service_name == "processor"
        assert error.original_error is original
    
    def test_service_error_inheritance(self):
        """测试 ServiceError 继承自 Exception"""
        error = ServiceError("测试错误")
        assert isinstance(error, Exception)


class TestCreateErrorResponse:
    """测试 create_error_response 函数"""
    
    def test_basic_error_response(self, app_context):
        """测试基本错误响应"""
        response, status_code = create_error_response(
            error_code="TEST_ERROR",
            message="测试错误消息",
            status_code=400
        )
        
        # 验证状态码
        assert status_code == 400
        
        # 验证响应内容
        data = json.loads(response.get_data(as_text=True))
        assert "error" in data
        assert data["error"]["code"] == "TEST_ERROR"
        assert data["error"]["message"] == "测试错误消息"
    
    def test_error_response_with_extra_fields(self, app_context):
        """测试包含额外字段的错误响应"""
        response, status_code = create_error_response(
            error_code="VALIDATION_ERROR",
            message="验证失败",
            status_code=400,
            field="email",
            details="邮箱格式不正确"
        )
        
        # 验证状态码
        assert status_code == 400
        
        # 验证响应内容
        data = json.loads(response.get_data(as_text=True))
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["message"] == "验证失败"
        assert data["error"]["field"] == "email"
        assert data["error"]["details"] == "邮箱格式不正确"
    
    def test_error_response_different_status_codes(self, app_context):
        """测试不同的HTTP状态码"""
        # 400 Bad Request
        _, status = create_error_response("ERROR", "消息", 400)
        assert status == 400
        
        # 404 Not Found
        _, status = create_error_response("ERROR", "消息", 404)
        assert status == 404
        
        # 500 Internal Server Error
        _, status = create_error_response("ERROR", "消息", 500)
        assert status == 500


class TestErrorResponseFormat:
    """测试错误响应格式的一致性"""
    
    def test_error_response_structure(self, app_context):
        """测试错误响应的结构"""
        response, _ = create_error_response(
            error_code="TEST",
            message="测试",
            status_code=400
        )
        
        data = json.loads(response.get_data(as_text=True))
        
        # 验证必需字段
        assert "error" in data
        assert isinstance(data["error"], dict)
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert isinstance(data["error"]["code"], str)
        assert isinstance(data["error"]["message"], str)
    
    def test_error_codes_are_uppercase(self, app_context):
        """测试错误代码使用大写"""
        test_cases = [
            "VALIDATION_ERROR",
            "NOT_FOUND",
            "SERVICE_ERROR",
            "INTERNAL_ERROR"
        ]
        
        for error_code in test_cases:
            response, _ = create_error_response(
                error_code=error_code,
                message="测试",
                status_code=400
            )
            data = json.loads(response.get_data(as_text=True))
            assert data["error"]["code"] == error_code
            assert data["error"]["code"].isupper()


class TestServiceErrorScenarios:
    """测试服务错误场景（需求 7.2, 7.3）"""
    
    def test_face_detection_service_unavailable(self, app_context, monkeypatch):
        """
        测试人脸检测服务不可用的情况
        需求 7.2: 当人脸检测服务不可用时，系统应当通知用户并建议稍后重试
        """
        # 模拟 face_recognition 库不可用
        def mock_face_locations(*args, **kwargs):
            raise RuntimeError("Face detection service is unavailable")
        
        # 使用 monkeypatch 替换 face_recognition.face_locations
        import face_recognition
        monkeypatch.setattr(face_recognition, 'face_locations', mock_face_locations)
        
        # 尝试检测人脸
        from face_detection import FaceDetectionModule
        detector = FaceDetectionModule()
        
        # 创建一个测试图片路径（使用现有的测试图片）
        import os
        test_image = os.path.join(os.path.dirname(__file__), '..', 'backend', 'temp_uploads', 'test.jpg')
        
        # 如果测试图片不存在，创建一个简单的图片
        if not os.path.exists(test_image):
            from PIL import Image
            os.makedirs(os.path.dirname(test_image), exist_ok=True)
            img = Image.new('RGB', (100, 100), color='white')
            img.save(test_image)
        
        # 检测应该返回错误
        result = detector.detectFaces(test_image)
        
        # 验证返回了错误信息
        assert result.error is not None
        assert "Error processing image" in result.error or "unavailable" in result.error.lower()
        assert len(result.faces) == 0
    
    def test_file_system_access_failure(self):
        """
        测试文件系统访问失败的情况
        需求 7.3: 当文件系统访问失败时，系统应当记录错误详情并显示用户友好的错误消息
        """
        from file_scanner import FileSystemScannerModule
        scanner = FileSystemScannerModule()
        
        # 测试不存在的文件夹
        result = scanner.scanFolder("/nonexistent/folder/path/12345")
        assert result.error is not None
        assert "does not exist" in result.error
        assert result.totalCount == 0
        assert len(result.imagePaths) == 0
    
    def test_file_system_permission_denied(self, tmp_path, monkeypatch):
        """
        测试文件系统权限被拒绝的情况
        需求 7.3: 当文件系统访问失败时，系统应当记录错误详情并显示用户友好的错误消息
        """
        from file_scanner import FileSystemScannerModule
        scanner = FileSystemScannerModule()
        
        # 创建一个临时文件夹
        test_folder = tmp_path / "test_folder"
        test_folder.mkdir()
        
        # 模拟 os.access 返回 False（无读取权限）
        import os
        original_access = os.access
        
        def mock_access(path, mode):
            if str(path) == str(test_folder):
                return False
            return original_access(path, mode)
        
        monkeypatch.setattr(os, 'access', mock_access)
        
        # 扫描应该返回权限错误
        result = scanner.scanFolder(str(test_folder))
        assert result.error is not None
        assert "not accessible" in result.error or "permission" in result.error.lower()
        assert result.totalCount == 0
    
    def test_face_detection_with_corrupted_image(self, tmp_path):
        """
        测试处理损坏图片文件的情况
        需求 7.3: 系统应当优雅地处理错误并显示用户友好的错误消息
        """
        from face_detection import FaceDetectionModule
        detector = FaceDetectionModule()
        
        # 创建一个损坏的图片文件（只包含文本内容）
        corrupted_image = tmp_path / "corrupted.jpg"
        corrupted_image.write_text("This is not a valid image file")
        
        # 检测应该返回错误而不是崩溃
        result = detector.detectFaces(str(corrupted_image))
        assert result.error is not None
        assert "Error processing image" in result.error
        assert len(result.faces) == 0
    
    def test_service_error_exception_handling(self, app_context):
        """
        测试 ServiceError 异常的处理
        需求 7.2: 系统应当通知用户服务不可用
        """
        from error_handlers import ServiceError
        
        # 创建一个服务错误
        error = ServiceError(
            "人脸检测服务暂时不可用，请稍后重试",
            service_name="face_detection"
        )
        
        # 验证错误属性
        assert error.message == "人脸检测服务暂时不可用，请稍后重试"
        assert error.service_name == "face_detection"
        assert isinstance(error, Exception)
    
    def test_file_scanner_with_invalid_path_type(self):
        """
        测试使用无效路径类型的情况
        需求 7.3: 系统应当优雅地处理错误
        """
        from file_scanner import FileSystemScannerModule
        scanner = FileSystemScannerModule()
        
        # 创建一个临时文件（不是文件夹）
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        
        try:
            # 尝试扫描一个文件而不是文件夹
            result = scanner.scanFolder(temp_file)
            assert result.error is not None
            assert "not a directory" in result.error
            assert result.totalCount == 0
        finally:
            # 清理临时文件
            import os
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
