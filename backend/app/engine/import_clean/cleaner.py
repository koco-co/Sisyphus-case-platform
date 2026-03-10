"""LLM-powered test case cleaning engine.

Provides utilities for:
- HTML tag stripping
- Empty value normalization
- Automated quality scoring
- LLM-based test case improvement
"""

from __future__ import annotations

import json
import logging
import re

from app.ai.llm_client import LLMResult, invoke_llm

logger = logging.getLogger(__name__)


def strip_html_tags(text: str) -> str:
    """Remove HTML tags while preserving text content and meaningful whitespace."""
    if not text:
        return ""
    cleaned = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"<p[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</p>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = re.sub(r"&nbsp;", " ", cleaned)
    cleaned = re.sub(r"&lt;", "<", cleaned)
    cleaned = re.sub(r"&gt;", ">", cleaned)
    cleaned = re.sub(r"&amp;", "&", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def normalize_empty_values(value: str) -> str:
    """Normalize empty/placeholder values to empty string."""
    if not value:
        return ""
    stripped = value.strip()
    empty_markers = {"无", "无。", "N/A", "n/a", "NA", "na", "-", "--", "——", "/", "null", "NULL", "None", "none", "空"}
    if stripped in empty_markers:
        return ""
    return stripped


def score_test_case(case: dict) -> float:
    """Score a test case on quality (0-100).

    Criteria:
    - title present and descriptive (0-25)
    - steps present and have action+expected (0-35)
    - precondition present (0-10)
    - priority valid (0-10)
    - no HTML remnants (0-10)
    - reasonable step count (0-10)
    """
    score = 0.0

    title = case.get("title", "")
    if title:
        score += 10.0
        if len(title) >= 10:
            score += 10.0
        if len(title) >= 20:
            score += 5.0

    steps = case.get("steps", [])
    if steps:
        score += 10.0
        steps_with_action = sum(1 for s in steps if s.get("action"))
        steps_with_expected = sum(1 for s in steps if s.get("expected_result"))
        if steps_with_action == len(steps):
            score += 15.0
        elif steps_with_action > 0:
            score += 15.0 * (steps_with_action / len(steps))
        if steps_with_expected == len(steps):
            score += 10.0
        elif steps_with_expected > 0:
            score += 10.0 * (steps_with_expected / len(steps))

    if case.get("precondition"):
        score += 10.0

    valid_priorities = {"P0", "P1", "P2", "P3"}
    if case.get("priority") in valid_priorities:
        score += 10.0

    # Check for HTML remnants
    all_text = f"{title} {case.get('precondition', '')} " + " ".join(
        f"{s.get('action', '')} {s.get('expected_result', '')}" for s in steps
    )
    if not re.search(r"<[^>]+>", all_text):
        score += 10.0

    if 2 <= len(steps) <= 15:
        score += 10.0
    elif 1 <= len(steps) <= 20:
        score += 5.0

    return round(min(score, 100.0), 1)


CLEAN_CASE_PROMPT = """你是测试用例质量优化助手。请优化以下测试用例，使其更加规范、清晰、可执行。

## 输入用例
标题：{title}
前置条件：{precondition}
步骤：
{steps_text}

## 优化要求
1. 标题：简明扼要，包含被测功能和验证点
2. 前置条件：明确列出执行前的环境/数据要求，无则写"无"
3. 步骤：每步包含操作（action）和预期结果（expected_result），编号连续
4. 去除 HTML 标签、特殊符号、冗余描述
5. 保持原始测试意图不变

## 输出格式（严格 JSON）
{{
  "title": "优化后标题",
  "precondition": "优化后前置条件",
  "steps": [
    {{"no": 1, "action": "操作描述", "expected_result": "预期结果"}}
  ]
}}

只输出 JSON，不要其他内容。"""


async def llm_clean_case(case: dict) -> dict:
    """Use LLM to clean and improve a single test case.

    Args:
        case: dict with title, precondition, steps fields

    Returns:
        Cleaned case dict with title, precondition, steps
    """
    title = case.get("title", "")
    precondition = case.get("precondition", "无")
    steps = case.get("steps", [])

    steps_text = "\n".join(
        f"{s.get('no', i + 1)}. 操作：{s.get('action', '')} | 预期：{s.get('expected_result', '')}"
        for i, s in enumerate(steps)
    )

    prompt = CLEAN_CASE_PROMPT.format(
        title=strip_html_tags(title),
        precondition=strip_html_tags(precondition or "无"),
        steps_text=strip_html_tags(steps_text) if steps_text else "（无步骤）",
    )

    result: LLMResult = await invoke_llm([{"role": "user", "content": prompt}])

    match = re.search(r"\{.*\}", result.content, re.DOTALL)
    if not match:
        logger.warning("LLM 清洗返回格式异常: %s", result.content[:200])
        return {
            "title": strip_html_tags(title),
            "precondition": strip_html_tags(precondition),
            "steps": [
                {
                    "no": s.get("no", i + 1),
                    "action": strip_html_tags(s.get("action", "")),
                    "expected_result": strip_html_tags(s.get("expected_result", "")),
                }
                for i, s in enumerate(steps)
            ],
        }

    cleaned = json.loads(match.group())

    if not isinstance(cleaned.get("steps"), list):
        cleaned["steps"] = []
    for i, step in enumerate(cleaned["steps"]):
        step.setdefault("no", i + 1)
        step.setdefault("action", "")
        step.setdefault("expected_result", "")

    return {
        "title": cleaned.get("title", title),
        "precondition": cleaned.get("precondition", ""),
        "steps": cleaned["steps"],
    }
