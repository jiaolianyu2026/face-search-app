# 需求文档 - 人像库管理功能

## 简介

本功能扩展现有的人脸识别搜索应用，添加多人像选择、人像库管理和历史人像功能。用户可以从上传的图片中选择多个人像，将人像保存到历史库中并为其命名，以及直接从历史库中选择人像进行搜索。

## 术语表

- **System**: 人脸识别搜索应用系统
- **Face_Library**: 人像库，存储历史检测到的人像特征和元数据的持久化存储
- **Source_Face**: 源人像，用户上传图片中检测到的人像
- **Library_Face**: 库人像，保存在人像库中的历史人像
- **Face_Feature**: 人像特征，128维特征向量
- **Thumbnail**: 缩略图，人像的小尺寸预览图片
- **Selection_State**: 选择状态，标识人像是否被用户选中
- **Face_Marker**: 人像标记，在图片上标识人像位置的可视化元素

## 需求

### 需求 1: 多人像可视化选择

**用户故事:** 作为用户，我希望能够在上传的图片中看到所有检测到的人像并选择其中的一个或多个，以便我可以精确控制搜索目标。

#### 验收标准

1. WHEN 系统检测到图片中的人像 THEN THE System SHALL 在每个人像位置绘制带有唯一颜色的圆形标记
2. WHEN 用户点击某个人像标记 THEN THE System SHALL 切换该人像的选择状态
3. WHEN 人像被选中 THEN THE System SHALL 显示明显的视觉反馈（边框加粗、高亮效果或颜色变化）
4. WHEN 人像未被选中 THEN THE System SHALL 显示正常的标记样式
5. THE System SHALL 支持同时选择多个人像
6. WHEN 用户选择人像后 THEN THE System SHALL 将选中的人像特征作为搜索输入

### 需求 2: 人像特征持久化存储

**用户故事:** 作为用户，我希望能够保存检测到的人像并为其命名，以便我可以在未来的搜索中重复使用这些人像而无需重新上传。

#### 验收标准

1. WHEN 用户选择保存人像 THEN THE System SHALL 将人像特征向量存储到 Face_Library
2. WHEN 保存人像 THEN THE System SHALL 生成并存储该人像的缩略图
3. WHEN 用户为人像提供名称 THEN THE System SHALL 将名称与人像关联存储
4. WHEN 保存人像 THEN THE System SHALL 记录创建时间戳
5. THE System SHALL 为每个保存的人像分配唯一标识符
6. WHEN 系统重启后 THEN THE System SHALL 能够从 Face_Library 加载所有历史人像
7. THE System SHALL 使用 SQLite 数据库作为 Face_Library 的存储后端

### 需求 3: 人像库管理界面

**用户故事:** 作为用户，我希望能够查看、编辑和删除历史保存的人像，以便我可以管理我的人像库。

#### 验收标准

1. THE System SHALL 提供人像库列表视图显示所有保存的人像
2. WHEN 显示人像库列表 THEN THE System SHALL 显示每个人像的缩略图、名称和创建时间
3. WHEN 用户选择编辑人像 THEN THE System SHALL 允许修改人像名称
4. WHEN 用户选择删除人像 THEN THE System SHALL 从 Face_Library 中移除该人像及其所有关联数据
5. WHEN 删除人像前 THEN THE System SHALL 请求用户确认删除操作
6. THE System SHALL 支持按名称搜索人像库中的人像
7. THE System SHALL 支持按创建时间排序人像列表

### 需求 4: 双模式搜索工作流

**用户故事:** 作为用户，我希望能够选择从新上传的图片或历史人像库中选择搜索目标，以便我可以灵活地进行人像搜索。

#### 验收标准

1. THE System SHALL 提供两种搜索模式：上传新图片模式和历史人像模式
2. WHEN 用户选择上传新图片模式 THEN THE System SHALL 显示图片上传界面
3. WHEN 用户选择历史人像模式 THEN THE System SHALL 显示人像库选择界面
4. WHEN 在上传新图片模式中检测到人像后 THEN THE System SHALL 提供选项将选中的人像保存到人像库
5. THE System SHALL 允许用户同时选择新上传图片中的人像和历史人像作为搜索输入
6. WHEN 用户在两种模式间切换 THEN THE System SHALL 保持当前已选择的人像状态
7. WHEN 用户开始搜索 THEN THE System SHALL 使用所有选中人像（来自新上传或历史库）的特征向量

### 需求 5: 缩略图生成

**用户故事:** 作为系统，我需要为保存的人像生成缩略图，以便在人像库界面中高效显示。

#### 验收标准

