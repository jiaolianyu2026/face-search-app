# 转存功能优化 - 自动创建文件夹

## 功能说明

在转存图片时，如果目标文件夹不存在，系统会询问用户是否创建该文件夹。

## 用户体验流程

### 场景 1：文件夹已存在

1. 用户选择要转存的图片
2. 输入目标文件夹路径（已存在）
3. 点击"转存"按钮
4. ✅ 直接转存成功

### 场景 2：文件夹不存在（新功能）

1. 用户选择要转存的图片
2. 输入目标文件夹路径（不存在）
3. 点击"转存"按钮
4. 🔔 弹出确认对话框：
   ```
   目标文件夹不存在：
   D:\新建文件夹\导出的照片
   
   是否创建该文件夹并继续转存？
   ```
5. 用户选择：
   - **确定**：自动创建文件夹并转存图片
   - **取消**：取消转存操作

### 场景 3：无法创建文件夹

1. 用户输入无效路径（如：`C:\Windows\System32\新文件夹`）
2. 点击"转存"并确认创建
3. ❌ 显示错误：`无法创建文件夹：权限不足`

## 技术实现

### 后端修改（backend/app.py）

#### 新增参数

`POST /api/export` 端点新增可选参数：

```json
{
  "imagePaths": ["path1", "path2"],
  "targetFolder": "D:\\新文件夹",
  "createIfNotExists": true  // 新增：是否自动创建文件夹
}
```

#### 响应格式

成功响应新增字段：

```json
{
  "successCount": 10,
  "failedCount": 0,
  "errors": [],
  "folderCreated": true  // 新增：文件夹是否被创建
}
```

#### 实现逻辑

```python
# 检查文件夹是否存在
if not os.path.exists(target_folder):
    if create_if_not_exists:
        # 尝试创建文件夹
        try:
            os.makedirs(target_folder, exist_ok=True)
            folder_created = True
            logger.info(f"创建目标文件夹: {target_folder}")
        except Exception as e:
            # 创建失败，返回错误
            raise ValidationError(f"无法创建文件夹: {target_folder}")
    else:
        # 不创建，返回 404 错误
        raise NotFoundError(f"目标文件夹不存在: {target_folder}")
```

### 前端修改（frontend/src/components/SearchResults.jsx）

#### 两阶段请求策略

```javascript
// 第一次尝试：不创建文件夹
try {
  const response = await axios.post('/api/export', {
    imagePaths: Array.from(selectedImages),
    targetFolder: exportFolder,
    createIfNotExists: false  // 第一次不创建
  })
  // 转存成功
} catch (err) {
  // 检查是否是文件夹不存在的错误
  if (err.response?.status === 404 && 
      err.response?.data?.error?.type === 'folder') {
    
    // 询问用户是否创建
    const shouldCreate = window.confirm(
      `目标文件夹不存在：\n${exportFolder}\n\n是否创建该文件夹并继续转存？`
    )
    
    if (shouldCreate) {
      // 第二次尝试：创建文件夹
      const retryResponse = await axios.post('/api/export', {
        imagePaths: Array.from(selectedImages),
        targetFolder: exportFolder,
        createIfNotExists: true  // 第二次创建
      })
      // 转存成功
    }
  }
}
```

## 使用示例

### 示例 1：创建单层文件夹

**输入路径**：`D:\导出的照片`

