# 设计文档 - 人像库管理功能

## 概述

本设计扩展现有的人脸识别搜索应用，添加人像库管理功能。核心改进包括：

1. **多人像可视化选择**: 在前端图片上叠加可交互的人像标记，支持多选
2. **人像持久化存储**: 使用 SQLite 数据库存储人像特征、缩略图和元数据
3. **人像库管理**: 提供 CRUD 操作管理历史人像
4. **双模式搜索**: 支持从新上传图片或历史库中选择搜索目标
5. **多人像搜索**: 同时使用多个人像特征进行搜索并合并结果

该设计遵循现有系统架构，复用 `CacheModule` 的 SQLite 模式，并扩展 Flask API 和 React 前端。

## 架构

### 系统层次

```
┌─────────────────────────────────────────────────────────┐
│                    前端层 (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ FaceSelector │  │ FaceLibrary  │  │ SearchMode   │  │
│  │   Component  │  │   Component  │  │   Selector   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │ HTTP REST API
┌─────────────────────────────────────────────────────────┐
│                    API 层 (Flask)                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  新增端点:                                        │   │
│  │  POST   /api/library/faces                       │   │
│  │  GET    /api/library/faces                       │   │
│  │  GET    /api/library/faces/{faceId}              │   │
│  │  PUT    /api/library/faces/{faceId}              │   │
│  │  DELETE /api/library/faces/{faceId}              │   │
│  │  GET    /api/library/faces/{faceId}/thumbnail    │   │
│  │  POST   /api/search (扩展支持多人像)              │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                   业务逻辑层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ FaceLibrary  │  │  Thumbnail   │  │ MultiSearch  │  │
│  │   Module     │  │  Generator   │  │   Module     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                   数据持久层                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SQLite 数据库: face_library.db                  │   │
│  │  表: library_faces                               │   │
│  │  - id (TEXT PRIMARY KEY)                         │   │
│  │  - name (TEXT NOT NULL)                          │   │
│  │  - feature_vector (BLOB NOT NULL)                │   │
│  │  - thumbnail_path (TEXT NOT NULL)                │   │
│  │  - created_at (REAL NOT NULL)                    │   │
│  │  - source_image_id (TEXT)                        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 模块职责

- **FaceLibraryModule**: 管理人像库的 CRUD 操作，与 SQLite 数据库交互
- **ThumbnailGenerator**: 从原始图片裁剪人像区域并生成缩略图
- **MultiSearchModule**: 协调多个人像的搜索任务并合并结果
- **FaceSelector (前端)**: 在图片上显示人像标记并处理用户选择
- **FaceLibrary (前端)**: 显示人像库列表并提供管理操作

## 组件和接口

### 后端模块

#### FaceLibraryModule

```python
class FaceLibraryModule:
    """管理人像库的持久化存储和检索"""
    
    def __init__(self, db_path: str = "cache/face_library.db"):
        """初始化数据库连接"""
        
    def saveFace(self, name: str, features: List[float], 
                 thumbnail_path: str, source_image_id: Optional[str] = None) -> LibraryFace:
        """
        保存人像到库
        
        Args:
            name: 人像名称
            features: 128维特征向量
            thumbnail_path: 缩略图文件路径
            source_image_id: 源图片ID（可选）
            
        Returns:
            LibraryFace: 保存的人像对象
            
        Validates: Requirements 2.1, 2.2, 2.4, 2.5
        """
        
    def getFace(self, face_id: str) -> Optional[LibraryFace]:
        """
        获取单个人像
        
        Args:
            face_id: 人像唯一标识符
            
        Returns:
            LibraryFace 或 None
            
        Validates: Requirements 3.2
        """
        
    def getAllFaces(self, sort_by: str = "created_at", 
                    search_name: Optional[str] = None) -> List[LibraryFace]:
        """
        获取所有人像列表
        
        Args:
            sort_by: 排序字段 ("created_at" 或 "name")
            search_name: 按名称搜索（可选）
            
        Returns:
            LibraryFace 列表
            
        Validates: Requirements 3.1, 3.6, 3.7
        """
        
    def updateFace(self, face_id: str, name: str) -> bool:
        """
        更新人像名称
        
        Args:
            face_id: 人像唯一标识符
            name: 新名称
            
        Returns:
            是否更新成功
            
        Validates: Requirements 3.3
        """
        
    def deleteFace(self, face_id: str) -> bool:
        """
        删除人像及其关联数据
        
        Args:
            face_id: 人像唯一标识符
            
        Returns:
            是否删除成功
            
        Validates: Requirements 3.4
        """
