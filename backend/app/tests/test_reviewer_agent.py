"""评审 Agent 测试"""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.reviewer import ReviewerAgent
from app.llm.base import LLMResponse


@pytest.mark.asyncio
async def test_reviewer_agent_mock():
    """测试评审 Agent（使用 Mock）"""
    # 创建 Mock LLM
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(
            text="""总体评价: 通过

详细评分:
- 规范性: 9
- 完整性: 8
- 可执行性: 9
- 数据真实性: 9
- 覆盖度: 8

问题列表:
无

改进建议:
继续保持高质量的用例编写""",
            model="test-model",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
        )
    )

    agent = ReviewerAgent(mock_llm)
    test_cases = [
        {
            "title": "用户登录测试",
            "steps": "1. 打开登录页面 2. 输入用户名密码 3. 点击登录",
            "expected_results": "登录成功",
        }
    ]

    result = await agent.run({"test_cases": test_cases})

    assert result.success is True
    assert "passed" in result.data
    assert result.data["passed"] is True
    assert "scores" in result.data
    assert result.data["scores"]["规范性"] == 9


@pytest.mark.asyncio
async def test_reviewer_agent_with_issues():
    """测试评审 Agent 发现问题的情况"""
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(
            text="""总体评价: 不通过

详细评分:
- 规范性: 6
- 完整性: 5
- 可执行性: 7
- 数据真实性: 4
- 覆盖度: 6

问题列表:
用例 1: 测试数据使用了 "XXX" 等模糊字眼
用例 2: 缺少前置条件说明

改进建议:
1. 使用真实的测试数据
2. 补充前置条件""",
            model="test-model",
            usage={},
        )
    )

    agent = ReviewerAgent(mock_llm)
    test_cases = [
        {
            "title": "用户登录测试",
            "steps": "1. 输入用户名 XXX 2. 点击登录",
            "expected_results": "登录成功",
        }
    ]

    result = await agent.run({"test_cases": test_cases})

    assert result.success is True
    assert result.data["passed"] is False
    assert len(result.data["issues"]) >= 1


    assert len(result.data["suggestions"]) >= 1


@pytest.mark.asyncio
async def test_reviewer_agent_missing_test_cases():
    """测试缺少测试用例的情况"""
    mock_llm = MagicMock()
    agent = ReviewerAgent(mock_llm)

    result = await agent.run({"test_cases": []})

    assert result.success is False
    assert "测试用例" in result.error


@pytest.mark.asyncio
async def test_reviewer_agent_quick_review():
    """测试快速评审功能"""
    mock_llm = MagicMock()
    agent = ReviewerAgent(mock_llm)

    # 测试用例包含模糊数据
    test_cases = [
        {
            "title": "测试用例",
            "steps": "1. 输入XXX测试数据",
            "expected_results": "比如登录成功",
        }
    ]

    result = await agent.quick_review(test_cases)

    # quick_review 返回字典，不是 AgentResponse
    assert result["passed"] is False
    assert len(result["issues"]) > 0


@pytest.mark.asyncio
async def test_validate_output():
    """测试输出验证"""
    mock_llm = MagicMock()
    agent = ReviewerAgent(mock_llm)

    # 有效的评审结果
    valid_result = {"passed": True, "scores": {}, "issues": [], "suggestions": []}
    assert await agent.validate_output(valid_result) is True

    # 无效的评审结果（缺少 passed 字段）
    invalid_result = {"scores": {}}
    assert await agent.validate_output(invalid_result) is False


@pytest.mark.asyncio
async def test_reviewer_agent_with_real_llm():
    """测试评审 Agent（使用真实 LLM，需要 API Key）"""
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        pytest.skip("需要 GLM_API_KEY 环境变量")

    from app.llm.factory import create_llm_provider

    llm = create_llm_provider("glm", api_key=api_key)
    agent = ReviewerAgent(llm)

    test_cases = [
        {
            "title": "用户登录测试",
            "steps": "1. 打开登录页面\n2. 输入用户名密码\n3. 点击登录",
            "expected_results": "登录成功",
        }
    ]

    result = await agent.run({"test_cases": test_cases})

    assert result.success is True
    assert "passed" in result.data
    assert "feedback" in result.data
