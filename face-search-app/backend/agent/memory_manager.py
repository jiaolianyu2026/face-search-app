# -*- coding: utf-8 -*-
"""
记忆管理模块
记录 Agent 的执行历史，支持会话级别的上下文保持
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class MemoryManager:
    """
    Agent 执行历史记忆管理器
    
    功能：
    - 记录每次任务的执行参数和结果
    - 支持按会话 ID 查询历史记录
    - 持久化到本地 JSON 文件（可选）
    """

    def __init__(self, persist_path: Optional[str] = None, max_history: int = 100):
        """
        初始化记忆管理器
        
        Args:
            persist_path: 持久化文件路径，None 表示仅内存存储
            max_history: 最大历史记录条数，超出后自动清理最旧记录
        """
        self.persist_path = persist_path
        self.max_history = max_history
        # 内存中的历史记录列表，每条记录为一个字典
        self._history: List[Dict[str, Any]] = []

        # 如果指定了持久化路径，尝试加载已有记录
        if persist_path and os.path.exists(persist_path):
            self._load_from_file()

    def add_record(
        self,
        instruction: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """
        添加一条执行记录
        
        Args:
            instruction: 用户原始指令
            params: 解析出的任务参数
            result: 执行结果摘要
            session_id: 会话 ID（可选）
            
        Returns:
            记录 ID（时间戳字符串）
        """
        record_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        record = {
            "id": record_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "instruction": instruction,
            "params": params,
            "result": result
        }
        self._history.append(record)

        # 超出最大条数时，删除最旧的记录
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]

        # 持久化到文件
        if self.persist_path:
            self._save_to_file()

        return record_id

    def get_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取执行历史记录
        
        Args:
            session_id: 按会话 ID 过滤，None 表示返回所有
            limit: 最多返回条数
            
        Returns:
            历史记录列表（最新的在前）
        """
        records = self._history
        if session_id:
            records = [r for r in records if r.get("session_id") == session_id]
        # 返回最新的 limit 条，倒序排列
        return list(reversed(records[-limit:]))

    def get_last_record(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取最近一条执行记录
        
        Args:
            session_id: 按会话 ID 过滤
            
        Returns:
            最近一条记录，无记录时返回 None
        """
        records = self.get_history(session_id=session_id, limit=1)
        return records[0] if records else None

    def clear(self, session_id: Optional[str] = None):
        """
        清空历史记录
        
        Args:
            session_id: 仅清空指定会话的记录，None 表示清空全部
        """
        if session_id:
            self._history = [r for r in self._history if r.get("session_id") != session_id]
        else:
            self._history = []

        if self.persist_path:
            self._save_to_file()

    def _save_to_file(self):
        """将历史记录持久化到 JSON 文件"""
        try:
            os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
            with open(self.persist_path, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # 持久化失败不影响主流程，仅打印警告
            print(f"[MemoryManager] 持久化历史记录失败: {e}")

    def _load_from_file(self):
        """从 JSON 文件加载历史记录"""
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                self._history = json.load(f)
        except Exception as e:
            print(f"[MemoryManager] 加载历史记录失败: {e}")
            self._history = []
