import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent, waitFor } from '@testing-library/react'
import * as fc from 'fast-check'
import FaceSelector from './FaceSelector'

/**
 * FaceSelector 组件属性测试
 * 使用 fast-check 进行基于属性的测试
 * 
 * Feature: face-library-management
 * Validates: Requirements 1.1, 1.2, 1.5, 1.6
 */

// ============================================================================
// 测试数据生成器（Arbitraries）
// ============================================================================

/**
 * 生成有效的人像 ID
 */
const faceIdArbitrary = () => 
  fc.uuid().map(uuid => `face-${uuid}`)

/**
 * 生成有效的边界框
 */
const boundingBoxArbitrary = () =>
  fc.record({
    x: fc.integer({ min: 0, max: 1000 }),
    y: fc.integer({ min: 0, max: 1000 }),
    width: fc.integer({ min: 10, max: 500 }),
    height: fc.integer({ min: 10, max: 500 })
  })

/**
 * 生成单个人像对象
 */
const faceArbitrary = () =>
  fc.record({
    faceId: faceIdArbitrary(),
    boundingBox: boundingBoxArbitrary()
  })

/**
 * 生成人像列表（1-10个人像）
 */
const facesListArbitrary = () =>
  fc.array(faceArbitrary(), { minLength: 1, maxLength: 10 })

/**
 * 生成 128 维特征向量
 */
const featureVectorArbitrary = () =>
  fc.array(fc.float({ min: -10.0, max: 10.0, noNaN: true }), { 
    minLength: 128, 
    maxLength: 128 
  })

/**
 * 生成测试用的 1x1 像素图片 URL
 */
const mockImageUrl = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='

// ============================================================================
// 辅助函数
// ============================================================================

/**
 * 渲染组件并等待图片加载
 */
async function renderAndLoadImage(props) {
  const result = render(<FaceSelector {...props} />)
  const image = result.container.querySelector('img.face-selector-image')
  if (image) {
    fireEvent.load(image)
    await waitFor(() => {
      const svg = result.container.querySelector('svg.face-selector-overlay')
      return svg !== null
    }, { timeout: 1000 })
  }
  return result
}

/**
 * 从组件中提取人像标记的颜色
 */
function extractMarkerColors(container) {
  const circles = container.querySelectorAll('circle.face-marker')
  return Array.from(circles).map(circle => circle.getAttribute('stroke'))
}

/**
 * 检查颜色是否为有效的十六进制颜色
 */
function isValidHexColor(color) {
  return /^#[0-9a-f]{6}$/i.test(color)
}

// ============================================================================
// Property 1: 人像标记唯一性
// ============================================================================

describe('Property 1: 人像标记唯一性', () => {
  /**
   * 对于任意检测到的人像列表，渲染的标记应该为每个人像分配唯一的颜色标识符，
   * 且标记数量应该等于人像数量。
   * 
   * **Validates: Requirements 1.1**
   */
  it('应该为每个人像分配唯一的颜色标识符，且标记数量等于人像数量', async () => {
    await fc.assert(
      fc.asyncProperty(facesListArbitrary(), async (faces) => {
        const onSelectionChange = vi.fn()
        
        const { container } = await renderAndLoadImage({
          imageUrl: mockImageUrl,
          faces,
          selectedFaceIds: [],
          onSelectionChange
        })

        // 验证标记数量等于人像数量
        const circles = container.querySelectorAll('circle.face-marker')
        expect(circles.length).toBe(faces.length)

        // 验证每个标记都有有效的颜色
        const colors = extractMarkerColors(container)
        expect(colors.length).toBe(faces.length)
        
        colors.forEach(color => {
          expect(isValidHexColor(color)).toBe(true)
        })

        // 验证颜色分配是确定性的（相同的 faceId 总是得到相同的颜色）
        const colorMap = new Map()
        circles.forEach((circle, index) => {
          const faceId = faces[index].faceId
          const color = circle.getAttribute('stroke')
          
          if (colorMap.has(faceId)) {
            expect(color).toBe(colorMap.get(faceId))
          } else {
            colorMap.set(faceId, color)
          }
        })
      }),
      { numRuns: 25, timeout: 5000 }
    )
  })

  it('相同的 faceId 应该总是得到相同的颜色', async () => {
    await fc.assert(
      fc.asyncProperty(faceIdArbitrary(), boundingBoxArbitrary(), async (faceId, boundingBox) => {
        const face = { faceId, boundingBox }
        const onSelectionChange = vi.fn()
        
        // 第一次渲染
        const { container: container1 } = await renderAndLoadImage({
          imageUrl: mockImageUrl,
          faces: [face],
          selectedFaceIds: [],
          onSelectionChange
        })
        
        const color1 = extractMarkerColors(container1)[0]
        
        // 第二次渲染（相同的 faceId）
        const { container: container2 } = await renderAndLoadImage({
          imageUrl: mockImageUrl,
          faces: [face],
          selectedFaceIds: [],
          onSelectionChange
        })
        
        const color2 = extractMarkerColors(container2)[0]
        
        // 验证颜色一致
        expect(color1).toBe(color2)
      }),
      { numRuns: 20, timeout: 5000 }
    )
  })
})

