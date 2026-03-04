"""Agent 抽象基类"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AgentResponse(BaseModel):
    """Agent 响应模型

    Attributes:
        success: 执行是否成功
        data: 响应数据
        error: 错误信息
        metadata: 元数据（如 token 使用量等）
    """

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None


class Agent(ABC):
    """Agent 抽象基类

    所有 Agent 必须继承此类并实现 run 和 validate_output 方法。
    """

    def __init__(self, llm_provider, name: str = "Agent"):
        """初始化 Agent

        Args:
            llm_provider: LLM 提供商实例
            name: Agent 名称
        """
        self.llm = llm_provider
        self.name = name

    @abstractmethod
    async def run(self, input_data: Any) -> AgentResponse:
        """执行 Agent 任务

        Args:
            input_data: 输入数据

        Returns:
            AgentResponse 包含执行结果
        """
        pass

    @abstractmethod
    async def validate_output(self, output: Any) -> bool:
        """验证输出是否符合要求

        Args:
            output: 输出数据

        Returns:
            是否验证通过
        """
        pass
