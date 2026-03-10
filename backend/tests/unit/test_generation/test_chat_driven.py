"""B-M05-08 — 对话驱动用例生成引擎测试"""

from __future__ import annotations

from unittest.mock import patch


class TestChatDrivenBuild:
    """测试对话驱动 task instruction 和消息构建。"""

    def test_build_task_instruction(self):
        from app.engine.case_gen.chat_driven import build_task_instruction

        result = build_task_instruction("数据导入", "CSV 批量导入功能")
        assert "数据导入" in result
        assert "CSV 批量导入" in result
        assert "对话引导策略" in result

    def test_build_task_with_existing_cases(self):
        from app.engine.case_gen.chat_driven import build_task_instruction

        existing = [{"title": "正常导入", "priority": "P0"}]
        result = build_task_instruction("数据导入", "内容", existing_cases=existing)
        assert "已生成用例" in result
        assert "正常导入" in result

    def test_build_messages(self):
        from app.engine.case_gen.chat_driven import build_messages

        history = [
            {"role": "user", "content": "帮我生成用例"},
            {"role": "assistant", "content": "好的，请问..."},
        ]
        result = build_messages(history, "测试异常场景")

        assert len(result) == 3
        assert result[-1]["role"] == "user"
        assert result[-1]["content"] == "测试异常场景"


class TestChatDrivenGenerate:
    """测试非流式对话生成（mock LLM）。"""

    async def test_chat_generate(self):
        """应返回 (full_text, parsed_cases) 元组。"""

        async def fake_stream(*args, **kwargs):
            yield 'event: content\ndata: {"delta": "好的"}\n\n'
            yield 'event: content\ndata: {"delta": "，生成用例"}\n\n'

        parsed_cases = [
            {
                "title": "空文件导入",
                "precondition": "准备空 CSV 文件",
                "priority": "P1",
                "case_type": "exception",
                "steps": [],
            }
        ]

        with (
            patch(
                "app.engine.case_gen.chat_driven.get_thinking_stream_with_fallback",
                return_value=fake_stream(),
            ),
            patch("app.engine.case_gen.chat_driven.assemble_prompt", return_value="system"),
            patch("app.engine.case_gen.chat_driven.parse_test_cases", return_value=parsed_cases),
        ):
            from app.engine.case_gen.chat_driven import chat_driven_generate

            full_text, cases = await chat_driven_generate(
                requirement_title="数据导入",
                requirement_content="CSV 批量导入",
                history=[],
                current_message="生成异常场景用例",
            )

        assert "好的" in full_text
        assert len(cases) == 1
        assert cases[0]["title"] == "空文件导入"
        assert cases[0]["source"] == "ai"

    async def test_chat_generate_no_cases(self):
        """追问阶段不产生用例时 parsed_cases 应为空。"""

        async def fake_stream(*args, **kwargs):
            yield 'event: content\ndata: {"delta": "请问您要测试哪些场景？"}\n\n'

        with (
            patch(
                "app.engine.case_gen.chat_driven.get_thinking_stream_with_fallback",
                return_value=fake_stream(),
            ),
            patch("app.engine.case_gen.chat_driven.assemble_prompt", return_value="system"),
            patch("app.engine.case_gen.chat_driven.parse_test_cases", return_value=[]),
        ):
            from app.engine.case_gen.chat_driven import chat_driven_generate

            full_text, cases = await chat_driven_generate(
                requirement_title="需求",
                requirement_content="内容",
                history=[],
                current_message="你好",
            )

        assert len(cases) == 0
        assert "请问" in full_text
