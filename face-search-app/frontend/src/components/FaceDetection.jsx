import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './FaceDetection.css'

function FaceDetection({ imageId, previewUrl, onFaceSelect, onBack, onFacesDetected }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [faces, setFaces] = useState([])
  const [selectedFaceIndex, setSelectedFaceIndex] = useState(null)
  const canvasRef = useRef(null)
  const imageRef = useRef(null)
  const detectCalledRef = useRef(false) // 防止重复调用

  useEffect(() => {
    // 只在首次加载或 imageId 改变时调用
    if (!detectCalledRef.current) {
      detectCalledRef.current = true
      detectFaces()
    }
    
    // 清理函数
    return () => {
      detectCalledRef.current = false
    }
  }, [imageId])

  const detectFaces = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post('/api/detect', { imageId })
      
      if (response.data.faces && response.data.faces.length > 0) {
        setFaces(response.data.faces)
        // 如果只有一个人脸，自动选中
        if (response.data.faces.length === 1) {
          setSelectedFaceIndex(0)
        }
        // 通知父组件检测到的人像
        if (onFacesDetected) {
          onFacesDetected(response.data.faces)
        }
      } else {
        setError('未检测到人脸，请上传包含清晰人脸的图片')
      }
    } catch (err) {
      console.error('检测错误:', err)
      if (err.response?.data?.error) {
        setError(err.response.data.error.message || '人脸检测失败')
      } else {
        setError('人脸检测失败，请重试')
      }
    } finally {
      setLoading(false)
    }
  }

  // 在图片上绘制人脸边界框
  useEffect(() => {
    if (faces.length > 0 && imageRef.current && canvasRef.current) {
      const image = imageRef.current
      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')

      // 设置 canvas 尺寸与图片一致
      canvas.width = image.naturalWidth
      canvas.height = image.naturalHeight

      // 先绘制原图
      ctx.drawImage(image, 0, 0)

      // 绘制所有人脸边界框
      faces.forEach((face, index) => {
        const { x, y, width, height } = face.boundingBox
        const isSelected = index === selectedFaceIndex

        // 绘制边界框
        ctx.strokeStyle = isSelected ? '#52c41a' : '#1890ff'
        ctx.lineWidth = isSelected ? 4 : 2
        ctx.strokeRect(x, y, width, height)

        // 绘制标签
        ctx.fillStyle = isSelected ? '#52c41a' : '#1890ff'
        ctx.fillRect(x, y - 25, 80, 25)
        ctx.fillStyle = 'white'
        ctx.font = '14px Arial'
        ctx.fillText(`人脸 ${index + 1}`, x + 5, y - 8)
      })
    }
  }, [faces, selectedFaceIndex])

  const handleFaceClick = (index) => {
    setSelectedFaceIndex(index)
  }

  const handleConfirm = () => {
    if (selectedFaceIndex !== null) {
      onFaceSelect(faces[selectedFaceIndex])
    }
  }

  return (
    <div className="card">
      <h2>👤 人脸检测</h2>
      <p className="description">
        {loading ? '正在检测人脸...' : 
         faces.length > 1 ? '检测到多个人脸，请选择要搜索的人脸' :
         faces.length === 1 ? '检测到 1 个人脸' : ''}
      </p>

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>正在分析图片中的人脸...</p>
        </div>
      )}

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {!loading && !error && faces.length > 0 && (
        <>
          <div className="image-container">
            <img
              ref={imageRef}
              src={previewUrl}
              alt="上传的图片"
              className="preview-image"
              onLoad={() => {
                // 图片加载完成后重新绘制边界框
                if (canvasRef.current) {
                  const event = new Event('load')
                  imageRef.current.dispatchEvent(event)
                }
              }}
            />
            <canvas
              ref={canvasRef}
              className="face-canvas"
            />
          </div>

          {faces.length > 1 && (
            <div className="face-list">
              <p className="face-list-title">点击选择人脸：</p>
              <div className="face-items">
                {faces.map((face, index) => (
                  <div
                    key={face.faceId}
                    className={`face-item ${selectedFaceIndex === index ? 'selected' : ''}`}
                    onClick={() => handleFaceClick(index)}
                  >
                    <div className="face-number">{index + 1}</div>
                    <div className="face-info">
                      <div>人脸 {index + 1}</div>
                      <div className="face-size">
                        {face.boundingBox.width} × {face.boundingBox.height}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="button-group">
            <button className="button" onClick={onBack}>
              ← 返回上传
            </button>
            <button
              className="button button-primary"
              onClick={handleConfirm}
              disabled={selectedFaceIndex === null}
            >
              确认选择 →
            </button>
          </div>
        </>
      )}

      {!loading && error && (
        <div className="button-group">
          <button className="button" onClick={onBack}>
            ← 重新上传
          </button>
          <button className="button button-primary" onClick={detectFaces}>
            🔄 重新检测
          </button>
        </div>
      )}
    </div>
  )
}

export default FaceDetection
