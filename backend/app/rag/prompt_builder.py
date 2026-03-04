from typing import List, Dict, Optional


class PromptBuilder:
    """Prompt 构建器"""

    def __init__(self):
        self.base_prompt = """你是一个资深的测试用例设计专家。

**任务：**
基于以下需求文档，生成高质量、规范的测试用例。

**重要约束（CRITICAL）：**
1. 测试数据必须真实、可用、符合行业实际
2. 禁止使用"比如""例如""XXX""测试数据"等模糊字眼
3. 手机号必须是真实格式（如：13812345678）
4. 身份证号必须是真实格式（如：110101199001011234）
5. 邮箱必须是真实格式（如：test@example.com）
6. 金额必须是合理数值（如：99.99，而非 999999999.99）
7. 日期必须是真实日期（如：2026-03-04）
8. URL 必须是真实格式（如：https://example.com/api/user）

**CSV 格式要求：**
所属模块,用例标题,前置条件,步骤,预期,关键词,优先级,用例类型,适用阶段
"""

    async def build_generation_prompt(
        self,
        requirement: str,
        test_points: List[str],
        examples: Optional[List[Dict]] = None
    ) -> str:
        """
        构建测试用例生成 Prompt

        Args:
            requirement: 需求文档
            test_points: 测试点列表
            examples: Few-shot 示例

        Returns:
            完整的 Prompt
        """
        prompt_parts = [self.base_prompt]

        # 添加历史示例
        if examples:
            prompt_parts.append("\n**历史参考用例（请模仿这些用例的风格和规范）：**\n")
            for i, example in enumerate(examples, 1):
                prompt_parts.append(f"示例 {i}:\n")
                prompt_parts.append(f"所属模块: {example.get('module', '通用')}\n")
                prompt_parts.append(f"用例标题: {example['title']}\n")
                prompt_parts.append(f"前置条件: {example.get('prerequisites', '无')}\n")
                prompt_parts.append(f"步骤: {example['steps']}\n")
                prompt_parts.append(f"预期: {example['expected_results']}\n")
                prompt_parts.append(f"优先级: {example.get('priority', '2')}\n")
                prompt_parts.append(f"用例类型: {example.get('case_type', '功能测试')}\n")
                prompt_parts.append(f"适用阶段: {example.get('stage', '功能测试阶段')}\n\n")

        # 添加需求文档
        prompt_parts.append("\n**需求文档：**\n")
        prompt_parts.append(requirement)
        prompt_parts.append("\n")

        # 添加测试点
        if test_points:
            prompt_parts.append("\n**测试点：**\n")
            for i, point in enumerate(test_points, 1):
                prompt_parts.append(f"{i}. {point}\n")

        # 添加生成要求
        prompt_parts.append("\n**生成要求：**\n")
        prompt_parts.append("请根据上述需求文档和测试点，生成符合规范的测试用例。\n")
        prompt_parts.append("确保每一条用例都是可执行的，测试数据真实可用。\n")
        prompt_parts.append("输出格式为 CSV，可以直接导入测试管理系统。\n")

        return "".join(prompt_parts)

    async def build_review_prompt(self, test_cases: List[Dict]) -> str:
        """
        构建测试用例评审 Prompt

        Args:
            test_cases: 测试用例列表

        Returns:
            评审 Prompt
        """
        prompt = """你是一个资深的测试用例评审专家。

**任务：**
评审以下测试用例的质量。

**评审维度：**
1. **规范性**：是否符合 CSV 格式要求，字段是否完整
2. **完整性**：前置条件、步骤、预期结果是否清晰
3. **可执行性**：步骤是否明确，预期是否可验证
4. **数据真实性**：测试数据是否真实、可用，无模糊字眼
5. **覆盖度**：是否覆盖了主要测试场景

**评审标准：**
- 通过：所有维度都符合要求
- 不通过：有任一维度不符合要求

**待评审用例：**
"""
        for i, case in enumerate(test_cases, 1):
            prompt += f"\n用例 {i}:\n"
            prompt += f"模块: {case.get('module', 'N/A')}\n"
            prompt += f"标题: {case['title']}\n"
            prompt += f"步骤: {case['steps']}\n"
            prompt += f"预期: {case['expected_results']}\n"

        prompt += """

**评审格式：**
请按以下格式输出评审结果：

```
总体评价: [通过/不通过]

详细评分:
- 规范性: [分数 1-10]
- 完整性: [分数 1-10]
- 可执行性: [分数 1-10]
- 数据真实性: [分数 1-10]
- 覆盖度: [分数 1-10]

问题列表:
[如果不通过，列出所有问题，每个问题包含：用例编号、问题描述、改进建议]

改进建议:
[整体改进建议]
```
"""
        return prompt