```

#### ThumbnailGenerator

```python
class ThumbnailGenerator:
    """生成人像缩略图"""
    
    def __init__(self, thumbnail_dir: str = "cache/thumbnails", 
                 thumbnail_size: int = 150):
        """
        初始化缩略图生成器
        
        Args:
            thumbnail_dir: 缩略图存储目录
            thumbnail_size: 缩略图尺寸（正方形边长）
        """
        
    def generateThumbnail(self, image_path: str, bounding_box: dict, 
                         face_id: str) -> str:
        """
        生成人像缩略图
        
        Args:
            image_path: 原始图片路径
            bounding_box: 人像边界框 {x, y, width, height}
            face_id: 人像ID（用于生成文件名）
            
        Returns:
            缩略图文件路径
            
        Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
        """
```

#### MultiSearchModule

```python
class MultiSearchModule:
    """协调多人像搜索"""
    
    def __init__(self, face_searcher: FaceSearchModule):
        """
        初始化多人像搜索模块
        
        Args:
            face_searcher: 单人像搜索模块实例
        """
        
    def searchMultipleFaces(self, target_features_list: List[List[float]], 
                           search_folder: str, threshold: float = 0.6,
                           progress_callback: Optional[Callable] = None) -> MultiSearchResult:
        """
        使用多个人像特征进行搜索
        
        Args:
            target_features_list: 多个128维特征向量列表
            search_folder: 搜索文件夹路径
            threshold: 相似度阈值
            progress_callback: 进度回调函数
            
        Returns:
            MultiSearchResult: 合并后的搜索结果
            
        Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
        """
