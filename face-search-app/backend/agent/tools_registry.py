# -*- coding: utf-8 -*-
"""
工具注册模块
将原有 /api/search、/api/export 的核心逻辑封装为 LangChain Tool 函数
Agent 通过调用这些工具复用原有业务逻辑，实现与接口层解耦
"""

import os
import sys
import json
import time
from typing import Any

# 将 backend 目录加入 Python 路径，以便导入原有模块
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from face_detection import FaceDetectionModule
from face_search import FaceSearchModule
from image_export import ImageExportModule
from config import DEFAULT_SIMILARITY_THRESHOLD

# 初始化原有模块实例（复用，不重复创建）
_face_detector = FaceDetectionModule()
_face_searcher = FaceSearchModule()
_image_exporter = ImageExportModule()


def validate_directory_tool(directory: str, create_if_missing: bool = False) -> str:
    """
    验证目录是否存在，可选自动创建
    
    封装目录校验逻辑，供 Agent 在执行搜索/转存前调用。
    
    Args:
        directory: 要验证的目录路径
        create_if_missing: 目录不存在时是否自动创建，默认 False
        
    Returns:
        JSON 字符串，包含 success、exists、created、message 字段
    """
    result = {"directory": directory, "exists": False, "created": False, "success": False, "message": ""}

    try:
        if os.path.exists(directory):
            if os.path.isdir(directory):
                result["exists"] = True
                result["success"] = True
                result["message"] = f"目录存在: {directory}"
            else:
                result["message"] = f"路径存在但不是目录: {directory}"
        elif create_if_missing:
            os.makedirs(directory, exist_ok=True)
            result["exists"] = True
            result["created"] = True
            result["success"] = True
            result["message"] = f"目录已创建: {directory}"
        else:
            result["message"] = f"目录不存在: {directory}"

        # 检查读写权限
        if result["exists"]:
            if not os.access(directory, os.R_OK):
                result["success"] = False
                result["message"] = f"目录无读取权限: {directory}"
            elif create_if_missing and not os.access(directory, os.W_OK):
                result["success"] = False
                result["message"] = f"目录无写入权限: {directory}"

    except PermissionError as e:
        result["message"] = f"权限不足，无法创建目录: {directory}，错误: {str(e)}"
    except Exception as e:
        result["message"] = f"目录验证失败: {str(e)}"

    return json.dumps(result, ensure_ascii=False)


def search_faces_tool(
    image_path: str,
    search_folder: str,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD
) -> str:
    """
    人像搜索工具
    
    封装原有 FaceDetectionModule + FaceSearchModule 的核心逻辑。
    检测目标图片中的人脸，然后在 search_folder 中搜索匹配的照片。
    原有 /api/search 接口不受影响。
    
    Args:
        image_path: 目标人像图片的本地路径
        search_folder: 要搜索的目录路径
        threshold: 相似度阈值（0-1），默认使用配置值
        
    Returns:
        JSON 字符串，包含 success、matches、total_processed、error 字段
    """
    result = {
        "success": False,
        "matches": [],
        "total_processed": 0,
        "match_count": 0,
        "error": None
    }

    try:
        # 1. 验证目标图片存在
        if not os.path.exists(image_path):
            result["error"] = f"目标图片不存在: {image_path}"
            return json.dumps(result, ensure_ascii=False)

        # 2. 验证搜索目录存在
        if not os.path.exists(search_folder) or not os.path.isdir(search_folder):
            result["error"] = f"搜索目录不存在或不是目录: {search_folder}"
            return json.dumps(result, ensure_ascii=False)

        # 3. 检测目标图片中的人脸
        detection_result = _face_detector.detectFaces(image_path)
        if detection_result.error or not detection_result.faces:
            result["error"] = f"目标图片中未检测到人脸: {detection_result.error or '无人脸'}"
            return json.dumps(result, ensure_ascii=False)

        # 4. 使用第一个检测到的人脸作为搜索目标
        target_face = detection_result.faces[0]
        target_features = target_face.features

        # 5. 执行搜索（复用原有 FaceSearchModule 逻辑）
        search_result = _face_searcher.searchFaces(
            targetFeatures=target_features,
            searchFolder=search_folder,
            threshold=float(threshold)
        )

        # 6. 整理结果
        matches_data = []
        for match in search_result.matches:
            matches_data.append({
                "image_path": match.imagePath,
                "similarity": round(match.similarity, 4),
                "face_location": match.faceLocation
            })

        result["success"] = True
        result["matches"] = matches_data
        result["match_count"] = len(matches_data)
        result["total_processed"] = search_result.totalProcessed

    except PermissionError as e:
        result["error"] = f"权限不足，无法读取文件: {str(e)}"
    except Exception as e:
        result["error"] = f"人像搜索失败: {str(e)}"

    return json.dumps(result, ensure_ascii=False)


