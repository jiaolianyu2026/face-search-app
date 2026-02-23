/**
 * UnifiedFaceSelector 组件 - 统一人像选择器
 * Feature: unified-face-selector
 * 
 * 整合历史人像库和新上传人像的统一选择界面
 * 需求：1.1, 1.2, 1.3, 1.4, 1.5
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import PropTypes from 'prop-types';
import Toolbar from './Toolbar';
import UploadedFacesSection from './UploadedFacesSection';
import LibraryFacesSection from './LibraryFacesSection';
import './UnifiedFaceSelector.css';

/**
 * @typedef {import('../types/index').UploadedFace} UploadedFace
 * @typedef {import('../types/index').LibraryFace} LibraryFace
 * @typedef {import('../types/index').FaceSelection} FaceSelection
 */

// 从后端错误响应中提取错误消息
const extractErrorMessage = (errorData, fallback) => {
  if (!errorData) return fallback;
  const err = errorData.error;
  if (typeof err === 'string') return err;
  if (err && typeof err.message === 'string') return err.message;
  if (typeof errorData.message === 'string') return errorData.message;
  return fallback;
};

/**
 * UnifiedFaceSelector 组件属性
 * @typedef {Object} UnifiedFaceSelectorProps
 * @property {(selection: FaceSelection) => void} onStartSearch - 开始搜索的回调
 * @property {(error: Error) => void} [onError] - 错误处理回调
 * @property {(message: string) => void} [onSuccess] - 成功提示回调
 */

/**
 * UnifiedFaceSelector 主组件
 * 需求 1.1: 显示双区域布局，包含新导入人像区域和历史人像库区域
 * 需求 1.2: 左侧显示新导入人像区域，右侧显示历史人像库区域
 * 需求 1.3: 顶部显示工具栏，包含选择计数、开始搜索按钮和清空选择按钮
 * 需求 1.4: 界面宽度小于 768px 时切换为垂直堆叠布局
 * 需求 1.5: 为每个区域提供清晰的标题标识
 * 
 * @param {UnifiedFaceSelectorProps} props
 */
