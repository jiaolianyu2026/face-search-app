import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import './ImageUpload.css'

function ImageUpload({ onUploadSuccess }) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]
    
    // 验证文件大小 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('文件大小不能超过 10MB')
      return
    }

    // 验证文件格式
    const validTypes = ['image/jpeg', 'image/png', 'image/webp']
    if (!validTypes.includes(file.type)) {
      setError('只支持 JPEG、PNG 和 WebP 格式的图片')
      return
    }

    setError(null)
    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.data.success) {
        onUploadSuccess({
          imageId: response.data.imageId,
          previewUrl: response.data.previewUrl
        })
      } else {
        setError(response.data.error || '上传失败')
      }
    } catch (err) {
      console.error('上传错误:', err)
      if (err.response?.data?.error) {
        setError(err.response.data.error.message || '上传失败')
      } else {
        setError('上传失败，请检查网络连接')
      }
    } finally {
      setUploading(false)
    }
  }, [onUploadSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/webp': ['.webp']
    },
    multiple: false,
    disabled: uploading
  })

  return (
    <div className="card">
      <h2>📤 上传图片</h2>
      <p className="description">
        上传一张包含人脸的图片，支持 JPEG、PNG、WebP 格式，最大 10MB
      </p>

      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'disabled' : ''}`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="upload-status">
            <div className="spinner"></div>
            <p>正在上传...</p>
          </div>
        ) : isDragActive ? (
          <p>📥 松开鼠标上传图片</p>
        ) : (
          <>
            <div className="upload-icon">📷</div>
            <p>拖拽图片到这里，或点击选择文件</p>
            <p className="upload-hint">支持 JPG、PNG、WebP 格式，最大 10MB</p>
          </>
        )}
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}
    </div>
  )
}

export default ImageUpload