```

### API 端点

#### POST /api/library/faces

保存人像到库。

**请求体:**
```json
{
  "imageId": "uuid-of-uploaded-image",
  "faceId": "uuid-of-detected-face",
  "name": "张三"
}
```

**响应:**
```json
{
  "id": "uuid-of-library-face",
  "name": "张三",
  "thumbnailUrl": "/api/library/faces/{id}/thumbnail",
  "createdAt": 1234567890.123
}
```

**验证:** Requirements 6.1

#### GET /api/library/faces

获取所有库人像列表。

**查询参数:**
- `sortBy`: "created_at" 或 "name" (可选，默认 "created_at")
- `search`: 按名称搜索 (可选)

**响应:**
```json
{
  "faces": [
    {
      "id": "uuid",
      "name": "张三",
      "thumbnailUrl": "/api/library/faces/{id}/thumbnail",
      "createdAt": 1234567890.123
    }
  ]
}
```

**验证:** Requirements 6.2

#### GET /api/library/faces/{faceId}

获取单个库人像详情。

**响应:**
```json
{
  "id": "uuid",
  "name": "张三",
  "features": [0.1, 0.2, ...],  // 128维向量
  "thumbnailUrl": "/api/library/faces/{id}/thumbnail",
  "createdAt": 1234567890.123,
  "sourceImageId": "uuid-of-source-image"
}
```

**验证:** Requirements 6.3

#### PUT /api/library/faces/{faceId}

更新库人像信息。

**请求体:**
```json
{
  "name": "新名称"
}
```

**响应:**
```json
{
  "id": "uuid",
  "name": "新名称",
  "thumbnailUrl": "/api/library/faces/{id}/thumbnail",
  "createdAt": 1234567890.123
}
```

**验证:** Requirements 6.4

#### DELETE /api/library/faces/{faceId}

删除库人像。

**响应:**
```json
{
  "success": true,
  "message": "人像已删除"
}
```

**验证:** Requirements 6.5

#### GET /api/library/faces/{faceId}/thumbnail

获取缩略图图片文件。

**响应:** JPEG 图片文件

**验证:** Requirements 6.6

#### POST /api/search (扩展)

扩展现有搜索端点以支持多人像搜索。

**请求体 (新格式):**
```json
{
  "targetFaces": [
    {
      "type": "uploaded",
      "imageId": "uuid",
      "faceId": "uuid"
    },
    {
      "type": "library",
      "libraryFaceId": "uuid"
    }
  ],
  "searchFolder": "/path/to/folder",
  "threshold": 0.6
}
```

**响应:**
```json
{
  "taskId": "uuid",
  "status": "pending"
}
```

**验证:** Requirements 4.5, 4.7, 8.1

### 前端组件

#### FaceSelector

在图片上显示人像标记并处理选择。

**Props:**
```typescript
interface FaceSelectorProps {
  imageUrl: string;
  faces: Face[];
  selectedFaceIds: string[];
  onSelectionChange: (faceIds: string[]) => void;
}
```

**功能:**
- 在图片上叠加 SVG 圆形标记
- 每个人像使用唯一颜色
- 点击切换选择状态
- 选中时显示高亮效果

**验证:** Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 9.1, 9.5

#### FaceLibrary

显示人像库列表并提供管理操作。

**Props:**
```typescript
interface FaceLibraryProps {
  onSelectFaces: (faceIds: string[]) => void;
  selectedFaceIds: string[];
}
```

**功能:**
- 网格布局显示所有库人像
- 显示缩略图、名称、创建时间
- 支持编辑名称
- 支持删除（带确认）
- 支持按名称搜索
- 支持按时间排序

**验证:** Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 9.2, 9.6

#### SearchModeSelector

在上传模式和历史模式间切换。

**Props:**
```typescript
interface SearchModeSelectorProps {
  mode: 'upload' | 'library';
  onModeChange: (mode: 'upload' | 'library') => void;
}
```

**功能:**
- 切换按钮或标签页
- 保持选择状态

**验证:** Requirements 4.1, 4.2, 4.3, 4.6, 9.4

## 数据模型

### LibraryFace

```python
@dataclass
class LibraryFace:
    """
    表示保存在人像库中的人像
    
    Attributes:
        id: 唯一标识符 (UUID)
        name: 人像名称
        features: 128维特征向量
        thumbnailPath: 缩略图文件路径
        createdAt: 创建时间戳
        sourceImageId: 源图片ID（可选）
    """
    id: str
    name: str
    features: List[float]
    thumbnailPath: str
    createdAt: float
    sourceImageId: Optional[str] = None
    
    def __post_init__(self):
        """验证数据"""
        if len(self.features) != 128:
            raise ValueError(f"特征向量必须是128维，实际为 {len(self.features)}")
        if not self.name or len(self.name) > 100:
            raise ValueError("名称不能为空且长度不超过100字符")
        if not self.id:
            raise ValueError("ID不能为空")
```

**验证:** Requirements 7.1, 7.3, 7.4, 7.5, 7.6, 7.7

### FaceSelection

```python
@dataclass
class FaceSelection:
    """
    表示用户选择的人像集合
    
    Attributes:
        uploadedFaces: 从上传图片中选择的人像列表
        libraryFaces: 从人像库中选择的人像列表
    """
    uploadedFaces: List[dict] = field(default_factory=list)  # [{imageId, faceId}]
    libraryFaces: List[str] = field(default_factory=list)    # [libraryFaceId]
    
    def getAllFeatures(self, detection_cache: dict, 
                      library_module: 'FaceLibraryModule') -> List[List[float]]:
        """
        获取所有选中人像的特征向量
        
        Args:
            detection_cache: 检测结果缓存
            library_module: 人像库模块实例
            
        Returns:
            特征向量列表
        """
```

**验证:** Requirements 7.2, 4.5

### MultiSearchResult

```python
@dataclass
class MultiSearchResult:
    """
    多人像搜索结果
    
    Attributes:
        matches: 匹配结果列表（已去重）
        totalProcessed: 处理的图片总数
        cancelled: 是否被取消
        sourceFaceMap: 每个匹配对应的源人像ID映射
    """
    matches: List[Match] = field(default_factory=list)
    totalProcessed: int = 0
    cancelled: bool = False
    sourceFaceMap: Dict[str, str] = field(default_factory=dict)  # {imagePath: sourceFaceId}
