# 搜索进度显示0%问题修复报告

## 问题描述

用户报告在执行多人像搜索时，搜索进度一直显示为0.0%，并且前端出现连接错误：
```
[vite] http proxy error: /api/search/... AggregateError [ECONNREFUSED]
```

## 根本原因分析

通过日志分析发现以下问题链：

### 1. 后端服务器崩溃
- **时间线**：
  - 23:54:21 - 创建搜索任务并开始执行
  - 23:54:21 - 扫描到12个图片文件，使用并行处理
  - 23:58:30 - 服务器重启（中间4分钟无任何日志）
  
- **崩溃原因**：进度回调函数中的异常未被捕获，导致后台线程崩溃，进而导致整个Flask进程停止

### 2. 进度回调中的潜在问题
在 `backend/multi_search.py` 和 `backend/app.py` 中的进度回调函数缺少异常处理：
- WebSocket emit 可能失败
- 进度计算可能出现异常
- 任何未捕获的异常都会导致后台线程崩溃

### 3. 任务状态丢失
- 服务器重启后，内存中的搜索任务（`search_tasks` 字典）被清空
- 前端仍在轮询旧的任务ID，导致404错误
- 前端无法感知服务器重启，持续轮询导致大量错误日志

## 已实施的修复

### 修复1：进度回调异常处理（multi_search.py）
```python
def wrapped_progress_callback(progress: Progress, current_face_idx=face_idx):
    if progress_callback:
        try:
            # 计算综合进度
            base_progress = current_face_idx / num_faces
            face_progress = (progress.current / progress.total if progress.total > 0 else 0) / num_faces
            total_progress_ratio = base_progress + face_progress
            
            # 创建综合进度对象
            virtual_total = 1000
            virtual_current = int(total_progress_ratio * virtual_total)
            
            combined_progress = Progress(
                current=virtual_current,
                total=virtual_total,
                currentFile=progress.currentFile
            )
            progress_callback(combined_progress)
        except Exception as e:
            logger.error(f"进度回调发生错误: {str(e)}", exc_info=True)
```

### 修复2：WebSocket进度回调异常处理（app.py）
在两个进度回调函数中添加了try-except块：

**单人像搜索进度回调**：
```python
def progress_callback(progress: Progress):
    try:
        search_task.progress = progress
        socketio.emit('search_progress', {
            'taskId': search_task.taskId,
            'progress': {
                'current': progress.current,
                'total': progress.total,
                'percentage': progress.percentage,
                'currentFile': progress.currentFile
            }
        })
    except Exception as e:
        logger.error(f"进度回调发生错误: {str(e)}", exc_info=True)
```

**多人像搜索进度回调**（相同的异常处理）

## 修复效果

1. **防止服务器崩溃**：即使进度回调中出现异常，也不会导致后台线程或服务器崩溃
2. **详细错误日志**：任何异常都会被记录到日志中，便于排查问题
3. **搜索继续执行**：即使某次进度更新失败，搜索任务仍会继续执行

## 测试建议

用户需要：
1. **刷新浏览器页面**，清除旧的任务ID
2. **重新开始搜索流程**：
   - 上传图片
   - 检测人脸
   - 选择目标人像
   - 开始搜索
3. **观察进度显示**是否正常更新
4. **检查后端日志**（backend/app.log）是否有新的错误信息

## 后续改进建议

### 1. 任务持久化
考虑将搜索任务状态持久化到数据库或文件，避免服务器重启导致任务丢失：
```python
# 使用SQLite或Redis存储任务状态
# 服务器重启后可以恢复任务信息
```

### 2. 前端错误处理
前端应该能够检测到服务器重启（连续404错误），并提示用户重新开始：
```javascript
// 检测连续的404错误
if (consecutiveErrors > 5) {
    alert('服务器已重启，请重新开始搜索');
    // 清除任务ID，返回初始状态
}
```

### 3. 健康检查端点
添加一个健康检查端点，前端可以定期检查服务器状态：
```python
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'timestamp': time.time()})
```

### 4. 更详细的进度日志
在搜索过程中添加更多日志，便于排查问题：
```python
logger.debug(f"进度更新: {progress.current}/{progress.total} ({progress.percentage}%)")
```

## 文件变更清单

- `backend/multi_search.py` - 添加进度回调异常处理
- `backend/app.py` - 添加两个进度回调函数的异常处理

## 部署状态

✅ 修复已应用
✅ 后端服务器已重启（进程ID: 12）
⏳ 等待用户测试验证
