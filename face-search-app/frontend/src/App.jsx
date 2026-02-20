import { useState } from 'react'
import './App.css'
import ImageUpload from './components/ImageUpload'
import FaceDetection from './components/FaceDetection'
import FolderSelection from './components/FolderSelection'
import SearchProgress from './components/SearchProgress'
import SearchResults from './components/SearchResults'

function App() {
  // 应用状态
  const [currentStep, setCurrentStep] = useState(1) // 1: 上传, 2: 检测, 3: 搜索, 4: 结果
  const [uploadedImage, setUploadedImage] = useState(null) // { imageId, previewUrl }
  const [selectedFace, setSelectedFace] = useState(null) // { faceId, features, boundingBox }
  const [searchFolder, setSearchFolder] = useState('')
  const [searchTask, setSearchTask] = useState(null) // { taskId, status, progress, results }

  // 处理图片上传成功
  const handleUploadSuccess = (imageData) => {
    setUploadedImage(imageData)
    setCurrentStep(2)
  }

  // 处理人脸选择
  const handleFaceSelect = (face) => {
    setSelectedFace(face)
    setCurrentStep(3)
  }

  // 处理搜索开始
  const handleSearchStart = (folder, taskData) => {
    setSearchFolder(folder)
    setSearchTask(taskData)
    setCurrentStep(4)
  }

  // 重新开始
  const handleReset = () => {
    setCurrentStep(1)
    setUploadedImage(null)
    setSelectedFace(null)
    setSearchFolder('')
    setSearchTask(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔍 人脸识别搜索应用</h1>
        <p>上传图片，识别人脸，搜索相似照片</p>
      </header>

      <div className="container">
        {/* 步骤指示器 */}
        <div className="steps">
          <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>
            <div className="step-number">1</div>
            <div className="step-title">上传图片</div>
          </div>
          <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
            <div className="step-number">2</div>
            <div className="step-title">检测人脸</div>
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

        {/* 步骤 1: 图片上传 */}
        {currentStep === 1 && (
          <ImageUpload onUploadSuccess={handleUploadSuccess} />
        )}

        {/* 步骤 2: 人脸检测 */}
        {currentStep === 2 && uploadedImage && (
          <FaceDetection
            imageId={uploadedImage.imageId}
            previewUrl={uploadedImage.previewUrl}
            onFaceSelect={handleFaceSelect}
            onBack={() => setCurrentStep(1)}
          />
        )}

        {/* 步骤 3: 文件夹选择 */}
        {currentStep === 3 && selectedFace && (
          <FolderSelection
            imageId={uploadedImage.imageId}
            faceId={selectedFace.faceId}
            onSearchStart={handleSearchStart}
            onBack={() => setCurrentStep(2)}
          />
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
