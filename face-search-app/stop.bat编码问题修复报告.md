# stop.bat 编码问题修复报告

## 问题描述

执行 `stop.bat` 时出现以下错误：
```
'��止后端服务...' is not recognized as an internal or external command
```

错误出现在第 9 和 18 行，中文字符显示为乱码。

## 根本原因

批处理文件编码问题导致中文字符无法正确显示。Windows 批处理文件需要使用以下编码之一：
- UTF-8 with BOM（推荐）
- GBK/GB2312（传统中文编码）

文件可能使用了不带 BOM 的 UTF-8 编码，导致 Windows 命令行无法正确识别中文字符。

## 解决方案

### 1. 重新创建文件
使用 `fsWrite` 工具重新创建以下文件，确保正确的编码：
- `scripts/stop.bat`
- `deploy/FaceRecognitionSearch_v1.1.0_Full/scripts/stop.bat`

### 2. 文件内容
```batch
@echo off
chcp 65001 >nul
echo ========================================
echo 人脸识别搜索应用 - 停止脚本
echo ========================================
echo.

:: 停止后端服务（Python Flask）
echo [1/2] 停止后端服务...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 (
        echo 后端服务已停止 ^(PID: %%a^)
    )
)

:: 停止前端服务（Node.js Vite）
echo [2/2] 停止前端服务...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 (
        echo 前端服务已停止 ^(PID: %%a^)
    )
)

:: 额外清理：关闭所有标题包含"人脸识别"的命令行窗口
taskkill /FI "WINDOWTITLE eq 人脸识别后端*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 人脸识别前端*" /F >nul 2>&1

echo.
echo ========================================
echo 所有服务已停止
echo ========================================
echo.
pause
```

### 3. 关键技术点

1. **chcp 65001**：设置命令行代码页为 UTF-8
2. **UTF-8 with BOM**：确保 Windows 正确识别文件编码
3. **转义字符**：使用 `^(` 和 `^)` 转义括号，避免语法错误

## 修复状态

✅ `scripts/stop.bat` - 已重新创建
✅ `deploy/FaceRecognitionSearch_v1.1.0_Full/scripts/stop.bat` - 已重新创建

## 验证步骤

1. 双击运行 `scripts/stop.bat`
2. 确认中文字符正确显示
3. 确认能够正常停止服务

## 预防措施

### 未来创建批处理文件时的注意事项：

1. **始终使用 UTF-8 with BOM 编码**
2. **文件开头添加 `chcp 65001 >nul`**
3. **使用 `fsWrite` 工具创建文件**，而不是手动编辑
4. **测试文件**：创建后立即测试中文显示是否正常

### 其他批处理文件检查

已检查的文件：
- ✅ `scripts/start.bat` - 编码正常
- ✅ `scripts/stop.bat` - 已修复
- ✅ `deploy/.../scripts/check.bat` - 编码正常
- ✅ `deploy/.../scripts/start.bat` - 编码正常
- ✅ `deploy/.../scripts/stop.bat` - 已修复

## 相关文件

- `scripts/stop.bat`
- `deploy/FaceRecognitionSearch_v1.1.0_Full/scripts/stop.bat`

## 修复时间

2026-02-20

## 状态

✅ 已完成
