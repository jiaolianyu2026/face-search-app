# 测试说明

## 问题修复总结

已完成以下修复，解决后端崩溃问题：

### ✅ 修复内容

1. **禁用 React StrictMode**（防止重复请求）
2. **添加重复调用保护**（确保 API 只调用一次）
3. **关闭 Flask Debug 模式**（提高稳定性）
4. **增强错误处理和日志**（便于问题追踪）

### 📋 测试步骤

#### 1. 刷新前端页面
打开浏览器，访问 http://localhost:3000，按 `Ctrl+F5` 强制刷新（清除缓存）

#### 2. 上传测试图片
- 点击"选择图片"或拖拽上传
- 使用测试图片：`D:\AI_workspace\忆颜图谱\微信图片_20260214100654_81_2.jpg`
- 点击"开始检测"

#### 3. 观察结果
**预期行为**：
- ✓ 上传成功
- ✓ 显示"正在分析图片中的人脸..."（约 3-5 秒）
- ✓ 显示"检测到 1 个人脸"
- ✓ 在图片上显示绿色边界框
- ✓ 可以点击"确认选择"继续

**如果失败**：
- 查看浏览器控制台（F12）的错误信息
- 查看后端日志：`backend\app.log`

#### 4. 监控后端日志（可选）
打开新的 PowerShell 窗口：
```powershell
cd D:\AI_workspace\face-search-app
Get-Content backend\app.log -Tail 20 -Wait
```

### 🔍 预期日志输出

上传成功后，应该看到：
```
INFO | app:upload_image | 图片上传成功: <imageId>, 文件名: 微信图片_20260214100654_81_2.jpg
INFO | app:detect_faces | 开始检测人脸: <imageId>, 文件大小: 1872.70 KB
DEBUG | face_detection:detectFaces | 开始检测人脸: <path>
DEBUG | face_detection:detectFaces | 图片文件大小: 1872.70 KB
DEBUG | face_detection:detectFaces | 加载图片...
DEBUG | face_detection:detectFaces | 图片加载成功，尺寸: (1808, 4096, 3)
DEBUG | face_detection:detectFaces | 开始检测人脸位置...
DEBUG | face_detection:detectFaces | 人脸位置检测完成，找到 1 个人脸
DEBUG | face_detection:detectFaces | 开始提取人脸特征...
DEBUG | face_detection:detectFaces | 人脸特征提取完成，特征数量: 1
INFO | face_detection:detectFaces | 人脸检测完成: <path>, 检测到 1 个人脸
INFO | app:detect_faces | 人脸检测成功: <imageId>, 检测到 1 个人脸
```

### ⚠️ 注意事项

1. **首次检测较慢**：大图片（4096x1808）需要 3-5 秒处理时间，这是正常的
2. **不要重复点击**：检测过程中请耐心等待，不要重复点击按钮
3. **浏览器缓存**：如果修改了前端代码，务必强制刷新（Ctrl+F5）

### 🐛 如果仍然崩溃

如果后端仍然崩溃，请执行以下操作：

1. **收集信息**：
   - 截图浏览器错误信息
   - 复制 `backend\app.log` 的最后 50 行
   - 记录崩溃时的操作步骤

2. **重启后端**：
   ```powershell
   # 停止后端（如果还在运行）
   # 在后端进程窗口按 Ctrl+C
   
   # 重新启动
   cd backend
   .\venv_new\Scripts\python.exe app.py
   ```

3. **尝试小图片**：
   - 使用较小的测试图片（< 500KB）
   - 如果小图片成功，说明是大图片处理的问题

### 📊 性能参考

| 图片尺寸 | 文件大小 | 预期检测时间 |
|---------|---------|------------|
| 800x600 | < 200KB | 1-2 秒 |
| 1920x1080 | < 500KB | 2-3 秒 |
| 4096x1808 | 1.8MB | 3-5 秒 |

### ✅ 成功标志

测试成功的标志：
- ✓ 前端显示检测结果
- ✓ 后端日志完整（从上传到检测完成）
- ✓ 后端进程保持运行
- ✓ 可以继续进行搜索操作

---

**准备就绪！** 现在可以在浏览器中测试了。
