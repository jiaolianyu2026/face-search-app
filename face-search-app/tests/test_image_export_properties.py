# -*- coding: utf-8 -*-
"""
Property-based tests for image export functionality.
Uses hypothesis to generate random test cases and verify universal properties.

**Feature: face-recognition-search, Property 15: 图片转存往返验证*
**Validates: Requirements 8.4**
"""

import pytest
import os
import sys
import tempfile
import shutil
from hypothesis import given, strategies as st, settings, assume

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from image_export import ImageExportModule
from models import ExportResult, Progress


class TestProperty15_ImageExportRoundTripVerification:
    """
    Property 15: 图片转存往返验证
    
    对于任何成功转存的图片，目标目录中应当存在对应的文件，且文件内容与源文件一致
    
    **Validates: Requirements 8.4**
    """
    
    def _setup_dirs(self):
        """创建测试用的临时目录"""
        temp_dir = tempfile.mkdtemp()
        source_dir = os.path.join(temp_dir, 'source')
        target_dir = os.path.join(temp_dir, 'target')
        os.makedirs(source_dir)
        os.makedirs(target_dir)
        return temp_dir, source_dir, target_dir
    
    def _cleanup_dirs(self, temp_dir):
        """清理临时目录"""
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    def _create_test_file(self, directory: str, filename: str, content: bytes) -> str:
        """在指定目录中创建测试文件"""
        filepath = os.path.join(directory, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        return filepath

    @given(
        file_content=st.binary(min_size=1, max_size=1024*100),  # 1字节到100KB
        extension=st.sampled_from(['.jpg', '.jpeg', '.png', '.webp'])
    )
    @settings(max_examples=3, deadline=5000)
    def test_exported_file_exists_and_content_matches(self, file_content, extension):
        """
        属性：对于任何成功转存的图片，文件应该存在于目标目录中，
        且其内容应该与源文件完全匹配。
        
        这是核心的往返验证属性。
        """
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            # 创建包含随机内容的源文件
            filename = f"test{extension}"
            source_path = self._create_test_file(source_dir, filename, file_content)
            
            # 转存文件
            result = export_module.exportImages([source_path], target_dir)
            
            # 验证转存成功
            assert result.successCount == 1, \
                f"转存应该成功"
            assert result.failedCount == 0, \
                f"不应该有失败"
            assert len(result.errors) == 0, \
                f"不应该有错误报告"
            
            # 验证目标文件存在
            target_path = os.path.join(target_dir, filename)
            assert os.path.exists(target_path), \
                f"转存的文件应该存在于 {target_path}"
            
            # 验证文件内容完全匹配（逐字节）
            with open(source_path, 'rb') as source_file:
                source_content = source_file.read()
            
            with open(target_path, 'rb') as target_file:
                target_content = target_file.read()
            
            assert source_content == target_content, \
                f"转存文件的内容应该与源文件完全匹配"
            
            # 验证文件大小匹配
            source_size = os.path.getsize(source_path)
            target_size = os.path.getsize(target_path)
            assert source_size == target_size, \
                f"转存文件的大小应该与源文件匹配"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)

    @given(
        num_files=st.integers(min_value=1, max_value=10),
        file_size=st.integers(min_value=100, max_value=10000)
    )
    @settings(max_examples=3, deadline=5000)
    def test_multiple_files_all_exported_correctly(self, num_files, file_size):
        """
        属性：对于任何文件列表，所有成功转存的文件都应该存在于
        目标目录中，且内容匹配。
        """
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            # 创建多个具有唯一内容的源文件
            source_files = []
            file_contents = {}
            
            for i in range(num_files):
                # 为每个文件生成唯一内容
                content = bytes([i % 256] * file_size)
                filename = f"image_{i}.jpg"
                source_path = self._create_test_file(source_dir, filename, content)
                source_files.append(source_path)
                file_contents[filename] = content
            
            # 转存所有文件
            result = export_module.exportImages(source_files, target_dir)
            
            # 验证所有转存都成功
            assert result.successCount == num_files, \
                f"所有{num_files} 个文件都应该成功转存"
            assert result.failedCount == 0, \
                f"不应该有失败"
            
            # 验证每个文件都存在且内容匹配
            for filename, expected_content in file_contents.items():
                target_path = os.path.join(target_dir, filename)
                
                assert os.path.exists(target_path), \
                    f"转存的文件 {filename} 应该存在"
                
                with open(target_path, 'rb') as f:
                    actual_content = f.read()
                
                assert actual_content == expected_content, \
                    f"{filename} 的内容应该与源文件匹配"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)

    @given(
        file_content=st.binary(min_size=1, max_size=1024*50),
        filename=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-'),
            min_size=1,
            max_size=20
        ).map(lambda s: s + '.jpg')
    )
    @settings(max_examples=3, deadline=5000)
    def test_various_filenames_exported_correctly(self, file_content, filename):
        """
        属性：具有各种有效文件名的文件都应该正确转存，
        且内容得到保留。
        """
        # 过滤掉无效的文件名
        assume(filename != '.jpg')  # 扩展名前必须有名称
        assume(not filename.startswith('.'))
        assume('..' not in filename)
        
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            # 创建源文件
            source_path = self._create_test_file(source_dir, filename, file_content)
            
            # 转存文件
            result = export_module.exportImages([source_path], target_dir)
            
            # 验证转存成功
            assert result.successCount == 1, \
                f"文件 {filename} 的转存应该成功"
            
            # 验证文件存在且内容匹配
            target_path = os.path.join(target_dir, filename)
            assert os.path.exists(target_path), \
                f"转存的文件{filename} 应该存在"
            
            with open(target_path, 'rb') as f:
                actual_content = f.read()
            
            assert actual_content == file_content, \
                f"{filename} 的内容应该匹配"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)

    @given(
        file_content=st.binary(min_size=1, max_size=1024*50)
    )
    @settings(max_examples=3, deadline=5000)
    def test_metadata_preserved_after_export(self, file_content):
        """
        属性：转存后应该保留文件元数据（修改时间）�?
        
        这验证了 shutil.copy2() 被正确使用�?
        """
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            # 创建源文件
            filename = "test.jpg"
            source_path = self._create_test_file(source_dir, filename, file_content)
            
            # 设置特定的修改时间
            old_time = 1000000000.0  # 过去的某个时间戳
            os.utime(source_path, (old_time, old_time))
            
            # 转存文件
            result = export_module.exportImages([source_path], target_dir)
            
            # 验证转存成功
            assert result.successCount == 1
            
            # 验证元数据被保留
            target_path = os.path.join(target_dir, filename)
            source_mtime = os.path.getmtime(source_path)
            target_mtime = os.path.getmtime(target_path)
            
            # 由于文件系统精度，允许小的差异
            assert abs(target_mtime - source_mtime) < 1.0, \
                f"修改时间应该被保留（源：{source_mtime}，目标：{target_mtime}）"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)

    @given(
        num_files=st.integers(min_value=1, max_value=5),
        num_invalid=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=3, deadline=5000)
    def test_partial_success_valid_files_exported_correctly(self, num_files, num_invalid):
        """
        属性：在混合成�?失败的场景中，所有成功转存的文件
        仍应该有正确的内容。
        """
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            # 创建有效的源文件
            valid_files = []
            valid_contents = {}
            
            for i in range(num_files):
                content = bytes([i % 256] * 1000)
                filename = f"valid_{i}.jpg"
                source_path = self._create_test_file(source_dir, filename, content)
                valid_files.append(source_path)
                valid_contents[filename] = content
            
            # 添加无效的文件路径（不存在的文件）
            invalid_files = []
            for i in range(num_invalid):
                invalid_path = os.path.join(source_dir, f"invalid_{i}.jpg")
                invalid_files.append(invalid_path)
            
            # 混合有效和无效文件
            all_files = valid_files + invalid_files
            
            # 转存所有文件
            result = export_module.exportImages(all_files, target_dir)
            
            # 验证统计信息
            assert result.successCount == num_files, \
                f"应该有 {num_files} 次成功转存"
            assert result.failedCount == num_invalid, \
                f"应该有 {num_invalid} 次失败转存"
            
            # 验证所有有效文件都被正确转存
            for filename, expected_content in valid_contents.items():
                target_path = os.path.join(target_dir, filename)
                
                assert os.path.exists(target_path), \
                    f"有效文件 {filename} 应该被转存"
                
                with open(target_path, 'rb') as f:
                    actual_content = f.read()
                
                assert actual_content == expected_content, \
                    f"尽管有其他失败，{filename} 的内容应该与源文件匹配"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)
    
    def test_empty_file_exported_correctly(self):
        """
        属性：即使是空文件（0字节）也应该被正确转存。
        
        这是一个边界情况，仍应该保留内容（空内容）。
        """
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            # 创建空文件
            filename = "empty.jpg"
            source_path = self._create_test_file(source_dir, filename, b'')
            
            # 转存文件
            result = export_module.exportImages([source_path], target_dir)
            
            # 验证转存成功
            assert result.successCount == 1
            assert result.failedCount == 0
            
            # 验证空文件存在
            target_path = os.path.join(target_dir, filename)
            assert os.path.exists(target_path)
            
            # 验证文件是空的
            assert os.path.getsize(target_path) == 0, \
                "转存的空文件应该保持为空"
            
            with open(target_path, 'rb') as f:
                content = f.read()
            
            assert content == b'', \
                "空文件内容应该被保留"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)



