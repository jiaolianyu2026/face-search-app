import { useState, useEffect } from 'react'
import axios from 'axios'
import './FaceLibrary.css'

/**
 * FaceLibrary 组件
 * 显示人像库列表并提供管理操作
 * 
 * @param {Function} onSelectFaces - 选择人像回调函数，接收选中的人像 ID 数组
 * @param {Array} selectedFaceIds - 已选中的人像 ID 列表
 */
function FaceLibrary({ onSelectFaces, selectedFaceIds = [] }) {
  const [faces, setFaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [editingFaceId, setEditingFaceId] = useState(null)
  const [editingName, setEditingName] = useState('')
  const [deletingFaceId, setDeletingFaceId] = useState(null)
  const [loadedImages, setLoadedImages] = useState(new Set()) // 跟踪已加载的图片

  // 加载人像库列表
  const loadFaces = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = {
        sortBy: sortBy
      }
      
      if (searchQuery.trim()) {
        params.search = searchQuery.trim()
      }
      
      const response = await axios.get('/api/library/faces', { params })
      setFaces(response.data.faces || [])
    } catch (err) {
      console.error('加载人像库失败:', err)
      setError(err.response?.data?.error?.message || '加载人像库失败')
    } finally {
      setLoading(false)
    }
  }

  // 初始加载和搜索/排序变化时重新加载
  useEffect(() => {
    loadFaces()
  }, [searchQuery, sortBy])

  // 处理人像选择
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

    onSelectFaces(newSelection)
  }

  // 开始编辑名称
  const startEditing = (face) => {
    setEditingFaceId(face.id)
    setEditingName(face.name)
  }

  // 取消编辑
  const cancelEditing = () => {
    setEditingFaceId(null)
    setEditingName('')
  }

  // 保存编辑
  const saveEditing = async (faceId) => {
    if (!editingName.trim()) {
      alert('名称不能为空')
      return
    }

    if (editingName.length > 100) {
      alert('名称长度不能超过 100 字符')
      return
    }

    try {
      await axios.put(`/api/library/faces/${faceId}`, {
        name: editingName.trim()
      })
      
      // 更新本地状态
      setFaces(faces.map(face => 
        face.id === faceId ? { ...face, name: editingName.trim() } : face
      ))
      
      setEditingFaceId(null)
      setEditingName('')
    } catch (err) {
      console.error('更新名称失败:', err)
      alert(err.response?.data?.error?.message || '更新名称失败')
    }
  }

  // 开始删除确认
  const startDeleting = (faceId) => {
    setDeletingFaceId(faceId)
  }

  // 取消删除
  const cancelDeleting = () => {
    setDeletingFaceId(null)
  }

  // 确认删除
  const confirmDelete = async (faceId) => {
    try {
      await axios.delete(`/api/library/faces/${faceId}`)
      
      // 从本地状态中移除
      setFaces(faces.filter(face => face.id !== faceId))
      
      // 如果该人像被选中，也从选择中移除
      if (selectedFaceIds.includes(faceId)) {
        onSelectFaces(selectedFaceIds.filter(id => id !== faceId))
      }
      
      setDeletingFaceId(null)
    } catch (err) {
      console.error('删除人像失败:', err)
      alert(err.response?.data?.error?.message || '删除人像失败')
    }
  }

  // 处理图片加载完成
  const handleImageLoad = (faceId) => {
    setLoadedImages(prev => new Set([...prev, faceId]))
  }

  // 处理图片加载错误
  const handleImageError = (e) => {
    e.target.style.display = 'none'
    const placeholder = e.target.nextSibling
    if (placeholder) {
      placeholder.classList.remove('hidden')
    }
  }

  // 格式化时间戳
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="face-library">
        <div className="face-library-loading">
          <div className="face-library-loading-spinner"></div>
          <p>加载人像库中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="face-library">
        <div className="face-library-error">
          <div className="face-library-error-icon">❌</div>
          <p>{error}</p>
          <button className="button button-primary" onClick={loadFaces}>
            重新加载
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="face-library">
      {/* 工具栏 */}
      <div className="face-library-toolbar">
        <div className="face-library-search">
          <input
            type="text"
            className="input"
            placeholder="搜索人像名称..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <div className="face-library-sort">
          <label>排序：</label>
          <select
            className="select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="created_at">按时间</option>
            <option value="name">按名称</option>
          </select>
        </div>
      </div>

      {/* 选择提示 */}
      {selectedFaceIds.length > 0 && (
        <div className="face-library-selection-hint">
          <p>已选择 {selectedFaceIds.length} 个人像</p>
        </div>
      )}

      {/* 人像网格 */}
      {faces.length === 0 ? (
        <div className="face-library-empty">
          <div className="face-library-empty-icon">
            {searchQuery ? '🔍' : '📭'}
          </div>
          <div className="face-library-empty-title">
            {searchQuery ? '未找到匹配的人像' : '人像库为空'}
          </div>
          <div className="face-library-empty-hint">
            {searchQuery 
              ? '尝试使用不同的搜索关键词' 
              : '上传图片并检测人像后，可以将人像保存到库中以便将来使用'}
          </div>
        </div>
      ) : (
        <div className="face-library-grid">
          {faces.map((face) => {
            const isSelected = selectedFaceIds.includes(face.id)
            const isEditing = editingFaceId === face.id
            const isDeleting = deletingFaceId === face.id

            return (
              <div
                key={face.id}
                className={`face-library-item ${isSelected ? 'selected' : ''}`}
              >
                {/* 缩略图 */}
                <div
                  className="face-library-thumbnail"
                  onClick={() => !isEditing && !isDeleting && handleFaceClick(face.id)}
                >
                  {/* 占位符 - 在图片加载时显示 */}
                  <div className={`face-library-thumbnail-placeholder ${loadedImages.has(face.id) ? 'hidden' : ''}`}>
                    👤
                  </div>
                  
                  {/* 缩略图 */}
                  <img
                    src={face.thumbnailUrl}
                    alt={face.name}
                    className={loadedImages.has(face.id) ? 'loaded' : 'loading'}
                    onLoad={() => handleImageLoad(face.id)}
                    onError={handleImageError}
                    loading="lazy"
                  />
                  
                  {isSelected && (
                    <div className="face-library-selected-badge">
                      ✓
                    </div>
                  )}
                </div>

                {/* 信息区域 */}
                <div className="face-library-info">
                  {/* 名称编辑 */}
                  {isEditing ? (
                    <div className="face-library-edit">
                      <input
                        type="text"
                        className="input"
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            saveEditing(face.id)
                          } else if (e.key === 'Escape') {
                            cancelEditing()
                          }
                        }}
                        autoFocus
                      />
                      <div className="face-library-edit-actions">
                        <button
                          className="button button-small button-primary"
                          onClick={() => saveEditing(face.id)}
                        >
                          保存
                        </button>
                        <button
                          className="button button-small"
                          onClick={cancelEditing}
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="face-library-name" title={face.name}>
                        {face.name}
                      </div>
                      <div className="face-library-time">
                        {formatTimestamp(face.createdAt)}
                      </div>
                    </>
                  )}

                  {/* 操作按钮 */}
                  {!isEditing && !isDeleting && (
                    <div className="face-library-actions">
                      <button
                        className="button button-small"
                        onClick={() => startEditing(face)}
                        title="编辑名称"
                      >
                        ✏️
                      </button>
                      <button
                        className="button button-small button-danger"
                        onClick={() => startDeleting(face.id)}
                        title="删除"
                      >
                        🗑️
                      </button>
                    </div>
                  )}

                  {/* 删除确认 */}
                  {isDeleting && (
                    <div className="face-library-delete-confirm">
                      <p>确定删除？</p>
                      <div className="face-library-delete-actions">
                        <button
                          className="button button-small button-danger"
                          onClick={() => confirmDelete(face.id)}
                        >
                          确定
                        </button>
                        <button
                          className="button button-small"
                          onClick={cancelDeleting}
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default FaceLibrary
