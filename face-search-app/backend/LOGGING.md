# 日志记录系统使用说明

## 概述

本应用使用 Python 标准库的 `logging` 模块实现统一的日志记录功能。所有错误、警告和关键操作都会被记录到日志文件中，便于调试和问题追踪。

## 日志配置

### 日志文件位置
- 文件路径：`backend/app.log`
- 最大文件大小：10MB
- 备份文件数量：5 个（自动轮转）

### 日志级别
- **DEBUG**：详细的调试信息
- **INFO**：一般信息（默认级别）
- **WARNING**：警告信息
- **ERROR**：错误信息
- **CRITICAL**：严重错误

可以在 `backend/config.py` 中修改 `LOG_LEVEL` 配置来调整日志级别。

### 日志格式
```
时间戳 | 级别 | 模块:函数:行号 | 消息
```

示例：
```
2026-02-14 08:22:08 | ERROR | face_detection:detectFaces:73 | 图片文件未找到: /nonexistent/path/image.jpg
```

## 使用方法

### 在模块中使用日志记录器

```python
from logger import get_logger

# 创建日志记录器（使用模块名称）
logger = get_logger('module_name')

# 记录不同级别的日志
logger.debug('调试信息')
logger.info('一般信息')
logger.warning('警告信息')
logger.error('错误信息')
logger.critical('严重错误')

# 记录异常堆栈跟踪
try:
    # 可能出错的代码
    pass
except Exception as e:
    logger.error(f'操作失败: {str(e)}', exc_info=True)
```

### 已集成日志的模块

以下模块已集成日志记录功能：

1. **app.py** - Flask 应用主模块
   - 应用启动/关闭
   - 图片上传成功/失败
   - 人脸检测请求
   - 搜索任务创建/完成/取消
   - 图片转存操作

2. **error_handlers.py** - 错误处理模块
   - 验证错误
   - 资源未找到错误
   - 服务错误
   - HTTP 错误（413, 500, 404, 405）

3. **face_detection.py** - 人脸检测模块
   - 人脸检测开始/完成
   - 检测到的人脸数量
   - 文件未找到错误
   - 图片处理错误

4. **face_search.py** - 人脸搜索模块
   - 搜索任务开始/完成
   - 扫描文件夹结果
   - 处理进度
   - 跳过的文件
   - 搜索取消

5. **image_export.py** - 图片转存模块
   - 转存操作开始/完成
   - 成功/失败统计
   - 文件复制错误
   - 权限错误

## 日志记录的内容

### 成功操作
- 图片上传成功（包含 imageId 和文件名）
- 人脸检测完成（包含检测到的人脸数量）
- 搜索任务完成（包含匹配结果数量）
- 图片转存完成（包含成功/失败数量）

### 错误和警告
- 文件不存在
- 权限错误
- 验证失败
- 服务不可用
- 异常堆栈跟踪（使用 `exc_info=True`）

### 调试信息
- 使用缓存的人脸特征
- 跳过的文件
- 详细的处理步骤

## 日志文件管理

### 自动轮转
当日志文件达到 10MB 时，系统会自动创建新的日志文件，旧文件会被重命名为：
- `app.log.1`
- `app.log.2`
- `app.log.3`
- `app.log.4`
- `app.log.5`

最多保留 5 个备份文件，超过的会被自动删除。

### 查看日志
```bash
# 查看最新的 20 行日志
tail -n 20 backend/app.log

# Windows PowerShell
Get-Content backend/app.log -Tail 20

# 实时监控日志
tail -f backend/app.log

# Windows PowerShell
Get-Content backend/app.log -Wait
```

### 清理日志
如果需要清理日志文件：
```bash
# 删除所有日志文件
rm backend/app.log*

# Windows PowerShell
Remove-Item backend/app.log*
```

## 配置选项

在 `backend/config.py` 中可以配置：

```python
# 日志文件路径
LOG_FILE = os.path.join(os.path.dirname(__file__), 'app.log')

# 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
LOG_LEVEL = 'INFO'
```

## 注意事项

1. **性能影响**：日志记录对性能影响很小，但在生产环境中建议使用 INFO 或 WARNING 级别
2. **敏感信息**：避免在日志中记录密码、密钥等敏感信息
3. **磁盘空间**：定期检查日志文件大小，确保有足够的磁盘空间
4. **编码问题**：日志文件使用 UTF-8 编码，支持中文字符

## 故障排查

### 日志文件未创建
- 检查 `backend/` 目录是否有写入权限
- 检查 `config.py` 中的 `LOG_FILE` 路径是否正确

### 日志内容乱码
- 确保使用 UTF-8 编码读取日志文件
- Windows 用户可以使用 `Get-Content -Encoding UTF8`

### 日志级别不正确
- 检查 `config.py` 中的 `LOG_LEVEL` 设置
- 确保使用大写字母（INFO, DEBUG, WARNING, ERROR, CRITICAL）

## 需求验证

本日志系统满足需求 7.4：
- ✅ 配置 Python logging 模块
- ✅ 创建日志文件（app.log）
- ✅ 记录所有错误和警告
- ✅ 包含时间戳、级别、消息
- ✅ 包含堆栈跟踪（使用 exc_info=True）
