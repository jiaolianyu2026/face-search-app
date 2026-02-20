"""
Property-based tests for Face Library Management API input validation.
Tests Property 21: API Input Validation

验证需求: 6.7, 6.8
"""

import pytest
import os
import sys
import json
import uuid
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from PIL import Image, ImageDraw

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, detection_cache
from models import Face, DetectionResult


# ==================== 测试策略定义 ====================

# 有效的字符串（非空）
valid_strings = st.text(min_size=1, max_size=100)

# 无效的参数值（None, 空字符串, 错误类型）
invalid_param_values = st.one_of(
    st.none(),
    st.just(''),
    st.integers(),
    st.floats(),
    st.booleans(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text())
)

# 有效的 UUID 字符串
valid_uuids = st.uuids().map(str)

# 无效的 UUID 字符串
invalid_uuids = st.one_of(
    st.text(min_size=1, max_size=20).filter(lambda x: not _is_valid_uuid(x)),
    st.just('not-a-uuid'),
    st.just('12345'),
    st.just('')
)


def _is_valid_uuid(s):
    """检查字符串是否是有效的 UUID"""
    try:
        uuid.UUID(s)
        return True
    except (ValueError, AttributeError):
        return False


# ==================== Fixtures ====================

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_detection_data():
    """创建模拟的检测数据"""
    image_id = str(uuid.uuid4())
    face_id = str(uuid.uuid4())
    
    # 在 detection_cache 中添加模拟数据
    mock_face = Face(
        faceId=face_id,
        boundingBox={'x': 100, 'y': 100, 'width': 200, 'height': 200},
        features=[0.1] * 128
    )
    detection_cache[image_id] = DetectionResult(
        faces=[mock_face],
        error=None
    )
    
    return {'imageId': image_id, 'faceId': face_id}


# ==================== Property 21: API 输入验证 ====================

