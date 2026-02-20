/**
 * FaceSelector 组件使用示例
 * 
 * 这个文件展示了如何在应用中使用 FaceSelector 组件
 */

import { useState } from 'react'
import FaceSelector from './FaceSelector'

function FaceSelectorExample() {
  // 示例人像数据
  const exampleFaces = [
    {
      faceId: 'face-1',
      boundingBox: { x: 100, y: 50, width: 150, height: 150 }
    },
    {
      faceId: 'face-2',
      boundingBox: { x: 300, y: 80, width: 120, height: 120 }
    },
    {
      faceId: 'face-3',
      boundingBox: { x: 500, y: 100, width: 140, height: 140 }
    }
  ]

  const [selectedFaceIds, setSelectedFaceIds] = useState([])

  const handleSelectionChange = (newSelection) => {
    console.log('选择变化:', newSelection)
    setSelectedFaceIds(newSelection)
  }

  return (
    <div>
      <h2>人像选择器示例</h2>
      
      <FaceSelector
        imageUrl="/path/to/your/image.jpg"
        faces={exampleFaces}
        selectedFaceIds={selectedFaceIds}
        onSelectionChange={handleSelectionChange}
      />

      <div style={{ marginTop: '20px' }}>
        <h3>已选择的人像 ID:</h3>
        <pre>{JSON.stringify(selectedFaceIds, null, 2)}</pre>
      </div>

      <div style={{ marginTop: '20px' }}>
        <button onClick={() => setSelectedFaceIds([])}>
          清除所有选择
        </button>
        <button onClick={() => setSelectedFaceIds(exampleFaces.map(f => f.faceId))}>
          全选
        </button>
      </div>
    </div>
  )
}

export default FaceSelectorExample

/**
 * 集成到 FaceDetection 组件的示例：
 * 
 * import FaceSelector from './FaceSelector'
 * 
 * function FaceDetection({ imageId, previewUrl, onFaceSelect, onBack }) {
 *   const [faces, setFaces] = useState([])
 *   const [selectedFaceIds, setSelectedFaceIds] = useState([])
 * 
 *   // ... 检测逻辑 ...
 * 
 *   return (
 *     <div className="card">
 *       <h2>👤 人脸检测</h2>
 *       
 *       <FaceSelector
 *         imageUrl={previewUrl}
 *         faces={faces}
 *         selectedFaceIds={selectedFaceIds}
 *         onSelectionChange={setSelectedFaceIds}
 *       />
 * 
 *       <div className="button-group">
 *         <button onClick={onBack}>返回</button>
 *         <button 
 *           onClick={() => onFaceSelect(selectedFaceIds)}
 *           disabled={selectedFaceIds.length === 0}
 *         >
 *           确认选择 ({selectedFaceIds.length})
 *         </button>
 *       </div>
 *     </div>
 *   )
 * }
 */
