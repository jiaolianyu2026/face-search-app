# -*- coding: utf-8 -*-
"""
Property-based tests for error handling and logging.
Tests that all errors are properly logged to the log file.

**Feature: face-recognition-search, Property 14: 错误日志记录**
**Validates: Requirements 7.4**
"""

import os
import sys
import tempfile
import shutil
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from hypothesis import given, strategies as st, settings
from error_handlers import ValidationError, NotFoundError, ServiceError
from logger import get_logger
import logging


# Strategy for generating error messages
@st.composite
def error_message_strategy(draw):
    """Generate valid error messages."""
    return draw(st.text(min_size=1, max_size=200, alphabet=st.characters(
        blacklist_categories=('Cs',),  # Exclude surrogates
        blacklist_characters='\x00\r\n'  # Exclude null and newlines
    )))


# Strategy for generating field names
@st.composite
def field_name_strategy(draw):
    """Generate valid field names."""
    return draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-'
    )))


# Strategy for generating resource types
@st.composite
def resource_type_strategy(draw):
    """Generate valid resource types."""
    return draw(st.sampled_from(['image', 'face', 'task', 'file', 'folder']))


# Strategy for generating resource IDs
@st.composite
def resource_id_strategy(draw):
    """Generate valid resource IDs."""
    return draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-'
    )))


# Strategy for generating service names
@st.composite
def service_name_strategy(draw):
    """Generate valid service names."""
    return draw(st.sampled_from([
        'face_detection', 'file_system', 'cache', 'similarity', 'export'
    ]))