class TestProperty16_FilenameConflictHandling:
    """
    Property 16: 文件名冲突处理
    
    对于任何转存操作，当目标目录中存在同名文件时，新文件应当被重命名（添加数字后缀），
    不应覆盖现有文件
    
    **Validates: Requirements 8.5**
    """
    
    def _setup_dirs(self):
        """创建测试用的临时目录"""
        temp_dir = tempfile.mkdtemp()
        source_dir = os.path.join(temp_dir, 'source')
        target_dir = os.path.join(temp_dir, 'target')
        os.makedirs(source_dir)
        os.makedirs(target_dir)
        return temp_dir, source_dir, target_dir
    
    def _cleanup_dirs(self, temp_dir):
        """清理临时目录"""
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    def _create_test_file(self, directory: str, filename: str, content: bytes) -> str:
        """在指定目录中创建测试文件"""
        filepath = os.path.join(directory, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        return filepath

    @given(
        original_content=st.binary(min_size=1, max_size=1024*10),
        new_content=st.binary(min_size=1, max_size=1024*10),
        extension=st.sampled_from(['.jpg', '.jpeg', '.png', '.webp'])
    )
    @settings(max_examples=3, deadline=5000)
    def test_existing_file_not_overwritten(self, original_content, new_content, extension):
        """
        属性：当目标目录中存在同名文件时，
        现有文件不应该被覆盖。
        """
        # 确保内容不同
        assume(original_content != new_content)
        
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            filename = f"photo{extension}"
            
            # 在目标目录中创建现有文件
            existing_path = self._create_test_file(target_dir, filename, original_content)
            
            # 在源目录中创建具有不同内容的新文件
            source_path = self._create_test_file(source_dir, filename, new_content)
            
            # 转存新文件
            result = export_module.exportImages([source_path], target_dir)
            
            # 验证转存成功
            assert result.successCount == 1, \
                "即使有文件名冲突，转存也应该成功"
            
            # 验证原始文件没有被覆盖
            with open(existing_path, 'rb') as f:
                existing_content_after = f.read()
            
            assert existing_content_after == original_content, \
                "现有文件不应该被覆盖"
            
            # 验证新文件以不同的名称创建
            # 应该命名为photo_1.jpg（或类似）
            base_name = filename.replace(extension, '')
            renamed_file = os.path.join(target_dir, f"{base_name}_1{extension}")
            
            assert os.path.exists(renamed_file), \
                f"新文件应该以后缀创建：{base_name}_1{extension}"
            
            # 验证重命名的文件包含新内容
            with open(renamed_file, 'rb') as f:
                renamed_content = f.read()
            
            assert renamed_content == new_content, \
                "重命名的文件应该包含新内容"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)

    @given(
        num_conflicts=st.integers(min_value=1, max_value=5),
        file_size=st.integers(min_value=100, max_value=5000)
    )
    @settings(max_examples=3, deadline=5000)
    def test_multiple_conflicts_all_files_preserved(self, num_conflicts, file_size):
        """
        属性：有多个文件名冲突时，所有文件都应该被保留，
        并使用适当的数字后缀。
        """
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            filename = "image.jpg"
            base_name = "image"
            extension = ".jpg"
            
            # 在目标中创建原始文件
            original_content = bytes([0] * file_size)
            self._create_test_file(target_dir, filename, original_content)
            
            # 创建并转存多个同名文件
            expected_contents = {filename: original_content}
            
            for i in range(num_conflicts):
                content = bytes([i + 1] * file_size)
                # 在源目录中创建临时文件
                temp_filename = f"temp_{i}.jpg"
                source_path = self._create_test_file(source_dir, temp_filename, content)
                
                # 重命名为冲突名称
                conflict_path = os.path.join(source_dir, filename)
                if os.path.exists(conflict_path):
                    os.remove(conflict_path)
                shutil.copy2(source_path, conflict_path)
                
                # 转存
                result = export_module.exportImages([conflict_path], target_dir)
                assert result.successCount == 1
                
                # 跟踪重命名文件的预期内容
                renamed_filename = f"{base_name}_{i + 1}{extension}"
                expected_contents[renamed_filename] = content
            
            # 验证所有文件都存在且内容正确
            for expected_filename, expected_content in expected_contents.items():
                file_path = os.path.join(target_dir, expected_filename)
                
                assert os.path.exists(file_path), \
                    f"文件 {expected_filename} 应该存在"
                
                with open(file_path, 'rb') as f:
                    actual_content = f.read()
                
                assert actual_content == expected_content, \
                    f"{expected_filename} 的内容应该被保留"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)

    @given(
        extension=st.sampled_from(['.jpg', '.jpeg', '.png', '.webp'])
    )
    @settings(max_examples=3, deadline=5000)
    def test_conflict_resolution_preserves_extension(self, extension):
        """
        属性：解决文件名冲突时，应该保留文件扩展名。
        """
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            filename = f"photo{extension}"
            
            # 创建现有文件
            self._create_test_file(target_dir, filename, b'existing')
            
            # 创建并转存同名的新文件
            source_path = self._create_test_file(source_dir, filename, b'new')
            result = export_module.exportImages([source_path], target_dir)
            
            assert result.successCount == 1
            
            # 查找重命名的文件
            files_in_target = os.listdir(target_dir)
            renamed_files = [f for f in files_in_target if f.startswith('photo_') and f.endswith(extension)]
            
            assert len(renamed_files) >= 1, \
                f"应该至少有一个带扩展名{extension} 的重命名文件"
            
            # 验证扩展名被保留
            for renamed_file in renamed_files:
                assert renamed_file.endswith(extension), \
                    f"重命名的文件应该保留扩展名{extension}"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)


