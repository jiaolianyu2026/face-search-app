"""
日志记录系统配置模块
提供统一的日志记录功能，记录所有错误和警告到日志文件
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from config import LOG_FILE, LOG_LEVEL


def setup_logger(name: str = 'face_recognition_app') -> logging.Logger:
    """
    配置并返回应用程序日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        配置好的 Logger 实例
        
    日志格式包含：
        - 时间戳（精确到毫秒）
        - 日志级别
        - 模块名称
        - 函数名称
        - 行号
        - 日志消息
        - 异常堆栈跟踪（如果有）
    """
    # 获取或创建日志记录器
    logger = logging.getLogger(name)
    
    # 避免重复配置
    if logger.handlers:
        return logger
    
    # 设置日志级别
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 创建日志格式器
    # 格式：时间戳 | 级别 | 模块:函数:行号 | 消息
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建文件处理器（带日志轮转）
    # 最大 10MB，保留 5 个备份文件
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # 创建控制台处理器（用于开发调试）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # 控制台只显示警告和错误
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 防止日志传播到根日志记录器
    logger.propagate = False
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器实例
    
    Args:
        name: 日志记录器名称，如果为 None 则使用默认名称
        
    Returns:
        Logger 实例
    """
    if name is None:
        name = 'face_recognition_app'
    
    logger = logging.getLogger(name)
    
    # 如果日志记录器还未配置，则进行配置
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


# 创建默认日志记录器实例
default_logger = setup_logger()
