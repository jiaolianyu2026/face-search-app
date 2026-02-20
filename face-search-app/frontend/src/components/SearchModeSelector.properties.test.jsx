import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
import { fc } from '@fast-check/vitest'
import SearchModeSelector from './SearchModeSelector'

// Feature: face-library-management

describe('SearchModeSelector - Property-Based Tests', () => {
  // Property 1: 模式切换一致性
  // 对于任意初始模式，点击另一个模式按钮应该调用 onModeChange 并传递正确的模式值
  it('Property 1: 模式切换应该传递正确的模式值', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('upload', 'library'),
        (initialMode) => {
          const mockOnModeChange = vi.fn()
          const { container } = render(
            <SearchModeSelector mode={initialMode} onModeChange={mockOnModeChange} />
          )
          
          // 获取两个按钮
          const tabs = container.querySelectorAll('.search-mode-tab')
          
          // 点击第一个按钮（上传模式）
          fireEvent.click(tabs[0])
          expect(mockOnModeChange).toHaveBeenCalledWith('upload')
          
          // 重置 mock
          mockOnModeChange.mockClear()
          
          // 点击第二个按钮（历史模式）
          fireEvent.click(tabs[1])
          expect(mockOnModeChange).toHaveBeenCalledWith('library')
        }
      ),
      { numRuns: 25 }
    )
  })

  // Property 2: 活动状态正确性
  // 对于任意模式，active 类应该只应用于对应的按钮
  it('Property 2: active 类应该只应用于当前模式的按钮', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('upload', 'library'),
        (mode) => {
          const mockOnModeChange = vi.fn()
          const { container } = render(
            <SearchModeSelector mode={mode} onModeChange={mockOnModeChange} />
          )
          
          const tabs = container.querySelectorAll('.search-mode-tab')
          const uploadTab = tabs[0]
          const libraryTab = tabs[1]
          
          if (mode === 'upload') {
            expect(uploadTab).toHaveClass('active')
            expect(libraryTab).not.toHaveClass('active')
          } else {
            expect(libraryTab).toHaveClass('active')
            expect(uploadTab).not.toHaveClass('active')
          }
        }
      ),
      { numRuns: 25 }
    )
  })

  // Property 3: 回调调用次数
  // 对于任意点击序列，每次点击应该触发一次回调
  it('Property 3: 每次点击应该触发一次回调', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('upload', 'library'),
        fc.array(fc.constantFrom('upload', 'library'), { minLength: 1, maxLength: 10 }),
        (initialMode, clickSequence) => {
          const mockOnModeChange = vi.fn()
          const { container } = render(
            <SearchModeSelector mode={initialMode} onModeChange={mockOnModeChange} />
          )
          
          const tabs = container.querySelectorAll('.search-mode-tab')
          
          clickSequence.forEach((targetMode) => {
            const tabIndex = targetMode === 'upload' ? 0 : 1
            fireEvent.click(tabs[tabIndex])
          })
          
          expect(mockOnModeChange).toHaveBeenCalledTimes(clickSequence.length)
        }
      ),
      { numRuns: 25 }
    )
  })

  // Property 4: 渲染稳定性
  // 对于任意模式，组件应该始终渲染两个按钮
  it('Property 4: 组件应该始终渲染两个模式按钮', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('upload', 'library'),
        (mode) => {
          const mockOnModeChange = vi.fn()
          const { container } = render(
            <SearchModeSelector mode={mode} onModeChange={mockOnModeChange} />
          )
          
          const tabs = container.querySelectorAll('.search-mode-tab')
          expect(tabs).toHaveLength(2)
          
          const icons = container.querySelectorAll('.search-mode-icon')
          expect(icons).toHaveLength(2)
          
          const labels = container.querySelectorAll('.search-mode-label')
          expect(labels).toHaveLength(2)
        }
      ),
      { numRuns: 25 }
    )
  })

  // Property 5: 模式值传递正确性
  // 对于任意点击的按钮，传递给回调的值应该与按钮对应的模式一致
  it('Property 5: 回调参数应该与点击的按钮对应', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('upload', 'library'),
        fc.constantFrom(0, 1), // 按钮索引
        (initialMode, buttonIndex) => {
          const mockOnModeChange = vi.fn()
          const { container } = render(
            <SearchModeSelector mode={initialMode} onModeChange={mockOnModeChange} />
          )
          
          const tabs = container.querySelectorAll('.search-mode-tab')
          fireEvent.click(tabs[buttonIndex])
          
          const expectedMode = buttonIndex === 0 ? 'upload' : 'library'
          expect(mockOnModeChange).toHaveBeenCalledWith(expectedMode)
        }
      ),
      { numRuns: 25 }
    )
  })
})
