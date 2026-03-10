"""AI 输出解析器 — 从 LLM 文本中提取结构化测试点和用例。"""

import json
import logging
import re

logger = logging.getLogger(__name__)


# ── JSON extraction ─────────────────────────────────────────────────


def _extract_json(text: str) -> list[dict] | dict | None:
    """Try to extract JSON from *text*, supporting ```json code blocks."""
    # 1. ```json ... ``` fenced blocks
    pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    for match in re.findall(pattern, text, re.DOTALL):
        try:
            result = json.loads(match.strip())
            if isinstance(result, (list, dict)):
                return result
        except json.JSONDecodeError:
            continue

    # 2. Whole text as JSON
    try:
        result = json.loads(text.strip())
        if isinstance(result, (list, dict)):
            return result
    except json.JSONDecodeError:
        pass

    # 3. First JSON array embedded in prose
    for match in re.finditer(r"\[[\s\S]*?\]", text):
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            continue

    return None


# ── Test-point parsing ──────────────────────────────────────────────


def parse_test_points(text: str) -> list[dict]:
    """Parse AI output into test-point dicts.

    Returns a list of dicts with keys:
    ``group_name``, ``title``, ``description``, ``priority``, ``estimated_cases``
    """
    json_data = _extract_json(text)
    if isinstance(json_data, list):
        points: list[dict] = []
        for item in json_data:
            point = {
                "group_name": item.get("group_name") or item.get("group") or item.get("分组") or "未分组",
                "title": item.get("title") or item.get("标题") or "",
                "description": item.get("description") or item.get("描述") or "",
                "priority": item.get("priority") or item.get("优先级") or "P1",
                "estimated_cases": int(item.get("estimated_cases") or item.get("预计用例数") or 3),
            }
            if point["title"]:
                points.append(point)
        if points:
            return points

    return _parse_test_points_from_markdown(text)


def _parse_test_points_from_markdown(text: str) -> list[dict]:
    """Fallback: extract test points from markdown-formatted text."""
    points: list[dict] = []
    current_group = "未分组"

    for line in text.split("\n"):
        line = line.strip()

        # Group headers: ## or ### (optionally numbered)
        if line.startswith("##"):
            group_match = re.match(r"#{2,4}\s*(?:\d+[.)]\s*)?(.+)", line)
            if group_match:
                current_group = group_match.group(1).strip()
            continue

        # List items: - / * / 1.
        item_match = re.match(
            r"(?:[-*]\s+|\d+[.)]\s+)(?:\*\*)?(.+?)(?:\*\*)?(?:\s*[：:]\s*(.+))?$",
            line,
        )
        if not item_match:
            continue

        title = item_match.group(1).strip()
        description = (item_match.group(2) or "").strip()

        priority = "P1"
        priority_match = re.search(r"[（(](P[0-2])[）)]", line)
        if priority_match:
            priority = priority_match.group(1)

        cases_match = re.search(r"(?:预计|估计)\s*(\d+)\s*(?:条|个|用例)", line)
        estimated = int(cases_match.group(1)) if cases_match else 3

        if title and len(title) > 2:
            points.append(
                {
                    "group_name": current_group,
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "estimated_cases": estimated,
                }
            )

    return points


# ── Test-case parsing ───────────────────────────────────────────────

_CASE_TYPE_MAP: dict[str, str] = {
    "正常": "normal",
    "异常": "exception",
    "边界": "boundary",
    "并发": "concurrent",
}


def parse_test_cases(text: str) -> list[dict]:
    """Parse AI output into test-case dicts.

    Returns a list of dicts with keys:
    ``title``, ``priority``, ``case_type``, ``precondition``, ``steps``

    Each step dict contains: ``step_num``, ``action``, ``expected_result``
    """
    json_data = _extract_json(text)
    if isinstance(json_data, list):
        cases: list[dict] = []
        for item in json_data:
            case = _build_case_from_json(item)
            if case["title"]:
                cases.append(case)
        if cases:
            return cases
    elif isinstance(json_data, dict):
        cases = _parse_test_cases_from_object(json_data)
        if cases:
            return cases

    return _parse_test_cases_from_markdown(text)