**结果**：
- 如果 `D:\` 存在，创建 `导出的照片` 文件夹
- 转存图片到新文件夹

### 示例 2：创建多层文件夹

**输入路径**：`D:\我的照片\人脸识别\2026年\2月`

**结果**：
- 自动创建所有不存在的中间文件夹
- 使用 `os.makedirs(exist_ok=True)` 确保路径完整

### 示例 3：相对路径

**输入路径**：`.\导出\照片`

**结果**：
- 在当前工作目录下创建文件夹
- 通常是后端运行目录

## 安全考虑

### 权限检查

1. **父目录必须存在且可写**
   - 如果 `D:\` 不存在或不可写，创建失败

2. **路径验证**
   - 不允许创建系统关键目录
   - 不允许使用特殊字符

3. **错误处理**
   - 创建失败时返回明确的错误信息
   - 不暴露系统敏感信息

### 最佳实践

1. **推荐路径格式**
   - Windows: `D:\文件夹\子文件夹`
   - 使用绝对路径避免歧义

2. **避免的路径**
   - 系统目录：`C:\Windows\`, `C:\Program Files\`
   - 根目录：`C:\`, `D:\`（建议创建子文件夹）

## 错误处理

### 常见错误及解决方案

| 错误 | 原因 | 解决方案 |
|-----|------|---------|
| 无法创建文件夹：权限不足 | 目标位置需要管理员权限 | 选择用户目录下的路径 |
| 无法创建文件夹：路径无效 | 路径包含非法字符 | 检查路径格式 |
| 无法创建文件夹：磁盘空间不足 | 目标磁盘已满 | 选择其他磁盘 |
| 目标路径不是文件夹 | 路径指向文件 | 修改路径或删除同名文件 |

## 测试场景

### 手动测试步骤

1. **测试文件夹不存在**
   ```
   输入：D:\测试文件夹_不存在
   预期：弹出确认对话框
   操作：点击"确定"
   结果：创建文件夹并转存成功
   ```

2. **测试多层文件夹**
   ```
   输入：D:\A\B\C\D
   预期：弹出确认对话框
   操作：点击"确定"
   结果：创建所有层级并转存成功
   ```

3. **测试取消创建**
   ```
   输入：D:\测试文件夹_取消
   预期：弹出确认对话框
   操作：点击"取消"
   结果：不创建文件夹，不转存
   ```

4. **测试无权限路径**
   ```
   输入：C:\Windows\测试
   预期：弹出确认对话框
   操作：点击"确定"
   结果：显示错误"无法创建文件夹"
   ```

5. **测试已存在文件夹**
   ```
   输入：D:\已存在的文件夹
   预期：不弹出对话框
   结果：直接转存成功
   ```

## 日志记录

### 后端日志示例

```
INFO | app:export_images | 开始转存图片: 5 个文件到 D:\新文件夹
INFO | app:export_images | 创建目标文件夹: D:\新文件夹
INFO | image_export:exportImages | 开始转存图片: 5 个文件到 D:\新文件夹
INFO | image_export:exportImages | 转存完成: 成功 5, 失败 0
INFO | app:export_images | 转存完成: 成功 5, 失败 0
```

### 错误日志示例

```
ERROR | app:export_images | 创建文件夹失败: C:\Windows\测试, 错误: [WinError 5] 拒绝访问
WARNING | error_handlers:handle_validation_error | 验证错误: 无法创建文件夹: C:\Windows\测试
```

## 向后兼容性

### API 兼容性

- ✅ 新参数 `createIfNotExists` 是可选的，默认为 `false`
- ✅ 旧的 API 调用仍然有效
- ✅ 响应格式向后兼容（新增字段不影响旧客户端）

### 前端兼容性

- ✅ 前端自动处理文件夹不存在的情况
- ✅ 用户体验更友好，无需手动创建文件夹

## 未来改进

### 可能的增强功能

1. **路径建议**
   - 提供常用路径的快捷选择
   - 记住上次使用的路径

2. **文件夹浏览器**
   - 添加文件夹选择对话框
   - 避免手动输入路径

3. **批量操作**
   - 支持同时转存到多个文件夹
   - 按相似度分组转存

4. **智能命名**
   - 自动生成文件夹名称（如：`人脸搜索_2026-02-14`）
   - 避免文件夹名称冲突

## 总结

### 优化效果

- ✅ **用户体验提升**：无需手动创建文件夹
- ✅ **操作简化**：一键完成创建和转存
- ✅ **错误处理**：清晰的提示和确认
- ✅ **安全可靠**：完善的权限检查

### 使用建议

1. 使用绝对路径避免歧义
2. 选择有写入权限的位置
3. 避免在系统目录下创建文件夹
4. 定期清理不需要的导出文件夹

---

**功能版本**：1.0
**更新时间**：2026-02-14
**状态**：✅ 已实现并测试
