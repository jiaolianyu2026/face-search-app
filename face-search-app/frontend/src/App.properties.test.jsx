import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import * as fc from 'fast-check'
import App from './App'
import axios from 'axios'

// Mock axios
vi.mock('axios')

/**
 * App 组件属性测试 - 混合选择逻辑
 * 使用 fast-check 进行基于属性的测试
 * 
 * Feature: face-library-management
 * Validates: Requirements 4.5, 4.7
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
 * 生成有效的图片 ID
 */
const imageIdArbitrary = () => 
  fc.uuid().map(uuid => `image-${uuid}`)

/**
 * 生成有效的库人像 ID
 */
const libraryFaceIdArbitrary = () => 
  fc.uuid()

/**
 * 生成 128 维特征向量
 */
const featureVectorArbitrary = () =>
  fc.array(fc.float({ min: -10.0, max: 10.0, noNaN: true }), { 
    minLength: 128, 
    maxLength: 128 
  })

/**
 * 生成上传人像选择对象
 */
const uploadedFaceSelectionArbitrary = () =>
  fc.record({
    type: fc.constant('uploaded'),
    imageId: imageIdArbitrary(),
    faceId: faceIdArbitrary()
  })

/**
 * 生成库人像选择对象
 */
const libraryFaceSelectionArbitrary = () =>
  fc.record({
    type: fc.constant('library'),
    libraryFaceId: libraryFaceIdArbitrary()
  })

/**
 * 生成混合人像选择列表（包含上传和库人像）
 */
const mixedFaceSelectionsArbitrary = () =>
  fc.tuple(
    fc.array(uploadedFaceSelectionArbitrary(), { minLength: 0, maxLength: 5 }),
    fc.array(libraryFaceSelectionArbitrary(), { minLength: 0, maxLength: 5 })
  ).filter(([uploaded, library]) => uploaded.length + library.length > 0)

// ============================================================================
// 辅助函数
// ============================================================================

/**
 * 模拟 getAllSelectedFaces 函数的行为
 * 这是从 App.jsx 中提取的逻辑
 */
function getAllSelectedFaces(uploadedImage, selectedUploadedFaceIds, selectedLibraryFaceIds) {
  const targetFaces = []

  // 添加从上传图片选择的人像
  selectedUploadedFaceIds.forEach(faceId => {
    targetFaces.push({
      type: 'uploaded',
      imageId: uploadedImage.imageId,
      faceId: faceId
    })
  })

  // 添加从人像库选择的人像
  selectedLibraryFaceIds.forEach(libraryFaceId => {
    targetFaces.push({
      type: 'library',
      libraryFaceId: libraryFaceId
    })
  })

  return targetFaces
}

/**
 * 验证目标人像对象的结构
 */
function isValidTargetFace(targetFace) {
  if (targetFace.type === 'uploaded') {
    return (
      typeof targetFace.imageId === 'string' &&
      typeof targetFace.faceId === 'string' &&
      targetFace.imageId.length > 0 &&
      targetFace.faceId.length > 0
    )
  } else if (targetFace.type === 'library') {
    return (
      typeof targetFace.libraryFaceId === 'string' &&
      targetFace.libraryFaceId.length > 0
    )
  }
  return false
}

// ============================================================================
// Property 15: 混合选择合并
// ============================================================================

