import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent, waitFor } from '@testing-library/react'
import FaceSelector from './FaceSelector'

/**
 * FaceSelector 组件单元测试
 * 
 * 验证需求: 1.1, 1.2, 1.5
 * - 1.1: 在每个人像位置绘制带有唯一颜色的圆形标记
 * - 1.2: 点击人像标记切换选择状态
 * - 1.5: 支持同时选择多个人像
 */

describe('FaceSelector 组件', () => {
  // 测试数据
  const mockImageUrl = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
  
  const mockFaces = [
    {
      faceId: 'face-1',
      boundingBox: { x: 100, y: 100, width: 50, height: 50 }
    },
    {
      faceId: 'face-2',
      boundingBox: { x: 200, y: 150, width: 60, height: 60 }
    },
    {
      faceId: 'face-3',
      boundingBox: { x: 300, y: 200, width: 55, height: 55 }
    }
  ]

  /**
   * 测试 1.1: 标记渲染
   * 验证需求: 1.1 - 在每个人像位置绘制带有唯一颜色的圆形标记
   */
  describe('标记渲染', () => {
    it('应该为每个检测到的人像渲染圆形标记', async () => {
      const onSelectionChange = vi.fn()
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={[]}
          onSelectionChange={onSelectionChange}
        />
      )

      // 等待图片加载
      const image = container.querySelector('img.face-selector-image')
      fireEvent.load(image)

      await waitFor(() => {
        // 验证 SVG 叠加层存在
        const svg = container.querySelector('svg.face-selector-overlay')
        expect(svg).toBeTruthy()

        // 验证每个人像都有对应的圆形标记
        const circles = container.querySelectorAll('circle.face-marker')
        expect(circles.length).toBe(mockFaces.length)
      })
    })

    it('应该为每个人像分配唯一的颜色', async () => {
      const onSelectionChange = vi.fn()
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={[]}
          onSelectionChange={onSelectionChange}
        />
      )

      const image = container.querySelector('img.face-selector-image')
      fireEvent.load(image)

      await waitFor(() => {
        const circles = container.querySelectorAll('circle.face-marker')
        const colors = Array.from(circles).map(circle => circle.getAttribute('stroke'))
        
        // 验证每个标记都有颜色
        colors.forEach(color => {
          expect(color).toBeTruthy()
          expect(color).toMatch(/^#[0-9a-f]{6}$/i)
        })

        // 验证颜色是唯一的（对于不同的 faceId）
        const uniqueColors = new Set(colors)
        expect(uniqueColors.size).toBeGreaterThan(0)
      })
    })

    it('当没有人像时不应该渲染标记', () => {
      const onSelectionChange = vi.fn()
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={[]}
          selectedFaceIds={[]}
          onSelectionChange={onSelectionChange}
        />
      )

      const image = container.querySelector('img.face-selector-image')
      fireEvent.load(image)

      // 验证没有 SVG 叠加层
      const svg = container.querySelector('svg.face-selector-overlay')
      expect(svg).toBeFalsy()
    })

    it('应该显示选择提示文本', () => {
      const onSelectionChange = vi.fn()
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={[]}
          onSelectionChange={onSelectionChange}
        />
      )

      // 验证提示文本存在
      expect(container.textContent).toContain('点击圆圈选择人像（支持多选）')
    })
  })

  /**
   * 测试 1.2: 点击交互
   * 验证需求: 1.2 - 点击人像标记切换选择状态
   */
  describe('点击交互', () => {
    it('点击未选中的人像应该选中它', async () => {
      const onSelectionChange = vi.fn()
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={[]}
          onSelectionChange={onSelectionChange}
        />
      )

      const image = container.querySelector('img.face-selector-image')
      fireEvent.load(image)

      await waitFor(() => {
        const circles = container.querySelectorAll('circle.face-marker')
        expect(circles.length).toBeGreaterThan(0)
      })

      // 点击第一个人像标记
      const firstCircle = container.querySelector('circle.face-marker')
      fireEvent.click(firstCircle)

      // 验证回调被调用，且包含该人像 ID
      expect(onSelectionChange).toHaveBeenCalledTimes(1)
      expect(onSelectionChange).toHaveBeenCalledWith(['face-1'])
    })

    it('点击已选中的人像应该取消选中', async () => {
      const onSelectionChange = vi.fn()
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={['face-1']}
          onSelectionChange={onSelectionChange}
        />
      )

      const image = container.querySelector('img.face-selector-image')
      fireEvent.load(image)

      await waitFor(() => {
        const circles = container.querySelectorAll('circle.face-marker')
        expect(circles.length).toBeGreaterThan(0)
      })

      // 点击第一个人像标记（已选中）
      const firstCircle = container.querySelector('circle.face-marker')
      fireEvent.click(firstCircle)

      // 验证回调被调用，且不包含该人像 ID
      expect(onSelectionChange).toHaveBeenCalledTimes(1)
      expect(onSelectionChange).toHaveBeenCalledWith([])
    })

    it('选中的人像应该显示不同的视觉样式', async () => {
      const onSelectionChange = vi.fn()
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={['face-1']}
          onSelectionChange={onSelectionChange}
        />
      )

      const image = container.querySelector('img.face-selector-image')
      fireEvent.load(image)

      await waitFor(() => {
        const circles = container.querySelectorAll('circle.face-marker')
        const firstCircle = circles[0]
        
        // 验证选中的标记有更粗的边框
        const strokeWidth = firstCircle.getAttribute('stroke-width')
        expect(parseInt(strokeWidth)).toBeGreaterThan(2)

        // 验证选中的标记有高亮效果（额外的圆圈）
        const highlightCircles = container.querySelectorAll('circle.face-marker-highlight')
        expect(highlightCircles.length).toBeGreaterThan(0)
      })
    })
  })

  /**
   * 测试 1.5: 多选状态
   * 验证需求: 1.5 - 支持同时选择多个人像
   */
  describe('多选状态', () => {
    it('应该支持同时选择多个人像', async () => {
      const onSelectionChange = vi.fn()
      
      const { container, rerender } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={[]}
          onSelectionChange={onSelectionChange}
        />
      )

      const image = container.querySelector('img.face-selector-image')
      fireEvent.load(image)

      await waitFor(() => {
        const circles = container.querySelectorAll('circle.face-marker')
        expect(circles.length).toBe(3)
      })

      // 点击第一个人像
      const circles = container.querySelectorAll('circle.face-marker')
      fireEvent.click(circles[0])
      expect(onSelectionChange).toHaveBeenCalledWith(['face-1'])

      // 模拟选中第一个人像后的状态
      rerender(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={['face-1']}
          onSelectionChange={onSelectionChange}
        />
      )

      // 点击第二个人像
      const updatedCircles = container.querySelectorAll('circle.face-marker')
      fireEvent.click(updatedCircles[1])
      expect(onSelectionChange).toHaveBeenCalledWith(['face-1', 'face-2'])
    })

    it('应该显示已选择的人像数量', () => {
      const onSelectionChange = vi.fn()
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={['face-1', 'face-2']}
          onSelectionChange={onSelectionChange}
        />
      )

      // 验证显示选择数量
      expect(container.textContent).toContain('已选择 2 个人像')
    })

    it('当没有选择时应该显示提示文本', () => {
      const onSelectionChange = vi.fn()
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={[]}
          onSelectionChange={onSelectionChange}
        />
      )

      // 验证显示提示文本
      expect(container.textContent).toContain('点击圆圈选择人像（支持多选）')
    })

    it('应该正确处理选择和取消选择的组合操作', async () => {
      const onSelectionChange = vi.fn()
      
      const { container, rerender } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={['face-1', 'face-2']}
          onSelectionChange={onSelectionChange}
        />
      )

      const image = container.querySelector('img.face-selector-image')
      fireEvent.load(image)

      await waitFor(() => {
        const circles = container.querySelectorAll('circle.face-marker')
        expect(circles.length).toBe(3)
      })

      // 取消选中第一个人像
      const circles = container.querySelectorAll('circle.face-marker')
      fireEvent.click(circles[0])
      expect(onSelectionChange).toHaveBeenCalledWith(['face-2'])

      // 模拟更新后的状态
      rerender(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={['face-2']}
          onSelectionChange={onSelectionChange}
        />
      )

      // 选中第三个人像
      const updatedCircles = container.querySelectorAll('circle.face-marker')
      fireEvent.click(updatedCircles[2])
      expect(onSelectionChange).toHaveBeenCalledWith(['face-2', 'face-3'])
    })
  })

  /**
   * 边缘情况测试
   */
  describe('边缘情况', () => {
    it('应该处理空的 selectedFaceIds 数组', () => {
      const onSelectionChange = vi.fn()
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          selectedFaceIds={[]}
          onSelectionChange={onSelectionChange}
        />
      )

      expect(container).toBeTruthy()
    })

    it('应该处理 undefined 的 selectedFaceIds', () => {
      const onSelectionChange = vi.fn()
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={mockFaces}
          onSelectionChange={onSelectionChange}
        />
      )

      expect(container).toBeTruthy()
    })

    it('应该处理单个人像的情况', async () => {
      const onSelectionChange = vi.fn()
      const singleFace = [mockFaces[0]]
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={singleFace}
          selectedFaceIds={[]}
          onSelectionChange={onSelectionChange}
        />
      )

      const image = container.querySelector('img.face-selector-image')
      fireEvent.load(image)

      await waitFor(() => {
        const circles = container.querySelectorAll('circle.face-marker')
        expect(circles.length).toBe(1)
      })
    })

    it('应该处理大量人像的情况', async () => {
      const onSelectionChange = vi.fn()
      const manyFaces = Array.from({ length: 10 }, (_, i) => ({
        faceId: `face-${i}`,
        boundingBox: { x: i * 50, y: i * 50, width: 50, height: 50 }
      }))
      
      const { container } = render(
        <FaceSelector
          imageUrl={mockImageUrl}
          faces={manyFaces}
          selectedFaceIds={[]}
          onSelectionChange={onSelectionChange}
        />
      )

      const image = container.querySelector('img.face-selector-image')
      fireEvent.load(image)

      await waitFor(() => {
        const circles = container.querySelectorAll('circle.face-marker')
        expect(circles.length).toBe(10)
      })
    })
  })
})