1. WHEN 保存人像到 Face_Library THEN THE System SHALL 从原始图片中裁剪人像区域
2. WHEN 裁剪人像区域 THEN THE System SHALL 使用人像边界框坐标并添加适当的边距
3. WHEN 生成缩略图 THEN THE System SHALL 将裁剪的图片缩放到固定尺寸（如 150x150 像素）
4. THE System SHALL 保持缩略图的宽高比
5. WHEN 缩略图尺寸不是正方形 THEN THE System SHALL 使用填充或居中裁剪
6. THE System SHALL 将缩略图编码为 JPEG 格式以优化存储空间
7. WHEN 缩略图生成失败 THEN THE System SHALL 记录错误并使用默认占位图

### 需求 6: API 扩展

**用户故事:** 作为前端开发者，我需要 REST API 端点来管理人像库，以便我可以构建用户界面。

#### 验收标准

1. THE System SHALL 提供 POST /api/library/faces 端点用于保存人像到库
2. THE System SHALL 提供 GET /api/library/faces 端点用于获取所有库人像列表
3. THE System SHALL 提供 GET /api/library/faces/{faceId} 端点用于获取单个库人像详情
4. THE System SHALL 提供 PUT /api/library/faces/{faceId} 端点用于更新库人像信息
5. THE System SHALL 提供 DELETE /api/library/faces/{faceId} 端点用于删除库人像
6. THE System SHALL 提供 GET /api/library/faces/{faceId}/thumbnail 端点用于获取缩略图
7. WHEN API 请求失败 THEN THE System SHALL 返回适当的 HTTP 状态码和错误消息
8. THE System SHALL 验证所有 API 输入参数

### 需求 7: 数据模型扩展

**用户故事:** 作为系统架构师，我需要定义清晰的数据模型来表示库人像，以便系统各模块可以一致地处理人像数据。

#### 验收标准

1. THE System SHALL 定义 LibraryFace 数据模型包含以下字段：id、name、feature_vector、thumbnail_path、created_at、source_image_id
2. THE System SHALL 定义 FaceSelection 数据模型表示用户选择的人像集合
3. THE System SHALL 验证 LibraryFace 的 name 字段非空且长度不超过 100 字符
4. THE System SHALL 验证 LibraryFace 的 feature_vector 为 128 维浮点数数组
5. THE System SHALL 确保 LibraryFace 的 id 字段为唯一的 UUID
6. THE System SHALL 将 created_at 存储为 ISO 8601 格式的时间戳
7. WHEN 创建 LibraryFace 实例时 THEN THE System SHALL 验证所有必需字段存在且格式正确

### 需求 8: 搜索功能集成

**用户故事:** 作为用户，我希望使用选中的多个人像（来自新上传或历史库）进行搜索，以便我可以找到包含任意一个目标人像的所有图片。

#### 验收标准

1. WHEN 用户开始搜索时选择了多个人像 THEN THE System SHALL 对每个选中人像执行独立搜索
2. WHEN 执行多人像搜索 THEN THE System SHALL 合并所有搜索结果
3. WHEN 合并搜索结果 THEN THE System SHALL 去除重复的匹配图片
4. WHEN 同一图片匹配多个搜索人像 THEN THE System SHALL 保留最高相似度分数
5. THE System SHALL 在搜索结果中标识每个匹配对应的源人像
6. WHEN 搜索进度更新 THEN THE System SHALL 显示所有人像的综合进度
7. THE System SHALL 支持取消多人像搜索操作

### 需求 9: 前端组件扩展

**用户故事:** 作为前端开发者，我需要新的 React 组件来实现人像选择和库管理功能，以便用户可以与新功能交互。

#### 验收标准

1. THE System SHALL 提供 FaceSelector 组件用于在图片上显示和选择人像
2. THE System SHALL 提供 FaceLibrary 组件用于显示和管理历史人像
3. THE System SHALL 提供 FaceLibraryItem 组件用于显示单个库人像
4. THE System SHALL 提供 SearchModeSelector 组件用于在上传和历史模式间切换
5. WHEN FaceSelector 渲染时 THEN THE System SHALL 在图片上叠加可点击的人像标记
6. WHEN FaceLibrary 渲染时 THEN THE System SHALL 以网格布局显示所有库人像
7. THE System SHALL 确保所有新组件遵循现有的设计系统和样式规范

### 需求 10: 数据库架构

**用户故事:** 作为数据库管理员，我需要定义人像库的数据库架构，以便系统可以高效存储和查询人像数据。

#### 验收标准

1. THE System SHALL 创建 library_faces 表包含列：id、name、feature_vector、thumbnail_path、created_at、source_image_id
2. THE System SHALL 在 library_faces 表的 id 列上设置主键约束
3. THE System SHALL 在 library_faces 表的 name 列上创建索引以优化搜索
4. THE System SHALL 在 library_faces 表的 created_at 列上创建索引以优化排序
5. THE System SHALL 将 feature_vector 存储为 BLOB 类型（序列化的 NumPy 数组）
6. THE System SHALL 在数据库初始化时自动创建表结构
7. WHEN 数据库架构版本更新 THEN THE System SHALL 提供迁移机制
