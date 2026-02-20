# 设计文档

## 概述

人脸识别搜索应用是一个基于Web的应用程序，采用前后端分离架构。前端提供用户界面用于图片上传、人脸选择和结果展示；后端负责人脸检测、特征提取、图片搜索和文件操作。系统使用成熟的人脸识别库进行人脸检测和特征提取，通过余弦相似度计算进行人脸匹配。

## 架构

### 系统架构

系统采用三层架构：

1. **表示层（前端）**
   - 基于现代Web框架构建的单页应用
   - 负责用户交互、图片预览、结果展示
   - 通过HTTP API与后端通信

2. **业务逻辑层（后端API）**
   - RESTful API服务
   - 处理业务逻辑：文件上传、人脸检测、搜索协调
   - 管理任务队列和进度跟踪

3. **数据处理层**
   - 人脸检测引擎：使用预训练模型检测人脸
   - 特征提取引擎：生成人脸特征向量
   - 文件系统访问：扫描和读取图片文件

### 技术栈建议

**后端:**
- 人脸识别库：face_recognition（基于dlib）或 InsightFace
- 图片处理：OpenCV 或 Pillow
- 向量计算：NumPy
- 并发处理：多线程或异步IO

**前端:**
- 现代Web框架（React/Vue/Svelte）
- 文件上传组件
- 图片预览和标注组件

**通信:**
- RESTful API
- WebSocket（用于实时进度更新）

## 组件和接口

### 1. 图片上传模块（ImageUploadModule）

**职责：** 处理用户上传的图片文件

**接口：**

```
function uploadImage(file: File) -> UploadResult
  输入：
    - file: 图片文件对象
  输出：
    - UploadResult {
        success: boolean
        imageId: string
        previewUrl: string
        error?: string
      }
  前置条件：
    - file 不为空
    - file.size <= 10MB
    - file.type in ['image/jpeg', 'image/png', 'image/webp']
  后置条件：
    - 如果成功，图片被保存到临时存储
    - 返回唯一的 imageId 用于后续操作
```

### 2. 人脸检测模块（FaceDetectionModule）

**职责：** 检测图片中的人脸并提取特征

**接口：**

```
function detectFaces(imageId: string) -> DetectionResult
  输入：
    - imageId: 图片唯一标识符
  输出：
    - DetectionResult {
        faces: Face[]
        error?: string
      }
    - Face {
        faceId: string
        boundingBox: {x, y, width, height}
        features: float[]  // 128维特征向量
      }
  前置条件：
    - imageId 对应的图片存在
  后置条件：
    - 返回图片中所有检测到的人脸
    - 每个人脸包含位置和特征向量
```

```
function extractFeatures(imageId: string, faceId: string) -> float[]
  输入：
    - imageId: 图片标识符
    - faceId: 人脸标识符
  输出：
    - 128维特征向量
  前置条件：
    - 指定的人脸存在
  后置条件：
    - 返回该人脸的特征向量
```

### 3. 文件系统扫描模块（FileSystemScannerModule）

**职责：** 扫描指定文件夹中的所有图片文件

**接口：**

```
function scanFolder(folderPath: string) -> ScanResult
  输入：
    - folderPath: 文件夹路径
  输出：
    - ScanResult {
        imagePaths: string[]
        totalCount: number
        error?: string
      }
  前置条件：
    - folderPath 存在且可访问
  后置条件：
    - 返回所有图片文件的完整路径
    - 递归包含所有子文件夹
```

### 4. 人脸搜索模块（FaceSearchModule）

**职责：** 在图片集合中搜索匹配的人脸

**接口：**

```
function searchFaces(
  targetFeatures: float[],
  searchFolder: string,
  threshold: float = 0.6,
  progressCallback?: (progress: Progress) -> void
) -> SearchResult
  输入：
    - targetFeatures: 目标人脸特征向量
    - searchFolder: 搜索文件夹路径
    - threshold: 相似度阈值（默认0.6）
    - progressCallback: 进度回调函数
  输出：
    - SearchResult {
        matches: Match[]
        totalProcessed: number
        cancelled: boolean
      }
    - Match {
        imagePath: string
        similarity: float
        faceLocation: {x, y, width, height}
      }
  前置条件：
    - targetFeatures 是有效的128维向量
    - searchFolder 存在且可访问
    - 0 <= threshold <= 1
  后置条件：
    - 返回所有相似度 >= threshold 的匹配结果
    - 结果按相似度降序排列
```

