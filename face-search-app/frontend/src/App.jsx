import { useState } from 'react'
import axios from 'axios'
import './App.css'
import UnifiedFaceSelector from './components/UnifiedFaceSelector'
import FolderSelection from './components/FolderSelection'
import SearchProgress from './components/SearchProgress'
import SearchResults from './components/SearchResults'

function App() {
  // 应用状态
  const [currentStep, setCurrentStep] = useState(1) // 1: 人像选择, 2: 文件夹选择, 3: 搜索结果
  const [selectedFaces, setSelectedFaces] = useState(null) // 选中的人像数据
  const [searchFolder, setSearchFolder] = useState('')
  const [searchTask, setSearchTask] = useState(null) // { taskId, status, progress, results }

  // 错误处理
  const handleError = (error) => {
    console.error('错误:', error)
    
    // 提取错误消息
    let message = '操作失败，请重试'
    
    if (error.response?.data) {
      // Axios 错误响应
      const data = error.response.data
      if (typeof data === 'string') {
        message = data
      } else if (data.error) {
        message = typeof data.error === 'string' ? data.error : data.error.message || JSON.stringify(data.error)
      } else if (data.message) {
        message = data.message
      }
    } else if (error.message) {
      // 标准 Error 对象
      message = error.message
    } else if (typeof error === 'string') {
      // 字符串错误
      message = error
    } else {
      // 其他类型，尝试转换为字符串
      try {
        message = JSON.stringify(error)
      } catch {
        message = String(error)
      }
    }
    
    alert(message) // 暂时使用 alert，后续可以改为 Toast
  }

  // 成功提示
  const handleSuccess = (message) => {
    console.log('成功:', message)
    // 暂时不显示成功提示，避免过多弹窗
  }

  // 处理开始搜索
  const handleStartSearch = async (selection) => {
    setSelectedFaces(selection)
    setCurrentStep(2)
  }

  // 处理文件夹搜索
  // 默认阈值 0.5 对应 face_recognition 欧氏距离 0.5（更严格的匹配阈值）
  const handleFolderSearchStart = async (folder, threshold = 0.5) => {
    if (!selectedFaces) {
      alert('请先选择人像')
      return
    }

    try {
      // 构建搜索请求
      const targetFaces = []
      
      // 添加上传的人像
      selectedFaces.uploadedFaces.forEach(face => {
        const parts = face.faceId.split(':')
        targetFaces.push({
          type: 'uploaded',
          imageId: parts[0],
          faceId: parts[1] || parts[0]
        })
      })
      
      // 添加库中的人像
      selectedFaces.libraryFaces.forEach(libraryFaceId => {
        targetFaces.push({
          type: 'library',
          libraryFaceId: libraryFaceId
        })
      })

      if (targetFaces.length === 0) {
        alert('请选择至少一个人像')
        return
      }

      // 调用搜索 API
      const response = await axios.post('/api/search', {
        targetFaces: targetFaces,
        searchFolder: folder,
        threshold: threshold
      })

      setSearchFolder(folder)
      setSearchTask({
        taskId: response.data.taskId,
        status: response.data.status
      })
      setCurrentStep(3)
      console.log('搜索已启动')
    } catch (err) {
      console.error('开始搜索失败:', err)
      handleError(err)
    }
  }

  // 重新开始
  const handleReset = () => {
    setCurrentStep(1)
    setSelectedFaces(null)
    setSearchFolder('')
    setSearchTask(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔍 忆颜图谱 - 人脸识别搜索</h1>
        <p>统一人像选择界面 - 上传新图片或从历史库选择人像进行搜索</p>
      </header>

      <div className="container">
        {/* 步骤指示器 */}
        <div className="steps">
          <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>
            <div className="step-number">1</div>
            <div className="step-title">选择人像</div>
          </div>
          <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
            <div className="step-number">2</div>
            <div className="step-title">选择文件夹</div>
          </div>
          <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>
            <div className="step-number">3</div>
            <div className="step-title">搜索结果</div>
          </div>
        </div>

        {/* 步骤 1: 统一人像选择界面 */}
        {currentStep === 1 && (
          <div className="card">
            <UnifiedFaceSelector
              onStartSearch={handleStartSearch}
              onError={handleError}
              onSuccess={handleSuccess}
            />
          </div>
        )}

        {/* 步骤 2: 文件夹选择 */}
        {currentStep === 2 && selectedFaces && (
          <div className="card">
            <h2>📁 选择搜索文件夹</h2>
            <p className="description">
              已选择 {selectedFaces.uploadedFaces.length + selectedFaces.libraryFaces.length} 个人像
              {selectedFaces.uploadedFaces.length > 0 && ` (新上传: ${selectedFaces.uploadedFaces.length})`}
              {selectedFaces.libraryFaces.length > 0 && ` (历史库: ${selectedFaces.libraryFaces.length})`}
            </p>

            <FolderSelection
              imageId={null}
              faceId={null}
              onSearchStart={handleFolderSearchStart}
              onBack={() => setCurrentStep(1)}
            />
          </div>
        )}

        {/* 步骤 3: 搜索进度和结果 */}
        {currentStep === 3 && searchTask && (
          <>
            <SearchProgress
              taskId={searchTask.taskId}
              onComplete={(results) => setSearchTask({ ...searchTask, results })}
            />
            {searchTask.results && (
              <SearchResults
                results={searchTask.results}
                onReset={handleReset}
              />
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default App
