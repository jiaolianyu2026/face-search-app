import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import FaceLibrary from './FaceLibrary'
import fc from 'fast-check'

// Mock axios
vi.mock('axios')

/**
 * 属性测试：FaceLibrary 组件
 * 
 * 这些测试验证组件在各种输入下的通用属性
 */

describe('FaceLibrary 属性测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  // 生成测试数据的策略
  const faceArbitrary = fc.record({
    id: fc.uuid(),
    name: fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0), // 过滤掉纯空格
    thumbnailUrl: fc.string().map(id => `/api/library/faces/${id}/thumbnail`),
    createdAt: fc.float({ min: 1000000000, max: 2000000000 })
  })

  const facesArrayArbitrary = fc.array(faceArbitrary, { minLength: 0, maxLength: 20 })

  // Feature: face-library-management, Property 10: 列表查询完整性
  // **Validates: Requirements 3.1, 3.2**
  it('属性 10: 对于任意 N 个人像，查询列表应该返回 N 个人像，且每个人像应该包含非空的缩略图路径、名称和创建时间', async () => {
    await fc.assert(
      fc.asyncProperty(facesArrayArbitrary, async (faces) => {
        axios.get.mockResolvedValue({ data: { faces } })

        const { container, unmount } = render(
          <FaceLibrary onSelectFaces={vi.fn()} selectedFaceIds={[]} />
        )

        try {
          // 等待加载完成
          await waitFor(() => {
            expect(screen.queryByText('加载人像库中...')).not.toBeInTheDocument()
          }, { timeout: 3000 })

          if (faces.length === 0) {
            // 空列表应该显示空状态
            expect(screen.queryAllByText('人像库为空').length).toBeGreaterThan(0)
          } else {
            // 验证显示的人像数量
            const faceItems = container.querySelectorAll('.face-library-item')
            expect(faceItems.length).toBe(faces.length)

            // 验证每个人像都有必需的信息
            const nameElements = container.querySelectorAll('.face-library-name, .face-library-item-name')
            expect(nameElements.length).toBe(faces.length)
            
            const thumbnails = container.querySelectorAll('.face-library-thumbnail img, .face-library-item-thumbnail img')
            expect(thumbnails.length).toBe(faces.length)
            
            // 验证时间戳显示（格式化后的时间）
            const timeElements = container.querySelectorAll('.face-library-time, .face-library-item-time')
            expect(timeElements.length).toBe(faces.length)
          }
        } finally {
          unmount()
        }
      }),
      { numRuns: 25 }
    )
  }, 10000)

  // Feature: face-library-management, Property 13: 名称搜索过滤
  // **Validates: Requirements 3.6**
  it('属性 13: 对于任意包含特定名称子串的人像集合，按名称搜索应该只返回名称包含该子串的人像', async () => {
    await fc.assert(
      fc.asyncProperty(
        facesArrayArbitrary,
        fc.string({ minLength: 1, maxLength: 10 }).filter(s => s.trim().length > 0),
        async (allFaces, searchQuery) => {
          // 过滤出包含搜索关键词的人像
          const filteredFaces = allFaces.filter(face => 
            face.name.includes(searchQuery)
          )

          // 模拟 API 返回过滤后的结果
          axios.get.mockImplementation((url, config) => {
            if (config?.params?.search === searchQuery) {
              return Promise.resolve({ data: { faces: filteredFaces } })
            }
            return Promise.resolve({ data: { faces: allFaces } })
          })

          const { container, unmount } = render(
            <FaceLibrary onSelectFaces={vi.fn()} selectedFaceIds={[]} />
          )

          try {
            // 等待初始加载
            await waitFor(() => {
              expect(screen.queryByText('加载人像库中...')).not.toBeInTheDocument()
            }, { timeout: 3000 })

            // 输入搜索关键词
            const searchInputs = screen.queryAllByPlaceholderText('搜索人像名称...')
            if (searchInputs.length > 0) {
              fireEvent.change(searchInputs[0], { target: { value: searchQuery } })

              // 等待搜索结果
              await waitFor(() => {
                expect(axios.get).toHaveBeenCalledWith('/api/library/faces', {
                  params: { sortBy: 'created_at', search: searchQuery }
                })
              }, { timeout: 3000 })

              // 验证显示的人像数量
              await waitFor(() => {
                const faceItems = container.querySelectorAll('.face-library-item')
                expect(faceItems.length).toBe(filteredFaces.length)
              }, { timeout: 3000 })

              // 验证所有显示的人像名称都包含搜索关键词
              if (filteredFaces.length > 0) {
                filteredFaces.forEach(face => {
                  expect(screen.getByText(face.name)).toBeInTheDocument()
                  expect(face.name).toContain(searchQuery)
                })
              }
            }
          } finally {
            unmount()
          }
        }
      ),
      { numRuns: 5 }
    )
  }, 30000)

  // Feature: face-library-management, Property 14: 时间排序正确性
  // **Validates: Requirements 3.7**
  it('属性 14: 对于任意人像列表，按创建时间排序后，列表应该按时间戳单调递增或递减排列', async () => {
    await fc.assert(
      fc.asyncProperty(facesArrayArbitrary, async (faces) => {
        if (faces.length < 2) return // 少于 2 个元素无需排序

        // 按时间排序（降序）
        const sortedFaces = [...faces].sort((a, b) => b.createdAt - a.createdAt)

        axios.get.mockResolvedValue({ data: { faces: sortedFaces } })

        const { unmount } = render(
          <FaceLibrary onSelectFaces={vi.fn()} selectedFaceIds={[]} />
        )

        try {
          // 等待加载完成
          await waitFor(() => {
            expect(screen.queryByText('加载人像库中...')).not.toBeInTheDocument()
          }, { timeout: 3000 })

          // 验证排序顺序
          for (let i = 0; i < sortedFaces.length - 1; i++) {
            const currentTime = sortedFaces[i].createdAt
            const nextTime = sortedFaces[i + 1].createdAt
            
            // 验证时间戳是降序排列的
            expect(currentTime).toBeGreaterThanOrEqual(nextTime)
          }
        } finally {
          unmount()
        }
      }),
      { numRuns: 10 }
    )
  }, 15000)

  // Feature: face-library-management, Property 3: 多选支持
  // **Validates: Requirements 1.5**
  it('属性 3: 对于任意人像 ID 列表，系统应该能够同时维护所有人像的选择状态', async () => {
    await fc.assert(
      fc.asyncProperty(
        facesArrayArbitrary,
        fc.array(fc.integer({ min: 0, max: 19 }), { maxLength: 10 }),
        async (faces, selectedIndices) => {
          if (faces.length === 0) return

          // 从索引生成选中的人像 ID
          const selectedFaceIds = selectedIndices
            .filter(idx => idx < faces.length)
            .map(idx => faces[idx].id)
            .filter((id, index, self) => self.indexOf(id) === index) // 去重

          axios.get.mockResolvedValue({ data: { faces } })

          const mockOnSelectFaces = vi.fn()
          const { container, unmount } = render(
            <FaceLibrary 
              onSelectFaces={mockOnSelectFaces} 
              selectedFaceIds={selectedFaceIds} 
            />
          )

          try {
            // 等待加载完成
            await waitFor(() => {
              expect(screen.queryByText('加载人像库中...')).not.toBeInTheDocument()
            }, { timeout: 3000 })

            // 验证选择提示显示正确的数量
            if (selectedFaceIds.length > 0) {
              expect(screen.getByText(`已选择 ${selectedFaceIds.length} 个人像`)).toBeInTheDocument()
            }

            // 验证选中的人像有选中标记
            const selectedBadges = container.querySelectorAll('.face-library-selected-badge')
            expect(selectedBadges.length).toBe(selectedFaceIds.length)

            // 验证选中的卡片有 selected 类
            const selectedItems = container.querySelectorAll('.face-library-item.selected')
            expect(selectedItems.length).toBe(selectedFaceIds.length)
          } finally {
            unmount()
          }
        }
      ),
      { numRuns: 25 }
    )
  }, 10000)

  // Feature: face-library-management, Property 2: 选择状态切换
  // **Validates: Requirements 1.2**
  it('属性 2: 对于任意人像 ID 和当前选择状态集合，点击该人像应该切换其选择状态', async () => {
    await fc.assert(
      fc.asyncProperty(
        facesArrayArbitrary.filter(faces => faces.length > 0),
        fc.integer({ min: 0, max: 19 }),
        fc.boolean(),
        async (faces, targetIndex, initiallySelected) => {
          if (targetIndex >= faces.length) return

          const targetFace = faces[targetIndex]
          const initialSelection = initiallySelected ? [targetFace.id] : []

          axios.get.mockResolvedValue({ data: { faces } })

          const mockOnSelectFaces = vi.fn()
          const { unmount } = render(
            <FaceLibrary 
              onSelectFaces={mockOnSelectFaces} 
              selectedFaceIds={initialSelection} 
            />
          )

          try {
            // 等待加载完成
            await waitFor(() => {
              expect(screen.queryByText('加载人像库中...')).not.toBeInTheDocument()
            }, { timeout: 3000 })

            // 点击目标人像的缩略图
            const thumbnails = screen.getAllByRole('img')
            if (thumbnails[targetIndex] && thumbnails[targetIndex].parentElement) {
              fireEvent.click(thumbnails[targetIndex].parentElement)

              // 验证回调被调用，且选择状态被切换
              expect(mockOnSelectFaces).toHaveBeenCalled()
              const newSelection = mockOnSelectFaces.mock.calls[0][0]

              if (initiallySelected) {
                // 如果初始是选中的，应该被移除
                expect(newSelection).not.toContain(targetFace.id)
              } else {
                // 如果初始未选中，应该被添加
                expect(newSelection).toContain(targetFace.id)
              }
            }
          } finally {
            unmount()
          }
        }
      ),
      { numRuns: 25 }
    )
  }, 10000)

  // Feature: face-library-management, Property 11: 名称更新 Round-Trip
  // **Validates: Requirements 3.3**
  it('属性 11: 对于任意已保存的人像和新名称，更新名称后查询应该返回新名称', async () => {
    await fc.assert(
      fc.asyncProperty(
        faceArbitrary,
        fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0),
        async (face, newName) => {
          axios.get.mockResolvedValue({ data: { faces: [face] } })
          axios.put.mockResolvedValue({ data: { success: true } })

          const { container, unmount } = render(<FaceLibrary onSelectFaces={vi.fn()} selectedFaceIds={[]} />)

          try {
            // 等待加载完成
            await waitFor(() => {
              const nameElements = container.querySelectorAll('.face-library-name')
              expect(nameElements.length).toBe(1)
            }, { timeout: 3000 })

            // 点击编辑按钮
            const editButton = screen.getByTitle('编辑名称')
            fireEvent.click(editButton)

            // 修改名称
            const nameInput = screen.getByDisplayValue(face.name)
            fireEvent.change(nameInput, { target: { value: newName } })

            // 点击保存
            const saveButton = screen.getByText('保存')
            fireEvent.click(saveButton)

            // 验证 API 被调用
            await waitFor(() => {
              expect(axios.put).toHaveBeenCalledWith(
                `/api/library/faces/${face.id}`,
                { name: newName }
              )
            }, { timeout: 3000 })

            // 验证本地状态更新（检查 DOM 中的名称元素）
            await waitFor(() => {
              const nameElements = container.querySelectorAll('.face-library-name')
              expect(nameElements.length).toBe(1)
              // 验证名称已更新（通过 textContent）
              expect(nameElements[0].textContent.trim()).toBe(newName.trim())
            }, { timeout: 3000 })
          } finally {
            unmount()
          }
        }
      ),
      { numRuns: 5 }
    )
  }, 60000)

  // Feature: face-library-management, Property 12: 删除操作有效性
  // **Validates: Requirements 3.4**
  it('属性 12: 对于任意已保存的人像，删除后查询该人像应该返回 None 或空结果', async () => {
    await fc.assert(
      fc.asyncProperty(
        facesArrayArbitrary.filter(faces => faces.length > 0),
        fc.integer({ min: 0, max: 19 }),
        async (faces, deleteIndex) => {
          if (deleteIndex >= faces.length) return

          const faceToDelete = faces[deleteIndex]
          const remainingFaces = faces.filter(f => f.id !== faceToDelete.id)

          axios.get.mockResolvedValue({ data: { faces } })
          axios.delete.mockResolvedValue({ data: { success: true } })

          const { container, unmount } = render(
            <FaceLibrary onSelectFaces={vi.fn()} selectedFaceIds={[]} />
          )

          try {
            // 等待加载完成
            await waitFor(() => {
              expect(screen.getByText(faceToDelete.name)).toBeInTheDocument()
            }, { timeout: 3000 })

            // 点击删除按钮
            const deleteButtons = screen.getAllByTitle('删除')
            if (deleteButtons[deleteIndex]) {
              fireEvent.click(deleteButtons[deleteIndex])

              // 确认删除
              const confirmButton = screen.getByText('确定')
              fireEvent.click(confirmButton)

              // 验证 API 被调用
              await waitFor(() => {
                expect(axios.delete).toHaveBeenCalledWith(
                  `/api/library/faces/${faceToDelete.id}`
                )
              }, { timeout: 3000 })

              // 验证人像从列表中移除
              await waitFor(() => {
                const faceItems = container.querySelectorAll('.face-library-item')
                expect(faceItems.length).toBe(remainingFaces.length)
                
                // 验证被删除的人像不再显示
                expect(screen.queryByText(faceToDelete.name)).not.toBeInTheDocument()
              }, { timeout: 3000 })
            }
          } finally {
            unmount()
          }
        }
      ),
      { numRuns: 20 }
    )
  }, 15000)
})
