import csv
import io
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.testcases.models import TestCase, TestCaseStep


class ExportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def export_cases_json(self, requirement_id: UUID | None = None) -> str:
        cases = await self._get_cases(requirement_id)
        return json.dumps(cases, ensure_ascii=False, indent=2)

    async def export_cases_csv(self, requirement_id: UUID | None = None) -> str:
        cases = await self._get_cases(requirement_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["case_id", "title", "priority", "case_type", "status", "precondition", "steps"])

        for case in cases:
            steps_text = "; ".join(
                f"Step {s['step_num']}: {s['action']} -> {s['expected_result']}" for s in case.get("steps", [])
            )
            writer.writerow(
                [
                    case["case_id"],
                    case["title"],
                    case["priority"],
                    case["case_type"],
                    case["status"],
                    case.get("precondition", ""),
                    steps_text,
                ]
            )

        return output.getvalue()

    async def _get_cases(self, requirement_id: UUID | None) -> list[dict]:
        q = select(TestCase).where(TestCase.deleted_at.is_(None))
        if requirement_id:
            q = q.where(TestCase.requirement_id == requirement_id)
        q = q.order_by(TestCase.created_at)
        result = await self.session.execute(q)
        cases = result.scalars().all()

        output: list[dict] = []
        for tc in cases:
            step_q = (
                select(TestCaseStep)
                .where(
                    TestCaseStep.test_case_id == tc.id,
                    TestCaseStep.deleted_at.is_(None),
                )
                .order_by(TestCaseStep.step_num)
            )
            step_result = await self.session.execute(step_q)
            steps = step_result.scalars().all()

            output.append(
                {
                    "case_id": tc.case_id,
                    "title": tc.title,
                    "priority": tc.priority,
                    "case_type": tc.case_type,
                    "status": tc.status,
                    "precondition": tc.precondition,
                    "steps": [
                        {"step_num": s.step_num, "action": s.action, "expected_result": s.expected_result}
                        for s in steps
                    ],
                }
            )

        return output