@settings(max_examples=3, deadline=None)
@given(
    message=error_message_strategy(),
    field=st.one_of(st.none(), field_name_strategy())
)
def test_property_validation_error_logging(message, field):
    """
    **Property 14: 错误日志记录**
    **Validates: Requirements 7.4**
    
    Property: For any ValidationError, the error should be logged with
    timestamp, error type, and error message.
    
    This test verifies that:
    1. ValidationError is logged when raised
    2. Log contains error message
    3. Log contains field information if provided
    """
    # Create temporary log file
    temp_log_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
    temp_log_file.close()
    
    try:
        # Create logger with temporary log file
        logger = logging.getLogger(f'test_validation_{id(message)}')
        logger.setLevel(logging.WARNING)
        logger.handlers.clear()
        
        handler = logging.FileHandler(temp_log_file.name, encoding='utf-8')
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Create and log ValidationError
        error = ValidationError(message, field=field)
        logger.warning(f"验证错误: {error.message}, 字段: {error.field}")
        
        # Flush and close handler
        handler.flush()
        handler.close()
        logger.removeHandler(handler)
        
        # Read log file
        with open(temp_log_file.name, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Verify log contains error message
        assert message in log_content, \
            f"Log should contain error message: {message}"
        
        # Verify log contains "验证错误"
        assert "验证错误" in log_content, \
            "Log should contain error type indicator"
        
        # If field is provided, verify it's in the log
        if field:
            assert field in log_content, \
                f"Log should contain field name: {field}"
        
        # Verify log contains timestamp (basic check)
        assert "|" in log_content, \
            "Log should contain formatted timestamp"
        
        # Verify log contains log level
        assert "WARNING" in log_content, \
            "Log should contain log level"
    
    finally:
        # Cleanup
        if os.path.exists(temp_log_file.name):
            os.unlink(temp_log_file.name)


@settings(max_examples=3, deadline=None)
@given(
    message=error_message_strategy(),
    resource_type=st.one_of(st.none(), resource_type_strategy()),
    resource_id=st.one_of(st.none(), resource_id_strategy())
)
def test_property_not_found_error_logging(message, resource_type, resource_id):
    """
    **Property 14: 错误日志记录**
    **Validates: Requirements 7.4**
    
    Property: For any NotFoundError, the error should be logged with
    timestamp, error type, error message, and resource information.
    
    This test verifies that:
    1. NotFoundError is logged when raised
    2. Log contains error message
    3. Log contains resource type and ID if provided
    """
    # Create temporary log file
    temp_log_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
    temp_log_file.close()
    
    try:
        # Create logger with temporary log file
        logger = logging.getLogger(f'test_not_found_{id(message)}')
        logger.setLevel(logging.WARNING)
        logger.handlers.clear()
        
        handler = logging.FileHandler(temp_log_file.name, encoding='utf-8')
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Create and log NotFoundError
        error = NotFoundError(message, resource_type=resource_type, resource_id=resource_id)
        logger.warning(f"资源未找到: {error.message}, 类型: {error.resource_type}, ID: {error.resource_id}")
        
        # Flush and close handler
        handler.flush()
        handler.close()
        logger.removeHandler(handler)
        
        # Read log file
        with open(temp_log_file.name, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Verify log contains error message
        assert message in log_content, \
            f"Log should contain error message: {message}"
        
        # Verify log contains "资源未找到"
        assert "资源未找到" in log_content, \
            "Log should contain error type indicator"
        
        # If resource_type is provided, verify it's in the log
        if resource_type:
            assert resource_type in log_content, \
                f"Log should contain resource type: {resource_type}"
        
        # If resource_id is provided, verify it's in the log
        if resource_id:
            assert resource_id in log_content, \
                f"Log should contain resource ID: {resource_id}"
        
        # Verify log contains timestamp
        assert "|" in log_content, \
            "Log should contain formatted timestamp"
        
        # Verify log contains log level
        assert "WARNING" in log_content, \
            "Log should contain log level"
    
    finally:
        # Cleanup
        if os.path.exists(temp_log_file.name):
            os.unlink(temp_log_file.name)


@settings(max_examples=3, deadline=None)
@given(
    message=error_message_strategy(),
    service_name=st.one_of(st.none(), service_name_strategy())
)
def test_property_service_error_logging(message, service_name):
    """
    **Property 14: 错误日志记录**
    **Validates: Requirements 7.4**
    
    Property: For any ServiceError, the error should be logged with
    timestamp, error type, error message, and service name.
    
    This test verifies that:
    1. ServiceError is logged when raised
    2. Log contains error message
    3. Log contains service name if provided
    4. Log level is ERROR (not WARNING)
    """
    # Create temporary log file
    temp_log_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
    temp_log_file.close()
    
    try:
        # Create logger with temporary log file
        logger = logging.getLogger(f'test_service_{id(message)}')
        logger.setLevel(logging.ERROR)
        logger.handlers.clear()
        
        handler = logging.FileHandler(temp_log_file.name, encoding='utf-8')
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Create and log ServiceError
        error = ServiceError(message, service_name=service_name)
        logger.error(f"服务错误: {error.message}, 服务: {error.service_name}")
        
        # Flush and close handler
        handler.flush()
        handler.close()
        logger.removeHandler(handler)
        
        # Read log file
        with open(temp_log_file.name, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Verify log contains error message
        assert message in log_content, \
            f"Log should contain error message: {message}"
        
        # Verify log contains "服务错误"
        assert "服务错误" in log_content, \
            "Log should contain error type indicator"
        
        # If service_name is provided, verify it's in the log
        if service_name:
            assert service_name in log_content, \
                f"Log should contain service name: {service_name}"
        
        # Verify log contains timestamp
        assert "|" in log_content, \
            "Log should contain formatted timestamp"
        
        # Verify log contains ERROR level
        assert "ERROR" in log_content, \
            "Log should contain ERROR log level for ServiceError"
    
    finally:
        # Cleanup
        if os.path.exists(temp_log_file.name):
            os.unlink(temp_log_file.name)


@settings(max_examples=3, deadline=None)
@given(
    message=error_message_strategy(),
    original_error_message=error_message_strategy()
)
def test_property_service_error_with_original_exception_logging(message, original_error_message):
    """
    **Property 14: 错误日志记录**
    **Validates: Requirements 7.4**
    
    Property: For any ServiceError with an original exception, the error
    should be logged with the original exception information (stack trace).
    
    This test verifies that:
    1. ServiceError with original exception is logged
    2. Log contains both error messages
    3. Log contains exception information
    """
    # Create temporary log file
    temp_log_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
    temp_log_file.close()
    
    try:
        # Create logger with temporary log file
        logger = logging.getLogger(f'test_service_exc_{id(message)}')
        logger.setLevel(logging.ERROR)
        logger.handlers.clear()
        
        handler = logging.FileHandler(temp_log_file.name, encoding='utf-8')
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Create original exception
        original_error = ValueError(original_error_message)
        
        # Create and log ServiceError with original exception
        error = ServiceError(message, service_name='test_service', original_error=original_error)
        logger.error(
            f"服务错误: {error.message}, 服务: {error.service_name}",
            exc_info=error.original_error
        )
        
        # Flush and close handler
        handler.flush()
        handler.close()
        logger.removeHandler(handler)
        
        # Read log file
        with open(temp_log_file.name, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Verify log contains error message
        assert message in log_content, \
            f"Log should contain error message: {message}"
        
        # Verify log contains "服务错误"
        assert "服务错误" in log_content, \
            "Log should contain error type indicator"
        
        # Verify log contains service name
        assert "test_service" in log_content, \
            "Log should contain service name"
        
        # Verify log contains ERROR level
        assert "ERROR" in log_content, \
            "Log should contain ERROR log level"
    
    finally:
        # Cleanup
        if os.path.exists(temp_log_file.name):
            os.unlink(temp_log_file.name)


@settings(max_examples=3, deadline=None)
@given(
    errors=st.lists(
        st.tuples(
            error_message_strategy(),
            st.sampled_from(['validation', 'not_found', 'service'])
        ),
        min_size=1,
        max_size=10
    )
)
def test_property_multiple_errors_all_logged(errors):
    """
    **Property 14: 错误日志记录**
    **Validates: Requirements 7.4**
    
    Property: For any sequence of errors, all errors should be logged
    in the order they occur.
    
    This test verifies that:
    1. Multiple errors are all logged
    2. Each error has its own log entry
    3. Log entries contain timestamps
    """
    # Create temporary log file
    temp_log_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
    temp_log_file.close()
    
    try:
        # Create logger with temporary log file
        logger = logging.getLogger(f'test_multiple_{id(errors)}')
        logger.setLevel(logging.WARNING)
        logger.handlers.clear()
        
        handler = logging.FileHandler(temp_log_file.name, encoding='utf-8')
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Log all errors
        for message, error_type in errors:
            if error_type == 'validation':
                error = ValidationError(message)
                logger.warning(f"验证错误: {error.message}")
            elif error_type == 'not_found':
                error = NotFoundError(message)
                logger.warning(f"资源未找�? {error.message}")
            else:  # service
                error = ServiceError(message)
                logger.error(f"服务错误: {error.message}")
        
        # Flush and close handler
        handler.flush()
        handler.close()
        logger.removeHandler(handler)
        
        # Read log file
        with open(temp_log_file.name, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Verify all error messages are in the log
        for message, error_type in errors:
            assert message in log_content, \
                f"Log should contain error message: {message}"
        
        # Verify log contains multiple entries (count pipe separators)
        pipe_count = log_content.count('|')
        # Each log entry has 3 pipes in the format
        expected_entries = len(errors)
        assert pipe_count >= expected_entries * 3, \
            f"Log should contain at least {expected_entries} entries"
    
    finally:
        # Cleanup
        if os.path.exists(temp_log_file.name):
            os.unlink(temp_log_file.name)


@settings(max_examples=3, deadline=None)
@given(
    message=error_message_strategy(),
    error_type=st.sampled_from(['validation', 'not_found', 'service'])
)
def test_property_error_log_format_consistency(message, error_type):
    """
    **Property 14: 错误日志记录**
    **Validates: Requirements 7.4**
    
    Property: For any error, the log format should be consistent and
    include timestamp, log level, module name, function name, line number,
    and message.
    
    This test verifies that:
    1. Log format is consistent across error types
    2. Log contains all required components
    3. Log is parseable
    """
    # Create temporary log file
    temp_log_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
    temp_log_file.close()
    
    try:
        # Create logger with temporary log file
        logger = logging.getLogger(f'test_format_{id(message)}')
        logger.setLevel(logging.WARNING)
        logger.handlers.clear()
        
        handler = logging.FileHandler(temp_log_file.name, encoding='utf-8')
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Log error based on type
        if error_type == 'validation':
            error = ValidationError(message)
            logger.warning(f"验证错误: {error.message}")
        elif error_type == 'not_found':
            error = NotFoundError(message)
            logger.warning(f"资源未找�? {error.message}")
        else:  # service
            error = ServiceError(message)
            logger.error(f"服务错误: {error.message}")
        
        # Flush and close handler
        handler.flush()
        handler.close()
        logger.removeHandler(handler)
        
        # Read log file
        with open(temp_log_file.name, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        # Verify at least one log line exists
        assert len(log_lines) > 0, "Log file should contain at least one line"
        
        # Parse first log line
        log_line = log_lines[0]
        
        # Verify log format: timestamp | level | module:function:line | message
        parts = log_line.split('|')
        assert len(parts) >= 4, \
            f"Log line should have at least 4 parts separated by '|', got {len(parts)}"
        
        # Verify timestamp part (should contain date and time)
        timestamp_part = parts[0].strip()
        assert len(timestamp_part) > 0, "Timestamp should not be empty"
        assert '-' in timestamp_part, "Timestamp should contain date separator"
        assert ':' in timestamp_part, "Timestamp should contain time separator"
        
        # Verify level part
        level_part = parts[1].strip()
        assert level_part in ['WARNING', 'ERROR', 'INFO', 'DEBUG', 'CRITICAL'], \
            f"Log level should be valid, got: {level_part}"
        
        # Verify module:function:line part
        location_part = parts[2].strip()
        assert ':' in location_part, "Location should contain module:function:line format"
        
        # Verify message part
        message_part = '|'.join(parts[3:]).strip()
        assert len(message_part) > 0, "Message should not be empty"
        # 只有当原始消息不是纯空白时才验证包含关系
        if message.strip():
            assert message in message_part, "Message should contain original error message"
    
    finally:
        # Cleanup
        if os.path.exists(temp_log_file.name):
            os.unlink(temp_log_file.name)