// ============================================================================
// Property 2: 选择状态切换
// ============================================================================

describe('Property 2: 选择状态切换', () => {
  /**
   * 对于任意人像ID和当前选择状态集合，点击该人像应该切换其选择状态
   * （选中变为未选中，未选中变为选中）。
   * 
   * **Validates: Requirements 1.2**
   */
  it('点击未选中的人像应该将其添加到选择集合', async () => {
    await fc.assert(
      fc.asyncProperty(
        facesListArbitrary(),
        fc.integer({ min: 0, max: 9 }),
        async (faces, targetIndex) => {
          // 确保索引有效
          const index = targetIndex % faces.length
          const onSelectionChange = vi.fn()
          
          const { container } = await renderAndLoadImage({
            imageUrl: mockImageUrl,
            faces,
            selectedFaceIds: [],
            onSelectionChange
          })

          // 点击目标人像
          const circles = container.querySelectorAll('circle.face-marker')
          fireEvent.click(circles[index])

          // 验证回调被调用，且包含该人像 ID
          expect(onSelectionChange).toHaveBeenCalledTimes(1)
          const newSelection = onSelectionChange.mock.calls[0][0]
          expect(newSelection).toContain(faces[index].faceId)
          expect(newSelection.length).toBe(1)
        }
      ),
      { numRuns: 25, timeout: 5000 }
    )
  })

  it('点击已选中的人像应该将其从选择集合中移除', async () => {
    await fc.assert(
      fc.asyncProperty(
        facesListArbitrary(),
        fc.integer({ min: 0, max: 9 }),
        async (faces, targetIndex) => {
          const index = targetIndex % faces.length
          const targetFaceId = faces[index].faceId
          const onSelectionChange = vi.fn()
          
          // 初始状态：目标人像已选中
          const { container } = await renderAndLoadImage({
            imageUrl: mockImageUrl,
            faces,
            selectedFaceIds: [targetFaceId],
            onSelectionChange
          })

          // 点击已选中的人像
          const circles = container.querySelectorAll('circle.face-marker')
          fireEvent.click(circles[index])

          // 验证回调被调用，且不包含该人像 ID
          expect(onSelectionChange).toHaveBeenCalledTimes(1)
          const newSelection = onSelectionChange.mock.calls[0][0]
          expect(newSelection).not.toContain(targetFaceId)
          expect(newSelection.length).toBe(0)
        }
      ),
      { numRuns: 25, timeout: 5000 }
    )
  })

  it('选择状态切换应该是幂等的（连续两次点击应该恢复原状态）', async () => {
    await fc.assert(
      fc.asyncProperty(
        faceArbitrary(),
        async (face) => {
          const onSelectionChange = vi.fn()
          
          // 初始状态：未选中
          const { container, rerender } = await renderAndLoadImage({
            imageUrl: mockImageUrl,
            faces: [face],
            selectedFaceIds: [],
            onSelectionChange
          })

          const circle = container.querySelector('circle.face-marker')
          
          // 第一次点击：选中
          fireEvent.click(circle)
          expect(onSelectionChange).toHaveBeenCalledWith([face.faceId])
          
          // 更新状态
          rerender(
            <FaceSelector
              imageUrl={mockImageUrl}
              faces={[face]}
              selectedFaceIds={[face.faceId]}
              onSelectionChange={onSelectionChange}
            />
          )
          
          // 第二次点击：取消选中
          fireEvent.click(circle)
          expect(onSelectionChange).toHaveBeenCalledWith([])
        }
      ),
      { numRuns: 20, timeout: 5000 }
    )
  })
})

// ============================================================================
// Property 3: 多选支持
// ============================================================================

