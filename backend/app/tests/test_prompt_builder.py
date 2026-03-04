import pytest
from app.rag.prompt_builder import PromptBuilder


@pytest.mark.asyncio
async def test_build_few_shot_prompt():
    """测试构建 Few-shot Prompt"""
    builder = PromptBuilder()

    examples = [
        {
            "title": "用户登录测试",
            "steps": "1. 打开登录页面\n2. 输入用户名密码",
            "expected_results": "登录成功"
        }
    ]

    prompt = await builder.build_generation_prompt(
        requirement="用户需要能够登录系统",
        test_points=["验证正常登录", "验证密码错误"],
        examples=examples
    )

    assert "用户需要能够登录系统" in prompt
    assert "验证正常登录" in prompt
    assert "用户登录测试" in prompt
    assert len(prompt) > 100


@pytest.mark.asyncio
async def test_build_review_prompt():
    """测试构建评审 Prompt"""
    builder = PromptBuilder()

    test_cases = [
        {
            "module": "用户管理",
            "title": "用户登录测试",
            "steps": "1. 打开登录页面\n2. 输入用户名密码",
            "expected_results": "登录成功"
        }
    ]

    prompt = await builder.build_review_prompt(test_cases)

    assert "评审专家" in prompt
    assert "用户登录测试" in prompt
    assert "规范性" in prompt
    assert "完整性" in prompt
    assert len(prompt) > 100


@pytest.mark.asyncio
async def test_build_generation_prompt_without_examples():
    """测试无示例的 Prompt 构建"""
    builder = PromptBuilder()

    prompt = await builder.build_generation_prompt(
        requirement="用户需要能够登录系统",
        test_points=["验证正常登录"],
        examples=None
    )

    assert "用户需要能够登录系统" in prompt
    assert "验证正常登录" in prompt
    assert "测试数据必须真实" in prompt
    assert len(prompt) > 100


@pytest.mark.asyncio
async def test_base_prompt_constraints():
    """测试基础 Prompt 包含所有约束"""
    builder = PromptBuilder()

    prompt = await builder.build_generation_prompt(
        requirement="测试需求",
        test_points=["测试点1"],
        examples=None
    )

    # 验证关键约束存在
    assert "测试数据必须真实" in prompt
    assert "禁止使用" in prompt
    assert "手机号必须是真实格式" in prompt
    assert "身份证号必须是真实格式" in prompt
    assert "邮箱必须是真实格式" in prompt
    assert "CSV 格式要求" in prompt
