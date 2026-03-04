"""编排器测试"""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.orchestrator import AgentOrchestrator
from app.llm.base import LLMResponse


@pytest.mark.asyncio
async def test_orchestrator_workflow():
    """测试编排器工作流"""
    # 创建 Mock LLM
    mock_generator_llm = MagicMock()
    mock_reviewer_llm = MagicMock()

    # 设置 Mock 返回值
    mock_generator_llm.generate = AsyncMock(
        return_value=LLMResponse(
            text="所属模块,用例标题,前置条件,步骤,预期,关键词,优先级,用例类型,适用阶段\n登录模块,用户正常登录,用户已注册,1.打开登录页面 2.输入用户名testuser 3.输入密码Test@123 4.点击登录按钮,登录成功,登录,2,功能测试,功能测试阶段\n登录模块,密码错误登录,用户已注册,1.打开登录页面 2.输入用户名testuser 3.输入密码WrongPwd 4.点击登录按钮,提示密码错误,登录,2,功能测试,功能测试阶段",
            model="test-model",
            usage={},
        )
    )

    mock_reviewer_llm.generate = AsyncMock(
        return_value=LLMResponse(
            text="总体评价: 通过\n详细评分:\n- 规范性: 9\n- 完整性: 8\n- 可执行性: 9\n- 数据真实性: 9\n- 覆盖度: 8",
            model="test-model",
            usage={},
        )
    )

    orchestrator = AgentOrchestrator(
        generator_llm=mock_generator_llm,
        reviewer_llm=mock_reviewer_llm,
        max_retries=3,
    )

    # 测试基本流程
    result = await orchestrator.generate_with_review(
        {
            "requirement": "用户登录功能",
            "test_points": ["验证正常登录", "验证密码错误"],
            "examples": [],
        }
    )

    assert result["success"] is True
    assert "test_cases" in result
    assert len(result["test_cases"]) == 2


@pytest.mark.asyncio
async def test_orchestrator_with_retry():
    """测试编排器重试机制"""
    # 创建 Mock LLM
    mock_generator_llm = MagicMock()
    mock_reviewer_llm = MagicMock()

    call_count = [0]

    async def mock_review_generate(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            # 第一次评审不通过
            return LLMResponse(
                text="总体评价: 不通过\n问题列表:\n用例 1: 测试数据不真实",
                model="test-model",
                usage={},
            )
        else:
            # 第二次评审通过
            return LLMResponse(
                text="总体评价: 通过",
                model="test-model",
                usage={},
            )

    mock_generator_llm.generate = AsyncMock(
        return_value=LLMResponse(
            text="所属模块,用例标题,前置条件,步骤,预期,关键词,优先级,用例类型,适用阶段\n登录模块,用户登录,无,1.打开登录页面 2.输入凭证 3.点击登录,登录成功,登录,2,功能测试,功能测试阶段",
            model="test-model",
            usage={},
        )
    )

    mock_reviewer_llm.generate = mock_review_generate

    orchestrator = AgentOrchestrator(
        generator_llm=mock_generator_llm,
        reviewer_llm=mock_reviewer_llm,
        max_retries=3,
    )

    result = await orchestrator.generate_with_review(
        {
            "requirement": "用户登录功能",
            "test_points": ["验证正常登录"],
            "examples": [],
        }
    )

    assert result["success"] is True
    assert result["attempts"] == 2


@pytest.mark.asyncio
async def test_orchestrator_max_retries_exceeded():
    """测试超过最大重试次数"""
    # 创建 Mock LLM
    mock_generator_llm = MagicMock()
    mock_reviewer_llm = MagicMock()

    mock_generator_llm.generate = AsyncMock(
        return_value=LLMResponse(
            text="所属模块,用例标题,前置条件,步骤,预期,关键词,优先级,用例类型,适用阶段\n登录模块,用户登录,无,1.输入XXX 2.点击登录,登录成功,登录,2,功能测试,功能测试阶段",
            model="test-model",
            usage={},
        )
    )

    mock_reviewer_llm.generate = AsyncMock(
        return_value=LLMResponse(
            text="总体评价: 不通过\n问题列表:\n用例 1: 测试数据使用了XXX等模糊字眼",
            model="test-model",
            usage={},
        )
    )

    orchestrator = AgentOrchestrator(
        generator_llm=mock_generator_llm,
        reviewer_llm=mock_reviewer_llm,
        max_retries=2,
    )

    result = await orchestrator.generate_with_review(
        {
            "requirement": "用户登录功能",
            "test_points": ["验证正常登录"],
            "examples": [],
        }
    )

    assert result["success"] is True
    assert result["review_passed"] is False
    assert result["attempts"] == 2
    assert "warning" in result


@pytest.mark.asyncio
async def test_orchestrator_with_real_llm():
    """测试编排器（使用真实 LLM，需要 API Key)"""
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        pytest.skip("需要 GLM_API_KEY 环境变量")

    from app.llm.factory import create_llm_provider

    llm = create_llm_provider("glm", api_key=api_key)
    orchestrator = AgentOrchestrator(
        generator_llm=llm,
        reviewer_llm=llm,
        max_retries=2
    )

    result = await orchestrator.generate_with_review(
        {
            "requirement": "用户登录功能：输入用户名和密码登录系统",
            "test_points": ["验证正常登录"],
            "examples": [],
        }
    )

    assert result["success"] is True
    assert "test_cases" in result
    assert len(result["test_cases"]) > 0