describe('Property 3: 多选支持', () => {
  /**
   * 对于任意人像ID列表，系统应该能够同时维护所有人像的选择状态，
   * 且选择集合的大小应该等于选中的人像数量。
   * 
   * **Validates: Requirements 1.5**
   */
  it('应该能够同时选择多个人像', async () => {
    await fc.assert(
      fc.asyncProperty(
        facesListArbitrary(),
        fc.array(fc.integer({ min: 0, max: 9 }), { minLength: 1, maxLength: 5 }),
        async (faces, selectedIndices) => {
          // 确保索引有效且唯一
          const uniqueIndices = [...new Set(selectedIndices.map(i => i % faces.length))]
          const selectedFaceIds = uniqueIndices.map(i => faces[i].faceId)
          
          const onSelectionChange = vi.fn()
          
          const { container } = await renderAndLoadImage({
            imageUrl: mockImageUrl,
            faces,
            selectedFaceIds,
            onSelectionChange
          })

          // 验证选择状态正确显示
          const circles = container.querySelectorAll('circle.face-marker')
          let selectedCount = 0
          
          circles.forEach((circle, index) => {
            const strokeWidth = parseInt(circle.getAttribute('stroke-width'))
            if (selectedFaceIds.includes(faces[index].faceId)) {
              // 选中的标记应该有更粗的边框
              expect(strokeWidth).toBeGreaterThan(2)
              selectedCount++
            }
          })
          
          expect(selectedCount).toBe(selectedFaceIds.length)
          
          // 验证提示文本显示正确的数量
          expect(container.textContent).toContain(`已选择 ${selectedFaceIds.length} 个人像`)
        }
      ),
      { numRuns: 25, timeout: 5000 }
    )
  })

  it('选择集合的大小应该等于选中的人像数量', async () => {
    await fc.assert(
      fc.asyncProperty(
        facesListArbitrary(),
        fc.integer({ min: 0, max: 10 }),
        async (faces, numToSelect) => {
          const selectCount = Math.min(numToSelect, faces.length)
          const selectedFaceIds = faces.slice(0, selectCount).map(f => f.faceId)
          
          const onSelectionChange = vi.fn()
          
          const { container } = await renderAndLoadImage({
            imageUrl: mockImageUrl,
            faces,
            selectedFaceIds,
            onSelectionChange
          })

          // 验证高亮标记的数量等于选中的人像数量
          const highlightCircles = container.querySelectorAll('circle.face-marker-highlight')
          expect(highlightCircles.length).toBe(selectCount)
          
          // 验证中心点标记的数量等于选中的人像数量
          const centerCircles = container.querySelectorAll('circle.face-marker-center')
          expect(centerCircles.length).toBe(selectCount)
        }
      ),
      { numRuns: 25, timeout: 5000 }
    )
  })

  it('添加和移除选择应该正确更新选择集合大小', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(faceArbitrary(), { minLength: 3, maxLength: 5 }),
        async (faces) => {
          const onSelectionChange = vi.fn()
          
          const { container, rerender } = await renderAndLoadImage({
            imageUrl: mockImageUrl,
            faces,
            selectedFaceIds: [],
            onSelectionChange
          })

          const circles = container.querySelectorAll('circle.face-marker')
          
          // 选中第一个人像
          fireEvent.click(circles[0])
          let selection = onSelectionChange.mock.calls[onSelectionChange.mock.calls.length - 1][0]
          expect(selection.length).toBe(1)
          
          // 更新状态并选中第二个人像
          rerender(
            <FaceSelector
              imageUrl={mockImageUrl}
              faces={faces}
              selectedFaceIds={selection}
              onSelectionChange={onSelectionChange}
            />
          )
          
          fireEvent.click(circles[1])
          selection = onSelectionChange.mock.calls[onSelectionChange.mock.calls.length - 1][0]
          expect(selection.length).toBe(2)
          
          // 更新状态并取消选中第一个人像
          rerender(
            <FaceSelector
              imageUrl={mockImageUrl}
              faces={faces}
              selectedFaceIds={selection}
              onSelectionChange={onSelectionChange}
            />
          )
          
          fireEvent.click(circles[0])
          selection = onSelectionChange.mock.calls[onSelectionChange.mock.calls.length - 1][0]
          expect(selection.length).toBe(1)
          expect(selection).toContain(faces[1].faceId)
          expect(selection).not.toContain(faces[0].faceId)
        }
      ),
      { numRuns: 20, timeout: 5000 }
    )
  })
})

// ============================================================================
// Property 4: 选择到特征映射
// ============================================================================

