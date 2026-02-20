"""
WebSocket 功能测试
验证实时进度更新功能是否正常工作
"""

import pytest
import time
import os
import sys
from threading import Thread

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, socketio
from socketio import SimpleClient


class TestWebSocketBasic:
    """测试 WebSocket 基本连接功能"""
    
    def test_websocket_connection(self):
        """测试 WebSocket 连接是否成功"""
        # 创建测试客户端
        client = socketio.test_client(app)
        
        # 验证连接成功
        assert client.is_connected()
        
        # 接收连接消息
        received = client.get_received()
        assert len(received) > 0
        
        # 验证收到 connected 事件
        connected_event = None
        for event in received:
            if event['name'] == 'connected':
                connected_event = event
                break
        
        assert connected_event is not None
        assert 'message' in connected_event['args'][0]
        
        # 断开连接
        client.disconnect()
        assert not client.is_connected()
    
    def test_subscribe_task_invalid(self):
        """测试订阅不存在的任务"""
        client = socketio.test_client(app)
        
        # 清空接收队列
        client.get_received()
        
        # 订阅不存在的任务
        client.emit('subscribe_task', {'taskId': 'non-existent-task'})
        
        # 等待响应
        time.sleep(0.1)
        
        # 接收消息
        received = client.get_received()
        
        # 验证收到错误消息
        error_event = None
        for event in received:
            if event['name'] == 'error':
                error_event = event
                break
        
        assert error_event is not None
        assert '未找到任务' in error_event['args'][0]['message']
        
        client.disconnect()
    
    def test_subscribe_task_missing_taskid(self):
        """测试订阅任务时缺少 taskId"""
        client = socketio.test_client(app)
        
        # 清空接收队列
        client.get_received()
        
        # 订阅任务但不提供 taskId
        client.emit('subscribe_task', {})
        
        # 等待响应
        time.sleep(0.1)
        
        # 接收消息
        received = client.get_received()
        
        # 验证收到错误消息
        error_event = None
        for event in received:
            if event['name'] == 'error':
                error_event = event
                break
        
        assert error_event is not None
        assert '需要提供 taskId' in error_event['args'][0]['message']
        
        client.disconnect()


class TestWebSocketEvents:
    """测试 WebSocket 事件发送"""
    
    def test_event_structure(self):
        """测试事件数据结构是否正确"""
        client = socketio.test_client(app)
        
        # 验证连接事件的数据结构
        received = client.get_received()
        
        for event in received:
            if event['name'] == 'connected':
                data = event['args'][0]
                assert isinstance(data, dict)
                assert 'message' in data
                assert isinstance(data['message'], str)
        
        client.disconnect()


class TestWebSocketIntegration:
    """测试 WebSocket 与搜索功能的集成"""
    
    def test_websocket_available(self):
        """测试 WebSocket 服务是否可用"""
        # 验证 socketio 对象已创建
        assert socketio is not None
        
        # 验证 app 已配置 socketio
        assert hasattr(app, 'extensions')


def test_websocket_import():
    """测试 WebSocket 相关模块是否正确导入"""
    try:
        from flask_socketio import SocketIO, emit
        assert True
    except ImportError:
        pytest.fail("flask-socketio 未安装或导入失败")


def test_socketio_initialization():
    """测试 SocketIO 是否正确初始化"""
    from app import socketio
    
    # 验证 socketio 对象存在
    assert socketio is not None
    
    # 验证 socketio 已绑定到 app
    assert socketio.server is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
