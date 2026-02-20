import { useState } from 'react'
import axios from 'axios'
import './SearchResults.css'

function SearchResults({ results, onReset }) {
  const [selectedImages, setSelectedImages] = useState(new Set())
  const [exportFolder, setExportFolder] = useState('')
  const [exporting, setExporting] = useState(false)
  const [exportResult, setExportResult] = useState(null)
  const [viewingImage, setViewingImage] = useState(null)

  const handleSelectImage = (imagePath) => {
    const newSelected = new Set(selectedImages)
    if (newSelected.has(imagePath)) {
      newSelected.delete(imagePath)
    } else {
      newSelected.add(imagePath)
    }
    setSelectedImages(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedImages.size === results.length) {
      setSelectedImages(new Set())
    } else {
      setSelectedImages(new Set(results.map(r => r.imagePath)))
    }
  }

  const handleExport = async () => {
    if (selectedImages.size === 0) {
      alert('请先选择要转存的图片')
      return
    }

    if (!exportFolder.trim()) {
      alert('请输入目标文件夹路径')
      return
    }

    setExporting(true)
    setExportResult(null)

    try {
      // 第一次尝试：不创建文件夹
      const response = await axios.post('/api/export', {
        imagePaths: Array.from(selectedImages),
        targetFolder: exportFolder,
        createIfNotExists: false
      })

      setExportResult(response.data)
      
      // 如果文件夹是新创建的，显示提示
      if (response.data.folderCreated) {
        alert(`已创建文件夹并成功转存 ${response.data.successCount} 张图片`)
      }
    } catch (err) {
      console.error('转存错误:', err)
      
      // 检查是否是文件夹不存在的错误
      if (err.response?.status === 404 && 
          err.response?.data?.error?.type === 'folder') {
        // 询问用户是否创建文件夹
        const shouldCreate = window.confirm(
          `目标文件夹不存在：\n${exportFolder}\n\n是否创建该文件夹并继续转存？`
        )
        
        if (shouldCreate) {
          try {
            // 第二次尝试：创建文件夹
            const retryResponse = await axios.post('/api/export', {
              imagePaths: Array.from(selectedImages),
              targetFolder: exportFolder,
              createIfNotExists: true
            })
            
            setExportResult(retryResponse.data)
            
            if (retryResponse.data.folderCreated) {
              alert(`已创建文件夹并成功转存 ${retryResponse.data.successCount} 张图片`)
            }
          } catch (retryErr) {
            console.error('重试转存错误:', retryErr)
            alert('转存失败：' + (retryErr.response?.data?.error?.message || '未知错误'))
          }
        }
      } else {
        // 其他错误直接显示
        alert('转存失败：' + (err.response?.data?.error?.message || '未知错误'))
      }
    } finally {
      setExporting(false)
    }
  }

  if (results.length === 0) {
    return (
      <div className="card">
        <h2>📭 未找到匹配结果</h2>
        <p className="description">
          在指定文件夹中没有找到相似的人脸，请尝试：
        </p>
        <ul className="suggestions">
          <li>降低相似度阈值</li>
          <li>选择包含更多照片的文件夹</li>
          <li>确保文件夹中的照片包含清晰的人脸</li>
        </ul>
        <div className="button-group">
          <button className="button button-primary" onClick={onReset}>
            🔄 重新开始
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <h2>🎯 搜索结果</h2>
      <p className="description">
        找到 {results.length} 个匹配的图片，相似度从高到低排序
      </p>

      <div className="results-header">
        <button
          className="button"
          onClick={handleSelectAll}
        >
          {selectedImages.size === results.length ? '取消全选' : '全选'}
        </button>
        <span className="selected-count">
          已选择 {selectedImages.size} / {results.length} 张图片
        </span>
      </div>

      <div className="results-grid">
        {results.map((result, index) => (
          <div
            key={index}
            className={`result-item ${selectedImages.has(result.imagePath) ? 'selected' : ''}`}
          >
            <div className="result-checkbox">
              <input
                type="checkbox"
                checked={selectedImages.has(result.imagePath)}
                onChange={() => handleSelectImage(result.imagePath)}
              />
            </div>
            <div
              className="result-image-container"
              onClick={() => setViewingImage(result)}
            >
              <div className="result-placeholder">
                🖼️
                <p>点击查看</p>
              </div>
              <div className="result-similarity">
                {(result.similarity * 100).toFixed(1)}%
              </div>
            </div>
            <div className="result-info">
              <div className="result-path" title={result.imagePath}>
                {result.imagePath.split('\\').pop() || result.imagePath.split('/').pop()}
              </div>
              <div className="result-full-path" title={result.imagePath}>
                {result.imagePath}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 转存功能 */}
      <div className="export-section">
        <h3>📦 转存选中的图片</h3>
        <div className="export-controls">
          <input
            type="text"
            className="input"
            placeholder="输入目标文件夹路径，例如: D:\ExportedPhotos"
            value={exportFolder}
            onChange={(e) => setExportFolder(e.target.value)}
            disabled={exporting}
          />
          <button
            className="button button-primary"
            onClick={handleExport}
            disabled={exporting || selectedImages.size === 0 || !exportFolder.trim()}
          >
            {exporting ? '转存中...' : `转存 ${selectedImages.size} 张图片`}
          </button>
        </div>

        {exportResult && (
          <div className={exportResult.failedCount > 0 ? 'error-message' : 'success-message'}>
            {exportResult.successCount > 0 && (
              <p>✅ 成功转存 {exportResult.successCount} 张图片</p>
            )}
            {exportResult.failedCount > 0 && (
              <p>❌ 失败 {exportResult.failedCount} 张图片</p>
            )}
          </div>
        )}
      </div>

      <div className="button-group">
        <button className="button button-primary" onClick={onReset}>
          🔄 重新开始
        </button>
      </div>

      {/* 图片查看器 */}
      {viewingImage && (
        <div className="image-viewer" onClick={() => setViewingImage(null)}>
          <div className="viewer-content" onClick={(e) => e.stopPropagation()}>
            <button className="viewer-close" onClick={() => setViewingImage(null)}>
              ✕
            </button>
            <div className="viewer-info">
              <h3>相似度: {(viewingImage.similarity * 100).toFixed(1)}%</h3>
              <p>{viewingImage.imagePath}</p>
            </div>
            <div className="viewer-placeholder">
              <p>🖼️ 图片预览</p>
              <p className="viewer-hint">（实际应用中这里会显示图片）</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SearchResults