```

**验证:** Requirements 8.2, 8.3, 8.4, 8.5

### 数据库架构

**表: library_faces**

```sql
CREATE TABLE library_faces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    feature_vector BLOB NOT NULL,
    thumbnail_path TEXT NOT NULL,
    created_at REAL NOT NULL,
    source_image_id TEXT
);

CREATE INDEX idx_name ON library_faces(name);
CREATE INDEX idx_created_at ON library_faces(created_at);
```

**验证:** Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6

## 正确性属性


*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: 人像标记唯一性

*对于任意* 检测到的人像列表，渲染的标记应该为每个人像分配唯一的颜色标识符，且标记数量应该等于人像数量。

**验证需求:** Requirements 1.1

### 属性 2: 选择状态切换

*对于任意* 人像ID和当前选择状态集合，点击该人像应该切换其选择状态（选中变为未选中，未选中变为选中）。

**验证需求:** Requirements 1.2

### 属性 3: 多选支持

*对于任意* 人像ID列表，系统应该能够同时维护所有人像的选择状态，且选择集合的大小应该等于选中的人像数量。

**验证需求:** Requirements 1.5

### 属性 4: 选择到特征映射

*对于任意* 选中的人像集合，提取的特征向量列表应该与选中人像一一对应，且每个特征向量应该是128维。

**验证需求:** Requirements 1.6

### 属性 5: 人像保存 Round-Trip

*对于任意* 有效的人像数据（名称、特征向量、缩略图），保存到人像库后立即查询应该返回包含相同数据的 LibraryFace 对象。

**验证需求:** Requirements 2.1, 2.3

### 属性 6: 缩略图文件存在性

*对于任意* 保存的人像，其缩略图文件路径应该指向一个存在且可读的文件。

**验证需求:** Requirements 2.2

### 属性 7: 创建时间戳有效性

*对于任意* 保存的人像，其创建时间戳应该在保存操作开始时间和结束时间之间。

**验证需求:** Requirements 2.4

### 属性 8: ID 唯一性

*对于任意* 保存的多个人像，所有人像的 ID 应该互不相同。

**验证需求:** Requirements 2.5

### 属性 9: 持久化验证

*对于任意* 保存的人像集合，关闭并重新打开数据库连接后，查询应该返回相同数量的人像且数据一致。

**验证需求:** Requirements 2.6

### 属性 10: 列表查询完整性

*对于任意* 保存的 N 个人像，查询列表应该返回 N 个人像，且每个人像应该包含非空的缩略图路径、名称和创建时间。

**验证需求:** Requirements 3.1, 3.2

### 属性 11: 名称更新 Round-Trip

*对于任意* 已保存的人像和新名称，更新名称后查询应该返回新名称。

**验证需求:** Requirements 3.3

### 属性 12: 删除操作有效性

*对于任意* 已保存的人像，删除后查询该人像应该返回 None 或空结果。

**验证需求:** Requirements 3.4

### 属性 13: 名称搜索过滤

*对于任意* 包含特定名称子串的人像集合，按名称搜索应该只返回名称包含该子串的人像。

**验证需求:** Requirements 3.6

### 属性 14: 时间排序正确性

*对于任意* 人像列表，按创建时间排序后，列表应该按时间戳单调递增或递减排列。

**验证需求:** Requirements 3.7

### 属性 15: 混合选择合并

*对于任意* 上传人像集合和历史人像集合，合并后的特征向量列表应该包含两个集合的所有特征向量。

**验证需求:** Requirements 4.5

### 属性 16: 搜索输入一致性

*对于任意* 选中的人像集合，传递给搜索函数的特征向量列表长度应该等于选中人像的数量。

**验证需求:** Requirements 4.7

### 属性 17: 裁剪区域计算

*对于任意* 边界框和边距参数，裁剪后的图像区域应该大于原始边界框（因为添加了边距）。

**验证需求:** Requirements 5.1, 5.2

### 属性 18: 缩略图尺寸固定

*对于任意* 输入图像和边界框，生成的缩略图的最大边长应该等于指定的固定尺寸。

**验证需求:** Requirements 5.3

### 属性 19: 缩略图格式验证

*对于任意* 生成的缩略图文件，文件应该是有效的 JPEG 格式且可以被图像库正确读取。

**验证需求:** Requirements 5.6

### 属性 20: 缩略图生成错误处理

*对于任意* 无效的输入图像或边界框，缩略图生成应该返回错误或默认占位图路径，而不是崩溃。

**验证需求:** Requirements 5.7

### 属性 21: API 输入验证

*对于任意* 缺失必需参数或参数类型错误的 API 请求，系统应该返回 400 状态码和描述性错误消息。

**验证需求:** Requirements 6.7, 6.8

### 属性 22: 名称字段验证

*对于任意* 空字符串或长度超过 100 字符的名称，创建 LibraryFace 应该抛出 ValueError 异常。

**验证需求:** Requirements 7.3

### 属性 23: 特征向量维度验证

*对于任意* 非 128 维的特征向量，创建 LibraryFace 应该抛出 ValueError 异常。

**验证需求:** Requirements 7.4

### 属性 24: UUID 格式验证

*对于任意* 生成的人像 ID，ID 应该符合标准 UUID 格式（8-4-4-4-12 十六进制字符）。

**验证需求:** Requirements 7.5

### 属性 25: 多人像搜索结果合并

*对于任意* N 个人像的搜索，合并后的结果中每个图片路径应该只出现一次（去重）。

**验证需求:** Requirements 8.2, 8.3

### 属性 26: 最高相似度保留

*对于任意* 同一图片匹配多个源人像的情况，最终结果中该图片的相似度分数应该是所有匹配中的最高值。

**验证需求:** Requirements 8.4

### 属性 27: 源人像标识

*对于任意* 搜索结果中的匹配，应该存在对应的源人像 ID 标识该匹配来自哪个搜索人像。

**验证需求:** Requirements 8.5

### 属性 28: 多人像搜索取消

*对于任意* 正在运行的多人像搜索任务，调用取消操作后，任务状态应该变为 'cancelled' 且停止处理新图片。

**验证需求:** Requirements 8.7

### 属性 29: 主键唯一性约束

*对于任意* 两个具有相同 ID 的人像，尝试插入第二个应该失败并抛出数据库约束错误。

**验证需求:** Requirements 10.2

## 错误处理

### 数据验证错误

- **无效名称**: 空字符串或超过 100 字符 → 抛出 `ValueError`
- **无效特征向量**: 非 128 维 → 抛出 `ValueError`
- **无效 ID**: 非 UUID 格式 → 抛出 `ValueError`

### 数据库错误

- **连接失败**: 无法连接到 SQLite 数据库 → 记录错误并返回 `ServiceError`
- **主键冲突**: 插入重复 ID → 抛出 `sqlite3.IntegrityError`
- **查询失败**: SQL 执行错误 → 记录错误并返回空结果或 None

### 文件系统错误

- **缩略图生成失败**: 无效图像或 I/O 错误 → 记录错误并返回默认占位图路径
- **缩略图文件不存在**: 查询不存在的缩略图 → 返回 404 错误
- **缩略图目录不可写**: 无法创建缩略图目录 → 抛出 `ServiceError`

### API 错误

- **缺失参数**: 必需参数未提供 → 返回 400 和 `ValidationError`
- **无效参数类型**: 参数类型不匹配 → 返回 400 和 `ValidationError`
- **人像不存在**: 查询不存在的人像 ID → 返回 404 和 `NotFoundError`
- **数据库操作失败**: 内部错误 → 返回 500 和 `ServiceError`

### 搜索错误

- **无效特征向量**: 空列表或维度错误 → 返回 400 和 `ValidationError`
- **搜索文件夹不存在**: 指定的搜索路径无效 → 返回 400 和 `ValidationError`
- **搜索超时**: 长时间运行的搜索 → 支持取消操作

## 测试策略

### 双重测试方法

本功能采用单元测试和基于属性的测试相结合的方法：

- **单元测试**: 验证特定示例、边缘情况和错误条件
- **属性测试**: 验证跨所有输入的通用属性
- 两者互补，共同提供全面覆盖

### 单元测试重点

单元测试应该专注于：
- API 端点的具体示例（6 个端点的基本功能）
- 数据库架构验证（表结构、索引、约束）
- 缩略图生成的边缘情况（空图像、超大图像、非正方形）
- 错误处理的具体场景（无效输入、文件不存在）
- 组件集成点（前端与 API 的交互）

避免编写过多的单元测试——基于属性的测试已经处理了大量输入覆盖。

### 基于属性的测试配置

- **测试库**: Hypothesis (Python)
- **最小迭代次数**: 每个属性测试 100 次
- **标签格式**: `# Feature: face-library-management, Property {N}: {property_text}`
- **每个正确性属性必须由单个属性测试实现**