def search_faces_by_library_tool(
    library_face_id: str,
    search_folder: str,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    base_url: str = "http://localhost:5000"
) -> str:
    """
    通过人像库 ID 搜索工具
    
    从人像库中获取指定人像的特征向量，然后在 search_folder 中搜索匹配照片。
    
    Args:
        library_face_id: 人像库中的人像 ID
        search_folder: 要搜索的目录路径
        threshold: 相似度阈值（0-1）
        base_url: 后端服务地址
        
    Returns:
        JSON 字符串，包含 success、matches、total_processed、error 字段
    """
    result = {
        "success": False,
        "matches": [],
        "total_processed": 0,
        "match_count": 0,
        "error": None
    }

    try:
        import requests

        # 1. 从人像库获取人像特征向量
        resp = requests.get(f"{base_url}/api/library/faces/{library_face_id}", timeout=10)
        if resp.status_code == 404:
            result["error"] = f"人像库中未找到人像: {library_face_id}"
            return json.dumps(result, ensure_ascii=False)
        if resp.status_code != 200:
            result["error"] = f"获取人像信息失败，HTTP {resp.status_code}"
            return json.dumps(result, ensure_ascii=False)

        face_data = resp.json()
        target_features = face_data.get("feature_vector")
        if not target_features:
            result["error"] = "人像库中该人像无特征向量数据"
            return json.dumps(result, ensure_ascii=False)

        # 2. 验证搜索目录
        if not os.path.exists(search_folder) or not os.path.isdir(search_folder):
            result["error"] = f"搜索目录不存在: {search_folder}"
            return json.dumps(result, ensure_ascii=False)

        # 3. 执行搜索（复用原有逻辑）
        search_result = _face_searcher.searchFaces(
            targetFeatures=target_features,
            searchFolder=search_folder,
            threshold=float(threshold)
        )

        matches_data = [
            {
                "image_path": m.imagePath,
                "similarity": round(m.similarity, 4),
                "face_location": m.faceLocation
            }
            for m in search_result.matches
        ]

        result["success"] = True
        result["matches"] = matches_data
        result["match_count"] = len(matches_data)
        result["total_processed"] = search_result.totalProcessed

    except requests.exceptions.ConnectionError:
        result["error"] = "无法连接到后端服务，请确认服务已启动"
    except requests.exceptions.Timeout:
        result["error"] = "请求后端服务超时"
    except PermissionError as e:
        result["error"] = f"权限不足: {str(e)}"
    except Exception as e:
        result["error"] = f"搜索失败: {str(e)}"

    return json.dumps(result, ensure_ascii=False)


def export_images_tool(image_paths: list, target_folder: str) -> str:
    """
    图片转存工具
    
    封装原有 ImageExportModule 的核心逻辑，将匹配的图片复制到目标目录。
    原有 /api/export 接口不受影响。
    
    Args:
        image_paths: 要转存的图片路径列表
        target_folder: 目标目录路径（必须已存在）
        
    Returns:
        JSON 字符串，包含 success、success_count、failed_count、errors 字段
    """
    result = {
        "success": False,
        "success_count": 0,
        "failed_count": 0,
        "errors": [],
        "target_folder": target_folder
    }

    try:
        # 验证参数
        if not image_paths:
            result["errors"].append("图片路径列表为空")
            return json.dumps(result, ensure_ascii=False)

        if not os.path.exists(target_folder):
            result["errors"].append(f"目标目录不存在: {target_folder}，请先调用 validate_directory_tool 创建")
            return json.dumps(result, ensure_ascii=False)

        if not os.access(target_folder, os.W_OK):
            result["errors"].append(f"目标目录无写入权限: {target_folder}")
            return json.dumps(result, ensure_ascii=False)

        # 调用原有导出模块
        export_result = _image_exporter.exportImages(
            imagePaths=image_paths,
            targetFolder=target_folder
        )

        result["success"] = True
        result["success_count"] = export_result.successCount
        result["failed_count"] = export_result.failedCount
        result["errors"] = export_result.errors or []

    except PermissionError as e:
        result["errors"].append(f"权限不足: {str(e)}")
    except Exception as e:
        result["errors"].append(f"转存失败: {str(e)}")

    return json.dumps(result, ensure_ascii=False)


#  LangChain Tool 包装 
# 尝试导入 LangChain，若未安装则提供降级方案

try:
    from langchain.tools import Tool as LangChainTool

    # 将各工具函数包装为 LangChain Tool 对象，供 Agent 使用
    LANGCHAIN_TOOLS = [
        LangChainTool(
            name="validate_directory",
            func=lambda args: validate_directory_tool(**json.loads(args)) if isinstance(args, str) else validate_directory_tool(**args),
            description=(
                "验证目录是否存在，可选自动创建。"
                "输入 JSON：{\"directory\": \"路径\", \"create_if_missing\": true/false}。"
                "返回 JSON 包含 success、exists、created、message 字段。"
            )
        ),
        LangChainTool(
            name="search_faces",
            func=lambda args: search_faces_tool(**json.loads(args)) if isinstance(args, str) else search_faces_tool(**args),
            description=(
                "在指定目录中搜索与目标人像匹配的照片。"
                "输入 JSON：{\"image_path\": \"目标图片路径\", \"search_folder\": \"搜索目录\", \"threshold\": 0.6}。"
                "返回 JSON 包含 success、matches（含 image_path 和 similarity）、match_count 字段。"
            )
        ),
        LangChainTool(
            name="search_faces_by_library",
            func=lambda args: search_faces_by_library_tool(**json.loads(args)) if isinstance(args, str) else search_faces_by_library_tool(**args),
            description=(
                "通过人像库 ID 在指定目录中搜索匹配照片。"
                "输入 JSON：{\"library_face_id\": \"人像ID\", \"search_folder\": \"搜索目录\", \"threshold\": 0.6}。"
                "返回 JSON 包含 success、matches、match_count 字段。"
            )
        ),
        LangChainTool(
            name="export_images",
            func=lambda args: export_images_tool(**json.loads(args)) if isinstance(args, str) else export_images_tool(**args),
            description=(
                "将图片列表转存到目标目录。"
                "输入 JSON：{\"image_paths\": [\"路径1\", \"路径2\"], \"target_folder\": \"目标目录\"}。"
                "返回 JSON 包含 success、success_count、failed_count、errors 字段。"
            )
        ),
    ]
    LANGCHAIN_AVAILABLE = True

except ImportError:
    LANGCHAIN_TOOLS = []
    LANGCHAIN_AVAILABLE = False
    print("[tools_registry] LangChain 未安装，LANGCHAIN_TOOLS 为空，将使用直接调用模式")
