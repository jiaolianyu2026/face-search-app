import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import FaceLibraryItem from './FaceLibraryItem'

describe('FaceLibraryItem', () => {
  const mockFace = {
    id: 'face-123',
    name: '张三',
    thumbnailUrl: '/api/library/faces/face-123/thumbnail',
    createdAt: 1234567890.123
  }

  const mockCallbacks = {
    onSelect: vi.fn(),
    onEdit: vi.fn(),
    onDelete: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该渲染人像卡片的基本信息', () => {
    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    expect(screen.getByText('张三')).toBeInTheDocument()
    expect(screen.getByAltText('张三')).toBeInTheDocument()
    expect(screen.getByText(/2009/)).toBeInTheDocument() // 时间戳对应的年份
  })

  it('应该在选中时显示选中徽章', () => {
    const { container } = render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={true}
        {...mockCallbacks}
      />
    )

    const badge = container.querySelector('.face-library-item-selected-badge')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveTextContent('✓')
  })

  it('应该在未选中时不显示选中徽章', () => {
    const { container } = render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    const badge = container.querySelector('.face-library-item-selected-badge')
    expect(badge).not.toBeInTheDocument()
  })

  it('应该在点击缩略图时调用 onSelect', () => {
    const { container } = render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    const thumbnail = container.querySelector('.face-library-item-thumbnail')
    fireEvent.click(thumbnail)

    expect(mockCallbacks.onSelect).toHaveBeenCalledWith('face-123')
  })

  it('应该显示编辑和删除按钮', () => {
    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    const editButton = screen.getByTitle('编辑名称')
    const deleteButton = screen.getByTitle('删除')

    expect(editButton).toBeInTheDocument()
    expect(deleteButton).toBeInTheDocument()
  })

  it('应该在点击编辑按钮时进入编辑模式', () => {
    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    const editButton = screen.getByTitle('编辑名称')
    fireEvent.click(editButton)

    const input = screen.getByDisplayValue('张三')
    expect(input).toBeInTheDocument()
    expect(screen.getByText('保存')).toBeInTheDocument()
    expect(screen.getByText('取消')).toBeInTheDocument()
  })

  it('应该在编辑模式下允许修改名称', () => {
    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    // 进入编辑模式
    const editButton = screen.getByTitle('编辑名称')
    fireEvent.click(editButton)

    // 修改名称
    const input = screen.getByDisplayValue('张三')
    fireEvent.change(input, { target: { value: '李四' } })

    expect(input.value).toBe('李四')
  })

  it('应该在保存编辑时调用 onEdit', () => {
    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    // 进入编辑模式
    const editButton = screen.getByTitle('编辑名称')
    fireEvent.click(editButton)

    // 修改名称
    const input = screen.getByDisplayValue('张三')
    fireEvent.change(input, { target: { value: '李四' } })

    // 保存
    const saveButton = screen.getByText('保存')
    fireEvent.click(saveButton)

    expect(mockCallbacks.onEdit).toHaveBeenCalledWith('face-123', '李四')
  })

  it('应该在取消编辑时恢复原名称', () => {
    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    // 进入编辑模式
    const editButton = screen.getByTitle('编辑名称')
    fireEvent.click(editButton)

    // 修改名称
    const input = screen.getByDisplayValue('张三')
    fireEvent.change(input, { target: { value: '李四' } })

    // 取消
    const cancelButton = screen.getByText('取消')
    fireEvent.click(cancelButton)

    // 应该显示原名称
    expect(screen.getByText('张三')).toBeInTheDocument()
    expect(mockCallbacks.onEdit).not.toHaveBeenCalled()
  })

  it('应该在按 Enter 键时保存编辑', () => {
    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    // 进入编辑模式
    const editButton = screen.getByTitle('编辑名称')
    fireEvent.click(editButton)

    // 修改名称并按 Enter
    const input = screen.getByDisplayValue('张三')
    fireEvent.change(input, { target: { value: '李四' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(mockCallbacks.onEdit).toHaveBeenCalledWith('face-123', '李四')
  })

  it('应该在按 Escape 键时取消编辑', () => {
    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    // 进入编辑模式
    const editButton = screen.getByTitle('编辑名称')
    fireEvent.click(editButton)

    // 修改名称并按 Escape
    const input = screen.getByDisplayValue('张三')
    fireEvent.change(input, { target: { value: '李四' } })
    fireEvent.keyDown(input, { key: 'Escape' })

    // 应该显示原名称
    expect(screen.getByText('张三')).toBeInTheDocument()
    expect(mockCallbacks.onEdit).not.toHaveBeenCalled()
  })

  it('应该在名称为空时阻止保存', () => {
    // Mock alert
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    // 进入编辑模式
    const editButton = screen.getByTitle('编辑名称')
    fireEvent.click(editButton)

    // 清空名称
    const input = screen.getByDisplayValue('张三')
    fireEvent.change(input, { target: { value: '   ' } })

    // 尝试保存
    const saveButton = screen.getByText('保存')
    fireEvent.click(saveButton)

    expect(alertSpy).toHaveBeenCalledWith('名称不能为空')
    expect(mockCallbacks.onEdit).not.toHaveBeenCalled()

    alertSpy.mockRestore()
  })

  it('应该在名称超过 100 字符时阻止保存', () => {
    // Mock alert
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    // 进入编辑模式
    const editButton = screen.getByTitle('编辑名称')
    fireEvent.click(editButton)

    // 输入超长名称
    const input = screen.getByDisplayValue('张三')
    const longName = 'a'.repeat(101)
    fireEvent.change(input, { target: { value: longName } })

    // 尝试保存
    const saveButton = screen.getByText('保存')
    fireEvent.click(saveButton)

    expect(alertSpy).toHaveBeenCalledWith('名称长度不能超过 100 字符')
    expect(mockCallbacks.onEdit).not.toHaveBeenCalled()

    alertSpy.mockRestore()
  })

  it('应该在点击删除按钮时显示确认对话框', () => {
    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    const deleteButton = screen.getByTitle('删除')
    fireEvent.click(deleteButton)

    expect(screen.getByText('确定删除？')).toBeInTheDocument()
    expect(screen.getByText('确定')).toBeInTheDocument()
  })

  it('应该在确认删除时调用 onDelete', () => {
    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    // 点击删除按钮
    const deleteButton = screen.getByTitle('删除')
    fireEvent.click(deleteButton)

    // 确认删除
    const confirmButton = screen.getByText('确定')
    fireEvent.click(confirmButton)

    expect(mockCallbacks.onDelete).toHaveBeenCalledWith('face-123')
  })

  it('应该在取消删除时不调用 onDelete', () => {
    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    // 点击删除按钮
    const deleteButton = screen.getByTitle('删除')
    fireEvent.click(deleteButton)

    // 取消删除
    const cancelButton = screen.getAllByText('取消')[0]
    fireEvent.click(cancelButton)

    expect(mockCallbacks.onDelete).not.toHaveBeenCalled()
  })

  it('应该在编辑或删除模式下禁用缩略图点击', () => {
    const { container } = render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    // 进入编辑模式
    const editButton = screen.getByTitle('编辑名称')
    fireEvent.click(editButton)

    // 点击缩略图
    const thumbnail = container.querySelector('.face-library-item-thumbnail')
    fireEvent.click(thumbnail)

    // 不应该调用 onSelect
    expect(mockCallbacks.onSelect).not.toHaveBeenCalled()
  })

  it('应该正确格式化时间戳', () => {
    render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    // 时间戳 1234567890.123 对应 2009-02-14 07:31:30 (UTC+8)
    const timeElement = screen.getByText(/2009/)
    expect(timeElement).toBeInTheDocument()
  })

  it('应该在图片加载失败时显示占位符', () => {
    const { container } = render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    const img = screen.getByAltText('张三')
    
    // 触发图片加载错误
    fireEvent.error(img)

    // 图片应该被隐藏
    expect(img.style.display).toBe('none')

    // 占位符应该显示
    const placeholder = container.querySelector('.face-library-item-thumbnail-placeholder')
    expect(placeholder.style.display).toBe('flex')
  })

  it('应该在选中状态下应用 selected 类', () => {
    const { container } = render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={true}
        {...mockCallbacks}
      />
    )

    const item = container.querySelector('.face-library-item')
    expect(item).toHaveClass('selected')
  })

  it('应该在未选中状态下不应用 selected 类', () => {
    const { container } = render(
      <FaceLibraryItem
        face={mockFace}
        isSelected={false}
        {...mockCallbacks}
      />
    )

    const item = container.querySelector('.face-library-item')
    expect(item).not.toHaveClass('selected')
  })
})