### 测试模块组织

```
tests/
├── test_face_library.py              # 单元测试：CRUD 操作
├── test_face_library_properties.py   # 属性测试：属性 5-14, 22-24, 29
├── test_thumbnail.py                 # 单元测试：缩略图生成示例
├── test_thumbnail_properties.py      # 属性测试：属性 17-20
├── test_multi_search.py              # 单元测试：多人像搜索示例
├── test_multi_search_properties.py   # 属性测试：属性 25-28
├── test_library_api.py               # 单元测试：API 端点示例
├── test_library_api_properties.py    # 属性测试：属性 21
├── test_face_selection.py            # 单元测试：前端选择逻辑
└── test_face_selection_properties.py # 属性测试：属性 1-4, 15-16
```

### 属性测试示例

```python
# Feature: face-library-management, Property 5: 人像保存 Round-Trip
@given(
    name=st.text(min_size=1, max_size=100),
    features=st.lists(st.floats(allow_nan=False), min_size=128, max_size=128)
)
def test_property_5_save_face_roundtrip(name, features):
    """对于任意有效的人像数据，保存后查询应该返回相同数据"""
    library = FaceLibraryModule()
    
    # 生成缩略图路径（模拟）
    thumbnail_path = f"cache/thumbnails/{uuid.uuid4()}.jpg"
    
    # 保存人像
    saved_face = library.saveFace(name, features, thumbnail_path)
    
    # 查询人像
    retrieved_face = library.getFace(saved_face.id)
    
    # 验证数据一致
    assert retrieved_face is not None
    assert retrieved_face.name == name
    assert retrieved_face.features == features
    assert retrieved_face.thumbnailPath == thumbnail_path
```