def _parse_test_cases_from_object(payload: dict) -> list[dict]:
    """Support single-case objects and keyed case maps."""
    if any(key in payload for key in ("title", "标题", "用例标题", "steps", "步骤")):
        case = _build_case_from_json(payload)
        return [case] if case["title"] else []

    cases: list[dict] = []
    for item in payload.values():
        if not isinstance(item, dict):
            continue
        case = _build_case_from_json(item)
        if case["title"]:
            cases.append(case)
    return cases


def _build_case_from_json(item: dict) -> dict:
    """Normalise a single JSON test-case object."""
    case_type = item.get("case_type") or item.get("type") or item.get("类型") or "normal"
    case_type = _CASE_TYPE_MAP.get(case_type, case_type)

    case: dict = {
        "title": item.get("title") or item.get("标题") or item.get("用例标题") or "",
        "priority": item.get("priority") or item.get("优先级") or "P1",
        "case_type": case_type,
        "precondition": item.get("precondition") or item.get("前置条件") or "",
        "steps": [],
    }

    raw_steps = item.get("steps") or item.get("步骤") or []
    if isinstance(raw_steps, list):
        for i, step in enumerate(raw_steps):
            case["steps"].append(_normalise_step(step, i))

    return case


def _normalise_step(step: dict | str, index: int) -> dict:
    """Convert a raw step value into a normalised step dict."""
    if isinstance(step, dict):
        raw_step_num = step.get("step_num") or step.get("序号")
        raw_step_text = step.get("step")
        step_num = raw_step_num if isinstance(raw_step_num, int) else index + 1
        action = step.get("action") or step.get("操作") or step.get("步骤") or ""
        if not action and isinstance(raw_step_text, str):
            action = raw_step_text
        return {
            "step_num": step_num,
            "action": action,
            "expected_result": step.get("expected_result")
            or step.get("预期结果")
            or step.get("expected")
            or step.get("expect")
            or "",
        }
    return {
        "step_num": index + 1,
        "action": str(step),
        "expected_result": "",
    }


# ── Markdown fallback for test cases ────────────────────────────────


def _parse_test_cases_from_markdown(text: str) -> list[dict]:
    """Fallback: extract test cases from markdown-formatted text."""
    cases: list[dict] = []
    current_case: dict | None = None
    step_num = 0
    in_steps = False

    for line in text.split("\n"):
        line = line.strip()

        # Case title (### 用例 1：xxx)
        title_match = re.match(r"#{2,4}\s*(?:用例\s*\d*[：:\s]*)?(.+)", line)
        if title_match and ("用例" in line or "TC" in line.upper()):
            if current_case and current_case["title"]:
                cases.append(current_case)
            current_case = {
                "title": title_match.group(1).strip(),
                "priority": "P1",
                "case_type": "normal",
                "precondition": "",
                "steps": [],
            }
            step_num = 0
            in_steps = False
            continue

        if not current_case:
            continue

        # Priority
        if "优先级" in line:
            pm = re.search(r"(P[0-2])", line)
            if pm:
                current_case["priority"] = pm.group(1)

        # Precondition
        if "前置条件" in line:
            pre = line.split("：", 1)[-1] if "：" in line else line.split(":", 1)[-1]
            current_case["precondition"] = pre.strip()

        # Steps section header
        if "步骤" in line or "操作" in line:
            in_steps = True
            continue

        # Individual steps
        if in_steps:
            step_match = re.match(r"(?:\d+[.)]\s*|[-*]\s+)(.+)", line)
            if step_match:
                step_num += 1
                step_text = step_match.group(1)
                parts = re.split(r"[→=>]\s*(?:预期|期望|验证)", step_text)
                action = parts[0].strip()
                expected = parts[1].strip() if len(parts) > 1 else ""
                current_case["steps"].append(
                    {
                        "step_num": step_num,
                        "action": action,
                        "expected_result": expected,
                    }
                )

    if current_case and current_case["title"]:
        cases.append(current_case)

    return cases
