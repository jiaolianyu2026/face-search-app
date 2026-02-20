# 部署清单 - Deployment Checklist

## 📋 打包前检查

在运行 `scripts\package.bat` 之前，请确认：

### 代码完整性
- [ ] 所有功能已实现并测试通过
- [ ] 所有测试用例通过（运行 `pytest tests/ -v`）
- [ ] 代码已提交到版本控制系统
- [ ] 没有调试代码或临时文件

### 配置文件
- [ ] `backend/config.py` 配置正确
- [ ] `.env.example` 包含所有必要的环境变量
- [ ] `deploy_config.json` 配置正确
- [ ] 端口配置无冲突（默认 3000 和 5000）

### 依赖文件
- [ ] `backend/requirements.txt` 包含所有后端依赖
- [ ] `frontend/package.json` 包含所有前端依赖
- [ ] 依赖版本已锁定（避免兼容性问题）

### 文档完整性
- [ ] `README.md` 更新到最新
- [ ] `INSTALLATION.md` 包含详细安装步骤
- [ ] `USAGE_GUIDE.md` 包含使用说明
- [ ] `backend/API_DOCUMENTATION.md` API 文档完整
- [ ] 所有文档使用中文

### 脚本文件
- [ ] `scripts/install.bat` 测试通过
- [ ] `scripts/start.bat` 测试通过
- [ ] `scripts/stop.bat` 测试通过
- [ ] `scripts/build_frontend.bat` 测试通过
- [ ] `scripts/package.bat` 可以正常运行

---

## 📦 打包步骤

### 1. 清理项目

```batch
# 删除临时文件
rmdir /s /q backend\temp_uploads
rmdir /s /q backend\cache
rmdir /s /q backend\__pycache__
rmdir /s /q frontend\dist
rmdir /s /q frontend\node_modules
rmdir /s /q backend\venv

# 删除测试生成的文件
del /q backend\*.log
del /q backend\*.db
```

### 2. 运行打包脚本

```batch
scripts\package.bat
```

### 3. 验证打包结果

检查生成的目录：`deploy\FaceRecognitionSearch_v1.0.0_YYYYMMDD\`

必须包含：
- [ ] `backend/` 目录及所有 .py 文件
- [ ] `backend/requirements.txt`
- [ ] `frontend/src/` 目录及所有源代码
- [ ] `frontend/package.json`
- [ ] `scripts/` 目录及所有 .bat 文件
- [ ] `tests/` 目录及所有测试文件
- [ ] `README.md`
- [ ] `INSTALLATION.md`
- [ ] `USAGE_GUIDE.md`
- [ ] `.env.example`
- [ ] `deploy_config.json`
- [ ] `VERSION.txt`

---

## 🧪 部署测试

### 1. 在干净的环境中测试

在一台没有安装过该应用的 Windows 机器上：

```batch
# 1. 解压部署包
# 2. 运行安装脚本
scripts\install.bat

# 3. 检查安装结果
dir backend\venv
dir frontend\node_modules
```

### 2. 测试启动

```batch
# 启动应用
scripts\start.bat

# 等待 10 秒后检查
# - 前端：http://localhost:3000 应该可以访问
# - 后端：http://localhost:5000 应该可以访问
```

### 3. 测试核心功能

- [ ] 上传图片成功
- [ ] 人脸检测成功
- [ ] 人脸搜索成功
- [ ] 结果导出成功

### 4. 测试停止

```batch
# 停止应用
scripts\stop.bat

# 检查进程是否已停止
netstat -ano | findstr :3000
netstat -ano | findstr :5000
# 应该没有输出
```

---

## 📝 发布前检查

### 版本信息
- [ ] 版本号正确（在 `deploy_config.json` 中）
- [ ] 发布日期正确
- [ ] `VERSION.txt` 信息完整

### 文件大小
- [ ] 压缩包大小合理（预计 < 50MB，不含 node_modules 和 venv）
- [ ] 解压后大小合理（预计 < 100MB）

### 安全检查
- [ ] 没有包含敏感信息（密码、密钥等）
- [ ] 没有包含 `.env` 文件（只包含 `.env.example`）
- [ ] 没有包含用户数据或测试数据

### 许可证
- [ ] 包含许可证文件（如果需要）
- [ ] 第三方库许可证合规

---

## 🚀 发布步骤

### 1. 创建发布包

```batch
# 运行打包脚本
scripts\package.bat

# 生成的文件：
# - deploy\FaceRecognitionSearch_v1.0.0_YYYYMMDD\（文件夹）
# - deploy\FaceRecognitionSearch_v1.0.0_YYYYMMDD.zip（压缩包）
```

### 2. 测试发布包

在干净的测试环境中：
1. 解压压缩包
2. 运行完整的安装和测试流程
3. 确认所有功能正常

### 3. 准备发布材料

- [ ] 压缩包文件
- [ ] 发布说明（Release Notes）
- [ ] 安装指南（INSTALLATION.md）
- [ ] 使用指南（USAGE_GUIDE.md）
- [ ] 已知问题列表（如果有）

### 4. 发布

根据发布渠道：
- 内部部署：复制到共享目录
- 外部发布：上传到下载服务器
- 版本控制：创建 Git tag

---

## 📊 发布后验证

### 1. 下载验证

- [ ] 从发布渠道下载压缩包
- [ ] 验证文件完整性（MD5/SHA256）
- [ ] 解压测试

### 2. 用户反馈

收集用户反馈：
- 安装是否顺利
- 功能是否正常
- 性能是否满足需求
- 文档是否清晰

### 3. 问题跟踪

- [ ] 建立问题跟踪系统
- [ ] 记录常见问题
- [ ] 准备快速修复方案

---

## 🔄 更新发布流程

### 版本号规则

使用语义化版本（Semantic Versioning）：
- **主版本号**（Major）：不兼容的 API 修改
- **次版本号**（Minor）：向下兼容的功能性新增
- **修订号**（Patch）：向下兼容的问题修正

示例：
- `1.0.0` → 首次发布
- `1.0.1` → Bug 修复
- `1.1.0` → 新增功能
- `2.0.0` → 重大更新

### 更新步骤

1. **更新版本号**
   - 修改 `deploy_config.json` 中的 `version`
   - 更新 `README.md` 中的版本信息

2. **更新文档**
   - 更新 `CHANGELOG.md`（如果有）
   - 更新 `INSTALLATION.md`（如果有变化）
   - 更新 `USAGE_GUIDE.md`（如果有新功能）

3. **测试**
   - 运行所有测试用例
   - 在干净环境中测试安装
   - 测试升级流程

4. **打包发布**
   - 运行 `scripts\package.bat`
   - 验证打包结果
   - 发布新版本

---

## 📋 快速检查清单

打印此清单，在每次发布前逐项检查：

```
部署前检查：
□ 代码完整性
□ 配置文件
□ 依赖文件
□ 文档完整性
□ 脚本文件

打包步骤：
□ 清理项目
□ 运行打包脚本
□ 验证打包结果

部署测试：
□ 干净环境测试
□ 测试启动
□ 测试核心功能
□ 测试停止

发布前检查：
□ 版本信息
□ 文件大小
□ 安全检查
□ 许可证

发布步骤：
□ 创建发布包
□ 测试发布包
□ 准备发布材料
□ 发布

发布后验证：
□ 下载验证
□ 用户反馈
□ 问题跟踪
```

---

## 📞 联系信息

如有问题，请联系：
- 技术支持：[support@example.com]
- 项目负责人：[project-lead@example.com]

---

**最后更新**：2026-02-14  
**文档版本**：1.0.0
