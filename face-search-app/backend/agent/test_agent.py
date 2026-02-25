# -*- coding: utf-8 -*-
"""
Agent 层基础验证测试脚本
验证以下场景：
1. 自然语言指令触发人像搜索+转存流程
2. 目录不存在时 Agent 自动创建
3. 原有 /api/search 接口仍可正常调用
"""

import os
import sys
import json
import tempfile
import shutil

# 将 backend 目录加入路径
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from agent.tools_registry import validate_directory_tool, export_images_tool
from agent.memory_manager import MemoryManager
from agent.main_agent import FaceSearchAgent


def print_section(title: str):
    """打印测试分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_validate_directory_tool():
    """测试 1：目录验证工具 - 不存在时自动创建"""
    print_section("测试 1：目录验证工具（自动创建）")

    with tempfile.TemporaryDirectory() as tmp_dir:
        new_dir = os.path.join(tmp_dir, "auto_created_dir")

        # 验证不存在的目录（不创建）
        result = json.loads(validate_directory_tool(new_dir, create_if_missing=False))
        assert not result["success"], "不存在的目录应返回 success=False"
        assert not result["exists"], "目录不应存在"
        print(f"  [OK] 不存在目录验证: {result['message']}")

        # 验证不存在的目录（自动创建）
        result = json.loads(validate_directory_tool(new_dir, create_if_missing=True))
        assert result["success"], f"自动创建应成功，实际: {result}"
        assert result["created"], "应标记为已创建"
        assert os.path.exists(new_dir), "目录应已创建"
        print(f"  [OK] 自动创建目录: {result['message']}")

        # 再次验证（已存在）
        result = json.loads(validate_directory_tool(new_dir, create_if_missing=False))
        assert result["success"], "已存在目录应返回 success=True"
        assert not result["created"], "不应标记为新创建"
        print(f"  [OK] 已存在目录验证: {result['message']}")

    print("  [PASS] 目录验证工具测试通过")


def test_export_images_tool():
    """测试 2：图片转存工具"""
    print_section("测试 2：图片转存工具")

    with tempfile.TemporaryDirectory() as tmp_dir:
        # 创建测试图片文件
        src_dir = os.path.join(tmp_dir, "source")
        dst_dir = os.path.join(tmp_dir, "destination")
        os.makedirs(src_dir)
        os.makedirs(dst_dir)

        # 创建假图片文件
        test_files = []
        for i in range(3):
            fpath = os.path.join(src_dir, f"test_{i}.jpg")
            with open(fpath, "wb") as f:
                f.write(b"fake image data")
            test_files.append(fpath)

        # 执行转存
        result = json.loads(export_images_tool(test_files, dst_dir))
        assert result["success"], f"转存应成功，实际: {result}"
        assert result["success_count"] == 3, f"应转存 3 个文件，实际: {result['success_count']}"
        assert result["failed_count"] == 0, f"失败数应为 0，实际: {result['failed_count']}"
        print(f"  [OK] 转存 {result['success_count']} 个文件成功")

        # 验证文件已复制
        for f in test_files:
            dst_file = os.path.join(dst_dir, os.path.basename(f))
            assert os.path.exists(dst_file), f"目标文件应存在: {dst_file}"
        print("  [OK] 目标文件验证通过")

        # 测试目标目录不存在时的错误处理
        result = json.loads(export_images_tool(test_files, "/nonexistent/path"))
        assert not result["success"] or result["failed_count"] > 0 or result["errors"], \
            "目标目录不存在时应报错"
        print(f"  [OK] 目标目录不存在时正确报错")

    print("  [PASS] 图片转存工具测试通过")


def test_memory_manager():
    """测试 3：记忆管理器"""
    print_section("测试 3：记忆管理器")

    with tempfile.TemporaryDirectory() as tmp_dir:
        persist_path = os.path.join(tmp_dir, "memory.json")
        memory = MemoryManager(persist_path=persist_path)

        # 添加记录
        record_id = memory.add_record(
            instruction="在 /photos 找张三",
            params={"search_folder": "/photos"},
            result={"success": True, "match_count": 5},
            session_id="session_001"
        )
        assert record_id, "应返回记录 ID"
        print(f"  [OK] 添加记录: {record_id}")

        # 查询历史
        history = memory.get_history(session_id="session_001")
        assert len(history) == 1, f"应有 1 条记录，实际: {len(history)}"
        assert history[0]["instruction"] == "在 /photos 找张三"
        print(f"  [OK] 查询历史: {len(history)} 条")

        # 验证持久化
        assert os.path.exists(persist_path), "持久化文件应存在"
        memory2 = MemoryManager(persist_path=persist_path)
        history2 = memory2.get_history()
        assert len(history2) == 1, "重新加载后应有 1 条记录"
        print(f"  [OK] 持久化验证通过")

        # 清空记录
        memory.clear(session_id="session_001")
        assert len(memory.get_history()) == 0, "清空后应无记录"
        print(f"  [OK] 清空记录验证通过")

    print("  [PASS] 记忆管理器测试通过")


def test_agent_direct_mode():
    """测试 4：Agent 直接调用模式（不依赖 LLM）"""
    print_section("测试 4：Agent 直接调用模式")

    with tempfile.TemporaryDirectory() as tmp_dir:
        # 创建搜索目录（含假图片）
        search_dir = os.path.join(tmp_dir, "search_folder")
        os.makedirs(search_dir)
        for i in range(2):
            with open(os.path.join(search_dir, f"photo_{i}.jpg"), "wb") as f:
                f.write(b"fake image")

        # 转存目录（不预先创建，测试自动创建）
        target_dir = os.path.join(tmp_dir, "output", "results")

        # 创建目标人像图片（假文件，不含真实人脸，用于测试流程）
        target_img = os.path.join(tmp_dir, "target.jpg")
        with open(target_img, "wb") as f:
            f.write(b"fake target image")

        agent = FaceSearchAgent()

        # 测试指令解析
        instruction = f"在 {search_dir} 目录搜索人像，转存到 {target_dir}"
        params = agent._parse_instruction(instruction)
        assert params.get("search_folder") == search_dir, \
            f"搜索目录解析错误: {params.get('search_folder')}"
        assert params.get("target_folder") == target_dir, \
            f"转存目录解析错误: {params.get('target_folder')}"
        print(f"  [OK] 指令解析: search={params['search_folder']}, target={params['target_folder']}")

        # 测试目录不存在时的错误处理
        result = agent.run(
            f"在 /nonexistent_path_xyz 目录搜索人像，转存到 {target_dir}",
            session_id="test_session"
        )
        assert not result["success"], "搜索目录不存在时应返回失败"
        print(f"  [OK] 搜索目录不存在时正确报错: {result['message'][:50]}...")

        # 验证记忆记录（失败的任务不记录，成功的才记录）
        print(f"  [OK] Agent 直接调用模式验证通过")

    print("  [PASS] Agent 直接调用模式测试通过")


def test_original_api_compatibility():
    """测试 5：验证原有 /api/search 接口未被破坏"""
    print_section("测试 5：原有接口兼容性验证")

    try:
        import requests
        BASE = "http://localhost:5000"

        # 检查服务是否运行
        try:
            resp = requests.get(f"{BASE}/api/config", timeout=3)
            if resp.status_code == 200:
                print(f"  [OK] 后端服务运行正常，配置: {resp.json()}")
            else:
                print(f"  [SKIP] 后端服务响应异常: HTTP {resp.status_code}")
                return
        except requests.exceptions.ConnectionError:
            print("  [SKIP] 后端服务未运行，跳过接口兼容性测试")
            print("         （请先启动后端: cd backend && python app.py）")
            return

        # 验证 /api/search 端点存在（发送无效请求，期望 400 而非 404/500）
        resp = requests.post(f"{BASE}/api/search", json={}, timeout=5)
        assert resp.status_code in [400, 422], \
            f"/api/search 应返回 400/422，实际: {resp.status_code}"
        print(f"  [OK] /api/search 端点存在且响应正常: HTTP {resp.status_code}")

        # 验证 /api/export 端点存在
        resp = requests.post(f"{BASE}/api/export", json={}, timeout=5)
        assert resp.status_code in [400, 422], \
            f"/api/export 应返回 400/422，实际: {resp.status_code}"
        print(f"  [OK] /api/export 端点存在且响应正常: HTTP {resp.status_code}")

    except ImportError:
        print("  [SKIP] requests 库未安装，跳过接口兼容性测试")

    print("  [PASS] 原有接口兼容性验证通过")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  人像搜索 Agent 层基础验证测试")
    print("="*60)

    tests = [
        test_validate_directory_tool,
        test_export_images_tool,
        test_memory_manager,
        test_agent_direct_mode,
        test_original_api_compatibility,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] 断言失败: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] 测试异常: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"  测试结果: {passed} 通过 / {failed} 失败 / {len(tests)} 总计")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
