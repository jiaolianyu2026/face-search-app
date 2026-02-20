import { useState } from 'react'
import PropTypes from 'prop-types'
import './FaceLibraryItem.css'

/**
 * FaceLibraryItem 组件
 * 显示单个人像卡片，包含缩略图、名称、创建时间和操作按钮
 * 
 * @param {Object} face - 人像对象，包含 id, name, thumbnailUrl, createdAt
 * @param {boolean} isSelected - 是否被选中
 * @param {Function} onSelect - 选择回调函数
 * @param {Function} onEdit - 编辑回调函数，接收 faceId 和新名称
 * @param {Function} onDelete - 删除回调函数，接收 faceId
 */
function FaceLibraryItem({ face, isSelected, onSelect, onEdit, onDelete }) {
  const [isEditing, setIsEditing] = useState(false)
  const [editingName, setEditingName] = useState(face.name)
  const [isDeleting, setIsDeleting] = useState(false)

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

  // 开始编辑
  const startEditing = () => {
    setEditingName(face.name)
    setIsEditing(true)
  }

  // 取消编辑
  const cancelEditing = () => {
    setEditingName(face.name)
    setIsEditing(false)
  }

  // 保存编辑
  const saveEditing = () => {
    const trimmedName = editingName.trim()
    
    if (!trimmedName) {
      alert('名称不能为空')
      return
    }

    if (trimmedName.length > 100) {
      alert('名称长度不能超过 100 字符')
      return
    }

    onEdit(face.id, trimmedName)
    setIsEditing(false)
  }

  // 处理键盘事件
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      saveEditing()
    } else if (e.key === 'Escape') {
      cancelEditing()
    }
  }

  // 开始删除确认
  const startDeleting = () => {
    setIsDeleting(true)
  }

  // 取消删除
  const cancelDeleting = () => {
    setIsDeleting(false)
  }

  // 确认删除
  const confirmDelete = () => {
    onDelete(face.id)
    setIsDeleting(false)
  }

  // 处理缩略图点击
  const handleThumbnailClick = () => {
    if (!isEditing && !isDeleting) {
      onSelect(face.id)
    }
  }

  // 处理缩略图加载错误
  const handleImageError = (e) => {
    e.target.style.display = 'none'
    e.target.nextSibling.style.display = 'flex'
  }

  return (
    <div className={`face-library-item ${isSelected ? 'selected' : ''}`}>
      {/* 缩略图 */}
      <div
        className="face-library-item-thumbnail"
        onClick={handleThumbnailClick}
      >
        <img
          src={face.thumbnailUrl}
          alt={face.name}
          onError={handleImageError}
        />
        <div className="face-library-item-thumbnail-placeholder">
          👤
        </div>
        
        {isSelected && (
          <div className="face-library-item-selected-badge">
            ✓
          </div>
        )}
      </div>

      {/* 信息区域 */}
      <div className="face-library-item-info">
        {/* 名称编辑 */}
        {isEditing ? (
          <div className="face-library-item-edit">
            <input
              type="text"
              className="input"
              value={editingName}
              onChange={(e) => setEditingName(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
            />
            <div className="face-library-item-edit-actions">
              <button
                className="button button-small button-primary"
                onClick={saveEditing}
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
            <div className="face-library-item-name" title={face.name}>
              {face.name}
            </div>
            <div className="face-library-item-time">
              {formatTimestamp(face.createdAt)}
            </div>
          </>
        )}

        {/* 操作按钮 */}
        {!isEditing && !isDeleting && (
          <div className="face-library-item-actions">
            <button
              className="button button-small"
              onClick={startEditing}
              title="编辑名称"
            >
              ✏️
            </button>
            <button
              className="button button-small button-danger"
              onClick={startDeleting}
              title="删除"
            >
              🗑️
            </button>
          </div>
        )}

        {/* 删除确认 */}
        {isDeleting && (
          <div className="face-library-item-delete-confirm">
            <p>确定删除？</p>
            <div className="face-library-item-delete-actions">
              <button
                className="button button-small button-danger"
                onClick={confirmDelete}
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
}

FaceLibraryItem.propTypes = {
  face: PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    thumbnailUrl: PropTypes.string.isRequired,
    createdAt: PropTypes.number.isRequired
  }).isRequired,
  isSelected: PropTypes.bool.isRequired,
  onSelect: PropTypes.func.isRequired,
  onEdit: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired
}

export default FaceLibraryItem