const UnifiedFaceSelector = ({
  onStartSearch,
  onError,
  onSuccess
}) => {
  // ========== 状态管理 ==========
  
  // 新上传的人像列表
  const [uploadedFaces, setUploadedFaces] = useState([]);
  
  // 历史人像列表
  const [libraryFaces, setLibraryFaces] = useState([]);
  
  // 选中的人像（使用 Set 存储 ID）
  const [selectedUploadedFaceIds, setSelectedUploadedFaceIds] = useState(new Set());
  const [selectedLibraryFaceIds, setSelectedLibraryFaceIds] = useState(new Set());
  
  // 加载状态
  const [loadingLibrary, setLoadingLibrary] = useState(false);

  // ========== 计算属性 ==========
  
  /**
   * 计算总选中数量
   * 需求 4.3: 在顶部工具栏实时显示当前选中的人像数量
   */
  const selectedCount = useMemo(() => {
    return selectedUploadedFaceIds.size + selectedLibraryFaceIds.size;
  }, [selectedUploadedFaceIds, selectedLibraryFaceIds]);

  /**
   * 检查是否达到选择上限
   * 需求 4.5: 选中人像数量达到 10 个时禁用未选中人像的点击
   */
  const isSelectionLimitReached = useMemo(() => {
    return selectedCount >= 10;
  }, [selectedCount]);

  // ========== 事件处理函数 ==========

  /**
   * 处理人脸检测完成
   * 需求 3.6: 检测完成后显示所有检测到的人脸
   */
  const handleFacesDetected = useCallback((newFaces) => {
    setUploadedFaces(prev => [...prev, ...newFaces]);
    if (onSuccess) {
      onSuccess(`成功检测到 ${newFaces.length} 个人脸`);
    }
  }, [onSuccess]);

  /**
   * 切换新上传人像的选中状态
   * 需求 4.1: 点击任意人像时切换该人像的选中状态
   * 需求 4.2: 为选中的人像显示视觉反馈
   * 需求 4.5: 选中数量达到 10 个时禁用未选中人像的点击
   * 需求 4.7: 点击已选中的人像时取消该人像的选中状态
   */
  const handleToggleUploadedFace = useCallback((faceId) => {
    setSelectedUploadedFaceIds(prev => {
      const newSet = new Set(prev);
      
      if (newSet.has(faceId)) {
        // 取消选择 - 需求 4.7
        newSet.delete(faceId);
      } else {
        // 检查是否达到上限 - 需求 4.5
        if (selectedCount >= 10) {
          if (onError) {
            onError(new Error('最多只能选择 10 个人像'));
          }
          return prev;
        }
        // 添加选择
        newSet.add(faceId);
      }
      
      return newSet;
    });
  }, [selectedCount, onError]);

  /**
   * 切换历史人像的选中状态
   * 需求 4.1, 4.2, 4.5, 4.7
   */
  const handleToggleLibraryFace = useCallback((faceId) => {
    setSelectedLibraryFaceIds(prev => {
      const newSet = new Set(prev);
      
      if (newSet.has(faceId)) {
        // 取消选择 - 需求 4.7
        newSet.delete(faceId);
      } else {
        // 检查是否达到上限 - 需求 4.5
        if (selectedCount >= 10) {
          if (onError) {
            onError(new Error('最多只能选择 10 个人像'));
          }
          return prev;
        }
        // 添加选择
        newSet.add(faceId);
      }
      
      return newSet;
    });
  }, [selectedCount, onError]);

  /**
   * 清空所有选择
   * 需求 4.6: 点击"清空选择"按钮时取消所有人像的选中状态
   */
  const handleClearSelection = useCallback(() => {
    setSelectedUploadedFaceIds(new Set());
    setSelectedLibraryFaceIds(new Set());
  }, []);

  /**
   * 保存新上传人像到库
   * 需求 5.3: 调用保存 API 将人像数据保存到人像库
   * 需求 5.4: 保存成功后在历史人像区域添加新保存的人像
   * 需求 5.5: 保存成功后从新导入人像区域移除该人像
   */
  const handleSaveFaceToLibrary = useCallback(async (face) => {
    try {
      // 构建保存请求
      const requestData = {
        name: face.name || `人像_${new Date().toISOString().replace(/[:.]/g, '-')}`,
        imageId: face.imageId,
        faceId: face.faceId,
        features: face.features,
        boundingBox: face.boundingBox
      };

      // 调用保存 API - 需求 5.3
      const response = await fetch('/api/library/faces', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(extractErrorMessage(errorData, '保存失败'));
      }

      const savedFaceRaw = await response.json();
      // 统一字段名（后端返回 snake_case，前端用 camelCase）
      const savedFace = {
        ...savedFaceRaw,
        createdAt: savedFaceRaw.createdAt || savedFaceRaw.created_at
      };

      // 添加到历史人像列表 - 需求 5.4
      setLibraryFaces(prev => [savedFace, ...prev]);

      // 从新上传人像列表中移除 - 需求 5.5
      setUploadedFaces(prev => 
        prev.filter(f => !(f.imageId === face.imageId && f.faceId === face.faceId))
      );

      // 如果该人像被选中，也要从选中列表中移除
      const faceKey = `${face.imageId}:${face.faceId}`;
      setSelectedUploadedFaceIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(faceKey);
        return newSet;
      });

      if (onSuccess) {
        onSuccess('人像已保存到库');
      }
    } catch (error) {
      console.error('保存人像失败:', error);
      if (onError) {
        onError(error);
      }
    }
  }, [onError, onSuccess]);

  /**
   * 加载历史人像
   * 需求 2.1: 打开界面时从人像库加载并显示所有历史人像
   */
  const handleLoadLibraryFaces = useCallback(async () => {
    try {
      setLoadingLibrary(true);
      
      const response = await fetch('/api/library/faces');
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(extractErrorMessage(errorData, '加载历史人像失败'));
      }

      const data = await response.json();
      setLibraryFaces(data.faces || []);
    } catch (error) {
      console.error('加载历史人像失败:', error);
      if (onError) {
        onError(error);
      }
    } finally {
      setLoadingLibrary(false);
    }
  }, [onError]);

  /**
   * 编辑历史人像名称
   * 需求 2.6: 修改历史人像名称并确认后更新人像库中的名称并刷新显示
   */
  const handleEditLibraryFace = useCallback(async (face) => {
    try {
      const newName = prompt('请输入新名称:', face.name);
      
      if (!newName || newName.trim() === '') {
        return; // 用户取消或输入为空
      }

      // 调用更新 API
      const response = await fetch(`/api/library/faces/${face.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: newName.trim() })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(extractErrorMessage(errorData, '更新名称失败'));
      }

      // 更新本地状态
      setLibraryFaces(prev => 
        prev.map(f => f.id === face.id ? { ...f, name: newName.trim() } : f)
      );

      if (onSuccess) {
        onSuccess('名称已更新');
      }
    } catch (error) {
      console.error('编辑人像名称失败:', error);
      if (onError) {
        onError(error);
      }
    }
  }, [onError, onSuccess]);

  /**
   * 删除历史人像
   * 需求 2.8: 确认删除后从人像库中删除该人像并从界面移除
   */
  const handleDeleteLibraryFace = useCallback(async (face) => {
    try {
      // 需求 2.7: 显示确认对话框
      const confirmed = window.confirm(`确定要删除人像"${face.name}"吗？`);
      
      if (!confirmed) {
        return;
      }

      // 调用删除 API
      const response = await fetch(`/api/library/faces/${face.id}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(extractErrorMessage(errorData, '删除失败'));
      }

      // 从本地状态中移除
      setLibraryFaces(prev => prev.filter(f => f.id !== face.id));

      // 如果该人像被选中，也要从选中列表中移除
      setSelectedLibraryFaceIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(face.id);
        return newSet;
      });

      if (onSuccess) {
        onSuccess('人像已删除');
      }
    } catch (error) {
      console.error('删除人像失败:', error);
      if (onError) {
        onError(error);
      }
    }
  }, [onError, onSuccess]);

  /**
   * 开始搜索
   * 需求 6.3: 收集所有选中人像的特征向量
   * 需求 6.4: 选中的人像包含新上传人像时使用其检测到的特征向量
   * 需求 6.5: 选中的人像包含历史人像时从人像库加载其特征向量
   * 需求 6.7: 搜索任务启动成功后导航到搜索结果界面
   */
  const handleStartSearch = useCallback(async () => {
    try {
      // 构建选择对象
      // Bug Fix 4: 返回完整的人像对象而非简化对象
      const selection = {
        uploadedFaces: Array.from(selectedUploadedFaceIds).map(compositeId => {
          return uploadedFaces.find(face => `${face.imageId}:${face.faceId}` === compositeId);
        }).filter(Boolean), // 过滤掉未找到的人像
        libraryFaces: Array.from(selectedLibraryFaceIds)
      };

      // 调用父组件的回调
      onStartSearch(selection);
    } catch (error) {
      console.error('开始搜索失败:', error);
      if (onError) {
        onError(error);
      }
    }
  }, [selectedUploadedFaceIds, selectedLibraryFaceIds, uploadedFaces, onStartSearch, onError]);

  // ========== 生命周期处理 ==========

  /**
   * 组件挂载时的初始化
   * 需求 9.3: 页面刷新时清空新上传人像区域的所有临时数据
   * 需求 9.4: 页面刷新时重新加载历史人像库数据
   */
  useEffect(() => {
    // 清空临时数据（uploadedFaces 初始状态已经是空数组）
    // 需求 9.3: 页面刷新时清空临时数据
    setUploadedFaces([]);
    setSelectedUploadedFaceIds(new Set());
    
    // 加载历史人像
    // 需求 9.4: 页面刷新时重新加载历史人像
    handleLoadLibraryFaces();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 空依赖数组，仅在组件挂载时执行一次

  /**
   * 组件卸载时的清理
   * 需求 9.6: 导航离开界面时清理所有临时上传的图片文件
   */
  useEffect(() => {
    return () => {
      // 组件卸载时清理临时上传的图片
      // 需求 9.6: 清理临时文件
      uploadedFaces.forEach(async (face) => {
        try {
          // 调用后端 API 清理临时文件
          await fetch(`/api/cleanup/${face.imageId}`, {
            method: 'DELETE'
          });
        } catch (error) {
          console.error('清理临时文件失败:', error);
          // 清理失败不影响组件卸载，只记录错误
        }
      });
    };
  }, [uploadedFaces]); // 依赖 uploadedFaces，确保清理最新的文件列表

  // ========== 渲染 ==========

  return (
    <div 
      className="unified-face-selector"
      role="main"
      aria-label="统一人像选择界面"
    >
      {/* 工具栏 - 需求 1.3 */}
      <div 
        className="unified-face-selector__toolbar"
        role="toolbar"
        aria-label="人像选择工具栏"
      >
        <Toolbar
          selectedCount={selectedCount}
          onStartSearch={handleStartSearch}
          onClearSelection={handleClearSelection}
          showExportControls={false}
        />
      </div>

      {/* 主内容区 - 需求 1.1, 1.2, 1.4 */}
      <div className="unified-face-selector__content">
        {/* 左侧：新导入人像区域 - 需求 1.2, 1.5 */}
        <section 
          className="unified-face-selector__section unified-face-selector__section--uploaded"
          aria-labelledby="uploaded-faces-heading"
        >
          <UploadedFacesSection
            uploadedFaces={uploadedFaces}
            selectedFaceIds={selectedUploadedFaceIds}
            onToggleSelect={handleToggleUploadedFace}
            onSave={handleSaveFaceToLibrary}
            onFacesDetected={handleFacesDetected}
            onError={onError}
          />
        </section>

        {/* 右侧：历史人像库区域 - 需求 1.2, 1.5 */}
        <section 
          className="unified-face-selector__section unified-face-selector__section--library"
          aria-labelledby="library-faces-heading"
        >
          <LibraryFacesSection
            libraryFaces={libraryFaces}
            selectedFaceIds={selectedLibraryFaceIds}
            onToggleSelect={handleToggleLibraryFace}
            onEdit={handleEditLibraryFace}
            onDelete={handleDeleteLibraryFace}
            onLoadFaces={handleLoadLibraryFaces}
            onError={onError}
            loading={loadingLibrary}
          />
        </section>
      </div>
    </div>
  );
};

UnifiedFaceSelector.propTypes = {
  onStartSearch: PropTypes.func.isRequired,
  onError: PropTypes.func,
  onSuccess: PropTypes.func
};

export default UnifiedFaceSelector;
