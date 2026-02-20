# 发布说明 - Release Notes

## 版本 1.0.0 (2026-02-14)

### 🎉 首次发布

这是人脸识别搜索应用的首个正式版本，提供完整的人脸检测和搜索功能。

---

## ✨ 新功能

### 核心功能

1. **图片上传**
   - 支持拖拽上传
   - 支持点击选择文件
   - 支持格式：JPEG, PNG, WebP
   - 最大文件大小：10MB
   - 实时预览上传的图片

2. **人脸检测**
   - 基于 dlib 深度学习模型
   - 自动检测图片中的所有人脸
   - 提取 128 维人脸特征向量
   - 显示人脸边界框
   - 支持多人脸检测

3. **人脸搜索**
   - 在指定文件夹中搜索匹配的人脸
   - 可调节相似度阈值（默认 0.6）
   - 实时显示搜索进度
   - 支持大量图片搜索（1000+ 张）
   - 按相似度排序显示结果

4. **结果导出**
   - 一键导出匹配的图片
   - 自动创建目标文件夹
   - 保留原始文件名
   - 支持批量导出

5. **性能优化**
   - SQLite 数据库缓存人脸特征
   - 避免重复检测
   - 多线程处理
   - 批量处理优化

### 用户界面

- 现代化的 React 界面
- 响应式设计
- 实时进度显示
- 友好的错误提示
- 直观的操作流程

### 技术特性

- RESTful API 设计
- 前后端分离架构
- 完整的错误处理
- 详细的日志记录
- 单元测试和属性测试覆盖

---

## 🔧 技术栈

### 后端
- Python 3.14+
- Flask 3.0+
- face_recognition 1.3.0+
- dlib-bin 19.7.0+
- OpenCV 4.8.0+
- NumPy 1.26.0+
- Pillow 10.0.0+

### 前端
- React 18.2.0
- Vite 5.0.8
- Axios 1.6.2
- React Dropzone 14.2.3

### 测试
- pytest 9.0.0+
- hypothesis 6.0.0+

---

## 📦 部署方式

### 独立部署包

提供完整的 Windows 部署包，包含：
- 自动安装脚本
- 启动/停止脚本
- 详细的安装手册
- 使用指南
- 配置示例

### 系统要求

- Windows 10/11 (64位)
- Python 3.10+
- Node.js 16+
- 8GB RAM（推荐）
- 2GB 磁盘空间

---

## 🐛 已知问题

### 限制

1. **平台支持**
   - 当前仅支持 Windows 平台
   - macOS 和 Linux 支持计划在未来版本中添加

2. **性能**
   - 大图片（> 5MB）检测时间较长（5-10 秒）
   - 搜索大量图片（> 5000 张）可能需要较长时间

3. **功能**
   - 不支持视频文件
   - 不支持批量上传
   - 不支持历史记录

### 已知 Bug

目前没有已知的严重 Bug。

---

## 🔄 升级说明

这是首次发布，无需升级。

---

## 📚 文档

### 包含的文档

- `README.md` - 项目概述
- `INSTALLATION.md` - 详细安装指南
- `USAGE_GUIDE.md` - 使用指南
- `backend/API_DOCUMENTATION.md` - API 文档
- `DEPLOYMENT_CHECKLIST.md` - 部署清单
- `RELEASE_NOTES.md` - 本文档

### 在线文档

（如果有在线文档，在此添加链接）

---

## 🎯 路线图

### 计划中的功能（v1.1.0）

- [ ] 批量上传支持
- [ ] 搜索历史记录
- [ ] 结果导出为 Excel
- [ ] 相似度可视化
- [ ] 性能优化（GPU 加速）

### 计划中的功能（v1.2.0）

- [ ] 视频文件支持
- [ ] 实时摄像头检测
- [ ] 人脸聚类功能
- [ ] 数据库管理界面
- [ ] 多语言支持

### 计划中的功能（v2.0.0）

- [ ] macOS 和 Linux 支持
- [ ] Web 服务部署
- [ ] 用户认证系统
- [ ] 云存储集成
- [ ] 移动端应用

---

## 🙏 致谢

### 开源项目

感谢以下开源项目：
- [dlib](http://dlib.net/) - 人脸检测和特征提取
- [face_recognition](https://github.com/ageitgey/face_recognition) - 人脸识别库
- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [React](https://react.dev/) - 前端框架
- [Vite](https://vitejs.dev/) - 构建工具

### 贡献者

- 项目负责人：[Name]
- 后端开发：[Name]
- 前端开发：[Name]
- 测试：[Name]
- 文档：[Name]

---

## 📞 支持

### 获取帮助

- 查看文档：`INSTALLATION.md` 和 `USAGE_GUIDE.md`
- 查看常见问题：`INSTALLATION.md` 的"常见问题"章节
- 提交问题：[GitHub Issues 链接]
- 技术支持：[support@example.com]

### 反馈

我们欢迎您的反馈和建议：
- 功能请求：[GitHub Issues 链接]
- Bug 报告：[GitHub Issues 链接]
- 一般反馈：[feedback@example.com]

---

## 📄 许可证

MIT License

Copyright (c) 2026 Face Recognition Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 📝 变更日志

### [1.0.0] - 2026-02-14

#### 新增
- 图片上传功能
- 人脸检测功能
- 人脸搜索功能
- 结果导出功能
- 特征缓存功能
- 完整的 Web 界面
- 自动化部署脚本
- 详细的文档

#### 修复
- 无（首次发布）

#### 变更
- 无（首次发布）

#### 移除
- 无（首次发布）

---

**发布日期**：2026-02-14  
**版本号**：1.0.0  
**构建类型**：生产版本  
**支持平台**：Windows 10/11 (64位)
