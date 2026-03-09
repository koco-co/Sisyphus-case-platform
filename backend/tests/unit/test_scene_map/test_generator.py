"""B-M04-06 — 场景地图生成引擎测试"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


class TestBuildTaskInstruction:
    """测试 task instruction 构建。"""

    def test_basic_instruction(self):
        from app.engine.scene_map.generator import build_task_instruction

        result = build_task_instruction("数据同步需求", "实现 MySQL 到 Hive 的增量同步")

        assert "数据同步需求" in result
        assert "MySQL 到 Hive" in result
        assert "JSON 数组" in result

    def test_with_existing_points(self):
        from app.engine.scene_map.generator import build_task_instruction

        existing = [
            {"group_name": "正常流程", "title": "增量同步正常执行"},
            {"group_name": "异常场景", "title": "源端连接中断"},
        ]
        result = build_task_instruction("数据同步需求", "内容", existing_points=existing)

        assert "已有测试点" in result
        assert "增量同步正常执行" in result
        assert "源端连接中断" in result

    def test_without_existing_points(self):
        from app.engine.scene_map.generator import build_task_instruction

        result = build_task_instruction("需求", "内容", existing_points=None)

        assert "已有测试点" not in result


class TestExtractContentFromSse:
    """测试 SSE 文本内容提取。"""

    def test_extract_content(self):
        from app.engine.scene_map.generator import extract_content_from_sse

        sse_text = (
            'event: thinking\ndata: {"delta": "思考中..."}\n\n'
            'event: content\ndata: {"delta": "测试点1"}\n\n'
            'event: content\ndata: {"delta": "测试点2"}\n\n'
            "event: done\ndata: {}\n\n"
        )
        result = extract_content_from_sse(sse_text)

        assert result == "测试点1测试点2"

    def test_extract_empty_sse(self):
        from app.engine.scene_map.generator import extract_content_from_sse

        result = extract_content_from_sse("")
        assert result == ""


class TestGenerateSceneMap:
    """测试非流式场景地图生成（mock LLM）。"""

    async def test_generate_scene_map(self):
        """应返回标准化测试点列表。"""
        sse_output = (
            'event: content\ndata: {"delta": "["}\n\n'
            'event: content\ndata: {"delta": "{\\"group_name\\": \\"正常流程\\", '
            '\\"title\\": \\"增量同步正常执行\\", '
            '\\"description\\": \\"验证正常增量同步\\", '
            '\\"priority\\": \\"P0\\", '
            '\\"estimated_cases\\": 3}"}\n\n'
            'event: content\ndata: {"delta": "]"}\n\n'
        )

        async def fake_stream(*args, **kwargs):
            for chunk in sse_output.split("\n\n"):
                if chunk.strip():
                    yield chunk + "\n\n"

        with (
            patch(
                "app.engine.scene_map.generator.get_thinking_stream_with_fallback",
                return_value=fake_stream(),
            ),
            patch("app.engine.scene_map.generator.assemble_prompt", return_value="system"),
            patch(
                "app.engine.scene_map.generator.parse_test_points",
                return_value=[
                    {
                        "group_name": "正常流程",
                        "title": "增量同步正常执行",
                        "description": "验证正常增量同步",
                        "priority": "P0",
                        "estimated_cases": 3,
                    }
                ],
            ),
        ):
            from app.engine.scene_map.generator import generate_scene_map

            result = await generate_scene_map("数据同步需求", "实现增量同步")

        assert len(result) == 1
        assert result[0]["group_name"] == "正常流程"
        assert result[0]["title"] == "增量同步正常执行"
        assert result[0]["source"] == "ai"
        assert result[0]["priority"] == "P0"


class TestStandardizePoints:
    """测试测试点标准化。"""

    def test_standardize_defaults(self):
        from app.engine.scene_map.generator import _standardize_points

        raw = [{"title": "测试点A"}]
        result = _standardize_points(raw)

        assert result[0]["group_name"] == "未分组"
        assert result[0]["priority"] == "P1"
        assert result[0]["estimated_cases"] == 3
        assert result[0]["source"] == "ai"
