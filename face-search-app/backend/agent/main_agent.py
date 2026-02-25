# -*- coding: utf-8 -*-
"""
Agent 主逻辑模块
接收自然语言指令，自动拆分任务并调用工具完成人像搜索+转存流程
支持 LangChain 框架（优先）和直接调用降级模式
"""

import json
import os
import sys
import uuid
from typing import Optional, Dict, Any

# 将 backend 目录加入路径
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from agent.prompt_template import SYSTEM_PROMPT, TASK_PARSE_PROMPT, RESULT_REPORT_TEMPLATE
from agent.memory_manager import MemoryManager
from agent.tools_registry import (
    validate_directory_tool,
    search_faces_tool,
    search_faces_by_library_tool,
    export_images_tool,
    LANGCHAIN_AVAILABLE,
    LANGCHAIN_TOOLS
)


class FaceSearchAgent:
    """
    人像搜索 Agent
    
    接收自然语言指令，自动完成：
    1. 目录校验（搜索目录 + 转存目录）
    2. 人像搜索（调用 search_faces_tool）
    3. 结果转存（调用 export_images_tool）
    4. 异常处理与结果汇报
    
    优先使用 LangChain ReAct Agent，若未安装则降级为直接调用模式。
    """

    def __init__(
        self,
        llm_api_key: Optional[str] = None,
        llm_model: str = "gpt-3.5-turbo",
        memory_persist_path: Optional[str] = None,
        base_url: str = "http://localhost:5000"
    ):
        """
        初始化 Agent
        
        Args:
            llm_api_key: LLM API 密钥（OpenAI 等），None 时使用环境变量 OPENAI_API_KEY
            llm_model: 使用的 LLM 模型名称
            memory_persist_path: 记忆持久化文件路径
            base_url: 后端服务地址，用于人像库查询
        """
        self.base_url = base_url
        self.memory = MemoryManager(persist_path=memory_persist_path)
        self._langchain_agent = None

        # 尝试初始化 LangChain Agent
        if LANGCHAIN_AVAILABLE:
            self._init_langchain_agent(llm_api_key, llm_model)

    def _init_langchain_agent(self, api_key: Optional[str], model: str):
        """初始化 LangChain ReAct Agent"""
        try:
            from langchain.chat_models import ChatOpenAI
            from langchain.agents import initialize_agent, AgentType

            # 获取 API Key（优先参数，其次环境变量）
            key = api_key or os.environ.get("OPENAI_API_KEY")
            if not key:
                print("[FaceSearchAgent] 未提供 OPENAI_API_KEY，LangChain Agent 不可用，将使用直接调用模式")
                return

            llm = ChatOpenAI(
                model_name=model,
                temperature=0,
                openai_api_key=key
            )

            self._langchain_agent = initialize_agent(
                tools=LANGCHAIN_TOOLS,
                llm=llm,
                agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                handle_parsing_errors=True,
                agent_kwargs={"system_message": SYSTEM_PROMPT}
            )
            print(f"[FaceSearchAgent] LangChain Agent 初始化成功，模型: {model}")

        except ImportError:
            print("[FaceSearchAgent] LangChain 导入失败，使用直接调用模式")
        except Exception as e:
            print(f"[FaceSearchAgent] LangChain Agent 初始化失败: {e}，使用直接调用模式")

    def run(
        self,
        instruction: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行自然语言指令
        
        Args:
            instruction: 用户自然语言指令，例如：
                "在 /photos 目录找张三的照片并转存到 /backup/张三"
            session_id: 会话 ID，用于记忆管理
            
        Returns:
            执行结果字典，包含 success、message、details 字段
        """
        if not session_id:
            session_id = str(uuid.uuid4())[:8]

        print(f"\n[Agent] 收到指令: {instruction}")

        # 优先使用 LangChain Agent
        if self._langchain_agent:
            return self._run_with_langchain(instruction, session_id)
        else:
            return self._run_direct(instruction, session_id)

    def _run_with_langchain(self, instruction: str, session_id: str) -> Dict[str, Any]:
        """使用 LangChain ReAct Agent 执行指令"""
        try:
            response = self._langchain_agent.run(instruction)
            result = {"success": True, "message": response, "details": {}, "mode": "langchain"}
            self.memory.add_record(instruction, {}, result, session_id)
            return result
        except Exception as e:
            print(f"[Agent] LangChain 执行失败，降级到直接调用模式: {e}")
            return self._run_direct(instruction, session_id)

    def _run_direct(self, instruction: str, session_id: str) -> Dict[str, Any]:
        """
        直接调用模式（不依赖 LLM）
        
        解析指令中的路径信息，按固定流程执行：
        目录校验  人像搜索  结果转存
        """
        params = self._parse_instruction(instruction)
        details = {}
        errors = []

        print(f"[Agent] 解析参数: {json.dumps(params, ensure_ascii=False)}")

        #  步骤 1：校验搜索目录 
        search_folder = params.get("search_folder")
        if not search_folder:
            return {
                "success": False,
                "message": "无法从指令中解析搜索目录，请明确指定搜索路径",
                "details": {},
                "mode": "direct"
            }

        dir_check = json.loads(validate_directory_tool(search_folder, create_if_missing=False))
        if not dir_check["success"]:
            return {
                "success": False,
                "message": f"搜索目录验证失败: {dir_check['message']}",
                "details": {"directory_check": dir_check},
                "mode": "direct"
            }
        print(f"[Agent] 搜索目录验证通过: {search_folder}")

        #  步骤 2：校验并创建转存目录 
        target_folder = params.get("target_folder")
        folder_created = False
        if target_folder:
            dir_check2 = json.loads(validate_directory_tool(target_folder, create_if_missing=True))
            if not dir_check2["success"]:
                errors.append(f"转存目录创建失败: {dir_check2['message']}")
                target_folder = None  # 转存目录不可用，跳过转存步骤
            else:
                folder_created = dir_check2.get("created", False)
                if folder_created:
                    print(f"[Agent] 转存目录已自动创建: {target_folder}")
                else:
                    print(f"[Agent] 转存目录已存在: {target_folder}")
            details["directory_check"] = dir_check2

        #  步骤 3：执行人像搜索 
        image_path = params.get("image_path")
        library_face_id = params.get("library_face_id")
        threshold = float(params.get("threshold", 0.6))

        search_result_raw = None
        if library_face_id:
            print(f"[Agent] 使用人像库 ID 搜索: {library_face_id}")
            search_result_raw = json.loads(
                search_faces_by_library_tool(library_face_id, search_folder, threshold, self.base_url)
            )
        elif image_path:
            print(f"[Agent] 使用图片文件搜索: {image_path}")
            search_result_raw = json.loads(
                search_faces_tool(image_path, search_folder, threshold)
            )
        else:
            return {
                "success": False,
                "message": "未提供搜索目标（需要图片路径或人像库 ID）",
                "details": details,
                "mode": "direct"
            }

        details["search"] = search_result_raw

        if not search_result_raw.get("success"):
            return {
                "success": False,
                "message": f"人像搜索失败: {search_result_raw.get('error', '未知错误')}",
                "details": details,
                "mode": "direct"
            }

        matches = search_result_raw.get("matches", [])
        match_count = len(matches)
        print(f"[Agent] 搜索完成，找到 {match_count} 个匹配结果")

        if match_count == 0:
            msg = (
                f"搜索完成，未找到匹配的人像。"
                f"已处理 {search_result_raw.get('total_processed', 0)} 张图片。"
                f"建议尝试降低相似度阈值（当前: {threshold}）。"
            )
            result = {"success": True, "message": msg, "details": details, "mode": "direct"}
            self.memory.add_record(instruction, params, result, session_id)
            return result

        #  步骤 4：转存匹配结果 
        export_result_raw = None
        if target_folder:
            image_paths_to_export = [m["image_path"] for m in matches]
            print(f"[Agent] 开始转存 {len(image_paths_to_export)} 张图片到: {target_folder}")
            export_result_raw = json.loads(
                export_images_tool(image_paths_to_export, target_folder)
            )
            details["export"] = export_result_raw

            if export_result_raw.get("errors"):
                errors.extend(export_result_raw["errors"])

        #  步骤 5：生成汇报 
        success_count = export_result_raw["success_count"] if export_result_raw else 0
        failed_count = export_result_raw["failed_count"] if export_result_raw else 0

        extra_lines = []
        if folder_created:
            extra_lines.append(f"- 转存目录已自动创建: {target_folder}")
        if errors:
            extra_lines.append(f"- 错误信息: {'; '.join(errors)}")
        if not target_folder:
            extra_lines.append("- 未指定转存目录，跳过转存步骤")

        message = RESULT_REPORT_TEMPLATE.format(
            search_folder=search_folder,
            target_folder=target_folder or "（未指定）",
            match_count=match_count,
            success_count=success_count,
            failed_count=failed_count,
            extra_info="\n".join(extra_lines)
        )

        final_result = {
            "success": True,
            "message": message.strip(),
            "details": details,
            "mode": "direct"
        }
        self.memory.add_record(instruction, params, final_result, session_id)
        return final_result

    def _parse_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        从自然语言指令中解析任务参数（规则匹配方式，不依赖 LLM）
        
        支持的指令格式示例：
        - "在 D:/photos 目录找张三的照片并转存到 D:/backup/张三"
        - "搜索 /data/images 中的人像，阈值 0.5，转存到 /output"
        
        Args:
            instruction: 用户自然语言指令
            
        Returns:
            解析出的参数字典
        """
        import re
        params: Dict[str, Any] = {"threshold": 0.6}

        # 提取 Windows/Unix 路径（支持中文路径）
        # 匹配形如 D:/path、/path/to/dir、./relative 的路径
        path_pattern = r'[A-Za-z]:[/\\][^\s，,。；;]+|/[^\s，,。；;]+'
        paths = re.findall(path_pattern, instruction)

        # 提取阈值
        threshold_match = re.search(r'阈值\s*([0-9.]+)', instruction)
        if threshold_match:
            try:
                params["threshold"] = float(threshold_match.group(1))
            except ValueError:
                pass

        # 提取人像库 ID（UUID 格式）
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        uuid_match = re.search(uuid_pattern, instruction, re.IGNORECASE)
        if uuid_match:
            params["library_face_id"] = uuid_match.group(0)

        # 根据关键词分配路径角色
        # 规则：含"转存到"/"保存到"/"复制到"后面的路径为目标目录，其余为搜索目录
        transfer_keywords = ["转存到", "保存到", "复制到", "导出到", "存到"]
        search_keywords = ["在", "搜索", "查找", "目录", "文件夹"]

        if len(paths) >= 2:
            # 尝试通过关键词定位转存目录
            target_idx = None
            for kw in transfer_keywords:
                kw_pos = instruction.find(kw)
                if kw_pos != -1:
                    # 找到关键词后最近的路径
                    for i, p in enumerate(paths):
                        if instruction.find(p) > kw_pos:
                            target_idx = i
                            break
                    if target_idx is not None:
                        break

            if target_idx is not None:
                params["target_folder"] = paths[target_idx]
                # 其余路径中第一个作为搜索目录
                search_paths = [p for i, p in enumerate(paths) if i != target_idx]
                if search_paths:
                    params["search_folder"] = search_paths[0]
            else:
                # 无法区分时：第一个为搜索目录，最后一个为转存目录
                params["search_folder"] = paths[0]
                params["target_folder"] = paths[-1]

        elif len(paths) == 1:
            params["search_folder"] = paths[0]

        # 提取图片路径（含图片扩展名的路径）
        img_pattern = r'[A-Za-z]:[/\\][^\s，,。；;]+\.(jpg|jpeg|png|webp)|/[^\s，,。；;]+\.(jpg|jpeg|png|webp)'
        img_match = re.search(img_pattern, instruction, re.IGNORECASE)
        if img_match:
            params["image_path"] = img_match.group(0)
            # 图片路径不应作为搜索目录
            if params.get("search_folder") == params.get("image_path"):
                params.pop("search_folder", None)

        return params
