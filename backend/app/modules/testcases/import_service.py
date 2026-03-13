"""Testcase import service: parse files, check duplicates, batch import."""

from __future__ import annotations

import csv
import io
import json
import logging
import re
import uuid
from typing import Any

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Auto-mapping dict: source column name -> target field key
AUTO_MAP: dict[str, str] = {
    "用例ID": "case_id",
    "ID": "case_id",
    "id": "case_id",
    "用例标题": "title",
    "标题": "title",
    "title": "title",
    "name": "title",
    "前置条件": "precondition",
    "precondition": "precondition",
    "测试步骤": "steps",
    "操作步骤": "steps",
    "steps": "steps",
    "预期结果": "expected_result",
    "expected_result": "expected_result",
    "expected": "expected_result",
    "优先级": "priority",
    "priority": "priority",
    "用例类型": "case_type",
    "type": "case_type",
    "case_type": "case_type",
    "模块路径": "module_path",
    "模块": "module_path",
    "module": "module_path",
    "module_path": "module_path",
    "标签": "tags",
    "tags": "tags",
}

REQUIRED_FIELDS = {"title", "steps", "expected_result"}


class FileParser:
    """Parse xlsx/csv/json/xmind files into (headers, rows) tuples."""

    @staticmethod
    def parse_xlsx(data: bytes) -> tuple[list[str], list[list[str]]]:
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True)
        ws = wb.active
        raw_rows = list(ws.iter_rows(values_only=True))
        if not raw_rows:
            return [], []
        headers = [str(c or "").strip() for c in raw_rows[0]]
        data_rows = [[str(c or "").strip() for c in row] for row in raw_rows[1:]]
        return headers, data_rows

    @staticmethod
    def parse_csv(data: bytes) -> tuple[list[str], list[list[str]]]:
        text = data.decode("utf-8-sig", errors="replace")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return [], []
        return [c.strip() for c in rows[0]], [[c.strip() for c in r] for r in rows[1:]]

    @staticmethod
    def parse_json(data: bytes) -> tuple[list[str], list[list[str]]]:
        payload = json.loads(data.decode("utf-8"))
        if isinstance(payload, list) and payload:
            headers = list(payload[0].keys())
            rows = [[str(row.get(h, "")) for h in headers] for row in payload]
            return headers, rows
        return [], []

    @staticmethod
    def parse_xmind(data: bytes) -> tuple[list[str], list[list[str]]]:
        """
        Parse XMind file using xmindparser.

        Expected XMind structure:
          Sheet → Root Topic → Child Topic (case title)
            → Sub-topic starting with "测试步骤" / "预期结果" / "前置条件"
        Leaf nodes with no recognized sub-topics are imported as title-only rows.
        """
        import os
        import tempfile

        from xmindparser import xmind_to_dict  # type: ignore[import-untyped]

        with tempfile.NamedTemporaryFile(suffix=".xmind", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            sheets = xmind_to_dict(tmp_path)
        finally:
            os.unlink(tmp_path)

        headers = ["标题", "前置条件", "测试步骤", "预期结果", "优先级", "用例类型"]
        rows: list[list[str]] = []

        def process_topic(topic: dict[str, Any]) -> None:
            title = topic.get("title", "").strip()
            children: list[dict[str, Any]] = topic.get("topics", [])

            if not children:
                rows.append([title, "", "", "", "P1", "功能测试"])
                return

            field_map: dict[str, str] = {}
            plain_children: list[dict[str, Any]] = []

            for child in children:
                ctitle = child.get("title", "").strip()
                if ctitle.startswith("测试步骤"):
                    field_map["steps"] = re.sub(r"^测试步骤[：:]?\s*", "", ctitle)
                elif ctitle.startswith("预期结果"):
                    field_map["expected"] = re.sub(r"^预期结果[：:]?\s*", "", ctitle)
                elif ctitle.startswith("前置条件"):
                    field_map["precondition"] = re.sub(r"^前置条件[：:]?\s*", "", ctitle)
                else:
                    plain_children.append(child)

            if field_map:
                rows.append(
                    [
                        title,
                        field_map.get("precondition", ""),
                        field_map.get("steps", ""),
                        field_map.get("expected", ""),
                        "P1",
                        "功能测试",
                    ]
                )
            for child in plain_children:
                process_topic(child)

        for sheet in sheets:
            root = sheet.get("topic", {})
            for child in root.get("topics", []):
                process_topic(child)

        return headers, rows

    @classmethod
    def parse(cls, filename: str, data: bytes) -> tuple[list[str], list[list[str]]]:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in ("xlsx", "xls"):
            return cls.parse_xlsx(data)
        if ext == "csv":
            return cls.parse_csv(data)
        if ext == "json":
            return cls.parse_json(data)
        if ext == "xmind":
            return cls.parse_xmind(data)
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")


def auto_map_columns(columns: list[str]) -> dict[str, str | None]:
    """Return {column -> mapped_field | None} for each column."""
    return {col: AUTO_MAP.get(col) for col in columns}


def is_standard_template(columns: list[str]) -> bool:
    """True if all REQUIRED_FIELDS can be resolved from column mappings."""
    mapped = {AUTO_MAP.get(c) for c in columns}
    return REQUIRED_FIELDS.issubset(mapped)


class TestCaseImportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def parse_file(self, file: UploadFile) -> dict[str, Any]:
        """Parse uploaded file; return columns, preview, mapping, and all rows."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        data = await file.read()
        columns, rows = FileParser.parse(file.filename, data)
        if not columns:
            raise HTTPException(status_code=422, detail="文件内容为空或格式不正确")

        return {
            "columns": columns,
            "preview_rows": rows[:5],
            "all_rows": rows,
            "total_rows": len(rows),
            "auto_mapping": auto_map_columns(columns),
            "is_standard": is_standard_template(columns),
        }

    async def check_duplicates(
        self,
        cases: list[dict[str, str]],
        folder_id: uuid.UUID | None,
    ) -> list[dict[str, Any]]:
        """Return duplicate info for any case whose title already exists in the folder."""
        from app.modules.testcases.models import TestCase

        duplicates: list[dict[str, Any]] = []
        for i, case in enumerate(cases):
            title = case.get("title", "").strip()
            if not title:
                continue
            q = select(TestCase).where(
                TestCase.title == title,
                TestCase.folder_id == folder_id,
                TestCase.deleted_at.is_(None),
            )
            existing = (await self.session.execute(q)).scalar_one_or_none()
            if existing:
                duplicates.append(
                    {
                        "index": i,
                        "title": title,
                        "existing_id": str(existing.id),
                        "existing_case_id": existing.case_id,
                    }
                )
        return duplicates

    async def batch_import(
        self,
        cases: list[dict[str, str]],
        folder_id: uuid.UUID | None,
        per_case_strategies: dict[int, str],
    ) -> dict[str, int]:
        """
        Import cases applying per-case duplicate strategies.

        Strategies: "skip" | "overwrite" | "rename"
        Returns counts: imported / skipped / overwritten / renamed.
        """
        from app.modules.testcases.models import TestCase

        imported = skipped = overwritten = renamed = 0

        for i, case_data in enumerate(cases):
            title = case_data.get("title", "").strip()
            if not title:
                skipped += 1
                continue

            strategy = per_case_strategies.get(i, "skip")

            q = select(TestCase).where(
                TestCase.title == title,
                TestCase.folder_id == folder_id,
                TestCase.deleted_at.is_(None),
            )
            existing = (await self.session.execute(q)).scalar_one_or_none()

            if existing:
                if strategy == "skip":
                    skipped += 1
                    continue
                if strategy == "overwrite":
                    existing.title = title
                    existing.precondition = case_data.get("precondition") or None
                    existing.steps = _parse_steps(case_data.get("steps", ""))
                    existing.priority = _normalize_priority(case_data.get("priority", "P1"))
                    existing.case_type = _normalize_case_type(case_data.get("case_type", "functional"))
                    overwritten += 1
                    continue
                # rename: fall through with modified title
                title = f"{title}_imported"

            tc = TestCase(
                requirement_id=None,
                case_id=f"TC-{uuid.uuid4().hex[:8].upper()}",
                title=title,
                precondition=case_data.get("precondition") or None,
                steps=_parse_steps(case_data.get("steps", "")),
                priority=_normalize_priority(case_data.get("priority", "P1")),
                case_type=_normalize_case_type(case_data.get("case_type", "functional")),
                source="imported",
                status="draft",
                folder_id=folder_id,
                tags=[],
            )
            self.session.add(tc)
            if strategy == "rename":
                renamed += 1
            else:
                imported += 1

        await self.session.commit()
        return {"imported": imported, "skipped": skipped, "overwritten": overwritten, "renamed": renamed}


# ── Helpers ────────────────────────────────────────────────────────


def _parse_steps(steps_raw: str) -> list[dict[str, Any]]:
    """Convert a newline-separated steps string to the canonical steps list."""
    if not steps_raw:
        return []
    lines = [ln.strip() for ln in steps_raw.split("\n") if ln.strip()]
    return [
        {"step": i, "action": re.sub(r"^\d+[.、。]\s*", "", line), "expected_result": ""}
        for i, line in enumerate(lines, 1)
    ]


def _normalize_priority(p: str) -> str:
    p = p.upper().strip()
    return p if p in ("P0", "P1", "P2", "P3") else "P1"


def _normalize_case_type(t: str) -> str:
    mapping = {
        "功能测试": "functional",
        "functional": "functional",
        "边界测试": "boundary",
        "boundary": "boundary",
        "异常测试": "exception",
        "exception": "exception",
        "性能测试": "performance",
        "performance": "performance",
        "安全测试": "security",
        "security": "security",
    }
    return mapping.get(t, "functional")
