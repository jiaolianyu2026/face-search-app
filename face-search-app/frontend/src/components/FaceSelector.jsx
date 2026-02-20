import { useState, useEffect, useRef } from 'react'
import './FaceSelector.css'

/**
 * FaceSelector 组件
 * 在图片上显示人像标记并处理多选
 * 
 * @param {string} imageUrl - 图片 URL
 * @param {Array} faces - 人像列表，每个人像包含 faceId 和 boundingBox
 * @param {Array} selectedFaceIds - 已选中的人像 ID 列表
 * @param {Function} onSelectionChange - 选择变化回调函数
 */
function FaceSelector({ imageUrl, faces, selectedFaceIds = [], onSelectionChange }) {
  const imageRef = useRef(null)
  const containerRef = useRef(null)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 })

  // 为每个人像生成唯一颜色
  const getColorForFace = (faceId) => {
    // 使用简单的哈希函数生成颜色
    let hash = 0
    for (let i = 0; i < faceId.length; i++) {
      hash = faceId.charCodeAt(i) + ((hash << 5) - hash)
    }
    
    // 预定义的调色板（明亮且易区分的颜色）
    const colors = [
      '#1890ff', // 蓝色
      '#52c41a', // 绿色
      '#faad14', // 橙色
      '#f5222d', // 红色
      '#722ed1', // 紫色
      '#13c2c2', // 青色
      '#eb2f96', // 粉色
      '#fa8c16', // 橙黄色
    ]
    
    const index = Math.abs(hash) % colors.length
    return colors[index]
  }

  // 处理图片加载
  const handleImageLoad = () => {
    if (imageRef.current) {
      setImageDimensions({
        width: imageRef.current.offsetWidth,
        height: imageRef.current.offsetHeight
      })
      setImageLoaded(true)
    }
  }

  // 监听窗口大小变化，重新计算图片尺寸
  useEffect(() => {
    const handleResize = () => {
      if (imageRef.current) {
        setImageDimensions({
          width: imageRef.current.offsetWidth,
          height: imageRef.current.offsetHeight
        })
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // 处理人像点击
  const handleFaceClick = (faceId) => {
    const isSelected = selectedFaceIds.includes(faceId)
    let newSelection

    if (isSelected) {
      // 取消选择
      newSelection = selectedFaceIds.filter(id => id !== faceId)
    } else {
      // 添加选择
      newSelection = [...selectedFaceIds, faceId]
    }

    onSelectionChange(newSelection)
  }

  // 计算人像标记的位置和大小
  const getFaceMarkerProps = (face) => {
    if (!imageRef.current || !imageLoaded) return null

    const img = imageRef.current
    const { boundingBox } = face
    
    // 计算缩放比例
    const scaleX = imageDimensions.width / img.naturalWidth
    const scaleY = imageDimensions.height / img.naturalHeight

    // 计算人像中心点
    const centerX = (boundingBox.x + boundingBox.width / 2) * scaleX
    const centerY = (boundingBox.y + boundingBox.height / 2) * scaleY
    
    // 计算圆形半径（取边界框较小边的一半，再加一些边距）
    const radius = Math.min(boundingBox.width, boundingBox.height) * Math.min(scaleX, scaleY) / 2 + 10

    return {
      cx: centerX,
      cy: centerY,
      r: radius
    }
  }

  return (
    <div className="face-selector" ref={containerRef}>
      <div className="face-selector-image-container">
        <img
          ref={imageRef}
          src={imageUrl}
          alt="人像选择"
          className="face-selector-image"
          onLoad={handleImageLoad}
        />
        
        {imageLoaded && faces.length > 0 && (
          <svg
            className="face-selector-overlay"
            width={imageDimensions.width}
            height={imageDimensions.height}
          >
            {faces.map((face) => {
              const markerProps = getFaceMarkerProps(face)
              if (!markerProps) return null

              const isSelected = selectedFaceIds.includes(face.faceId)
              const color = getColorForFace(face.faceId)

              return (
                <g key={face.faceId}>
                  {/* 圆形标记 */}
                  <circle
                    cx={markerProps.cx}
                    cy={markerProps.cy}
                    r={markerProps.r}
                    fill="none"
                    stroke={color}
                    strokeWidth={isSelected ? 4 : 2}
                    opacity={isSelected ? 1 : 0.7}
                    className="face-marker"
                    onClick={() => handleFaceClick(face.faceId)}
                    style={{ cursor: 'pointer' }}
                  />
                  
                  {/* 选中时的高亮效果 */}
                  {isSelected && (
                    <>
                      <circle
                        cx={markerProps.cx}
                        cy={markerProps.cy}
                        r={markerProps.r + 5}
                        fill="none"
                        stroke={color}
                        strokeWidth={2}
                        opacity={0.3}
                        className="face-marker-highlight"
                        style={{ pointerEvents: 'none' }}
                      />
                      <circle
                        cx={markerProps.cx}
                        cy={markerProps.cy}
                        r={8}
                        fill={color}
                        className="face-marker-center"
                        style={{ pointerEvents: 'none' }}
                      />
                    </>
                  )}
                </g>
              )
            })}
          </svg>
        )}
      </div>

      {/* 选择提示 */}
      {faces.length > 0 && (
        <div className="face-selector-hint">
          <p>
            {selectedFaceIds.length === 0 
              ? '点击圆圈选择人像（支持多选）' 
              : `已选择 ${selectedFaceIds.length} 个人像`}
          </p>
        </div>
      )}
    </div>
  )
}

export default FaceSelector
