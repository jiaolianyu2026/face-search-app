import { useState } from 'react'
import './FolderSelection.css'

function FolderSelection({ imageId, faceId, onSearchStart, onBack }) {
  const [folderPath, setFolderPath] = useState('')
  const [threshold, setThreshold] = useState(0.6)
  const [error, setError] = useState(null)

  const handleStartSearch = async () => {
    if (!folderPath.trim()) {
      setError('请输入文件夹路径')
      return
    }

    setError(null)
    
    // 直接调用父组件的回调，由父组件处理搜索逻辑
    onSearchStart(folderPath, threshold)
  }

  return (
    <div className="card">
      <h2>📁 选择搜索文件夹</h2>
      <p className="description">
        输入要搜索的文件夹路径，系统将在该文件夹及其子文件夹中搜索相似人脸
      </p>

      <div className="form-group">
        <label htmlFor="folderPath">文件夹路径：</label>
        <input
          id="folderPath"
          type="text"
          className="input"
          placeholder="例如: C:\Users\用户名\Pictures"
          value={folderPath}
          onChange={(e) => setFolderPath(e.target.value)}
        />
        <p className="input-hint">
          💡 提示：输入完整的文件夹路径，例如 D:\Photos 或 C:\Users\用户名\Pictures
        </p>
      </div>

      <div className="form-group">
        <label htmlFor="threshold">相似度阈值：</label>
        <div className="threshold-control">
          <input
            id="threshold"
            type="range"
            min="0.3"
            max="0.9"
            step="0.05"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            className="slider"
          />
          <span className="threshold-value">{threshold.toFixed(2)}</span>
        </div>
        <p className="input-hint">
          💡 阈值越高，匹配越严格。推荐值：0.6
        </p>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      <div className="button-group">
        <button
          className="button"
          onClick={onBack}
        >
          ← 返回
        </button>
        <button
          className="button button-primary"
          onClick={handleStartSearch}
          disabled={!folderPath.trim()}
        >
          🔍 开始搜索
        </button>
      </div>
    </div>
  )
}

export default FolderSelection
