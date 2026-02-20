import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import * as fc from 'fast-check'
import FaceLibraryItem from './FaceLibraryItem'

// Feature: face-library-management

describe('FaceLibraryItem - Property-Based Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  // 生成有效的人像名称（1-100 字符）
  const validNameArb = fc.string({ minLength: 1, maxLength: 100 })

  // 生成有效的 UUID
  const uuidArb = fc.uuid()

  // 生成有效的时间戳（Unix 时间戳，秒）
  const timestampArb = fc.integer({ min: 946684800, max: 2147483647 }) // 2000-01-01 到 2038-01-19

  // 生成完整的人像对象
  const faceArb = fc.record({
    id: uuidArb,
    name: validNameArb,
    thumbnailUrl: fc.string().map(id => `/api/library/faces/${id}/thumbnail`),
    createdAt: timestampArb.map(ts => ts + Math.random()) // 添加小数部分
  })

  /**
   * Property 1: 选择状态切换
   * **Validates: Requirements 1.2**
   * 
   * 对于任意人像和选择状态，点击缩略图应该调用 onSelect 回调
   */
  it('Property 1: 点击缩略图应该触发选择回调', () => {
    fc.assert(
      fc.property(faceArb, fc.boolean(), (face, isSelected) => {
        const onSelect = vi.fn()
        const { container } = render(
          <FaceLibraryItem
            face={face}
            isSelected={isSelected}
            onSelect={onSelect}
            onEdit={vi.fn()}
            onDelete={vi.fn()}
          />
        )

        const thumbnail = container.querySelector('.face-library-item-thumbnail')
        fireEvent.click(thumbnail)

        expect(onSelect).toHaveBeenCalledWith(face.id)
        
        // 清理
        cleanup()
      }),
      { numRuns: 20 }
    )
  })

  /**
   * Property 2: 选中状态视觉反馈
   * **Validates: Requirements 1.3, 1.4**
   * 
   * 对于任意人像，选中时应该显示选中徽章，未选中时不显示
   */
  it('Property 2: 选中状态应该有正确的视觉反馈', () => {
    fc.assert(
      fc.property(faceArb, fc.boolean(), (face, isSelected) => {
        const { container } = render(
          <FaceLibraryItem
            face={face}
            isSelected={isSelected}
            onSelect={vi.fn()}
            onEdit={vi.fn()}
            onDelete={vi.fn()}
          />
        )

        const badge = container.querySelector('.face-library-item-selected-badge')
        const item = container.querySelector('.face-library-item')

        if (isSelected) {
          expect(badge).toBeTruthy()
          expect(item.classList.contains('selected')).toBe(true)
        } else {
          expect(badge).toBeFalsy()
          expect(item.classList.contains('selected')).toBe(false)
        }
        
        // 清理
        cleanup()
      }),
      { numRuns: 20 }
    )
  })

  /**
   * Property 3: 名称编辑 Round-Trip
   * **Validates: Requirements 3.3**
   * 
   * 对于任意有效的新名称，编辑并保存后应该调用 onEdit 回调
   */
  it('Property 3: 编辑名称应该正确保存', () => {
    fc.assert(
      fc.property(faceArb, validNameArb, (face, newName) => {
        const onEdit = vi.fn()
        const { container } = render(
          <FaceLibraryItem
            face={face}
            isSelected={false}
            onSelect={vi.fn()}
            onEdit={onEdit}
            onDelete={vi.fn()}
          />
        )

        // 进入编辑模式
        const editButton = container.querySelector('button[title="编辑名称"]')
        fireEvent.click(editButton)

        // 修改名称 - 使用 container.querySelector 而不是 getByDisplayValue
        const input = container.querySelector('input.input')
        expect(input).toBeTruthy()
        fireEvent.change(input, { target: { value: newName } })

        // 保存
        const saveButton = container.querySelector('button.button-primary')
        fireEvent.click(saveButton)

        expect(onEdit).toHaveBeenCalledWith(face.id, newName.trim())
        
        // 清理
        cleanup()
      }),
      { numRuns: 20 }
    )
  })

  /**
   * Property 4: 名称验证 - 空字符串
   * **Validates: Requirements 7.3**
   * 
   * 对于任意空白字符串，保存时应该阻止并显示错误
   */
  it('Property 4: 空名称应该被拒绝', () => {
    fc.assert(
      fc.property(faceArb, fc.string({ minLength: 0, maxLength: 5 }).filter(s => s.trim() === ''), (face, emptyName) => {
        const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
        const onEdit = vi.fn()

        const { container } = render(
          <FaceLibraryItem
            face={face}
            isSelected={false}
            onSelect={vi.fn()}
            onEdit={onEdit}
            onDelete={vi.fn()}
          />
        )

        // 进入编辑模式
        const editButton = container.querySelector('button[title="编辑名称"]')
        fireEvent.click(editButton)

        // 输入空白名称
        const input = container.querySelector('input.input')
        expect(input).toBeTruthy()
        fireEvent.change(input, { target: { value: emptyName } })

        // 尝试保存
        const saveButton = container.querySelector('button.button-primary')
        fireEvent.click(saveButton)

        expect(alertSpy).toHaveBeenCalledWith('名称不能为空')
        expect(onEdit).not.toHaveBeenCalled()

        alertSpy.mockRestore()
        
        // 清理
        cleanup()
      }),
      { numRuns: 20 }
    )
  })

  /**
   * Property 5: 名称验证 - 超长字符串
   * **Validates: Requirements 7.3**
   * 
   * 对于任意超过 100 字符的名称，保存时应该阻止并显示错误
   */
  it('Property 5: 超长名称应该被拒绝', () => {
    fc.assert(
      fc.property(faceArb, fc.string({ minLength: 101, maxLength: 200 }), (face, longName) => {
        const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
        const onEdit = vi.fn()

        const { container } = render(
          <FaceLibraryItem
            face={face}
            isSelected={false}
            onSelect={vi.fn()}
            onEdit={onEdit}
            onDelete={vi.fn()}
          />
        )

        // 进入编辑模式
        const editButton = container.querySelector('button[title="编辑名称"]')
        fireEvent.click(editButton)

        // 输入超长名称
        const input = container.querySelector('input.input')
        expect(input).toBeTruthy()
        fireEvent.change(input, { target: { value: longName } })

        // 尝试保存
        const saveButton = container.querySelector('button.button-primary')
        fireEvent.click(saveButton)

        expect(alertSpy).toHaveBeenCalledWith('名称长度不能超过 100 字符')
        expect(onEdit).not.toHaveBeenCalled()

        alertSpy.mockRestore()
        
        // 清理
        cleanup()
      }),
      { numRuns: 20 }
    )
  })

  /**
   * Property 6: 取消编辑不改变状态
   * **Validates: Requirements 3.3**
   * 
   * 对于任意名称修改，取消编辑后不应该调用 onEdit
   */
  it('Property 6: 取消编辑不应该保存更改', () => {
    fc.assert(
      fc.property(faceArb, validNameArb, (face, newName) => {
        const onEdit = vi.fn()
        const { container } = render(
          <FaceLibraryItem
            face={face}
            isSelected={false}
            onSelect={vi.fn()}
            onEdit={onEdit}
            onDelete={vi.fn()}
          />
        )

        // 进入编辑模式
        const editButton = container.querySelector('button[title="编辑名称"]')
        fireEvent.click(editButton)

        // 修改名称
        const input = container.querySelector('input.input')
        expect(input).toBeTruthy()
        fireEvent.change(input, { target: { value: newName } })

        // 取消 - 查找所有取消按钮，选择不是 button-danger 的那个
        const cancelButtons = container.querySelectorAll('button')
        const cancelButton = Array.from(cancelButtons).find(btn => 
          btn.textContent === '取消' && !btn.classList.contains('button-danger')
        )
        fireEvent.click(cancelButton)

        // 应该显示原名称
        const nameElement = container.querySelector('.face-library-item-name')
        expect(nameElement.textContent).toBe(face.name)
        expect(onEdit).not.toHaveBeenCalled()
        
        // 清理
        cleanup()
      }),
      { numRuns: 20 }
    )
  })

  /**
   * Property 7: 删除确认流程
   * **Validates: Requirements 3.4, 3.5**
   * 
   * 对于任意人像，确认删除应该调用 onDelete，取消删除不应该调用
   */
  it('Property 7: 删除确认流程应该正确工作', () => {
    fc.assert(
      fc.property(faceArb, fc.boolean(), (face, shouldConfirm) => {
        const onDelete = vi.fn()
        const { container } = render(
          <FaceLibraryItem
            face={face}
            isSelected={false}
            onSelect={vi.fn()}
            onEdit={vi.fn()}
            onDelete={onDelete}
          />
        )

        // 点击删除按钮
        const deleteButton = container.querySelector('button[title="删除"]')
        fireEvent.click(deleteButton)

        // 应该显示确认对话框
        const confirmDialog = container.querySelector('.face-library-item-delete-confirm')
        expect(confirmDialog).toBeTruthy()

        if (shouldConfirm) {
          // 确认删除
          const confirmButton = container.querySelector('.face-library-item-delete-actions .button-danger')
          fireEvent.click(confirmButton)
          expect(onDelete).toHaveBeenCalledWith(face.id)
        } else {
          // 取消删除
          const cancelButtons = container.querySelectorAll('.face-library-item-delete-actions button')
          const cancelButton = Array.from(cancelButtons).find(btn => btn.textContent === '取消')
          fireEvent.click(cancelButton)
          expect(onDelete).not.toHaveBeenCalled()
        }
        
        // 清理
        cleanup()
      }),
      { numRuns: 20 }
    )
  })

  /**
   * Property 8: 时间戳格式化
   * **Validates: Requirements 3.2**
   * 
   * 对于任意有效的时间戳，应该能够正确格式化并显示
   */
  it('Property 8: 时间戳应该正确格式化', () => {
    fc.assert(
      fc.property(faceArb, (face) => {
        const { container } = render(
          <FaceLibraryItem
            face={face}
            isSelected={false}
            onSelect={vi.fn()}
            onEdit={vi.fn()}
            onDelete={vi.fn()}
          />
        )

        // 验证时间显示存在
        const date = new Date(face.createdAt * 1000)
        const year = date.getFullYear()
        
        // 使用 container 查询而不是 screen
        const timeElement = container.querySelector('.face-library-item-time')
        expect(timeElement).toBeTruthy()
        expect(timeElement.textContent).toContain(year.toString())
        
        // 清理
        cleanup()
      }),
      { numRuns: 20 }
    )
  })

  /**
   * Property 9: 编辑和删除模式互斥
   * **Validates: Requirements 3.3, 3.4**
   * 
   * 对于任意人像，在编辑或删除模式下，缩略图点击不应该触发选择
   */
  it('Property 9: 编辑/删除模式下禁用选择', () => {
    fc.assert(
      fc.property(faceArb, fc.constantFrom('edit', 'delete'), (face, mode) => {
        const onSelect = vi.fn()
        const { container } = render(
          <FaceLibraryItem
            face={face}
            isSelected={false}
            onSelect={onSelect}
            onEdit={vi.fn()}
            onDelete={vi.fn()}
          />
        )

        // 进入编辑或删除模式
        if (mode === 'edit') {
          const editButton = screen.getByTitle('编辑名称')
          fireEvent.click(editButton)
        } else {
          const deleteButton = screen.getByTitle('删除')
          fireEvent.click(deleteButton)
        }

        // 点击缩略图
        const thumbnail = container.querySelector('.face-library-item-thumbnail')
        fireEvent.click(thumbnail)

        // 不应该触发选择
        expect(onSelect).not.toHaveBeenCalled()
      }),
      { numRuns: 25 }
    )
  })

  /**
   * Property 10: 键盘快捷键
   * **Validates: Requirements 3.3**
   * 
   * 对于任意名称修改，Enter 键应该保存，Escape 键应该取消
   */
  it('Property 10: 键盘快捷键应该正确工作', () => {
    fc.assert(
      fc.property(faceArb, validNameArb, fc.constantFrom('Enter', 'Escape'), (face, newName, key) => {
        const onEdit = vi.fn()
        const { container } = render(
          <FaceLibraryItem
            face={face}
            isSelected={false}
            onSelect={vi.fn()}
            onEdit={onEdit}
            onDelete={vi.fn()}
          />
        )

        // 进入编辑模式 - 使用 container 查询
        const editButton = container.querySelector('button[title="编辑名称"]')
        expect(editButton).toBeTruthy()
        fireEvent.click(editButton)

        // 修改名称
        const input = container.querySelector('input.input')
        expect(input).toBeTruthy()
        fireEvent.change(input, { target: { value: newName } })

        // 按键
        fireEvent.keyDown(input, { key })

        if (key === 'Enter') {
          expect(onEdit).toHaveBeenCalledWith(face.id, newName.trim())
        } else {
          expect(onEdit).not.toHaveBeenCalled()
          const nameElement = container.querySelector('.face-library-item-name')
          expect(nameElement.textContent).toBe(face.name)
        }
        
        // 清理
        cleanup()
      }),
      { numRuns: 20 }
    )
  })
})
