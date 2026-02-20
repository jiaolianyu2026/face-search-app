# WebSocket 实时进度更新使用指南

## 概述

本应用支持通过 WebSocket 实时推送搜索进度更新，无需客户端轮询 API。这提供了更好的用户体验和更低的服务器负载。

## 服务器端实现

### WebSocket 事件

服务器会发送以下 WebSocket 事件：

1. **connected** - 客户端连接成功
   ```json
   {
     "message": "已连接到服务器"
   }
   ```

2. **search_status** - 搜索任务状态更新
   ```json
   {
     "taskId": "uuid",
     "status": "running",
     "progress": {
       "current": 0,
       "total": 100,
       "percentage": 0,
       "currentFile": null
     }
   }
   ```

3. **search_progress** - 搜索进度更新（实时）
   ```json
   {
     "taskId": "uuid",
     "progress": {
       "current": 45,
       "total": 100,
       "percentage": 45,
       "currentFile": "/path/to/current/image.jpg"
     }
   }
   ```

4. **search_completed** - 搜索完成
   ```json
   {
     "taskId": "uuid",
     "status": "completed",
     "totalProcessed": 100,
     "matchesFound": 15
   }
   ```

5. **search_cancelled** - 搜索被取消
   ```json
   {
     "taskId": "uuid",
     "status": "cancelled",
     "totalProcessed": 45,
     "matchesFound": 8
   }
   ```

6. **search_error** - 搜索过程中发生错误
   ```json
   {
     "taskId": "uuid",
     "error": "错误描述"
   }
   ```

### 客户端可发送的事件

1. **subscribe_task** - 订阅特定任务的更新
   ```json
   {
     "taskId": "uuid"
   }
   ```

## 前端集成示例

### 使用 Socket.IO 客户端库

#### 1. 安装依赖

```bash
npm install socket.io-client
```

#### 2. React 示例

```javascript
import { useEffect, useState } from 'react';
import io from 'socket.io-client';

function SearchProgress({ taskId }) {
  const [progress, setProgress] = useState({
    current: 0,
    total: 0,
    percentage: 0,
    currentFile: null
  });
  const [status, setStatus] = useState('pending');
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    // 连接到 WebSocket 服务器
    const newSocket = io('http://localhost:5000');
    
    // 监听连接事件
    newSocket.on('connected', (data) => {
      console.log('WebSocket 已连接:', data.message);
      
      // 订阅任务更新
      newSocket.emit('subscribe_task', { taskId });
    });
    
    // 监听任务状态
    newSocket.on('task_status', (data) => {
      if (data.taskId === taskId) {
        setStatus(data.status);
        setProgress(data.progress);
      }
    });
    
    // 监听进度更新
    newSocket.on('search_progress', (data) => {
      if (data.taskId === taskId) {
        setProgress(data.progress);
      }
    });
    
    // 监听搜索完成
    newSocket.on('search_completed', (data) => {
      if (data.taskId === taskId) {
        setStatus('completed');
        console.log(`搜索完成: 处理 ${data.totalProcessed} 个文件, 找到 ${data.matchesFound} 个匹配`);
      }
    });
    
    // 监听搜索取消
    newSocket.on('search_cancelled', (data) => {
      if (data.taskId === taskId) {
        setStatus('cancelled');
        console.log(`搜索已取消: 处理 ${data.totalProcessed} 个文件, 找到 ${data.matchesFound} 个匹配`);
      }
    });
    
    // 监听错误
    newSocket.on('search_error', (data) => {
      if (data.taskId === taskId) {
        console.error('搜索错误:', data.error);
      }
    });
    
    setSocket(newSocket);
    
    // 清理函数
    return () => {
      newSocket.close();
    };
  }, [taskId]);

  return (
    <div>
      <h3>搜索进度</h3>
      <p>状态: {status}</p>
      <p>进度: {progress.current} / {progress.total} ({progress.percentage}%)</p>
      {progress.currentFile && (
        <p>当前文件: {progress.currentFile}</p>
      )}
      <progress value={progress.percentage} max="100" />
    </div>
  );
}

export default SearchProgress;
```

#### 3. Vue 示例

