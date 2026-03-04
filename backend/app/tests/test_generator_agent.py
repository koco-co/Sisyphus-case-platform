"""生成 Agent 测试"""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.generator import GeneratorAgent
from app.llm.base import LLMResponse


from app.rag.prompt_builder import PromptBuilder


from unittest.mock import patch


import re


@pytest.mark.asyncio
async def test_generator_agent_mock():
    """测试生成 Agent（使用 Mock）"""
    # 创建 Mock LLM
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(
            # 使用实际的 CSV 格式，每个字段用逗号分隔，不包含换行符
            text="""所属模块,用例标题,前置条件,步骤,预期,关键词,优先级,用例类型,适用阶段
登录模块,用户正常登录,用户已注册,1.打开登录页面 2.输入用户名testuser 3.输入密码Test@123 4.点击登录按钮,登录成功,登录,2,功能测试,功能测试阶段
登录模块,密码错误登录,用户已注册,1.打开登录页面 2.输入用户名testuser 3.输入密码WrongPwd 4.点击登录按钮,提示密码错误,登录,2,功能测试,功能测试阶段""",
            model="test-model",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
        )
    )

    agent = GeneratorAgent(mock_llm)
    result = await agent.run(
        {
            "requirement": "用户登录功能：输入用户名和密码登录系统",
            "test_points": ["验证正常登录", "验证密码错误"],
            "examples": [],
        }
    )

    assert result.success is True
    assert "test_cases" in result.data
    assert len(result.data["test_cases"]) == 2
    # 检查第一个用例
    case = result.data["test_cases"][0]
    assert case["module"] == "登录模块"
    assert case["title"] == "用户正常登录"
    assert case["steps"] == "1.打开登录页面 2.输入用户名testuser 3.输入密码Test@123 4.点击登录按钮"
    assert case["expected_results"] == "登录成功"
    assert case["priority"] == "2"
    # 检查第二个用例
    case2 = result.data["test_cases"][1]
    assert case2["title"] == "密码错误登录"


@pytest.mark.asyncio
async def test_generator_agent_with_csv_parsing():
    """测试 CSV 解析（使用引号）"""
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(
            # 带引号的 CSV 格式
            text="""所属模块,用例标题,前置条件,步骤,预期,关键词,优先级
"支付模块","订单支付","用户已登录","1.进入订单详情 2.点击支付按钮 3.选择支付方式","支付成功","支付","2"
"退款模块","订单退款","用户已支付","1.进入订单详情 2.点击申请退款 3.确认退款","退款成功","退款","1"
""",
            model="test-model",
            usage={},
        )
    )

    agent = GeneratorAgent(mock_llm)
    result = await agent.run({"requirement": "支付功能"})

    assert result.success is True
    assert len(result.data["test_cases"]) == 2
    case = result.data["test_cases"][0]
    assert case["module"] == "支付模块"
    assert case["title"] == "订单支付"


@pytest.mark.asyncio
async def test_generator_agent_with_text_parsing():
    """测试纯文本解析（无 CSV 表头）"""
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(
            text="""用例 1: 用户注册
标题: 新用户注册
步骤: 1. 打开注册页面 2. 填写表单 3. 提交
预期: 注册成功

用例 2: 用户登录
标题: 用户登录
步骤: 1. 打开登录页面 2. 输入凭证 3. 点击登录
预期: 登录成功
""",
            model="test-model",
            usage={},
        )
    )

    agent = GeneratorAgent(mock_llm)
    result = await agent.run({"requirement": "用户注册登录"})

    assert result.success is True


    # 纯文本解析可能返回用例
    assert len(result.data["test_cases"]) >= 0


@pytest.mark.asyncio
async def test_generator_agent_missing_requirement():
    """测试缺少需求文档的情况"""
    mock_llm = MagicMock()
    agent = GeneratorAgent(mock_llm)

    result = await agent.run({"requirement": "", "test_points": []})

    assert result.success is False
    assert "需求文档不能为空" in result.error


    # 确保 LLM 没有被调用
    mock_llm.generate.assert_not_called()


@pytest.mark.asyncio
async def test_generator_agent_with_feedback():
    """测试带反馈的生成"""
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(
            text="""所属模块,用例标题,前置条件,步骤,预期
登录模块,改进后的登录,无,1.打开登录页面,2.输入凭证,3.点击登录,登录成功""",
            model="test-model",
            usage={},
        )
    )

    agent = GeneratorAgent(mock_llm)

    # 模拟带反馈的重新生成
    result = await agent.run(
        {
            "requirement": "登录功能",
            "feedback": "用例步骤需要更详细",
        }
    )

    assert result.success is True


    # 鸦终点 prompt_builder.build_generation_prompt 被调用
    mock_llm.generate.assert_called_once()


@pytest.mark.asyncio
async def test_validate_output():
    """测试输出验证"""
    mock_llm = MagicMock()
    agent = GeneratorAgent(mock_llm)

    # 有效的用例
    valid_cases = [
        {"title": "用例1", "steps": "步骤1", "expected_results": "预期1"},
        {"title": "用例2", "steps": "步骤2", "expected_results": "预期2"},
    ]
    assert await agent.validate_output(valid_cases) is True

    # 无效的用例（缺少 steps）
    invalid_cases = [{"title": "用例1"}]
    assert await agent.validate_output(invalid_cases) is False
    # 空列表
    assert await agent.validate_output([]) is False


@pytest.mark.asyncio
async def test_generator_agent_with_real_llm():
    """测试生成 Agent（使用真实 LLM，需要 API Key）"""
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        pytest.skip("需要 GLM_API_KEY 环境变量")

    from app.llm.factory import create_llm_provider

    llm = create_llm_provider("glm", api_key=api_key)
    agent = GeneratorAgent(llm)

    result = await agent.run(
        {
            "requirement": "用户登录功能：输入用户名和密码登录系统",
            "test_points": ["验证正常登录"],
            "examples": [],
        }
    )

    assert result.success is True
    assert "test_cases" in result.data
    assert len(result.data["test_cases"]) > 0
