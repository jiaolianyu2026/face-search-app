import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import FaceLibrary from './FaceLibrary'

// Mock axios
vi.mock('axios')

describe('FaceLibrary 组件', () => {
  const mockFaces = [
    {
      id: 'face-1',
      name: '张三',
      thumbnailUrl: '/api/library/faces/face-1/thumbnail',
      createdAt: 1234567890.123
    },
    {
      id: 'face-2',
      name: '李四',
      thumbnailUrl: '/api/library/faces/face-2/thumbnail',
      createdAt: 1234567900.456
    },
    {
      id: 'face-3',
      name: '王五',
      thumbnailUrl: '/api/library/faces/face-3/thumbnail',
      createdAt: 1234567910.789
    }
  ]

  const mockOnSelectFaces = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确加载并显示人像列表', async () => {
    axios.get.mockResolvedValue({ data: { faces: mockFaces } })

    render(<FaceLibrary onSelectFaces={mockOnSelectFaces} selectedFaceIds={[]} />)

    // 等待加载完成
    await waitFor(() => {
      expect(screen.queryByText('加载人像库中...')).not.toBeInTheDocument()
    })

    // 验证所有人像都显示
    expect(screen.getByText('张三')).toBeInTheDocument()
    expect(screen.getByText('李四')).toBeInTheDocument()
    expect(screen.getByText('王五')).toBeInTheDocument()
  })

  it('应该显示加载状态', () => {
    axios.get.mockImplementation(() => new Promise(() => {})) // 永不解决的 Promise

    render(<FaceLibrary onSelectFaces={mockOnSelectFaces} selectedFaceIds={[]} />)

    expect(screen.getByText('加载人像库中...')).toBeInTheDocument()
  })

  it('应该显示错误状态', async () => {
    axios.get.mockRejectedValue({
      response: { data: { error: { message: '加载失败' } } }
    })

    render(<FaceLibrary onSelectFaces={mockOnSelectFaces} selectedFaceIds={[]} />)

    await waitFor(() => {
      expect(screen.getByText('加载失败')).toBeInTheDocument()
    })
  })

  it('应该显示空状态', async () => {
    axios.get.mockResolvedValue({ data: { faces: [] } })

    render(<FaceLibrary onSelectFaces={mockOnSelectFaces} selectedFaceIds={[]} />)

    await waitFor(() => {
      expect(screen.getByText('人像库为空')).toBeInTheDocument()
    })
  })

  it('应该支持点击选择人像', async () => {
    axios.get.mockResolvedValue({ data: { faces: mockFaces } })

    render(<FaceLibrary onSelectFaces={mockOnSelectFaces} selectedFaceIds={[]} />)

    await waitFor(() => {
      expect(screen.getByText('张三')).toBeInTheDocument()
    })

    // 点击第一个人像的缩略图
    const thumbnails = screen.getAllByRole('img')
    fireEvent.click(thumbnails[0].parentElement)

    // 验证回调被调用
    expect(mockOnSelectFaces).toHaveBeenCalledWith(['face-1'])
  })

  it('应该支持取消选择人像', async () => {
    axios.get.mockResolvedValue({ data: { faces: mockFaces } })

    render(
      <FaceLibrary 
        onSelectFaces={mockOnSelectFaces} 
        selectedFaceIds={['face-1']} 
      />
    )

    await waitFor(() => {
      expect(screen.getByText('张三')).toBeInTheDocument()
    })

    // 点击已选中的人像
    const thumbnails = screen.getAllByRole('img')
    fireEvent.click(thumbnails[0].parentElement)

    // 验证回调被调用，移除选择
    expect(mockOnSelectFaces).toHaveBeenCalledWith([])
  })

  it('应该显示选中状态', async () => {
    axios.get.mockResolvedValue({ data: { faces: mockFaces } })

    render(
      <FaceLibrary 
        onSelectFaces={mockOnSelectFaces} 
        selectedFaceIds={['face-1', 'face-2']} 
      />
    )

    await waitFor(() => {
      expect(screen.getByText('已选择 2 个人像')).toBeInTheDocument()
    })
  })

  it('应该支持名称搜索', async () => {
    axios.get.mockResolvedValue({ data: { faces: mockFaces } })

    render(<FaceLibrary onSelectFaces={mockOnSelectFaces} selectedFaceIds={[]} />)

    await waitFor(() => {
      expect(screen.getByText('张三')).toBeInTheDocument()
    })

    // 输入搜索关键词
    const searchInput = screen.getByPlaceholderText('搜索人像名称...')
    fireEvent.change(searchInput, { target: { value: '张' } })

    // 验证 API 被调用，带搜索参数
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith('/api/library/faces', {
        params: { sortBy: 'created_at', search: '张' }
      })
    })
  })

  it('应该支持排序切换', async () => {
    axios.get.mockResolvedValue({ data: { faces: mockFaces } })

    render(<FaceLibrary onSelectFaces={mockOnSelectFaces} selectedFaceIds={[]} />)

    await waitFor(() => {
      expect(screen.getByText('张三')).toBeInTheDocument()
    })

    // 切换排序方式
    const sortSelect = screen.getByRole('combobox')
    fireEvent.change(sortSelect, { target: { value: 'name' } })

    // 验证 API 被调用，带排序参数
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith('/api/library/faces', {
        params: { sortBy: 'name' }
      })
    })
  })

  it('应该支持编辑名称', async () => {
    axios.get.mockResolvedValue({ data: { faces: mockFaces } })
    axios.put.mockResolvedValue({ data: { success: true } })

    render(<FaceLibrary onSelectFaces={mockOnSelectFaces} selectedFaceIds={[]} />)

    await waitFor(() => {
      expect(screen.getByText('张三')).toBeInTheDocument()
    })

    // 点击编辑按钮
    const editButtons = screen.getAllByTitle('编辑名称')
    fireEvent.click(editButtons[0])

    // 修改名称
    const nameInput = screen.getByDisplayValue('张三')
    fireEvent.change(nameInput, { target: { value: '张三丰' } })

    // 点击保存
    const saveButton = screen.getByText('保存')
    fireEvent.click(saveButton)

    // 验证 API 被调用
    await waitFor(() => {
      expect(axios.put).toHaveBeenCalledWith('/api/library/faces/face-1', {
        name: '张三丰'
      })
    })
  })

  it('应该验证名称不能为空', async () => {
    axios.get.mockResolvedValue({ data: { faces: mockFaces } })
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    render(<FaceLibrary onSelectFaces={mockOnSelectFaces} selectedFaceIds={[]} />)

    await waitFor(() => {
      expect(screen.getByText('张三')).toBeInTheDocument()
    })

    // 点击编辑按钮
    const editButtons = screen.getAllByTitle('编辑名称')
    fireEvent.click(editButtons[0])

    // 清空名称
    const nameInput = screen.getByDisplayValue('张三')
    fireEvent.change(nameInput, { target: { value: '   ' } })

    // 点击保存
    const saveButton = screen.getByText('保存')
    fireEvent.click(saveButton)

    // 验证显示错误提示
    expect(alertSpy).toHaveBeenCalledWith('名称不能为空')
    
    alertSpy.mockRestore()
  })

  it('应该支持删除人像', async () => {
    axios.get.mockResolvedValue({ data: { faces: mockFaces } })
    axios.delete.mockResolvedValue({ data: { success: true } })

    render(<FaceLibrary onSelectFaces={mockOnSelectFaces} selectedFaceIds={[]} />)

    await waitFor(() => {
      expect(screen.getByText('张三')).toBeInTheDocument()
    })

    // 点击删除按钮
    const deleteButtons = screen.getAllByTitle('删除')
    fireEvent.click(deleteButtons[0])

    // 确认删除
    const confirmButton = screen.getByText('确定')
    fireEvent.click(confirmButton)

    // 验证 API 被调用
    await waitFor(() => {
      expect(axios.delete).toHaveBeenCalledWith('/api/library/faces/face-1')
    })
  })

  it('应该支持取消删除', async () => {
    axios.get.mockResolvedValue({ data: { faces: mockFaces } })

    render(<FaceLibrary onSelectFaces={mockOnSelectFaces} selectedFaceIds={[]} />)

    await waitFor(() => {
      expect(screen.getByText('张三')).toBeInTheDocument()
    })

    // 点击删除按钮
    const deleteButtons = screen.getAllByTitle('删除')
    fireEvent.click(deleteButtons[0])

    // 取消删除
    const cancelButton = screen.getByText('取消')
    fireEvent.click(cancelButton)

    // 验证 API 未被调用
    expect(axios.delete).not.toHaveBeenCalled()
  })

  it('应该正确格式化时间戳', async () => {
    axios.get.mockResolvedValue({ data: { faces: mockFaces } })

    render(<FaceLibrary onSelectFaces={mockOnSelectFaces} selectedFaceIds={[]} />)

    await waitFor(() => {
      // 验证时间格式显示（具体格式取决于本地化设置）
      const timeElements = screen.getAllByText(/\d{4}/)
      expect(timeElements.length).toBeGreaterThan(0)
    })
  })
})
