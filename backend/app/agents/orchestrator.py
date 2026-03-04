"""Agent 编排器"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base import AgentResponse
from app.agents.generator import GeneratorAgent
from app.agents.reviewer import ReviewerAgent
from app.rag.prompt_builder import PromptBuilder

from app.rag.retriever import VectorRetriever

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Agent 编排器

    协调生成 Agent 和评审 Agent 的交互，
    实现迭代优化的工作流。
    """

    def __init__(
        self,
        generator_llm,
        reviewer_llm,
        max_retries: int = 3,
        prompt_builder: Optional[PromptBuilder] = None,
        retriever: Optional[VectorRetriever] = None,
    ):
        """初始化编排器

        Args:
            generator_llm: 生成 Agent 使用的 LLM
            reviewer_llm: 评审 Agent 使用的 LLM
            max_retries: 最大重试次数
            prompt_builder: Prompt 构建器（可选）
            retriever: 向量检索器（可选）
        """
        self.generator = GeneratorAgent(generator_llm, prompt_builder)
        self.reviewer = ReviewerAgent(reviewer_llm, prompt_builder)
        self.max_retries = max_retries
        self.retriever = retriever or VectorRetriever()

    async def generate_with_review(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """生成测试用例并评审（自动迭代优化）

        Args:
            input_data: 包含以下字段：
                - requirement: 需求文档（必需）
                - test_points: 测试点列表（可选）
                - examples: Few-shot 示例用例（可选）
                - project_id: 项目 ID（可选，用于检索历史用例）
                - use_rag: 是否使用 RAG（可选，默认 True）
            progress_callback: 进度回调函数（可选）

        Returns:
            生成和评审结果，包含：
                - success: 是否成功
                - test_cases: 生成的测试用例
                - review_passed: 评审是否通过
                - attempts: 尝试次数
                - review: 评审详情
        """
        last_feedback = None
        examples = input_data.get("examples", [])

        # 如果启用 RAG 且没有提供示例，从向量库检索
        if input_data.get("use_rag", True) and not examples:
            project_id = input_data.get("project_id")
            requirement = input_data.get("requirement", "")

            if progress_callback:
                await progress_callback("retrieving", "正在检索相似的历史用例...")

            try:
                similar_cases = await self.retriever.search_similar_cases(
                    query=requirement,
                    top_k=5,
                    project_id=project_id,
                )

                examples = [
                    {
                        "module": case.module,
                        "title": case.title,
                        "prerequisites": case.prerequisites,
                        "steps": case.steps,
                        "expected_results": case.expected_results,
                        "priority": case.priority,
                    }
                    for case in similar_cases
                ]

                if progress_callback:
                    await progress_callback(
                        "retrieved", f"找到 {len(examples)} 个相似用例"
                    )

            except Exception as e:
                logger.warning(f"检索历史用例失败: {e}, 继续生成...")

        for attempt in range(self.max_retries):
            # 1. 生成测试用例
            if progress_callback:
                await progress_callback(
                    "generating",
                    f"正在生成测试用例（第 {attempt + 1} 次尝试）...",
                )

            if attempt > 0 and last_feedback:
                # 使用反馈重新生成
                input_data["feedback"] = last_feedback

            input_data["examples"] = examples
            generation_result = await self.generator.run(input_data)

            if not generation_result.success:
                return {
                    "success": False,
                    "error": f"生成失败: {generation_result.error}",
                    "attempt": attempt + 1,
                }

            test_cases = generation_result.data["test_cases"]

            # 2. 评审测试用例
            if progress_callback:
                await progress_callback("reviewing", "正在评审测试用例...")

            review_result = await self.reviewer.run({"test_cases": test_cases})

            if not review_result.success:
                return {
                    "success": False,
                    "error": f"评审失败: {review_result.error}",
                    "test_cases": test_cases,
                    "attempt": attempt + 1,
                }

            review_data = review_result.data

            # 3. 检查是否通过
            if review_data["passed"]:
                if progress_callback:
                    await progress_callback("completed", "评审通过，生成完成！")

                return {
                    "success": True,
                    "test_cases": test_cases,
                    "review_passed": True,
                    "attempts": attempt + 1,
                    "review": review_data,
                }
            else:
                # 4. 不通过，收集反馈重试
                last_feedback = self._collect_feedback(review_data)

                if attempt < self.max_retries - 1:
                    # 还有重试机会
                    if progress_callback:
                        await progress_callback(
                            "retrying",
                            f"评审未通过，正在重新生成（第 {attempt + 2} 次尝试）..."
                        )
                    continue
                else:
                    # 达到最大重试次数，返回当前结果
                    if progress_callback:
                        await progress_callback(
                            "completed",
                            "达到最大重试次数，返回当前结果",
                        )

                    return {
                        "success": True,
                        "test_cases": test_cases,
                        "review_passed": False,
                        "attempts": self.max_retries,
                        "review": review_data,
                        "warning": "达到最大重试次数，评审未通过",
                    }

        # 如果循环结束，没有返回，返回最后一次的结果
        return {
            "success": False,
            "error": "未知错误",
        }
    async def generate_only(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[callable] = None,
    ) -> AgentResponse:
        """仅生成测试用例（不评审）

        Args:
            input_data: 输入数据

        Returns:
            AgentResponse
        """
        if progress_callback:
            await progress_callback("generating", "正在生成测试用例...")

        result = await self.generator.run(input_data)

        if progress_callback:
            if result.success:
                await progress_callback("completed", "生成完成！")
            else:
                await progress_callback("error", f"生成失败: {result.error}")
        return result

    async def review_only(
        self,
        test_cases: List[Dict[str, Any]],
        progress_callback: Optional[callable] = None,
    ) -> AgentResponse:
        """仅评审测试用例（不生成）

        Args:
            test_cases: 测试用例列表

        Returns:
            AgentResponse
        """
        if progress_callback:
            await progress_callback("reviewing", "正在评审测试用例...")

        result = await self.reviewer.run({"test_cases": test_cases})

        if progress_callback:
            if result.success:
                await progress_callback("completed", "评审完成！")
            else:
                await progress_callback("error", f"评审失败: {result.error}")
        return result
    def _collect_feedback(self, review_data: Dict) -> str:
        """从评审结果中收集反馈

        Args:
            review_data: 评审数据

        Returns:
            反馈文本
        """
        feedback_parts = []

        if review_data.get("issues"):
            feedback_parts.append("发现以下问题：")
            for issue in review_data["issues"]:
                case_num = issue.get("case_number")
                case_info = f"用例 {case_num}: " if case_num else ""
                feedback_parts.append(f"- {case_info}{issue['issue']}")

        if review_data.get("suggestions"):
            feedback_parts.append("\n改进建议：")
            for suggestion in review_data["suggestions"]:
                feedback_parts.append(f"- {suggestion}")

        return "\n".join(feedback_parts)