class TestProperty17_ExportStatisticsAccuracy:
    """
    Property 17: 转存结果统计准确�?
    
    对于任何转存操作，返回的ExportResult中的successCount + failedCount应当等于请求转存的图片总数
    
    **Validates: Requirements 8.6, 8.7**
    """
    
    def _setup_dirs(self):
        """创建测试用的临时目录"""
        temp_dir = tempfile.mkdtemp()
        source_dir = os.path.join(temp_dir, 'source')
        target_dir = os.path.join(temp_dir, 'target')
        os.makedirs(source_dir)
        os.makedirs(target_dir)
        return temp_dir, source_dir, target_dir
    
    def _cleanup_dirs(self, temp_dir):
        """清理临时目录"""
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    def _create_test_file(self, directory: str, filename: str, content: bytes) -> str:
        """在指定目录中创建测试文件"""
        filepath = os.path.join(directory, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        return filepath

    @given(
        num_files=st.integers(min_value=0, max_value=20)
    )
    @settings(max_examples=3, deadline=5000)
    def test_statistics_sum_equals_total_all_success(self, num_files):
        """
        属性：对于所有有效文件的任何转存操作�?
        successCount + failedCount 应该等于文件总数�?
        """
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            # 创建有效的源文件
            source_files = []
            for i in range(num_files):
                content = bytes([i % 256] * 100)
                filename = f"image_{i}.jpg"
                source_path = self._create_test_file(source_dir, filename, content)
                source_files.append(source_path)
            
            # 转存所有文件
            result = export_module.exportImages(source_files, target_dir)
            
            # 验证统计准确�?
            total_processed = result.successCount + result.failedCount
            assert total_processed == num_files, \
                f"successCount ({result.successCount}) + failedCount ({result.failedCount}) 应该等于总文件数 ({num_files})"
            
            # 对于所有有效文件，都应该成�?
            assert result.successCount == num_files, \
                f"所有{num_files} 个有效文件都应该成功"
            assert result.failedCount == 0, \
                "所有有效文件都不应该有失败"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)
    
    @given(
        num_valid=st.integers(min_value=0, max_value=10),
        num_invalid=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=3, deadline=5000)
    def test_statistics_sum_equals_total_mixed_results(self, num_valid, num_invalid):
        """
        属性：对于混合有效/无效文件的任何转存操作，
        successCount + failedCount 应该等于文件总数�?
        """
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            total_files = num_valid + num_invalid
            
            # 创建有效的源文件
            valid_files = []
            for i in range(num_valid):
                content = bytes([i % 256] * 100)
                filename = f"valid_{i}.jpg"
                source_path = self._create_test_file(source_dir, filename, content)
                valid_files.append(source_path)
            
            # 创建无效的文件路径（不存在）
            invalid_files = []
            for i in range(num_invalid):
                invalid_path = os.path.join(source_dir, f"invalid_{i}.jpg")
                invalid_files.append(invalid_path)
            
            # 混合有效和无效文件
            all_files = valid_files + invalid_files
            
            # 转存所有文件
            result = export_module.exportImages(all_files, target_dir)
            
            # 验证统计准确性（核心属性）
            total_processed = result.successCount + result.failedCount
            assert total_processed == total_files, \
                f"successCount ({result.successCount}) + failedCount ({result.failedCount}) 应该等于总文件数 ({total_files})"
            
            # 验证各个计数
            assert result.successCount == num_valid, \
                f"应该有 {num_valid} 次成功转存"
            assert result.failedCount == num_invalid, \
                f"应该有 {num_invalid} 次失败转存"
            
            # 验证错误列表长度与失败计数匹配
            assert len(result.errors) == result.failedCount, \
                f"错误数量 ({len(result.errors)}) 应该与 failedCount ({result.failedCount}) 匹配"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)

    @given(
        num_files=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=3, deadline=5000)
    def test_error_list_length_matches_failed_count(self, num_files):
        """
        属性：错误列表的长度应该始终等�?failedCount�?
        """
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            # 只创建无效文件（全部失败�?
            invalid_files = []
            for i in range(num_files):
                invalid_path = os.path.join(source_dir, f"nonexistent_{i}.jpg")
                invalid_files.append(invalid_path)
            
            # 转存所有文件
            result = export_module.exportImages(invalid_files, target_dir)
            
            # 验证全部失败
            assert result.failedCount == num_files, \
                f"所有{num_files} 个无效文件都应该失败"
            assert result.successCount == 0, \
                "没有文件应该成功"
            
            # 验证错误列表长度与失败计数匹配
            assert len(result.errors) == result.failedCount, \
                f"错误数量 ({len(result.errors)}) 应该与 failedCount ({result.failedCount}) 匹配"
            
            # 验证每个错误都有必需的字�?
            for error in result.errors:
                assert 'path' in error, \
                    "每个错误都应该有 'path' 字段"
                assert 'error' in error, \
                    "每个错误都应该有 'error' 字段"
                assert error['path'] in invalid_files, \
                    "错误路径应该是无效文件之一"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)
    
    def test_empty_list_statistics(self):
        """
        属性：转存空列表应该导致零计数�?
        """
        # 为此测试设置目录
        temp_dir, source_dir, target_dir = self._setup_dirs()
        export_module = ImageExportModule()
        
        try:
            # 转存空列�?
            result = export_module.exportImages([], target_dir)
            
            # 验证统计信息
            assert result.successCount == 0, \
                "空列表应该有 0 次成功"
            assert result.failedCount == 0, \
                "空列表应该有 0 次失败"
            assert len(result.errors) == 0, \
                "空列表应该没有错误"
            
            # 验证总和属�?
            total = result.successCount + result.failedCount
            assert total == 0, \
                "空列表的总数应该有0"
        finally:
            # 清理
            self._cleanup_dirs(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