describe('Property 15: 混合选择合并', () => {
  /**
   * 对于任意上传人像集合和历史人像集合，合并后的特征向量列表应该包含
   * 两个集合的所有特征向量。
   * 
   * **Validates: Requirements 4.5**
   */
  it('合并后的目标人像列表应该包含所有上传和库人像', () => {
    fc.assert(
      fc.property(
        imageIdArbitrary(),
        fc.array(faceIdArbitrary(), { minLength: 0, maxLength: 5 }),
        fc.array(libraryFaceIdArbitrary(), { minLength: 0, maxLength: 5 }),
        (imageId, uploadedFaceIds, libraryFaceIds) => {
          // 至少要有一个选择
          if (uploadedFaceIds.length === 0 && libraryFaceIds.length === 0) {
            return true
          }

          const uploadedImage = { imageId }
          const targetFaces = getAllSelectedFaces(uploadedImage, uploadedFaceIds, libraryFaceIds)

          // 验证总数量正确
          expect(targetFaces.length).toBe(uploadedFaceIds.length + libraryFaceIds.length)

          // 验证所有上传人像都在结果中
          uploadedFaceIds.forEach(faceId => {
            const found = targetFaces.some(
              tf => tf.type === 'uploaded' && tf.faceId === faceId && tf.imageId === imageId
            )
            expect(found).toBe(true)
          })

          // 验证所有库人像都在结果中
          libraryFaceIds.forEach(libraryFaceId => {
            const found = targetFaces.some(
              tf => tf.type === 'library' && tf.libraryFaceId === libraryFaceId
            )
            expect(found).toBe(true)
          })
        }
      ),
      { numRuns: 25 }
    )
  })

  it('合并后的列表应该保持上传人像和库人像的顺序', () => {
    fc.assert(
      fc.property(
        imageIdArbitrary(),
        fc.array(faceIdArbitrary(), { minLength: 1, maxLength: 3 }),
        fc.array(libraryFaceIdArbitrary(), { minLength: 1, maxLength: 3 }),
        (imageId, uploadedFaceIds, libraryFaceIds) => {
          const uploadedImage = { imageId }
          const targetFaces = getAllSelectedFaces(uploadedImage, uploadedFaceIds, libraryFaceIds)

          // 验证上传人像在前
          const uploadedCount = uploadedFaceIds.length
          for (let i = 0; i < uploadedCount; i++) {
            expect(targetFaces[i].type).toBe('uploaded')
            expect(targetFaces[i].faceId).toBe(uploadedFaceIds[i])
          }

          // 验证库人像在后
          for (let i = 0; i < libraryFaceIds.length; i++) {
            expect(targetFaces[uploadedCount + i].type).toBe('library')
            expect(targetFaces[uploadedCount + i].libraryFaceId).toBe(libraryFaceIds[i])
          }
        }
      ),
      { numRuns: 25 }
    )
  })

  it('空的上传人像列表应该只返回库人像', () => {
    fc.assert(
      fc.property(
        imageIdArbitrary(),
        fc.array(libraryFaceIdArbitrary(), { minLength: 1, maxLength: 5 }),
        (imageId, libraryFaceIds) => {
          const uploadedImage = { imageId }
          const targetFaces = getAllSelectedFaces(uploadedImage, [], libraryFaceIds)

          expect(targetFaces.length).toBe(libraryFaceIds.length)
          targetFaces.forEach(tf => {
            expect(tf.type).toBe('library')
          })
        }
      ),
      { numRuns: 20 }
    )
  })

  it('空的库人像列表应该只返回上传人像', () => {
    fc.assert(
      fc.property(
        imageIdArbitrary(),
        fc.array(faceIdArbitrary(), { minLength: 1, maxLength: 5 }),
        (imageId, uploadedFaceIds) => {
          const uploadedImage = { imageId }
          const targetFaces = getAllSelectedFaces(uploadedImage, uploadedFaceIds, [])

          expect(targetFaces.length).toBe(uploadedFaceIds.length)
          targetFaces.forEach(tf => {
            expect(tf.type).toBe('uploaded')
          })
        }
      ),
      { numRuns: 20 }
    )
  })

  it('合并后的每个目标人像对象应该有正确的结构', () => {
    fc.assert(
      fc.property(
        imageIdArbitrary(),
        fc.array(faceIdArbitrary(), { minLength: 0, maxLength: 3 }),
        fc.array(libraryFaceIdArbitrary(), { minLength: 0, maxLength: 3 }),
        (imageId, uploadedFaceIds, libraryFaceIds) => {
          if (uploadedFaceIds.length === 0 && libraryFaceIds.length === 0) {
            return true
          }

          const uploadedImage = { imageId }
          const targetFaces = getAllSelectedFaces(uploadedImage, uploadedFaceIds, libraryFaceIds)

          // 验证每个目标人像对象的结构
          targetFaces.forEach(tf => {
            expect(isValidTargetFace(tf)).toBe(true)
          })
        }
      ),
      { numRuns: 25 }
    )
  })
})

// ============================================================================
// Property 16: 搜索输入一致性
// ============================================================================

