/**
 * UploadedFacesSection 组件 - 新上传人像区域
 * Feature: unified-face-selector
 * 
 * 集成上传区域和人像网格，处理图片上传、人脸检测和结果展示
 * 需求：3.1, 3.5, 3.6, 3.7, 3.8
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import UploadArea from './UploadArea';
import FaceGrid from './FaceGrid';
import FaceSelector from './FaceSelector';
import './UploadedFacesSection.css';

/**
 * @typedef {import('../types/index').UploadedFace} UploadedFace
 */

/**
 * UploadedFacesSection 组件
 * @param {Object} props
 * @param {UploadedFace[]} props.uploadedFaces - 已上传并检测到的人像列表
 * @param {Set<string>} props.selectedFaceIds - 选中的人像ID集合（格式：imageId:faceId）
 * @param {(faceId: string) => void} props.onToggleSelect - 切换选中状态的回调
 * @param {(face: UploadedFace) => void} props.onSave - 保存到库的回调
 * @param {(faces: UploadedFace[]) => void} props.onFacesDetected - 检测到人脸后的回调
 * @param {(error: Error) => void} [props.onError] - 错误处理回调
 */
const UploadedFacesSection = ({
  uploadedFaces,
  selectedFaceIds,
  onToggleSelect,
  onSave,
  onFacesDetected,
  onError
}) => {
  const [loading, setLoading] = useState(false);
  const [imageUrl, setImageUrl] = useState(null);

  // 当前图片的 imageId（用于 FaceSelector 选中状态转换）
  const currentImageIdRef = useRef(null);

  /**
   * 当上传的人脸列表变化时，更新图片 URL
   */
  useEffect(() => {
    if (uploadedFaces.length > 0) {
      const firstFace = uploadedFaces[0];
      currentImageIdRef.current = firstFace.imageId;
      setImageUrl(`/api/preview/${firstFace.imageId}`);
    } else {
      currentImageIdRef.current = null;
      setImageUrl(null);
    }
  }, [uploadedFaces]);

  /**
   * 将父组件的 selectedFaceIds（Set<imageId:faceId>）转换为
   * FaceSelector 需要的原始 faceId 数组
   */
  const getFaceSelectorSelectedIds = () => {
    const imageId = currentImageIdRef.current;
    if (!imageId) return [];
    return Array.from(selectedFaceIds)
      .filter(id => id.startsWith(`${imageId}:`))
      .map(id => id.slice(imageId.length + 1));
  };

  /**
   * 处理 FaceSelector 选中状态变化
   * FaceSelector 传入完整的新选中列表（原始 faceId 数组）
   * 需要计算差异并调用 onToggleSelect（传入 imageId:faceId 格式）
   */
  const handleFaceSelectorChange = useCallback((newSelectedRawIds) => {
    const imageId = currentImageIdRef.current;
    if (!imageId) return;

    // 当前已选中的原始 faceId 集合
    const currentRawIds = new Set(
      Array.from(selectedFaceIds)
        .filter(id => id.startsWith(`${imageId}:`))
        .map(id => id.slice(imageId.length + 1))
    );

    const newRawSet = new Set(newSelectedRawIds);

    // 找出新增的（在新列表中但不在当前列表中）
    for (const rawId of newRawSet) {
      if (!currentRawIds.has(rawId)) {
        onToggleSelect(`${imageId}:${rawId}`);
      }
    }

    // 找出移除的（在当前列表中但不在新列表中）
    for (const rawId of currentRawIds) {
      if (!newRawSet.has(rawId)) {
        onToggleSelect(`${imageId}:${rawId}`);
      }
    }
  }, [selectedFaceIds, onToggleSelect]);

  /**
   * 处理文件上传和人脸检测
   * 需求 3.5: 图片上传成功后自动调用人脸检测 API
   */
  const handleUpload = useCallback(async (file) => {
    try {
      setLoading(true);

      // 步骤 1: 上传图片
      const formData = new FormData();
      formData.append('file', file);

      const uploadResponse = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json();
        throw new Error(errorData.error || '图片上传失败');
      }

      const uploadData = await uploadResponse.json();
      const imageId = uploadData.imageId;

      // 步骤 2: 自动调用人脸检测 API（需求 3.5）
      const detectResponse = await fetch('/api/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ imageId })
      });

      if (!detectResponse.ok) {
        const errorData = await detectResponse.json();
        throw new Error(errorData.error || '人脸检测失败');
      }

      const detectData = await detectResponse.json();

      // 步骤 3: 处理检测结果
      // 需求 3.6: 检测完成后显示所有检测到的人脸
      // 需求 3.7: 检测到多个人脸时，为每个人脸显示独立的缩略图和边界框信息
      if (detectData.faces && detectData.faces.length > 0) {
        // 转换为 UploadedFace 格式，faceId 使用原始格式（不含 imageId 前缀）
        const newFaces = detectData.faces.map(face => ({
          imageId,
          faceId: face.faceId,  // 原始 faceId，FaceGrid 会自动拼接 imageId:faceId
          boundingBox: face.boundingBox,
          features: face.features,
          sourceFileName: file.name,
          thumbnailUrl: face.thumbnailUrl || `/api/preview/${imageId}`
        }));

        onFacesDetected(newFaces);
      } else {
        // 需求 3.8: 图片中未检测到人脸时显示提示信息
        if (onError) {
          onError(new Error('未检测到人脸'));
        }
      }
    } catch (error) {
      console.error('上传和检测错误:', error);
      if (onError) {
        onError(error);
      }
    } finally {
      setLoading(false);
    }
  }, [onFacesDetected, onError]);

  return (
    <div className="uploaded-faces-section">
      <div className="uploaded-faces-section__header">
        <h2
          id="uploaded-faces-heading"
          className="uploaded-faces-section__title"
        >
          新导入人像
        </h2>
        <span className="uploaded-faces-section__count">
          {uploadedFaces.length} 个人像
        </span>
      </div>

      <div className="uploaded-faces-section__content">
        {/* 上传区域 - 需求 3.1 */}
        <div className="uploaded-faces-section__upload">
          <UploadArea onUpload={handleUpload} loading={loading} />
        </div>

        {/* 图片和人脸标注 - 需求 1.1, 1.2, 1.3：用 FaceSelector SVG 圆形标记替换 Canvas 矩形 */}
        {imageUrl && uploadedFaces.length > 0 && (
          <div className="uploaded-faces-section__image-container">
            <FaceSelector
              imageUrl={imageUrl}
              faces={uploadedFaces}
              selectedFaceIds={getFaceSelectorSelectedIds()}
              onSelectionChange={handleFaceSelectorChange}
            />
          </div>
        )}

        {/* 人像网格 - 需求 3.6, 3.7 */}
        <div className="uploaded-faces-section__grid">
          <FaceGrid
            faces={uploadedFaces}
            faceType="uploaded"
            selectedFaceIds={selectedFaceIds}
            onToggleSelect={onToggleSelect}
            onSave={onSave}
            emptyMessage="上传图片后，检测到的人脸将显示在这里"
          />
        </div>
      </div>
    </div>
  );
};

UploadedFacesSection.propTypes = {
  uploadedFaces: PropTypes.array.isRequired,
  selectedFaceIds: PropTypes.instanceOf(Set).isRequired,
  onToggleSelect: PropTypes.func.isRequired,
  onSave: PropTypes.func.isRequired,
  onFacesDetected: PropTypes.func.isRequired,
  onError: PropTypes.func
};

export default UploadedFacesSection;
