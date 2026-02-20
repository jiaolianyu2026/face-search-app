import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './SearchProgress.css'

function SearchProgress({ taskId, onComplete }) {
  const [progress, setProgress] = useState({ current: 0, total: 0, percentage: 0 })
  const [status, setStatus] = useState('running')
  const [currentFile, setCurrentFile] = useState('')
  const [cancelling, setCancelling] = useState(false)
  const intervalRef = useRef(null)

  useEffect(() => {
    // 开始轮询搜索状态
    checkProgress()
    intervalRef.current = setInterval(checkProgress, 500) // 每500ms检查一次

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [taskId])

  const checkProgress = async () => {
    try {
      const response = await axios.get(`/api/search/${taskId}`)
      const data = response.data

      setStatus(data.status)
      setProgress(data.progress)
      setCurrentFile(data.progress.currentFile || '')

      // 如果搜索完成或取消，停止轮询
      if (data.status === 'completed' || data.status === 'cancelled') {
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
        }
        onComplete(data.results || [])
      }
    } catch (err) {
      console.error('获取进度错误:', err)
    }
  }

  const handleCancel = async () => {
    setCancelling(true)
    try {
      await axios.post(`/api/search/${taskId}/cancel`)
      // 取消成功后会在下次轮询时更新状态
    } catch (err) {
      console.error('取消搜索错误:', err)
      setCancelling(false)
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'pending':
        return '准备中...'
      case 'running':
        return '搜索中...'
      case 'completed':
        return '搜索完成'
      case 'cancelled':
        return '已取消'
      default:
        return '未知状态'
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'running':
        return '🔍'
      case 'completed':
        return '✅'
      case 'cancelled':
        return '⚠️'
      default:
        return '⏳'
    }
  }

  return (
    <div className="card">
      <h2>{getStatusIcon()} {getStatusText()}</h2>
      
      <div className="progress-info">
        <div className="progress-stats">
          <span className="stat-item">
            <strong>已处理：</strong>{progress.current} / {progress.total}
          </span>
          <span className="stat-item">
            <strong>进度：</strong>{progress.percentage.toFixed(1)}%
          </span>
        </div>

        {currentFile && status === 'running' && (
          <div className="current-file">
            <strong>当前文件：</strong>
            <span className="file-path">{currentFile}</span>
          </div>
        )}
      </div>

      <div className="progress-bar-container">
        <div
          className="progress-bar"
          style={{ width: `${progress.percentage}%` }}
        >
          <span className="progress-text">{progress.percentage.toFixed(1)}%</span>
        </div>
      </div>

      {status === 'running' && (
        <div className="button-group">
          <button
            className="button button-danger"
            onClick={handleCancel}
            disabled={cancelling}
          >
            {cancelling ? '正在取消...' : '⏹️ 取消搜索'}
          </button>
        </div>
      )}

      {status === 'cancelled' && (
        <div className="success-message">
          ℹ️ 搜索已取消，显示部分结果
        </div>
      )}
    </div>
  )
}

export default SearchProgress
