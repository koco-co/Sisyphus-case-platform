"""Agent 基类测试"""

import pytest

from app.agents.base import Agent, AgentResponse


def test_agent_response_model():
    """测试 Agent 响应模型"""
    response = AgentResponse(
        success=True,
        data={"test": "value"},
        metadata={"attempt": 1},
    )
    assert response.success is True
    assert response.data["test"] == "value"
    assert response.metadata["attempt"] == 1


def test_agent_response_error():
    """测试 Agent 响应错误情况"""
    response = AgentResponse(
        success=False,
        error="Something went wrong",
    )
    assert response.success is False
    assert response.error == "Something went wrong"
    assert response.data is None


def test_agent_is_abstract():
    """测试 Agent 是抽象类，不能直接实例化"""
    with pytest.raises(TypeError):
        Agent(llm_provider=None, name="TestAgent")


def test_agent_subclass_must_implement_run():
    """测试 Agent 子类必须实现 run 方法"""

    class IncompleteAgent(Agent):
        pass

    with pytest.raises(TypeError):
        IncompleteAgent(llm_provider=None, name="IncompleteAgent")
