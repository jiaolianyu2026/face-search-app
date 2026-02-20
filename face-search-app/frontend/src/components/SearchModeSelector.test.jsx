import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import SearchModeSelector from './SearchModeSelector'

describe('SearchModeSelector', () => {
  it('应该渲染两个模式选项', () => {
    const mockOnModeChange = vi.fn()
    render(<SearchModeSelector mode="upload" onModeChange={mockOnModeChange} />)
    
    expect(screen.getByText('上传新图片')).toBeInTheDocument()
    expect(screen.getByText('历史人像')).toBeInTheDocument()
  })

  it('应该正确显示当前选中的模式（upload）', () => {
    const mockOnModeChange = vi.fn()
    const { container } = render(
      <SearchModeSelector mode="upload" onModeChange={mockOnModeChange} />
    )
    
    const tabs = container.querySelectorAll('.search-mode-tab')
    expect(tabs[0]).toHaveClass('active')
    expect(tabs[1]).not.toHaveClass('active')
  })

  it('应该正确显示当前选中的模式（library）', () => {
    const mockOnModeChange = vi.fn()
    const { container } = render(
      <SearchModeSelector mode="library" onModeChange={mockOnModeChange} />
    )
    
    const tabs = container.querySelectorAll('.search-mode-tab')
    expect(tabs[0]).not.toHaveClass('active')
    expect(tabs[1]).toHaveClass('active')
  })

  it('点击上传模式按钮应该调用 onModeChange', () => {
    const mockOnModeChange = vi.fn()
    render(<SearchModeSelector mode="library" onModeChange={mockOnModeChange} />)
    
    const uploadButton = screen.getByText('上传新图片')
    fireEvent.click(uploadButton)
    
    expect(mockOnModeChange).toHaveBeenCalledWith('upload')
    expect(mockOnModeChange).toHaveBeenCalledTimes(1)
  })

  it('点击历史模式按钮应该调用 onModeChange', () => {
    const mockOnModeChange = vi.fn()
    render(<SearchModeSelector mode="upload" onModeChange={mockOnModeChange} />)
    
    const libraryButton = screen.getByText('历史人像')
    fireEvent.click(libraryButton)
    
    expect(mockOnModeChange).toHaveBeenCalledWith('library')
    expect(mockOnModeChange).toHaveBeenCalledTimes(1)
  })

  it('点击当前已选中的模式按钮也应该触发回调', () => {
    const mockOnModeChange = vi.fn()
    render(<SearchModeSelector mode="upload" onModeChange={mockOnModeChange} />)
    
    const uploadButton = screen.getByText('上传新图片')
    fireEvent.click(uploadButton)
    
    expect(mockOnModeChange).toHaveBeenCalledWith('upload')
  })

  it('应该显示图标', () => {
    const mockOnModeChange = vi.fn()
    const { container } = render(
      <SearchModeSelector mode="upload" onModeChange={mockOnModeChange} />
    )
    
    const icons = container.querySelectorAll('.search-mode-icon')
    expect(icons).toHaveLength(2)
    expect(icons[0]).toHaveTextContent('📤')
    expect(icons[1]).toHaveTextContent('📚')
  })

  it('应该在多次切换时正确更新状态', () => {
    const mockOnModeChange = vi.fn()
    const { rerender } = render(
      <SearchModeSelector mode="upload" onModeChange={mockOnModeChange} />
    )
    
    // 切换到 library
    const libraryButton = screen.getByText('历史人像')
    fireEvent.click(libraryButton)
    expect(mockOnModeChange).toHaveBeenCalledWith('library')
    
    // 重新渲染为 library 模式
    rerender(<SearchModeSelector mode="library" onModeChange={mockOnModeChange} />)
    
    // 切换回 upload
    const uploadButton = screen.getByText('上传新图片')
    fireEvent.click(uploadButton)
    expect(mockOnModeChange).toHaveBeenCalledWith('upload')
    
    expect(mockOnModeChange).toHaveBeenCalledTimes(2)
  })

  it('模式切换时应该保持组件结构不变（需求4.6）', () => {
    const mockOnModeChange = vi.fn()
    const { container, rerender } = render(
      <SearchModeSelector mode="upload" onModeChange={mockOnModeChange} />
    )
    
    // 记录初始结构
    const initialTabsCount = container.querySelectorAll('.search-mode-tab').length
    const initialIconsCount = container.querySelectorAll('.search-mode-icon').length
    const initialLabelsCount = container.querySelectorAll('.search-mode-label').length
    
    // 切换到 library 模式
    rerender(<SearchModeSelector mode="library" onModeChange={mockOnModeChange} />)
    
    // 验证结构保持不变
    expect(container.querySelectorAll('.search-mode-tab')).toHaveLength(initialTabsCount)
    expect(container.querySelectorAll('.search-mode-icon')).toHaveLength(initialIconsCount)
    expect(container.querySelectorAll('.search-mode-label')).toHaveLength(initialLabelsCount)
    
    // 切换回 upload 模式
    rerender(<SearchModeSelector mode="upload" onModeChange={mockOnModeChange} />)
    
    // 再次验证结构保持不变
    expect(container.querySelectorAll('.search-mode-tab')).toHaveLength(initialTabsCount)
    expect(container.querySelectorAll('.search-mode-icon')).toHaveLength(initialIconsCount)
    expect(container.querySelectorAll('.search-mode-label')).toHaveLength(initialLabelsCount)
  })

  it('应该正确处理无效的模式值', () => {
    const mockOnModeChange = vi.fn()
    const { container } = render(
      <SearchModeSelector mode="invalid" onModeChange={mockOnModeChange} />
    )
    
    // 组件应该仍然渲染，但没有 active 类
    const tabs = container.querySelectorAll('.search-mode-tab')
    expect(tabs).toHaveLength(2)
    
    // 两个按钮都不应该有 active 类
    tabs.forEach(tab => {
      expect(tab).not.toHaveClass('active')
    })
  })
})
