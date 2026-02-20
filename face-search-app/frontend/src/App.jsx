import { useState } from 'react'
import axios from 'axios'
import './App.css'
import ImageUpload from './components/ImageUpload'
import FaceDetection from './components/FaceDetection'
import FolderSelection from './components/FolderSelection'
import SearchProgress from './components/SearchProgress'
import SearchResults from './components/SearchResults'
import SearchModeSelector from './components/SearchModeSelector'
import FaceSelector from './components/FaceSelector'
import FaceLibrary from './components/FaceLibrary'

function App() {
  // 应用状态
  const [currentStep, setCurrentStep] = useState(1) // 1: 上传/选择, 2: 检测, 3: 搜索, 4: 结果
  const [searchMode, setSearchMode] = useState('upload') // 'upload' 或 'library'
  const [uploadedImage, setUploadedImage] = useState(null) // { imageId, previewUrl }
  const [detectedFaces, setDetectedFaces] = useState([]) // 检测到的人像列表
  const [selectedUploadedFaceIds, setSelectedUploadedFaceIds] = useState([]) // 从上传图片选择的人像 ID
  const [selectedLibraryFaceIds, setSelectedLibraryFaceIds] = useState([]) // 从人像库选择的人像 ID
  const [searchFolder, setSearchFolder] = useState('')
  const [searchTask, setSearchTask] = useState(null) // { taskId, status, progress, results }

  // 处理图片上传成功
  const handleUploadSuccess = (imageData) => {
    setUploadedImage(imageData)
    setCurrentStep(2)
  }

  // 处理人脸检测完成
  const handleFacesDetected = (faces) => {
    setDetectedFaces(faces)
  }

  // 处理上传图片中的人像选择变化
  const handleUploadedFaceSelectionChange = (faceIds) => {
    setSelectedUploadedFaceIds(faceIds)
  }

  // 处理人像库中的人像选择变化
  const handleLibraryFaceSelectionChange = (faceIds) => {
    setSelectedLibraryFaceIds(faceIds)
  }

  // 处理模式切换
  const handleModeChange = (mode) => {
    setSearchMode(mode)
  }

  // 保存人像到库
  const handleSaveToLibrary = async (face) => {
    const name = prompt('请输入人像名称：')
    if (!name || !name.trim()) {
      return
    }

    if (name.length > 100) {
      alert('名称长度不能超过 100 字符')
      return
    }

    try {
      const response = await axios.post('/api/library/faces', {
        imageId: uploadedImage.imageId,
        faceId: face.faceId,
        name: name.trim()
      })

      alert(`人像 "${name}" 已成功保存到库！`)
      
      // 保存成功后，可以选择将该人像添加到库选择中
      // 这样用户可以立即使用刚保存的人像进行搜索
      if (response.data && response.data.id) {
        // 可选：自动添加到选中的库人像列表
        // setSelectedLibraryFaceIds(prev => [...prev, response.data.id])
      }
    } catch (err) {
      console.error('保存人像失败:', err)
      const errorMessage = err.response?.data?.error?.message || '保存人像失败，请重试'
      alert(`错误: ${errorMessage}`)
    }
  }

  // 获取所有选中的人像（合并上传和库人像）
  const getAllSelectedFaces = () => {
    const targetFaces = []

    // 添加从上传图片选择的人像
    selectedUploadedFaceIds.forEach(faceId => {
      targetFaces.push({
        type: 'uploaded',
        imageId: uploadedImage.imageId,
        faceId: faceId
      })
    })

    // 添加从人像库选择的人像
    selectedLibraryFaceIds.forEach(libraryFaceId => {
      targetFaces.push({
        type: 'library',
        libraryFaceId: libraryFaceId
      })
    })

    return targetFaces
  }

  // 处理搜索开始
  const handleSearchStart = async (folder, threshold = 0.6) => {
    const targetFaces = getAllSelectedFaces()

    if (targetFaces.length === 0) {
      alert('请至少选择一个人像')
      return
    }

    try {
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
      setCurrentStep(4)
    } catch (err) {
      console.error('开始搜索失败:', err)
      alert(err.response?.data?.error?.message || '开始搜索失败')
    }
  }

  // 重新开始
  const handleReset = () => {
    setCurrentStep(1)
    setSearchMode('upload')
    setUploadedImage(null)
    setDetectedFaces([])
    setSelectedUploadedFaceIds([])
    setSelectedLibraryFaceIds([])
    setSearchFolder('')
    setSearchTask(null)
  }

  // 检查是否有选中的人像
  const hasSelectedFaces = () => {
    return selectedUploadedFaceIds.length > 0 || selectedLibraryFaceIds.length > 0
  }

  // 获取选中人像的总数
  const getSelectedFacesCount = () => {
    return selectedUploadedFaceIds.length + selectedLibraryFaceIds.length
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔍 人脸识别搜索应用</h1>
        <p>上传图片或从历史库选择人像，搜索相似照片</p>
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
            <div className="step-title">检测/选择</div>
          </div>
          <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>
            <div className="step-number">3</div>
            <div className="step-title">选择文件夹</div>
          </div>
          <div className={`step ${currentStep >= 4 ? 'active' : ''}`}>
            <div className="step-number">4</div>
            <div className="step-title">搜索结果</div>
          </div>
        </div>

        {/* 步骤 1: 模式选择和人像选择 */}
        {currentStep === 1 && (
          <div className="card">
            <h2>选择搜索模式</h2>
            
            {/* 模式选择器 */}
            <SearchModeSelector
              mode={searchMode}
              onModeChange={handleModeChange}
            />

            {/* 上传新图片模式 */}
            {searchMode === 'upload' && (
              <ImageUpload onUploadSuccess={handleUploadSuccess} />
            )}

            {/* 历史人像模式 */}
            {searchMode === 'library' && (
              <>
                <FaceLibrary
                  onSelectFaces={handleLibraryFaceSelectionChange}
                  selectedFaceIds={selectedLibraryFaceIds}
                />
                
                {selectedLibraryFaceIds.length > 0 && (
                  <div className="button-group" style={{ marginTop: '20px' }}>
                    <button
                      className="button button-primary"
                      onClick={() => setCurrentStep(3)}
                    >
                      继续搜索 ({selectedLibraryFaceIds.length} 个人像) →
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* 步骤 2: 人脸检测和选择 */}
        {currentStep === 2 && uploadedImage && (
          <div className="card">
            <h2>👤 人脸检测</h2>
            <p className="description">
              检测图片中的人像并选择要搜索的人像（支持多选）
            </p>

            <FaceDetection
              imageId={uploadedImage.imageId}
              previewUrl={uploadedImage.previewUrl}
              onFaceSelect={(face) => {
                // 兼容旧的单选接口，但不再使用
              }}
              onBack={() => setCurrentStep(1)}
              onFacesDetected={handleFacesDetected}
            />

            {/* 使用 FaceSelector 进行多选 */}
            {detectedFaces.length > 0 && (
              <>
                <div style={{ marginTop: '20px' }}>
                  <FaceSelector
                    imageUrl={uploadedImage.previewUrl}
                    faces={detectedFaces}
                    selectedFaceIds={selectedUploadedFaceIds}
                    onSelectionChange={handleUploadedFaceSelectionChange}
                  />
                </div>

                {/* 保存到库和继续搜索按钮 */}
                {selectedUploadedFaceIds.length > 0 && (
                  <div className="button-group" style={{ marginTop: '20px' }}>
                    <button
                      className="button"
                      onClick={() => {
                        const selectedFace = detectedFaces.find(
                          f => f.faceId === selectedUploadedFaceIds[0]
                        )
                        if (selectedFace) {
                          handleSaveToLibrary(selectedFace)
                        }
                      }}
                      disabled={selectedUploadedFaceIds.length !== 1}
                      title={selectedUploadedFaceIds.length !== 1 ? '请选择单个人像以保存到库' : '保存选中的人像到库以便将来使用'}
                    >
                      💾 保存到库
                    </button>
                    <button
                      className="button button-primary"
                      onClick={() => setCurrentStep(3)}
                    >
                      继续搜索 ({selectedUploadedFaceIds.length} 个人像) →
                    </button>
                  </div>
                )}
                
                {/* 提示信息 */}
                {selectedUploadedFaceIds.length === 0 && detectedFaces.length > 0 && (
                  <div className="info-hint info">
                    <p>
                      💡 提示：点击图片上的人像标记来选择要搜索的人像
                    </p>
                  </div>
                )}
                
                {selectedUploadedFaceIds.length > 1 && (
                  <div className="info-hint warning">
                    <p>
                      💡 提示：保存到库功能仅支持单个人像。如需保存多个人像，请逐个选择并保存。
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* 步骤 3: 文件夹选择 */}
        {currentStep === 3 && hasSelectedFaces() && (
          <div className="card">
            <h2>📁 选择搜索文件夹</h2>
            <p className="description">
              已选择 {getSelectedFacesCount()} 个人像
              {selectedUploadedFaceIds.length > 0 && ` (上传: ${selectedUploadedFaceIds.length})`}
              {selectedLibraryFaceIds.length > 0 && ` (库: ${selectedLibraryFaceIds.length})`}
            </p>

            <FolderSelection
              imageId={uploadedImage?.imageId}
              faceId={null} // 不再使用单个 faceId
              onSearchStart={handleSearchStart}
              onBack={() => setCurrentStep(searchMode === 'upload' ? 2 : 1)}
            />
          </div>
        )}

        {/* 步骤 4: 搜索进度和结果 */}
        {currentStep === 4 && searchTask && (
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