```
function cancelSearch(searchId: string) -> boolean
  输入：
    - searchId: 搜索任务标识符
  输出：
    - 是否成功取消
  后置条件：
    - 搜索任务被标记为取消状态
    - 不再处理新的图片
```

### 5. 相似度计算模块（SimilarityModule）

**职责：** 计算两个人脸特征向量的相似度

**接口：**

```
function computeSimilarity(features1: float[], features2: float[]) -> float
  输入：
    - features1: 第一个特征向量
    - features2: 第二个特征向量
  输出：
    - 相似度分数（0-1之间）
  前置条件：
    - features1 和 features2 长度相同
    - 两个向量都已归一化
  后置条件：
    - 返回余弦相似度
    - 值越接近1表示越相似
  
  算法：
    similarity = dot(features1, features2) / (norm(features1) * norm(features2))
```

### 6. 图片转存模块（ImageExportModule）

**职责：** 将匹配的图片复制到目标目录

**接口：**

```
function exportImages(
  imagePaths: string[],
  targetFolder: string,
  progressCallback?: (progress: Progress) -> void
) -> ExportResult
  输入：
    - imagePaths: 要转存的图片路径列表
    - targetFolder: 目标文件夹路径
    - progressCallback: 进度回调函数
  输出：
    - ExportResult {
        successCount: number
        failedCount: number
        errors: {path: string, error: string}[]
      }
  前置条件：
    - targetFolder 存在且可写
    - imagePaths 不为空
  后置条件：
    - 图片被复制到目标文件夹
    - 文件名冲突时自动重命名（添加数字后缀）
    - 保持原始文件扩展名
```

### 7. 缓存模块（CacheModule）

**职责：** 缓存已处理图片的人脸特征

**接口：**

```
function getCachedFeatures(imagePath: string) -> CacheEntry?
  输入：
    - imagePath: 图片文件路径
  输出：
    - CacheEntry {
        features: Face[]
        timestamp: number
        fileHash: string
      } 或 null
  后置条件：
    - 如果缓存存在且文件未修改，返回缓存的特征
    - 否则返回 null
```

```
function setCachedFeatures(imagePath: string, faces: Face[]) -> void
  输入：
    - imagePath: 图片文件路径
    - faces: 检测到的人脸列表
  后置条件：
    - 特征被缓存，关联文件路径和修改时间
```

## 数据模型

### Face（人脸）

```
Face {
  faceId: string           // 唯一标识符
  boundingBox: {           // 人脸位置
    x: number
    y: number
    width: number
    height: number
  }
  features: float[128]     // 特征向量
}
```

### Match（匹配结果）

```
Match {
  imagePath: string        // 图片完整路径
  similarity: float        // 相似度分数 [0, 1]
  faceLocation: {          // 匹配人脸的位置
    x: number
    y: number
    width: number
    height: number
  }
  thumbnailUrl?: string    // 缩略图URL（可选）
}
```

### Progress（进度信息）

```
Progress {
  current: number          // 当前处理数量
  total: number            // 总数量
  currentFile?: string     // 当前处理的文件
  percentage: number       // 百分比 [0, 100]
}
```

### SearchTask（搜索任务）

```
SearchTask {
  taskId: string           // 任务唯一标识符
  targetFeatures: float[]  // 目标特征向量
  searchFolder: string     // 搜索文件夹
  threshold: float         // 相似度阈值
  status: 'pending' | 'running' | 'completed' | 'cancelled'
  progress: Progress       // 当前进度
  results: Match[]         // 搜索结果
  createdAt: number        // 创建时间戳
}
```

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*


### 属性 1: 图片格式验证

*对于任何*文件输入，系统应当接受JPEG、PNG、WebP格式的文件，并拒绝其他格式的文件

**验证需求：1.1, 4.1**