class TestProperty21_APIInputValidation:
    """
    Feature: face-library-management, Property 21: API 输入验证
    
    对于任意缺失必需参数或参数类型错误的 API 请求，
    系统应该返回 400 状态码和描述性错误消息。
    
    **Validates: Requirements 6.7, 6.8**
    """
    
    # ==================== POST /api/library/faces ====================
    
    @given(
        missing_field=st.sampled_from(['imageId', 'faceId', 'name'])
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_face_missing_required_field(self, client, mock_detection_data, missing_field):
        """
        测试保存人像时缺少必需参数
        
        对于任意缺失的必需参数（imageId, faceId, name），
        API 应该返回 400 状态码和描述性错误消息。
        """
        # 构建请求数据，故意缺少一个字段
        request_data = {
            'imageId': mock_detection_data['imageId'],
            'faceId': mock_detection_data['faceId'],
            'name': '测试人像'
        }
        del request_data[missing_field]
        
        response = client.post(
            '/api/library/faces',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证返回 400 状态码
        assert response.status_code == 400, \
            f"缺少 {missing_field} 时应返回 400，实际返回 {response.status_code}"
        
        # 验证响应包含错误信息
        data = json.loads(response.data)
        assert 'error' in data, "响应应包含 error 字段"
        assert 'code' in data['error'], "错误应包含 code 字段"
        assert data['error']['code'] == 'VALIDATION_ERROR', \
            f"错误代码应为 VALIDATION_ERROR，实际为 {data['error']['code']}"
        
        # 验证错误消息是描述性的（提到了缺失的字段）
        error_message = data['error']['message'].lower()
        assert missing_field.lower() in error_message or '参数' in error_message or '缺少' in error_message, \
            f"错误消息应提到缺失的字段 {missing_field}，实际消息: {data['error']['message']}"
    
    @given(
        invalid_value=invalid_param_values
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_face_invalid_imageId_type(self, client, invalid_value):
        """
        测试保存人像时 imageId 类型错误
        
        对于任意无效的 imageId 值（None, 空字符串, 错误类型），
        API 应该返回 400 或 404 状态码。
        """
        # 跳过字符串类型（因为字符串是有效类型，只是值可能不存在）
        assume(not isinstance(invalid_value, str) or invalid_value == '')
        
        request_data = {
            'imageId': invalid_value,
            'faceId': str(uuid.uuid4()),
            'name': '测试人像'
        }
        
        response = client.post(
            '/api/library/faces',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证返回 400 或 404 状态码
        assert response.status_code in [400, 404], \
            f"无效的 imageId 应返回 400 或 404，实际返回 {response.status_code}"
        
        # 验证响应包含错误信息
        data = json.loads(response.data)
        assert 'error' in data, "响应应包含 error 字段"
    
    # ==================== GET /api/library/faces/{faceId} ====================
    
    @given(
        invalid_face_id=invalid_uuids
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_get_face_invalid_id(self, client, invalid_face_id):
        """
        测试获取人像时使用无效的 ID
        
        对于任意无效的人像 ID，API 应该返回 404 状态码。
        """
        response = client.get(f'/api/library/faces/{invalid_face_id}')
        
        # 验证返回 404 状态码
        assert response.status_code == 404, \
            f"无效的 faceId 应返回 404，实际返回 {response.status_code}"
        
        # 验证响应包含错误信息
        data = json.loads(response.data)
        assert 'error' in data, "响应应包含 error 字段"
        assert data['error']['code'] == 'NOT_FOUND', \
            f"错误代码应为 NOT_FOUND，实际为 {data['error']['code']}"
    
    # ==================== PUT /api/library/faces/{faceId} ====================
    
    @given(
        face_id=valid_uuids
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_update_face_missing_name(self, client, face_id):
        """
        测试更新人像时缺少 name 参数
        
        对于任意人像 ID，如果请求体缺少 name 参数，
        API 应该返回 400 状态码。
        """
        # 发送空请求体
        response = client.put(
            f'/api/library/faces/{face_id}',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        # 验证返回 400 状态码
        assert response.status_code == 400, \
            f"缺少 name 参数应返回 400，实际返回 {response.status_code}"
        
        # 验证响应包含错误信息
        data = json.loads(response.data)
        assert 'error' in data, "响应应包含 error 字段"
        assert data['error']['code'] == 'VALIDATION_ERROR', \
            f"错误代码应为 VALIDATION_ERROR，实际为 {data['error']['code']}"
        
        # 验证错误消息提到了名称
        error_message = data['error']['message'].lower()
        assert 'name' in error_message or '名称' in error_message, \
            f"错误消息应提到名称，实际消息: {data['error']['message']}"
    
    @given(
        invalid_face_id=invalid_uuids,
        name=valid_strings
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_update_face_invalid_id(self, client, invalid_face_id, name):
        """
        测试更新不存在的人像
        
        对于任意无效的人像 ID，API 应该返回 404 状态码。
        """
        response = client.put(
            f'/api/library/faces/{invalid_face_id}',
            data=json.dumps({'name': name}),
            content_type='application/json'
        )
        
        # 验证返回 404 状态码
        assert response.status_code == 404, \
            f"无效的 faceId 应返回 404，实际返回 {response.status_code}"
        
        # 验证响应包含错误信息
        data = json.loads(response.data)
        assert 'error' in data, "响应应包含 error 字段"
        assert data['error']['code'] == 'NOT_FOUND', \
            f"错误代码应为 NOT_FOUND，实际为 {data['error']['code']}"
    
    # ==================== DELETE /api/library/faces/{faceId} ====================
    
    @given(
        invalid_face_id=invalid_uuids
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_delete_face_invalid_id(self, client, invalid_face_id):
        """
        测试删除不存在的人像
        
        对于任意无效的人像 ID，API 应该返回 404 状态码。
        """
        response = client.delete(f'/api/library/faces/{invalid_face_id}')
        
        # 验证返回 404 状态码
        assert response.status_code == 404, \
            f"无效的 faceId 应返回 404，实际返回 {response.status_code}"
        
        # 验证响应包含错误信息
        data = json.loads(response.data)
        assert 'error' in data, "响应应包含 error 字段"
        assert data['error']['code'] == 'NOT_FOUND', \
            f"错误代码应为 NOT_FOUND，实际为 {data['error']['code']}"
    
    # ==================== GET /api/library/faces/{faceId}/thumbnail ====================
    
    @given(
        invalid_face_id=invalid_uuids
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_get_thumbnail_invalid_id(self, client, invalid_face_id):
        """
        测试获取不存在人像的缩略图
        
        对于任意无效的人像 ID，API 应该返回 404 状态码。
        """
        response = client.get(f'/api/library/faces/{invalid_face_id}/thumbnail')
        
        # 验证返回 404 状态码
        assert response.status_code == 404, \
            f"无效的 faceId 应返回 404，实际返回 {response.status_code}"
        
        # 验证响应包含错误信息
        data = json.loads(response.data)
        assert 'error' in data, "响应应包含 error 字段"
        assert data['error']['code'] == 'NOT_FOUND', \
            f"错误代码应为 NOT_FOUND，实际为 {data['error']['code']}"
    
    # ==================== 综合测试：多个端点的输入验证 ====================
    
    @given(
        endpoint=st.sampled_from([
            ('POST', '/api/library/faces'),
            ('GET', '/api/library/faces'),
            ('GET', '/api/library/faces/test-id'),
            ('PUT', '/api/library/faces/test-id'),
            ('DELETE', '/api/library/faces/test-id'),
            ('GET', '/api/library/faces/test-id/thumbnail')
        ])
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_endpoints_handle_invalid_content_type(self, client, endpoint):
        """
        测试所有端点处理无效的 Content-Type
        
        对于任意端点，如果发送非 JSON 的请求体（对于需要 JSON 的端点），
        应该返回适当的错误响应。
        """
        method, path = endpoint
        
        # 只测试需要 JSON 请求体的端点
        if method in ['POST', 'PUT']:
            response = client.open(
                path,
                method=method,
                data='not-json-data',
                content_type='text/plain'
            )
            
            # 验证返回错误状态码（400 或 415）
            assert response.status_code in [400, 415], \
                f"{method} {path} 应返回 400 或 415，实际返回 {response.status_code}"
    
    @given(
        malformed_json=st.one_of(
            st.just('{invalid json}'),
            st.just('{"unclosed": '),
            st.just('[1, 2, 3]'),  # 数组而不是对象
            st.just('null'),
            st.just('true'),
            st.just('123')
        )
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_face_malformed_json(self, client, malformed_json):
        """
        测试保存人像时发送格式错误的 JSON
        
        对于任意格式错误的 JSON，API 应该返回 400 状态码。
        """
        response = client.post(
            '/api/library/faces',
            data=malformed_json,
            content_type='application/json'
        )
        
        # 验证返回 400 状态码
        assert response.status_code == 400, \
            f"格式错误的 JSON 应返回 400，实际返回 {response.status_code}"


# ==================== 辅助测试：验证错误响应格式一致性 ====================

class TestErrorResponseFormat:
    """验证所有 API 端点的错误响应格式一致"""
    
    def test_error_response_structure(self, client):
        """
        测试错误响应的结构一致性
        
        所有错误响应应该包含：
        - error.code: 错误代码
        - error.message: 错误消息
        - error.timestamp: 时间戳（可选）
        """
        # 触发一个验证错误
        response = client.post(
            '/api/library/faces',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        # 验证错误结构
        assert 'error' in data, "响应应包含 error 字段"
        assert 'code' in data['error'], "错误应包含 code 字段"
        assert 'message' in data['error'], "错误应包含 message 字段"
        
        # 验证错误代码是字符串
        assert isinstance(data['error']['code'], str), "错误代码应为字符串"
        
        # 验证错误消息是字符串且非空
        assert isinstance(data['error']['message'], str), "错误消息应为字符串"
        assert len(data['error']['message']) > 0, "错误消息不应为空"
    
    def test_not_found_error_includes_resource_info(self, client):
        """
        测试 404 错误包含资源信息
        
        NotFoundError 应该包含：
        - resourceType: 资源类型
        - resourceId: 资源ID（可选）
        """
        # 触发一个 404 错误
        response = client.get('/api/library/faces/nonexistent-id')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        # 验证包含资源类型信息
        assert 'error' in data
        assert 'resourceType' in data['error'], "404 错误应包含 resourceType"
        assert isinstance(data['error']['resourceType'], str), "resourceType 应为字符串"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