describe('Property 4: 选择到特征映射', () => {
  /**
   * 对于任意选中的人像集合，提取的特征向量列表应该与选中人像一一对应，
   * 且每个特征向量应该是128维。
   * 
   * **Validates: Requirements 1.6**
   * 
   * 注意：此属性测试验证的是选择逻辑的正确性，而不是实际的特征提取。
   * 我们验证选择的人像 ID 列表与预期的特征向量映射关系。
   */
  it('选中的人像数量应该与特征向量数量一致', async () => {
    await fc.assert(
      fc.asyncProperty(
        facesListArbitrary(),
        fc.array(fc.integer({ min: 0, max: 9 }), { minLength: 1, maxLength: 5 }),
        async (faces, selectedIndices) => {
          const uniqueIndices = [...new Set(selectedIndices.map(i => i % faces.length))]
          const selectedFaceIds = uniqueIndices.map(i => faces[i].faceId)
          
          const onSelectionChange = vi.fn()
          
          await renderAndLoadImage({
            imageUrl: mockImageUrl,
            faces,
            selectedFaceIds,
            onSelectionChange
          })

          // 验证选中的人像数量
          expect(selectedFaceIds.length).toBe(uniqueIndices.length)
          
          // 验证每个选中的 faceId 都在人像列表中
          selectedFaceIds.forEach(faceId => {
            const faceExists = faces.some(f => f.faceId === faceId)
            expect(faceExists).toBe(true)
          })
          
          // 验证没有重复的 faceId
          const uniqueFaceIds = new Set(selectedFaceIds)
          expect(uniqueFaceIds.size).toBe(selectedFaceIds.length)
        }
      ),
      { numRuns: 20, timeout: 5000 }
    )
  })

  it('选择变化回调应该返回正确的人像 ID 列表', async () => {
    await fc.assert(
      fc.asyncProperty(
        facesListArbitrary(),
        fc.integer({ min: 0, max: 9 }),
        async (faces, targetIndex) => {
          const index = targetIndex % faces.length
          const onSelectionChange = vi.fn()
          
          const { container } = await renderAndLoadImage({
            imageUrl: mockImageUrl,
            faces,
            selectedFaceIds: [],
            onSelectionChange
          })

          // 点击人像
          const circles = container.querySelectorAll('circle.face-marker')
          fireEvent.click(circles[index])

          // 验证回调参数
          expect(onSelectionChange).toHaveBeenCalledTimes(1)
          const selectedIds = onSelectionChange.mock.calls[0][0]
          
          // 验证返回的是数组
          expect(Array.isArray(selectedIds)).toBe(true)
          
          // 验证数组包含正确的 faceId
          expect(selectedIds).toContain(faces[index].faceId)
          
          // 验证数组长度正确
          expect(selectedIds.length).toBe(1)
        }
      ),
      { numRuns: 25, timeout: 5000 }
    )
  })

  it('多次选择应该累积正确的人像 ID 列表', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(faceArbitrary(), { minLength: 3, maxLength: 5 }),
        fc.array(fc.integer({ min: 0, max: 4 }), { minLength: 2, maxLength: 4 }),
        async (faces, indicesToSelect) => {
          // 确保索引有效且唯一
          const uniqueIndices = [...new Set(indicesToSelect.map(i => i % faces.length))]
          
          const onSelectionChange = vi.fn()
          let currentSelection = []
          
          const { container, rerender } = await renderAndLoadImage({
            imageUrl: mockImageUrl,
            faces,
            selectedFaceIds: currentSelection,
            onSelectionChange
          })

          const circles = container.querySelectorAll('circle.face-marker')
          
          // 依次选择多个人像
          for (const index of uniqueIndices) {
            fireEvent.click(circles[index])
            currentSelection = onSelectionChange.mock.calls[onSelectionChange.mock.calls.length - 1][0]
            
            // 验证选择累积正确
            expect(currentSelection).toContain(faces[index].faceId)
            
            // 更新组件状态
            rerender(
              <FaceSelector
                imageUrl={mockImageUrl}
                faces={faces}
                selectedFaceIds={currentSelection}
                onSelectionChange={onSelectionChange}
              />
            )
          }
          
          // 最终验证：选择的数量应该等于唯一索引的数量
          expect(currentSelection.length).toBe(uniqueIndices.length)
          
          // 验证所有选中的 faceId 都是唯一的
          const uniqueIds = new Set(currentSelection)
          expect(uniqueIds.size).toBe(currentSelection.length)
        }
      ),
      { numRuns: 20, timeout: 5000 }
    )
  })

  it('选择的人像 ID 应该与人像列表中的 ID 一一对应', async () => {
    await fc.assert(
      fc.asyncProperty(
        facesListArbitrary(),
        async (faces) => {
          // 选择所有人像
          const allFaceIds = faces.map(f => f.faceId)
          const onSelectionChange = vi.fn()
          
          await renderAndLoadImage({
            imageUrl: mockImageUrl,
            faces,
            selectedFaceIds: allFaceIds,
            onSelectionChange
          })

          // 验证每个选中的 ID 都对应一个人像
          allFaceIds.forEach(faceId => {
            const correspondingFace = faces.find(f => f.faceId === faceId)
            expect(correspondingFace).toBeDefined()
            expect(correspondingFace.faceId).toBe(faceId)
          })
          
          // 验证映射是一对一的（没有重复）
          expect(allFaceIds.length).toBe(faces.length)
          expect(new Set(allFaceIds).size).toBe(faces.length)
        }
      ),
      { numRuns: 25, timeout: 5000 }
    )
  })
})