### 属性 2: 文件大小限制

*对于任何*上传的文件，如果大小超过10MB，系统应当拒绝该文件

**验证需求：1.2**

### 属性 3: 图片上传往返一致性

*对于任何*成功上传的图片，使用返回的imageId应当能够检索到该图片进行后续处理

**验证需求：1.4**

### 属性 4: 人脸检测结果完整性

*对于任何*检测到的人脸，结果应当包含边界框位置信息和128维特征向量

**验证需求：2.3, 2.5**

### 属性 5: 文件夹路径验证

*对于任何*文件夹路径输入，系统应当验证路径是否存在且可访问，无效路径应当返回错误

**验证需求：3.2, 3.3**

### 属性 6: 递归扫描完整性

*对于任何*有效的文件夹路径，扫描结果应当包含该文件夹及所有子文件夹中的所有支持格式的图片文件

**验证需求：3.4**

### 属性 7: 搜索错误恢复

*对于任何*包含部分损坏或无法读取文件的文件夹，搜索应当跳过这些文件并继续处理其他有效文件

**验证需求：4.3**

### 属性 8: 人脸比对完整性

*对于任何*搜索任务，搜索文件夹中所有检测到的人脸都应当与目标人脸特征进行相似度计算

**验证需求：4.2, 4.4**

### 属性 9: 相似度阈值匹配

*对于任何*搜索结果，所有返回的匹配图片的相似度分数都应当大于或等于设定的阈值

**验证需求：4.5, 5.1**

### 属性 10: 搜索结果数据完整性

*对于任何*匹配结果，每个Match对象都应当包含图片路径、相似度分数和人脸位置信息

**验证需求：5.2**

### 属性 11: 结果排序不变性

*对于任何*搜索结果列表，匹配图片应当按相似度分数从高到低排序，即对于任意i < j，results[i].similarity >= results[j].similarity

**验证需求：5.3**

### 属性 12: 搜索进度信息完整性

*对于任何*搜索进度更新，Progress对象应当包含当前处理数量、总数量、当前文件路径和百分比信息

**验证需求：6.2, 6.3**

### 属性 13: 搜索取消有效性

*对于任何*正在运行的搜索任务，调用取消操作后，系统应当停止处理新文件，并保留已找到的结果

**验证需求：6.4, 6.5**

### 属性 14: 错误日志记录

*对于任何*系统错误，都应当在日志文件中记录错误详情（时间戳、错误类型、错误消息）

**验证需求：7.4**

### 属性 15: 图片转存往返验证

*对于任何*成功转存的图片，目标目录中应当存在对应的文件，且文件内容与源文件一致

**验证需求：8.4**

### 属性 16: 文件名冲突处理

*对于任何*转存操作，当目标目录中存在同名文件时，新文件应当被重命名（添加数字后缀），不应覆盖现有文件

**验证需求：8.5**

### 属性 17: 转存结果统计准确性

*对于任何*转存操作，返回的ExportResult中的successCount + failedCount应当等于请求转存的图片总数

**验证需求：8.6, 8.7**

### 属性 18: 缓存一致性

*对于任何*图片文件，如果文件内容未修改（基于文件哈希或修改时间），第二次处理时应当使用缓存的特征数据，而不是重新计算

**验证需求：9.4**

### 属性 19: 相似度计算对称性

*对于任何*两个特征向量A和B，computeSimilarity(A, B)应当等于computeSimilarity(B, A)

**验证需求：隐含的数学属性**

### 属性 20: 相似度范围约束

*对于任何*两个有效的特征向量，计算得到的相似度分数应当在[0, 1]范围内

**验证需求：隐含的数学属性**

## 错误处理

### 错误类型

1. **输入验证错误**
   - 无效的文件格式
   - 文件大小超限
   - 无效的文件夹路径
   - 错误：返回HTTP 400，包含具体错误原因

2. **业务逻辑错误**
   - 图片中未检测到人脸
   - 无效的imageId或faceId
   - 错误：返回HTTP 404或422，包含描述性消息

3. **系统错误**
   - 人脸检测服务不可用
   - 文件系统访问失败
   - 内存不足
   - 错误：返回HTTP 500，记录详细日志，显示用户友好消息

