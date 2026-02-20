import './SearchModeSelector.css'

/**
 * SearchModeSelector 组件
 * 在上传新图片模式和历史人像模式之间切换
 * 
 * @param {string} mode - 当前模式：'upload' 或 'library'
 * @param {Function} onModeChange - 模式变化回调函数
 */
function SearchModeSelector({ mode, onModeChange }) {
  return (
    <div className="search-mode-selector">
      <div className="search-mode-tabs">
        <button
          className={`search-mode-tab ${mode === 'upload' ? 'active' : ''}`}
          onClick={() => onModeChange('upload')}
        >
          <span className="search-mode-icon">📤</span>
          <span className="search-mode-label">上传新图片</span>
        </button>
        
        <button
          className={`search-mode-tab ${mode === 'library' ? 'active' : ''}`}
          onClick={() => onModeChange('library')}
        >
          <span className="search-mode-icon">📚</span>
          <span className="search-mode-label">历史人像</span>
        </button>
      </div>
    </div>
  )
}

export default SearchModeSelector
