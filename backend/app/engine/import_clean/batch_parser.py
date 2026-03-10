"""CSV batch parser — discovers and normalizes CSV files from 待清洗数据/ directory.

Supports two formats:
- 数栈平台 (25-column 禅道 export): 用例编号,所属产品,所属模块,...
- 信永中和 (9-column simple): 所属模块,用例标题,前置条件,...
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from app.engine.import_clean.cleaner import normalize_empty_values, strip_html_tags
from app.engine.import_clean.csv_parser import parse_csv_bytes

logger = logging.getLogger(__name__)

SHUZHAN_COLUMNS = {"用例编号", "所属产品", "所属模块", "用例标题", "步骤", "预期"}
XINYONGZHONGHE_COLUMNS = {"所属模块", "用例标题", "步骤", "预期"}

PRIORITY_MAP = {
    "1": "P0",
    "2": "P1",
    "3": "P2",
    "4": "P3",
    "高": "P0",
    "中": "P1",
    "低": "P2",
    "P0": "P0",
    "P1": "P1",
    "P2": "P2",
    "P3": "P3",
}


def detect_format(row: dict) -> str:
    """Detect CSV format from column names.

    Returns:
        'shuzhan' | 'xinyongzhonghe' | 'unknown'
    """
    keys = set(row.keys())
    if SHUZHAN_COLUMNS.issubset(keys):
        return "shuzhan"
    if XINYONGZHONGHE_COLUMNS.issubset(keys):
        return "xinyongzhonghe"
    return "unknown"


def extract_module_from_path(module_path: str) -> str:
    """Extract clean module name from 禅道-style path.

    Example:
        '/版本迭代测试用例/v6.4.8/【规则调度设置】任务时长限制(#10220)'
        → '【规则调度设置】任务时长限制'
    """
    if not module_path:
        return ""
    # Remove ID references like (#10220)
    cleaned = re.sub(r"\(#\d+\)", "", module_path)
    # Take the last path segment
    parts = [p.strip() for p in cleaned.split("/") if p.strip()]
    if parts:
        return parts[-1]
    return cleaned.strip()


def _parse_steps_text(text: str) -> list[dict]:
    """Parse step text (possibly with numbered steps) into structured steps.

    Handles formats like:
    - '1. step one\\n2. step two'
    - 'step one' (single step)
    """
    if not text:
        return []

    text = strip_html_tags(text)
    text = normalize_empty_values(text)
    if not text:
        return []

    # Try to split on numbered patterns
    parts = re.split(r"(?:^|\n)\s*(\d+)[.、．)\s]+", text.strip())

    steps: list[dict] = []
    if len(parts) > 2:
        # Numbered format: parts = ['', '1', 'action1', '2', 'action2', ...]
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                action = parts[i + 1].strip()
                if action:
                    steps.append({"no": int(parts[i]), "action": action, "expected_result": ""})
    else:
        # Single step or no numbering
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for idx, line in enumerate(lines, 1):
            steps.append({"no": idx, "action": line, "expected_result": ""})

    return steps


def _parse_expected_text(text: str, steps: list[dict]) -> list[dict]:
    """Parse expected result text and merge with existing steps."""
    if not text:
        return steps

    text = strip_html_tags(text)
    text = normalize_empty_values(text)
    if not text:
        return steps

    parts = re.split(r"(?:^|\n)\s*(\d+)[.、．)\s]+", text.strip())
    expectations: dict[int, str] = {}

    if len(parts) > 2:
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                expectations[int(parts[i])] = parts[i + 1].strip()
    else:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for idx, line in enumerate(lines, 1):
            expectations[idx] = line

    for step in steps:
        step_no = step.get("no", 0)
        if step_no in expectations:
            step["expected_result"] = expectations[step_no]

    # If no steps yet but we have expectations, create steps
    if not steps and expectations:
        for no, expected in sorted(expectations.items()):
            steps.append({"no": no, "action": "", "expected_result": expected})

    return steps


def normalize_csv_row(row: dict, fmt: str) -> dict:
    """Normalize a CSV row into a standard test case dict.

    Returns:
        dict with keys: case_id, title, precondition, steps, priority,
        module_path, case_type, tags, source, original_raw
    """
    if fmt == "shuzhan":
        return _normalize_shuzhan(row)
    if fmt == "xinyongzhonghe":
        return _normalize_xinyongzhonghe(row)
    return _normalize_generic(row)


def _normalize_shuzhan(row: dict) -> dict:
    """Normalize 数栈平台 (禅道 export) format."""
    steps = _parse_steps_text(row.get("步骤", ""))
    steps = _parse_expected_text(row.get("预期", ""), steps)

    raw_priority = normalize_empty_values(row.get("优先级", ""))
    priority = PRIORITY_MAP.get(raw_priority, "P1")

    module_raw = row.get("所属模块", "")
    module_path = extract_module_from_path(module_raw)

    return {
        "case_id": normalize_empty_values(row.get("用例编号", "")),
        "title": strip_html_tags(normalize_empty_values(row.get("用例标题", ""))),
        "precondition": strip_html_tags(normalize_empty_values(row.get("前置条件", ""))),
        "steps": steps,
        "priority": priority,
        "module_path": module_path,
        "case_type": normalize_empty_values(row.get("用例类型", "")) or "functional",
        "tags": [t.strip() for t in row.get("关键词", "").split(",") if t.strip()],
        "source": "imported",
        "original_raw": row,
    }


def _normalize_xinyongzhonghe(row: dict) -> dict:
    """Normalize 信永中和 (simple 9-column) format."""
    steps = _parse_steps_text(row.get("步骤", ""))
    steps = _parse_expected_text(row.get("预期", ""), steps)

    raw_priority = normalize_empty_values(row.get("优先级", ""))
    priority = PRIORITY_MAP.get(raw_priority, "P1")

    return {
        "case_id": "",
        "title": strip_html_tags(normalize_empty_values(row.get("用例标题", ""))),
        "precondition": strip_html_tags(normalize_empty_values(row.get("前置条件", ""))),
        "steps": steps,
        "priority": priority,
        "module_path": normalize_empty_values(row.get("所属模块", "")),
        "case_type": normalize_empty_values(row.get("用例类型", "")) or "functional",
        "tags": [t.strip() for t in row.get("关键词", "").split(",") if t.strip()],
        "source": "imported",
        "original_raw": row,
    }


def _normalize_generic(row: dict) -> dict:
    """Fallback normalizer for unknown formats."""
    title = ""
    for key in ["用例标题", "标题", "title", "用例名称"]:
        if row.get(key):
            title = row[key]
            break

    return {
        "case_id": "",
        "title": strip_html_tags(normalize_empty_values(title)),
        "precondition": "",
        "steps": [],
        "priority": "P1",
        "module_path": "",
        "case_type": "functional",
        "tags": [],
        "source": "imported",
        "original_raw": row,
    }


def parse_csv_file(file_path: str | Path) -> list[dict]:
    """Parse a CSV file and return normalized test case dicts.

    Auto-detects format (数栈平台 vs 信永中和) from column headers.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    data = path.read_bytes()
    rows = parse_csv_bytes(data)

    if not rows:
        logger.warning("CSV file is empty: %s", path)
        return []

    fmt = detect_format(rows[0])
    logger.info("Detected format '%s' for %s (%d rows)", fmt, path.name, len(rows))

    results: list[dict] = []
    for row in rows:
        try:
            normalized = normalize_csv_row(row, fmt)
            if normalized["title"]:
                results.append(normalized)
        except Exception:
            logger.warning("Failed to normalize row %s in %s", row.get("_row_number", "?"), path, exc_info=True)

    logger.info("Parsed %d valid cases from %s", len(results), path.name)
    return results


def discover_csv_files(root_dir: str | Path) -> list[Path]:
    """Recursively discover all CSV files under root_dir."""
    root = Path(root_dir)
    if not root.exists():
        logger.warning("Data directory not found: %s", root)
        return []
    csv_files = sorted(root.rglob("*.csv"))
    logger.info("Discovered %d CSV files under %s", len(csv_files), root)
    return csv_files
