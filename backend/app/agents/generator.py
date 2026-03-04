"""测试用例生成 Agent"""

import logging
import re
from typing import Any, Dict, List, Optional

from app.agents.base import Agent, AgentResponse
from app.rag.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class GeneratorAgent(Agent):
    """测试用例生成 Agent

    负责根据需求文档和测试点生成高质量的测试用例。
    支持从历史用例中学习（Few-shot）。
    """

    def __init__(
        self,
        llm_provider,
        prompt_builder: Optional[PromptBuilder] = None,
        default_model: Optional[str] = None,
    ):
        """初始化生成 Agent

        Args:
            llm_provider: LLM 提供商实例
            prompt_builder: Prompt 构建器（可选）
            default_model: 默认使用的模型（可选）
        """
        super().__init__(llm_provider, name="GeneratorAgent")
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.default_model = default_model

    async def run(self, input_data: Dict[str, Any]) -> AgentResponse:
        """生成测试用例

        Args:
            input_data: 包含以下字段：
                - requirement: 需求文档（必需）
                - test_points: 测试点列表（可选）
                - examples: Few-shot 示例用例（可选）
                - feedback: 上一轮评审反馈（可选，用于迭代优化）
                - model: 使用的模型（可选）

        Returns:
            AgentResponse，包含生成的测试用例
        """
        try:
            requirement = input_data.get("requirement", "")
            test_points = input_data.get("test_points", [])
            examples = input_data.get("examples", [])
            feedback = input_data.get("feedback")
            model = input_data.get("model", self.default_model)

            if not requirement:
                return AgentResponse(
                    success=False,
                    error="需求文档不能为空",
                )

            # 构建 Prompt
            prompt = await self.prompt_builder.build_generation_prompt(
                requirement=requirement,
                test_points=test_points,
                examples=examples,
            )

            # 如果有反馈，添加到 Prompt 中
            if feedback:
                prompt += f"\n\n**上一轮评审反馈：**\n{feedback}\n"
                prompt += "\n请根据以上反馈改进测试用例。\n"

            # 调用 LLM 生成
            response = await self.llm.generate(
                prompt=prompt,
                model=model or "default",
                temperature=0.7,
                max_tokens=4000,
            )

            # 解析生成的用例
            test_cases = await self._parse_test_cases(response.text)

            return AgentResponse(
                success=True,
                data={"test_cases": test_cases},
                metadata={
                    "model": response.model,
                    "usage": response.usage,
                    "raw_text": response.text,
                },
            )

        except Exception as e:
            logger.error(f"生成测试用例失败: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
            )

    async def _parse_test_cases(self, text: str) -> List[Dict[str, Any]]:
        """解析 LLM 输出的测试用例

        支持 CSV 格式和纯文本格式。

        Args:
            text: LLM 生成的文本

        Returns:
            测试用例列表
        """
        # 尝试解析 CSV 格式
        lines = text.strip().split("\n")
        test_cases = []

        # 找到 CSV 表头
        header_index = -1
        for i, line in enumerate(lines):
            if "所属模块" in line or "用例标题" in line:
                header_index = i
                break

        if header_index == -1:
            # 没有找到表头，尝试按行解析
            return await self._parse_text_to_cases(text)

        # 解析 CSV 行
        for line in lines[header_index + 1 :]:
            if not line.strip() or line.startswith("-") or line.startswith("="):
                continue

            # 简单的 CSV 解析（处理逗号分隔）
            parts = self._split_csv_line(line)
            if len(parts) >= 5:  # 至少包含：模块、标题、前置条件、步骤、预期
                test_cases.append(
                    {
                        "module": parts[0].strip('"'),
                        "title": parts[1].strip('"'),
                        "prerequisites": parts[2].strip('"') if len(parts) > 2 else "",
                        "steps": parts[3].strip('"') if len(parts) > 3 else "",
                        "expected_results": parts[4].strip('"') if len(parts) > 4 else "",
                        "keywords": parts[5].strip('"') if len(parts) > 5 else "",
                        "priority": parts[6].strip('"') if len(parts) > 6 else "2",
                        "case_type": parts[7].strip('"') if len(parts) > 7 else "功能测试",
                        "stage": parts[8].strip('"') if len(parts) > 8 else "功能测试阶段",
                    }
                )

        return test_cases

    async def _parse_text_to_cases(self, text: str) -> List[Dict[str, Any]]:
        """从纯文本解析测试用例（备用方案）

        Args:
            text: 纯文本

        Returns:
            测试用例列表
        """
        # 简单实现：提取"用例 X:"格式的用例
        cases = []
        case_pattern = r"用例\s*\d+[:：]\s*(.+?)(?=用例\s*\d+[:：]|$)"

        matches = re.findall(case_pattern, text, re.DOTALL)
        for match in matches:
            # 尝试提取字段
            title = self._extract_field(match, ["标题", "用例名称"])
            steps = self._extract_field(match, ["步骤", "操作步骤"])
            expected = self._extract_field(
                match, ["预期", "期望结果", "预期结果"]
            )

            if title and steps:
                cases.append(
                    {
                        "title": title,
                        "steps": steps,
                        "expected_results": expected or "待补充",
                        "module": "通用",
                        "prerequisites": "",
                        "priority": "2",
                        "case_type": "功能测试",
                        "stage": "功能测试阶段",
                    }
                )

        return cases

    def _extract_field(self, text: str, keywords: List[str]) -> Optional[str]:
        """从文本中提取字段值

        Args:
            text: 文本内容
            keywords: 关键词列表

        Returns:
            提取到的字段值
        """
        for keyword in keywords:
            pattern = f"{keyword}[:：](.+?)(?=\\n|$)"
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None

    def _split_csv_line(self, line: str) -> List[str]:
        """分割 CSV 行（处理引号内的逗号）

        Args:
            line: CSV 行

        Returns:
            分割后的字段列表
        """
        parts = []
        current = []
        in_quotes = False

        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == "," and not in_quotes:
                parts.append("".join(current))
                current = []
            else:
                current.append(char)

        if current:
            parts.append("".join(current))

        return parts

    async def validate_output(self, output: List[Dict]) -> bool:
        """验证输出是否包含有效的测试用例

        Args:
            output: 测试用例列表

        Returns:
            是否验证通过
        """
        if not output:
            return False

        for case in output:
            if not case.get("title") or not case.get("steps"):
                return False

        return True