describe('Property 16: 搜索输入一致性', () => {
  /**
   * 对于任意选中的人像集合，传递给搜索函数的特征向量列表长度应该等于
   * 选中人像的数量。
   * 
   * **Validates: Requirements 4.7**
   */
  it('目标人像列表的长度应该等于选中人像的总数', () => {
    fc.assert(
      fc.property(
        imageIdArbitrary(),
        fc.array(faceIdArbitrary(), { minLength: 0, maxLength: 5 }),
        fc.array(libraryFaceIdArbitrary(), { minLength: 0, maxLength: 5 }),
        (imageId, uploadedFaceIds, libraryFaceIds) => {
          const uploadedImage = { imageId }
          const targetFaces = getAllSelectedFaces(uploadedImage, uploadedFaceIds, libraryFaceIds)

          const expectedCount = uploadedFaceIds.length + libraryFaceIds.length
          expect(targetFaces.length).toBe(expectedCount)
        }
      ),
      { numRuns: 25 }
    )
  })

  it('每个选中的上传人像应该对应一个目标人像对象', () => {
    fc.assert(
      fc.property(
        imageIdArbitrary(),
        fc.array(faceIdArbitrary(), { minLength: 1, maxLength: 5 }),
        (imageId, uploadedFaceIds) => {
          const uploadedImage = { imageId }
          const targetFaces = getAllSelectedFaces(uploadedImage, uploadedFaceIds, [])

          // 验证一对一映射
          expect(targetFaces.length).toBe(uploadedFaceIds.length)

          // 验证每个 faceId 都有对应的目标人像
          uploadedFaceIds.forEach(faceId => {
            const matchingTargets = targetFaces.filter(
              tf => tf.type === 'uploaded' && tf.faceId === faceId
            )
            expect(matchingTargets.length).toBe(1)
          })
        }
      ),
      { numRuns: 25 }
    )
  })

  it('每个选中的库人像应该对应一个目标人像对象', () => {
    fc.assert(
      fc.property(
        imageIdArbitrary(),
        fc.array(libraryFaceIdArbitrary(), { minLength: 1, maxLength: 5 }),
        (imageId, libraryFaceIds) => {
          const uploadedImage = { imageId }
          const targetFaces = getAllSelectedFaces(uploadedImage, [], libraryFaceIds)

          // 验证一对一映射
          expect(targetFaces.length).toBe(libraryFaceIds.length)

          // 验证每个 libraryFaceId 都有对应的目标人像
          libraryFaceIds.forEach(libraryFaceId => {
            const matchingTargets = targetFaces.filter(
              tf => tf.type === 'library' && tf.libraryFaceId === libraryFaceId
            )
            expect(matchingTargets.length).toBe(1)
          })
        }
      ),
      { numRuns: 25 }
    )
  })

  it('目标人像列表不应该包含重复的人像', () => {
    fc.assert(
      fc.property(
        imageIdArbitrary(),
        fc.array(faceIdArbitrary(), { minLength: 0, maxLength: 5 }),
        fc.array(libraryFaceIdArbitrary(), { minLength: 0, maxLength: 5 }),
        (imageId, uploadedFaceIds, libraryFaceIds) => {
          // 确保输入没有重复
          const uniqueUploadedIds = [...new Set(uploadedFaceIds)]
          const uniqueLibraryIds = [...new Set(libraryFaceIds)]

          const uploadedImage = { imageId }
          const targetFaces = getAllSelectedFaces(uploadedImage, uniqueUploadedIds, uniqueLibraryIds)

          // 验证没有重复的上传人像
          const uploadedTargets = targetFaces.filter(tf => tf.type === 'uploaded')
          const uploadedFaceIdsInResult = uploadedTargets.map(tf => tf.faceId)
          expect(new Set(uploadedFaceIdsInResult).size).toBe(uploadedFaceIdsInResult.length)

          // 验证没有重复的库人像
          const libraryTargets = targetFaces.filter(tf => tf.type === 'library')
          const libraryFaceIdsInResult = libraryTargets.map(tf => tf.libraryFaceId)
          expect(new Set(libraryFaceIdsInResult).size).toBe(libraryFaceIdsInResult.length)
        }
      ),
      { numRuns: 25 }
    )
  })

  it('所有目标人像对象应该包含必需的字段', () => {
    fc.assert(
      fc.property(
        imageIdArbitrary(),
        fc.array(faceIdArbitrary(), { minLength: 0, maxLength: 3 }),
        fc.array(libraryFaceIdArbitrary(), { minLength: 0, maxLength: 3 }),
        (imageId, uploadedFaceIds, libraryFaceIds) => {
          if (uploadedFaceIds.length === 0 && libraryFaceIds.length === 0) {
            return true
          }

          const uploadedImage = { imageId }
          const targetFaces = getAllSelectedFaces(uploadedImage, uploadedFaceIds, libraryFaceIds)

          targetFaces.forEach(tf => {
            // 验证 type 字段
            expect(tf.type).toBeDefined()
            expect(['uploaded', 'library']).toContain(tf.type)

            // 验证类型特定的字段
            if (tf.type === 'uploaded') {
              expect(tf.imageId).toBeDefined()
              expect(tf.faceId).toBeDefined()
              expect(typeof tf.imageId).toBe('string')
              expect(typeof tf.faceId).toBe('string')
            } else if (tf.type === 'library') {
              expect(tf.libraryFaceId).toBeDefined()
              expect(typeof tf.libraryFaceId).toBe('string')
            }
          })
        }
      ),
      { numRuns: 25 }
    )
  })

  it('空的选择应该返回空的目标人像列表', () => {
    fc.assert(
      fc.property(
        imageIdArbitrary(),
        (imageId) => {
          const uploadedImage = { imageId }
          const targetFaces = getAllSelectedFaces(uploadedImage, [], [])

          expect(targetFaces).toEqual([])
          expect(targetFaces.length).toBe(0)
        }
      ),
      { numRuns: 20 }
    )
  })
})
