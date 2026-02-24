/**
 * Toolbar 组件属性测试
 * Feature: unified-face-selector
 * 
 * 使用 fast-check 进行基于属性的测试
 */

import React from 'react';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import fc from 'fast-check';
import Toolbar from './Toolbar';

describe('Toolbar 属性测试', () => {
  /**
   * 属性 10：清空选择完整性
   * 
   * 对于任意选择状态，点击"清空选择"按钮后，应该调用 onClearSelection 回调
   * 
   * **验证：需求 4.6**
   */
  test('Property 10: 清空选择完整性', () => {
    fc.assert(
      fc.property(
        // 生成选择计数（1-10）
        fc.integer({ min: 1, max: 10 }),
        (selectedCount) => {
          const onClearSelection = vi.fn();
          
          const { unmount } = render(
            <Toolbar
              selectedCount={selectedCount}
              onStartSearch={vi.fn()}
              onClearSelection={onClearSelection}
            />
          );
          
          // 点击清空选择按钮
          const clearButton = screen.getByRole('button', { name: /清空所有选择/ });
          expect(clearButton).not.toBeDisabled();
          
          fireEvent.click(clearButton);
          
          // 验证回调被调用
          expect(onClearSelection).toHaveBeenCalledTimes(1);
          
          // 清理
          unmount();
          vi.clearAllMocks();
        }
      ),
      { numRuns: 100 }
    );
  }, 30000);

  /**
   * 属性 13：搜索按钮状态正确性
   * 
   * 对于任意选择状态，"开始搜索"按钮的启用状态应该与是否至少选中一个人像一致：
   * - 选中数量 > 0：启用
   * - 选中数量 = 0：禁用
   * 
   * **验证：需求 6.2**
   */
  test('Property 13: 搜索按钮状态正确性', () => {
    fc.assert(
      fc.property(
        // 生成选择计数（0-10）
        fc.integer({ min: 0, max: 10 }),
        (selectedCount) => {
          render(
            <Toolbar
              selectedCount={selectedCount}
              onStartSearch={vi.fn()}
              onClearSelection={vi.fn()}
            />
          );
          
          const searchButton = screen.getByRole('button', { name: /开始搜索/ });
          
          // 验证按钮状态
          if (selectedCount > 0) {
            expect(searchButton).not.toBeDisabled();
          } else {
            expect(searchButton).toBeDisabled();
          }
          
          // 清理DOM
          cleanup();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * 属性：选择计数显示正确性
   * 
   * 对于任意选择计数（0-10），工具栏应该正确显示该数字
   */
  test('Property: 选择计数显示正确性', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 10 }),
        (selectedCount) => {
          render(
            <Toolbar
              selectedCount={selectedCount}
              onStartSearch={vi.fn()}
              onClearSelection={vi.fn()}
            />
          );
          
          // 验证计数显示
          expect(screen.getByText(selectedCount.toString())).toBeInTheDocument();
          expect(screen.getByText('/ 10')).toBeInTheDocument();
          
          // 清理DOM
          cleanup();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * 属性：清空选择按钮状态正确性
   * 
   * 对于任意选择状态，"清空选择"按钮的启用状态应该与选择计数一致：
   * - 选中数量 > 0：启用
   * - 选中数量 = 0：禁用
   */
  test('Property: 清空选择按钮状态正确性', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 10 }),
        (selectedCount) => {
          render(
            <Toolbar
              selectedCount={selectedCount}
              onStartSearch={vi.fn()}
              onClearSelection={vi.fn()}
            />
          );
          
          const clearButton = screen.getByRole('button', { name: /清空所有选择/ });
          
          // 验证按钮状态
          if (selectedCount > 0) {
            expect(clearButton).not.toBeDisabled();
          } else {
            expect(clearButton).toBeDisabled();
          }
          
          // 清理DOM
          cleanup();
        }
      ),
      { numRuns: 100 }
    );
  }, 30000);

  /**
   * 属性：转存按钮状态正确性
   * 
   * 对于任意转存路径，"转存图片"按钮的启用状态应该与路径是否有效一致：
   * - 路径非空且非纯空格：启用
   * - 路径为空或纯空格：禁用
   */
  test('Property: 转存按钮状态正确性', () => {
    fc.assert(
      fc.property(
        // 生成各种路径字符串
        fc.oneof(
          fc.constant(''),
          fc.constant('   '),
          fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0)
        ),
        (exportPath) => {
          render(
            <Toolbar
              selectedCount={1}
              onStartSearch={vi.fn()}
              onClearSelection={vi.fn()}
              showExportControls={true}
              exportPath={exportPath}
              onExportPathChange={vi.fn()}
              onExport={vi.fn()}
            />
          );
          
          const exportButton = screen.getByRole('button', { name: /转存图片/ });
          
          // 验证按钮状态
          if (exportPath && exportPath.trim()) {
            expect(exportButton).not.toBeDisabled();
          } else {
            expect(exportButton).toBeDisabled();
          }
          
          // 清理DOM
          cleanup();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * 属性：按钮点击回调正确性
   * 
   * 对于任意有效的选择状态，点击启用的按钮应该调用相应的回调函数
   */
  test('Property: 按钮点击回调正确性', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 10 }),
        (selectedCount) => {
          const onStartSearch = vi.fn();
          const onClearSelection = vi.fn();
          
          render(
            <Toolbar
              selectedCount={selectedCount}
              onStartSearch={onStartSearch}
              onClearSelection={onClearSelection}
            />
          );
          
          // 点击开始搜索按钮
          const searchButton = screen.getByRole('button', { name: /开始搜索/ });
          fireEvent.click(searchButton);
          expect(onStartSearch).toHaveBeenCalledTimes(1);
          
          // 点击清空选择按钮
          const clearButton = screen.getByRole('button', { name: /清空所有选择/ });
          fireEvent.click(clearButton);
          expect(onClearSelection).toHaveBeenCalledTimes(1);
          
          // 清理
          cleanup();
          vi.clearAllMocks();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * 属性：转存路径显示一致性
   * 
   * 对于任意转存路径字符串，路径输入框应该显示该路径
   */
  test('Property: 转存路径显示一致性', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 0, maxLength: 200 }),
        (exportPath) => {
          render(
            <Toolbar
              selectedCount={1}
              onStartSearch={vi.fn()}
              onClearSelection={vi.fn()}
              showExportControls={true}
              exportPath={exportPath}
              onExportPathChange={vi.fn()}
              onExport={vi.fn()}
            />
          );
          
          // 验证路径显示 - 使用 aria-label 定位以避免多个元素匹配
          const pathInput = screen.getByLabelText('转存路径');
          expect(pathInput).toHaveValue(exportPath);
          expect(pathInput).toHaveAttribute('readonly');
          
          // 清理DOM
          cleanup();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * 属性：aria-label 正确性
   * 
   * 对于任意选择计数，开始搜索按钮的 aria-label 应该包含正确的数字
   */
  test('Property: aria-label 正确性', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 10 }),
        (selectedCount) => {
          render(
            <Toolbar
              selectedCount={selectedCount}
              onStartSearch={vi.fn()}
              onClearSelection={vi.fn()}
            />
          );
          
          const searchButton = screen.getByLabelText(new RegExp(`开始搜索.*${selectedCount}.*个人像`));
          expect(searchButton).toBeInTheDocument();
          
          // 清理DOM
          cleanup();
        }
      ),
      { numRuns: 100 }
    );
  }, 30000);

  /**
   * 属性：转存控件可见性
   * 
   * 对于任意 showExportControls 值，转存控件的可见性应该与该值一致
   */
  test('Property: 转存控件可见性', () => {
    fc.assert(
      fc.property(
        fc.boolean(),
        (showExportControls) => {
          render(
            <Toolbar
              selectedCount={1}
              onStartSearch={vi.fn()}
              onClearSelection={vi.fn()}
              showExportControls={showExportControls}
              exportPath=""
              onExportPathChange={vi.fn()}
              onExport={vi.fn()}
            />
          );
          
          const pathInput = screen.queryByPlaceholderText('选择转存路径...');
          const exportButton = screen.queryByRole('button', { name: /转存图片/ });
          
          if (showExportControls) {
            expect(pathInput).toBeInTheDocument();
            expect(exportButton).toBeInTheDocument();
          } else {
            expect(pathInput).not.toBeInTheDocument();
            expect(exportButton).not.toBeInTheDocument();
          }
          
          // 清理DOM
          cleanup();
        }
      ),
      { numRuns: 100 }
    );
  }, 30000);
});
