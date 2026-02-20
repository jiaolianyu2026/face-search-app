# 人脸识别搜索应用 - 前端

这是人脸识别搜索应用的前端部分，使用 React + Vite 构建。

## 🚀 快速开始

### 1. 安装依赖

**重要：请先关闭当前终端，重新打开一个新的终端窗口**，然后运行：

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

前端服务将运行在 http://localhost:3000

### 3. 启动后端服务

在另一个终端窗口中：

```bash
cd backend
venv\Scripts\activate
python app.py
```

后端服务将运行在 http://localhost:5000

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/          # React 组件
│   │   ├── ImageUpload.jsx      # 图片上传组件
│   │   ├── FaceDetection.jsx    # 人脸检测组件
│   │   ├── FolderSelection.jsx  # 文件夹选择组件
│   │   ├── SearchProgress.jsx   # 搜索进度组件
│   │   └── SearchResults.jsx    # 搜索结果组件
│   ├── App.jsx              # 主应用组件
│   ├── main.jsx             # 应用入口
│   └── index.css            # 全局样式
├── index.html               # HTML 模板
├── vite.config.js           # Vite 配置
└── package.json             # 项目依赖
```

## 🎨 功能特性

### 1. 图片上传 (ImageUpload)
- ✅ 拖拽上传支持
- ✅ 文件格式验证（JPEG、PNG、WebP）
- ✅ 文件大小验证（最大 10MB）
- ✅ 实时上传进度显示
- ✅ 错误提示

### 2. 人脸检测 (FaceDetection)
- ✅ 自动检测图片中的人脸
- ✅ 在图片上绘制人脸边界框
- ✅ 多人脸选择支持
- ✅ 单人脸自动选中

### 3. 文件夹选择 (FolderSelection)
- ✅ 文件夹路径输入
- ✅ 相似度阈值调整（滑块控制）
- ✅ 路径验证
- ✅ 友好的提示信息

### 4. 搜索进度 (SearchProgress)
- ✅ 实时进度条显示
- ✅ 当前处理文件显示
- ✅ 进度百分比显示
- ✅ 取消搜索功能
- ✅ 自动轮询更新（每 500ms）

### 5. 搜索结果 (SearchResults)
- ✅ 网格布局展示结果
- ✅ 相似度排序（从高到低）
- ✅ 图片选择（复选框）
- ✅ 全选/取消全选
- ✅ 图片转存功能
- ✅ 点击查看大图
- ✅ 转存结果反馈

## 🔧 技术栈

- **React 18** - UI 框架
- **Vite 5** - 构建工具
- **Axios** - HTTP 客户端
- **React Dropzone** - 文件上传组件

## 📡 API 集成

前端通过 Vite 代理与后端 API 通信：

- `POST /api/upload` - 上传图片
- `POST /api/detect` - 检测人脸
- `POST /api/search` - 开始搜索
- `GET /api/search/{taskId}` - 获取搜索进度
- `POST /api/search/{taskId}/cancel` - 取消搜索
- `POST /api/export` - 转存图片

## 🎯 使用流程

1. **上传图片** - 拖拽或选择包含人脸的图片
2. **检测人脸** - 系统自动检测并标记人脸
3. **选择人脸** - 如果有多个人脸，选择要搜索的人脸
4. **选择文件夹** - 输入要搜索的文件夹路径
5. **调整阈值** - 设置相似度阈值（默认 0.6）
6. **开始搜索** - 系统在文件夹中搜索相似人脸
7. **查看结果** - 浏览匹配的图片，按相似度排序
8. **转存图片** - 选择图片并转存到指定文件夹

## 🐛 故障排查

### 问题：npm 命令不可用

**解决方案**：
1. 确认 Node.js 已正确安装
2. **关闭当前终端**
3. **重新打开一个新的终端窗口**
4. 运行 `node --version` 验证安装

### 问题：无法连接到后端

**解决方案**：
1. 确认后端服务正在运行（http://localhost:5000）
2. 检查 `vite.config.js` 中的代理配置
3. 查看浏览器控制台的网络请求

### 问题：图片上传失败

**解决方案**：
1. 检查文件格式（只支持 JPEG、PNG、WebP）
2. 检查文件大小（最大 10MB）
3. 确认后端 `temp_uploads` 目录存在且可写

## 📝 开发说明

### 添加新组件

1. 在 `src/components/` 目录创建新组件文件
2. 创建对应的 CSS 文件
3. 在 `App.jsx` 中导入并使用

### 修改样式

- 全局样式：编辑 `src/index.css`
- 组件样式：编辑对应的 `.css` 文件
- 应用样式：编辑 `src/App.css`

### 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

## 🔗 相关文档

- [React 文档](https://react.dev/)
- [Vite 文档](https://vitejs.dev/)
- [Axios 文档](https://axios-http.com/)
- [React Dropzone 文档](https://react-dropzone.js.org/)

## 📄 许可证

本项目仅用于学习和演示目的。