```javascript
<template>
  <div>
    <h3>搜索进度</h3>
    <p>状态: {{ status }}</p>
    <p>进度: {{ progress.current }} / {{ progress.total }} ({{ progress.percentage }}%)</p>
    <p v-if="progress.currentFile">当前文件: {{ progress.currentFile }}</p>
    <progress :value="progress.percentage" max="100"></progress>
  </div>
</template>

<script>
import io from 'socket.io-client';

export default {
  props: ['taskId'],
  data() {
    return {
      socket: null,
      status: 'pending',
      progress: {
        current: 0,
        total: 0,
        percentage: 0,
        currentFile: null
      }
    };
  },
  mounted() {
    // 连接到 WebSocket 服务器
    this.socket = io('http://localhost:5000');
    
    // 监听连接事件
    this.socket.on('connected', (data) => {
      console.log('WebSocket 已连接:', data.message);
      
      // 订阅任务更新
      this.socket.emit('subscribe_task', { taskId: this.taskId });
    });
    
    // 监听任务状态
    this.socket.on('task_status', (data) => {
      if (data.taskId === this.taskId) {
        this.status = data.status;
        this.progress = data.progress;
      }
    });
    
    // 监听进度更新
    this.socket.on('search_progress', (data) => {
      if (data.taskId === this.taskId) {
        this.progress = data.progress;
      }
    });
    
    // 监听搜索完成
    this.socket.on('search_completed', (data) => {
      if (data.taskId === this.taskId) {
        this.status = 'completed';
        console.log(`搜索完成: 处理 ${data.totalProcessed} 个文件, 找到 ${data.matchesFound} 个匹配`);
      }
    });
    
    // 监听搜索取消
    this.socket.on('search_cancelled', (data) => {
      if (data.taskId === this.taskId) {
        this.status = 'cancelled';
        console.log(`搜索已取消: 处理 ${data.totalProcessed} 个文件, 找到 ${data.matchesFound} 个匹配`);
      }
    });
    
    // 监听错误
    this.socket.on('search_error', (data) => {
      if (data.taskId === this.taskId) {
        console.error('搜索错误:', data.error);
      }
    });
  },
  beforeUnmount() {
    if (this.socket) {
      this.socket.close();
    }
  }
};
</script>
```

#### 4. 原生 JavaScript 示例

```javascript
// 连接到 WebSocket 服务器
const socket = io('http://localhost:5000');

// 监听连接事件
socket.on('connected', (data) => {
  console.log('WebSocket 已连接:', data.message);
  
  // 订阅任务更新
  socket.emit('subscribe_task', { taskId: 'your-task-id' });
});

// 监听进度更新
socket.on('search_progress', (data) => {
  console.log('进度更新:', data.progress);
  
  // 更新 UI
  document.getElementById('progress-bar').value = data.progress.percentage;
  document.getElementById('progress-text').textContent = 
    `${data.progress.current} / ${data.progress.total}`;
  
  if (data.progress.currentFile) {
    document.getElementById('current-file').textContent = data.progress.currentFile;
  }
});

// 监听搜索完成
socket.on('search_completed', (data) => {
  console.log('搜索完成:', data);
  alert(`搜索完成！找到 ${data.matchesFound} 个匹配结果`);
});

// 监听搜索取消
socket.on('search_cancelled', (data) => {
  console.log('搜索已取消:', data);
  alert(`搜索已取消。已处理 ${data.totalProcessed} 个文件`);
});

// 监听错误
socket.on('search_error', (data) => {
  console.error('搜索错误:', data.error);
  alert(`搜索出错: ${data.error}`);
});
```

## 与轮询方式的对比

### 轮询方式（旧方法）

```javascript
// 需要定期调用 API
const pollInterval = setInterval(async () => {
  const response = await fetch(`/api/search/${taskId}`);
  const data = await response.json();
  
  updateProgress(data.progress);
  
  if (data.status === 'completed' || data.status === 'cancelled') {
    clearInterval(pollInterval);
  }
}, 1000); // 每秒轮询一次
```

**缺点：**
- 增加服务器负载（即使没有更新也要请求）
- 延迟较高（最多 1 秒延迟）
- 浪费带宽

### WebSocket 方式（新方法）

```javascript
// 实时接收更新，无需轮询
socket.on('search_progress', (data) => {
  updateProgress(data.progress);
});
```

**优点：**
- 实时更新（几乎零延迟）
- 减少服务器负载
- 节省带宽
- 更好的用户体验

## 兼容性说明

- WebSocket 是可选功能，不影响现有的 REST API
- 客户端可以选择使用 WebSocket 或继续使用轮询方式
- 两种方式可以同时使用（WebSocket 用于实时更新，API 用于获取完整结果）

## 测试 WebSocket 连接

可以使用浏览器控制台测试 WebSocket 连接：

```javascript
// 在浏览器控制台中运行
const socket = io('http://localhost:5000');

socket.on('connected', (data) => {
  console.log('已连接:', data);
});

socket.on('search_progress', (data) => {
  console.log('进度:', data);
});
```

## 故障排除

### 连接失败

1. 确保服务器正在运行
2. 检查 CORS 设置
3. 确认端口号正确（默认 5000）

### 未收到更新

1. 确认已订阅任务：`socket.emit('subscribe_task', { taskId })`
2. 检查 taskId 是否正确
3. 查看服务器日志

### 性能问题

- WebSocket 连接是持久的，不要为每个请求创建新连接
- 在组件卸载时记得关闭连接：`socket.close()`
- 考虑使用连接池管理多个任务

## 需求验证

此实现满足以下需求：

- **需求 6.2**: 实时更新已处理的图片数量和总图片数量
- **需求 6.3**: 显示当前正在处理的文件路径
- **需求 6.4**: 支持取消操作并通知客户端
- **需求 6.5**: 取消后显示部分结果

## 性能优化

WebSocket 实现相比轮询方式的性能提升：

- 减少 HTTP 请求数量：从每秒 1 次减少到 0 次（仅在有更新时推送）
- 降低延迟：从最多 1 秒减少到几乎实时（< 100ms）
- 节省带宽：仅传输变化的数据，而不是完整的状态
- 减少服务器负载：无需处理大量轮询请求