4. **运行时错误**
   - 图片文件损坏
   - 读取权限不足
   - 处理：跳过该文件，记录警告，继续处理其他文件

### 错误处理策略

1. **优雅降级**
   - 单个文件处理失败不应影响整体搜索
   - 部分结果优于完全失败
   - 提供清晰的错误统计

2. **错误恢复**
   - 允许用户重试失败的操作
   - 保持系统状态一致性
   - 清理临时资源

3. **日志记录**
   - 所有错误记录到日志文件
   - 包含时间戳、错误类型、堆栈跟踪
   - 区分错误级别（ERROR、WARNING、INFO）

4. **用户反馈**
   - 显示清晰的错误消息
   - 提供可能的解决方案
   - 避免暴露技术细节

## 测试策略

### 双重测试方法

本系统采用单元测试和基于属性的测试相结合的方法，以确保全面的测试覆盖：

- **单元测试**：验证特定示例、边界情况和错误条件
- **基于属性的测试**：验证所有输入的通用属性

两者是互补的，都是全面覆盖所必需的。

### 单元测试

单元测试专注于：
- **特定示例**：演示正确行为的具体案例
- **边界情况**：空输入、最大值、特殊字符等
- **错误条件**：无效输入、服务不可用、权限错误
- **集成点**：组件之间的交互

**测试覆盖领域：**

1. **图片上传模块**
   - 测试有效格式（JPEG、PNG、WebP）
   - 测试无效格式（GIF、BMP、TXT）
   - 测试边界大小（9.9MB、10MB、10.1MB）
   - 测试空文件和损坏文件

2. **人脸检测模块**
   - 测试包含单个人脸的图片
   - 测试包含多个人脸的图片
   - 测试不包含人脸的图片
   - 测试模糊或低质量图片

3. **文件系统扫描模块**
   - 测试空文件夹
   - 测试嵌套文件夹结构
   - 测试混合文件类型
   - 测试符号链接和权限问题

4. **相似度计算模块**
   - 测试相同特征向量（相似度=1）
   - 测试完全不同的向量（相似度≈0）
   - 测试已知相似度的测试向量

5. **图片转存模块**
   - 测试正常转存
   - 测试文件名冲突
   - 测试目标目录不存在
   - 测试磁盘空间不足

### 基于属性的测试

基于属性的测试通过在许多生成的输入上测试通用属性来验证软件正确性。每个属性都是一个应该对所有有效输入成立的形式化规范。

**配置：**
- 使用适合目标语言的属性测试库
- 每个属性测试最少运行100次迭代（由于随机化）
- 每个测试必须引用其设计文档属性
- 标签格式：**Feature: face-recognition-search, Property {number}: {property_text}**

**属性测试实现：**

1. **属性 1-2：输入验证**
   - 生成随机文件类型和大小
   - 验证接受/拒绝逻辑

2. **属性 3：上传往返**
   - 生成随机图片数据
   - 验证上传后可检索

3. **属性 4：检测结果完整性**
   - 对任何检测结果，验证数据结构完整性

4. **属性 6：递归扫描**
   - 生成随机文件夹结构
   - 验证所有图片被找到

5. **属性 8-9：搜索逻辑**
   - 生成随机特征向量和阈值
   - 验证匹配逻辑正确性

6. **属性 11：排序不变性**
   - 对任何搜索结果，验证降序排列

7. **属性 15-17：转存功能**
   - 生成随机文件列表
   - 验证转存完整性和统计准确性

8. **属性 19-20：数学属性**
   - 生成随机特征向量
   - 验证相似度计算的对称性和范围

### 集成测试

端到端流程测试：
1. 上传图片 → 检测人脸 → 选择人脸 → 搜索 → 查看结果 → 转存
2. 测试取消搜索功能
3. 测试缓存机制
4. 测试并发搜索任务

### 性能测试

虽然不是自动化单元测试的一部分，但应进行性能验证：
- 单张图片检测时间 < 2秒
- 1000张图片搜索的内存使用
- 并发处理的吞吐量
- UI响应性测试
