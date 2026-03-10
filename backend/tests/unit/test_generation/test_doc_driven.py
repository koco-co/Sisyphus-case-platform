"""B-M05-08 / T-UNIT-06 — 文档驱动用例生成引擎测试"""

from __future__ import annotations

from unittest.mock import patch


class TestBuildTaskInstruction:
    """测试 doc_driven task instruction 构建。"""

    def test_basic_instruction(self):
        from app.engine.case_gen.doc_driven import build_task_instruction

        result = build_task_instruction("用户登录", "实现基于 JWT 的用户登录功能")

        assert "用户登录" in result
        assert "JWT" in result
        assert "JSON 数组" in result

    def test_with_scope(self):
        from app.engine.case_gen.doc_driven import build_task_instruction

        result = build_task_instruction("用户登录", "内容", scope="仅测试异常场景")

        assert "测试范围限定" in result
        assert "仅测试异常场景" in result


class TestExtractContentFromSse:
    """测试 SSE 内容提取。"""

    def test_extract(self):
        from app.engine.case_gen.doc_driven import _extract_content_from_sse

        sse = (
            'event: thinking\ndata: {"delta": "思考"}\n\n'
            'event: content\ndata: {"delta": "用例1"}\n\n'
            'event: content\ndata: {"delta": "用例2"}\n\n'
        )
        result = _extract_content_from_sse(sse)
        assert result == "用例1用例2"


class TestDocDrivenGenerate:
    """测试非流式文档驱动生成（mock LLM）。"""

    async def test_generate_from_doc(self):
        """应返回标准化用例列表。"""

        async def fake_stream(*args, **kwargs):
            yield 'event: content\ndata: {"delta": "fake"}\n\n'

        parsed_cases = [
            {
                "title": "正常登录",
                "precondition": "用户已注册",
                "priority": "P0",
                "case_type": "normal",
                "steps": [
                    {"step_num": 1, "action": "输入用户名密码", "expected_result": "登录成功"},
                ],
            }
        ]

        with (
            patch(
                "app.engine.case_gen.doc_driven.get_thinking_stream_with_fallback",
                return_value=fake_stream(),
            ),
            patch("app.engine.case_gen.doc_driven.assemble_prompt", return_value="system"),
            patch("app.engine.case_gen.doc_driven.parse_test_cases", return_value=parsed_cases),
        ):
            from app.engine.case_gen.doc_driven import doc_driven_generate

            result = await doc_driven_generate("用户登录", "JWT 登录")

        assert len(result) == 1
        assert result[0]["title"] == "正常登录"
        assert result[0]["source"] == "ai"
        assert result[0]["priority"] == "P0"


class TestStandardizeCases:
    """测试用例标准化。"""

    def test_defaults(self):
        from app.engine.case_gen.doc_driven import _standardize_cases

        raw = [{"title": "测试A"}]
        result = _standardize_cases(raw)

        assert result[0]["precondition"] == ""
        assert result[0]["priority"] == "P1"
        assert result[0]["case_type"] == "normal"
        assert result[0]["source"] == "ai"
