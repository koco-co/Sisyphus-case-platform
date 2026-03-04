"""测试用例评审 Agent"""

import logging
import re
from typing import Any, Dict, List, Optional

from app.agents.base import Agent, AgentResponse
from app.rag.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class ReviewerAgent(Agent):
    """测试用例评审 Agent

    负责评审测试用例的质量，规范性、完整性、可执行性等。
    """

    def __init__(
        self,
        llm_provider,
        prompt_builder: Optional[PromptBuilder] = None,
        default_model: Optional[str] = None,
    ):
        """初始化评审 Agent

        Args:
            llm_provider: LLM 提供商实例
            prompt_builder: Prompt 构建器（可选）
            default_model: 默认使用的模型（可选）
        """
        super().__init__(llm_provider, name="ReviewerAgent")
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.default_model = default_model

    async def run(self, input_data: Dict[str, Any]) -> AgentResponse:
        """评审测试用例

        Args:
            input_data: 包含以下字段：
                - test_cases: 测试用例列表（必需）
                - model: 使用的模型（可选）

        Returns:
            AgentResponse，包含评审结果
        """
        try:
            test_cases = input_data.get("test_cases", [])
            model = input_data.get("model", self.default_model)

            if not test_cases:
                return AgentResponse(
                    success=False,
                    error="测试用例列表不能为空",
                )

            # 构建评审 Prompt
            prompt = await self.prompt_builder.build_review_prompt(test_cases)

            # 调用 LLM 评审
            response = await self.llm.generate(
                prompt=prompt,
                model=model or "default",
                temperature=0.3,  # 评审使用较低的温度，更稳定
                max_tokens=2000,
            )

            # 解析评审结果
            review_result = await self._parse_review_result(response.text)

            return AgentResponse(
                success=True,
                data=review_result,
                metadata={
                    "model": response.model,
                    "usage": response.usage,
                    "raw_review": response.text,
                },
            )

        except Exception as e:
            logger.error(f"评审测试用例失败: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
            )

    async def _parse_review_result(self, text: str) -> Dict[str, Any]:
        """解析评审结果

        Args:
            text: LLM 输出的评审文本

        Returns:
            评审结果字典
        """
        # 提取总体评价
        passed = False
        if "通过" in text and "不通过" not in text:
            passed = True
        elif "PASS" in text.upper() and "FAIL" not in text.upper():
            passed = True

        # 提取评分
        scores = self._extract_scores(text)

        # 提取问题列表
        issues = self._extract_issues(text)

        # 提取改进建议
        suggestions = self._extract_suggestions(text)

        return {
            "passed": passed,
            "scores": scores,
            "issues": issues,
            "suggestions": suggestions,
            "raw_review": text,
        }

    def _extract_scores(self, text: str) -> Dict[str, int]:
        """提取评分

        Args:
            text: 评审文本

        Returns:
            评分字典
        """
        scores = {}
        score_patterns = {
            "规范性": r"规范性[:：]\s*(\d+)",
            "完整性": r"完整性[:：]\s*(\d+)",
            "可执行性": r"可执行性[:：]\s*(\d+)",
            "数据真实性": r"数据真实性[:：]\s*(\d+)",
            "覆盖度": r"覆盖度[:：]\s*(\d+)",
        }

        for dimension, pattern in score_patterns.items():
            match = re.search(pattern, text)
            if match:
                scores[dimension] = int(match.group(1))

        return scores

    def _extract_issues(self, text: str) -> List[Dict[str, Any]]:
        """提取问题列表

        Args:
            text: 评审文本

        Returns:
            问题列表
        """
        issues = []

        # 查找问题列表部分
        issue_section = ""
        if "问题列表" in text:
            parts = text.split("改进建议")
            issue_section = parts[0] if parts else ""
            if "问题列表" in issue_section:
                issue_section = issue_section.split("问题列表")[-1]

        # 提取具体问题
        issue_pattern = r"用例\s*(\d+)[：:]?\s*(.+?)(?=\n|用例|$)"
        matches = re.findall(issue_pattern, issue_section, re.DOTALL)

        for case_num, issue in matches:
            issue_text = issue.strip()
            if issue_text:
                issues.append(
                    {
                        "case_number": int(case_num) if case_num.isdigit() else None,
                        "issue": issue_text,
                    }
                )

        return issues

    def _extract_suggestions(self, text: str) -> List[str]:
        """提取改进建议

        Args:
            text: 评审文本

        Returns:
            建议列表
        """
        suggestions = []

        if "改进建议" in text:
            suggestion_section = text.split("改进建议")[-1]
            # 按行提取建议
            for line in suggestion_section.split("\n"):
                line = line.strip()
                # 跳过空行和分隔线
                if line and not line.startswith("-") and not line.startswith("="):
                    # 移除开头的列表符号
                    if line.startswith(("1.", "2.", "3.", "4.", "5.", "- ", "* ")):
                        line = line[2:].strip()
                    if line:
                        suggestions.append(line)

        return suggestions

    async def validate_output(self, output: Dict) -> bool:
        """验证评审结果是否有效

        Args:
            output: 评审结果

        Returns:
            是否验证通过
        """
        return "passed" in output and isinstance(output["passed"], bool)



    async def quick_review(self, test_cases: List[Dict]) -> Dict[str, Any]:
        """快速评审（不调用 LLM）

        用于快速检查用例的基本问题。

        Args:
            test_cases: 测试用例列表

        Returns:
            快速评审结果
        """
        issues = []

        for i, case in enumerate(test_cases, 1):
            # 检查必填字段
            if not case.get("title"):
                issues.append({
                    "case_number": i + 1,
                    "issue": "缺少用例标题"
                })
            if not case.get("steps"):
                issues.append({
                    "case_number": i + 1,
                    "issue": "缺少操作步骤"
                })
            if not case.get("expected_results"):
                issues.append({
                    "case_number": i + 1,
                    "issue": "缺少预期结果"
                })

            # 检查模糊数据
            steps = case.get("steps", "")
            if "XXX" in steps or "测试数据" in steps or "比如" in steps:
                issues.append({
                    "case_number": i + 1,
                    "issue": "步骤包含模糊数据（XXX、测试数据、比如等）"
                })

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "scores": {},
            "suggestions": [],
        }
