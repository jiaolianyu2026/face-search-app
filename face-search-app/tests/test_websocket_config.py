"""
WebSocket 配置测试
验证 WebSocket 依赖和配置是否正确
"""

import pytest


def test_flask_socketio_installed():
    """测试 flask-socketio 是否已安装"""
    try:
        import flask_socketio
        assert True
    except ImportError:
        pytest.fail("flask-socketio 未安装")


def test_socketio_imports():
    """测试 SocketIO 相关导入"""
    try:
        from flask_socketio import SocketIO, emit
        assert SocketIO is not None
        assert emit is not None
    except ImportError as e:
        pytest.fail(f"导入失败: {e}")


def test_python_socketio_installed():
    """测试 python-socketio 是否已安装"""
    try:
        import socketio
        assert True
    except ImportError:
        pytest.fail("python-socketio 未安装")


def test_websocket_dependencies():
    """测试 WebSocket 所需的所有依赖"""
    dependencies = [
        'flask_socketio',
        'socketio',
        'engineio'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        pytest.fail(f"缺少依赖: {', '.join(missing)}")


def test_socketio_test_client():
    """测试 SocketIO 测试客户端是否可用"""
    try:
        from flask import Flask
        from flask_socketio import SocketIO
        
        # 创建简单的测试应用
        test_app = Flask(__name__)
        test_socketio = SocketIO(test_app)
        
        # 创建测试客户端
        client = test_socketio.test_client(test_app)
        
        # 验证客户端可用
        assert client is not None
        assert hasattr(client, 'is_connected')
        assert hasattr(client, 'emit')
        assert hasattr(client, 'get_received')
        
        # 断开连接
        client.disconnect()
        
    except Exception as e:
        pytest.fail(f"测试客户端创建失败: {e}")


def test_socketio_events():
    """测试 SocketIO 事件处理"""
    try:
        from flask import Flask
        from flask_socketio import SocketIO, emit
        
        # 创建测试应用（禁用 session 管理以避免兼容性问题）
        test_app = Flask(__name__)
        test_socketio = SocketIO(test_app, manage_session=False)
        
        # 定义测试事件处理器
        @test_socketio.on('test_event')
        def handle_test_event(data):
            emit('test_response', {'received': data})
        
        # 创建测试客户端
        client = test_socketio.test_client(test_app)
        
        # 发送测试事件
        client.emit('test_event', {'message': 'hello'})
        
        # 接收响应
        received = client.get_received()
        
        # 验证收到响应
        assert len(received) > 0
        
        # 断开连接
        client.disconnect()
        
    except Exception as e:
        pytest.fail(f"事件处理测试失败: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