### 集成测试

集成测试应该验证端到端工作流：

1. **上传并保存工作流**: 上传图片 → 检测人像 → 选择人像 → 保存到库 → 验证库中存在
2. **历史搜索工作流**: 从库中选择人像 → 开始搜索 → 验证搜索使用正确特征
3. **混合搜索工作流**: 选择上传人像和库人像 → 开始搜索 → 验证结果合并正确
4. **库管理工作流**: 保存人像 → 编辑名称 → 删除人像 → 验证操作成功

### 前端测试

前端组件测试应该使用 React Testing Library：

- **FaceSelector**: 渲染测试、点击交互、多选状态
- **FaceLibrary**: 列表渲染、搜索过滤、排序、编辑/删除操作
- **SearchModeSelector**: 模式切换、状态保持

### 性能测试

- **大量人像**: 测试库中有 1000+ 人像时的查询性能
- **大图片缩略图**: 测试生成超大图片的缩略图时的内存使用
- **多人像搜索**: 测试同时搜索 10+ 人像时的性能和进度更新

### 测试数据生成

使用 Hypothesis 策略生成测试数据：

```python
# 有效的人像名称
valid_names = st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',)))

# 128 维特征向量
feature_vectors = st.lists(
    st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    min_size=128,
    max_size=128
)

# 边界框
bounding_boxes = st.builds(
    dict,
    x=st.integers(min_value=0, max_value=1000),
    y=st.integers(min_value=0, max_value=1000),
    width=st.integers(min_value=10, max_value=500),
    height=st.integers(min_value=10, max_value=500)
)

# UUID
uuids = st.uuids().map(str)
```
