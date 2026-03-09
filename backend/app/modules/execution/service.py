import logging
from uuid import UUID

import httpx
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.execution.models import ExecutionResult
from app.modules.execution.schemas import ExecutionResultCreate

logger = logging.getLogger(__name__)


class ExecutionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_result(self, data: ExecutionResultCreate) -> ExecutionResult:
        q = select(ExecutionResult).where(
            ExecutionResult.test_case_id == data.test_case_id,
            ExecutionResult.iteration_id == data.iteration_id,
            ExecutionResult.deleted_at.is_(None),
        )
        existing = (await self.session.execute(q)).scalar_one_or_none()

        if existing:
            for field, value in data.model_dump(exclude={"test_case_id", "iteration_id"}).items():
                if value is not None:
                    setattr(existing, field, value)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        result = ExecutionResult(**data.model_dump())
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def batch_import_results(self, results: list[ExecutionResultCreate]) -> list[ExecutionResult]:
        created = []
        for data in results:
            result = await self.record_result(data)
            created.append(result)
        return created

    async def get_execution_summary(self, iteration_id: UUID) -> dict:
        count_q = select(
            func.count().label("total"),
            func.sum(case((ExecutionResult.status == "passed", 1), else_=0)).label("passed"),
            func.sum(case((ExecutionResult.status == "failed", 1), else_=0)).label("failed"),
            func.sum(case((ExecutionResult.status == "blocked", 1), else_=0)).label("blocked"),
            func.sum(case((ExecutionResult.status == "skipped", 1), else_=0)).label("skipped"),
            func.min(ExecutionResult.executed_at).label("earliest"),
            func.max(ExecutionResult.executed_at).label("latest"),
        ).where(
            ExecutionResult.iteration_id == iteration_id,
            ExecutionResult.deleted_at.is_(None),
        )

        row = (await self.session.execute(count_q)).one()
        total = row.total or 0
        passed = row.passed or 0
        failed = row.failed or 0
        blocked = row.blocked or 0
        skipped = row.skipped or 0

        executed_at_range = None
        if row.earliest and row.latest:
            executed_at_range = {
                "earliest": row.earliest.isoformat(),
                "latest": row.latest.isoformat(),
            }

        return {
            "iteration_id": iteration_id,
            "total": total,
            "passed": passed,
            "failed": failed,
            "blocked": blocked,
            "skipped": skipped,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0.0,
            "executed_at_range": executed_at_range,
        }

    async def get_case_history(self, case_id: UUID) -> list[ExecutionResult]:
        q = (
            select(ExecutionResult)
            .where(
                ExecutionResult.test_case_id == case_id,
                ExecutionResult.deleted_at.is_(None),
            )
            .order_by(ExecutionResult.executed_at.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def mark_failed(
        self,
        test_case_id: UUID,
        iteration_id: UUID,
        defect_id: str | None = None,
        actual_result: str | None = None,
    ) -> ExecutionResult:
        """Mark a test case as failed with optional defect linkage."""
        from app.modules.execution.schemas import ExecutionResultCreate

        data = ExecutionResultCreate(
            test_case_id=test_case_id,
            iteration_id=iteration_id,
            status="failed",
            defect_id=defect_id,
            actual_result=actual_result,
        )
        return await self.record_result(data)

    async def get_failed_cases(self, iteration_id: UUID) -> list[ExecutionResult]:
        """List all failed execution results for an iteration."""
        q = (
            select(ExecutionResult)
            .where(
                ExecutionResult.iteration_id == iteration_id,
                ExecutionResult.status == "failed",
                ExecutionResult.deleted_at.is_(None),
            )
            .order_by(ExecutionResult.executed_at.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    # ── RAG Weight Adjustment (B-M13-04) ──────────────────────────────

    async def adjust_rag_weights(self, execution_results: list[dict]) -> dict:
        """根据执行结果调整 RAG 权重。

        失败用例关联的知识文档降权，成功用例关联的知识文档升权。
        """
        from app.modules.knowledge.models import KnowledgeDocument
        from app.modules.testcases.models import TestCase

        adjusted_docs: list[dict] = []
        skipped = 0

        for er in execution_results:
            test_case_id = er.get("test_case_id")
            status = er.get("status", "")
            if not test_case_id or status not in ("passed", "failed"):
                skipped += 1
                continue

            # 查找用例关联的知识文档（通过 tags 中的 knowledge_doc_ids）
            tc_q = select(TestCase).where(
                TestCase.id == test_case_id,
                TestCase.deleted_at.is_(None),
            )
            tc = (await self.session.execute(tc_q)).scalar_one_or_none()
            if not tc or not tc.tags:
                skipped += 1
                continue

            doc_ids = [t for t in tc.tags if isinstance(t, str) and t.startswith("kdoc:")]
            if not doc_ids:
                skipped += 1
                continue

            for doc_ref in doc_ids:
                doc_id_str = doc_ref.replace("kdoc:", "")
                try:
                    doc_uuid = UUID(doc_id_str)
                except ValueError:
                    continue

                doc_q = select(KnowledgeDocument).where(
                    KnowledgeDocument.id == doc_uuid,
                    KnowledgeDocument.deleted_at.is_(None),
                )
                doc = (await self.session.execute(doc_q)).scalar_one_or_none()
                if not doc:
                    continue

                tags = dict(doc.tags) if doc.tags else {}
                current_weight = float(tags.get("rag_weight", 1.0))

                new_weight = min(current_weight + 0.1, 2.0) if status == "passed" else max(current_weight - 0.2, 0.1)

                tags["rag_weight"] = round(new_weight, 2)
                doc.tags = tags
                adjusted_docs.append({"doc_id": str(doc_uuid), "old_weight": current_weight, "new_weight": new_weight})

        await self.session.commit()

        return {
            "adjusted_count": len(adjusted_docs),
            "skipped_count": skipped,
            "adjustments": adjusted_docs,
        }

    # ── Jira/Xray Results Sync (B-M13-06) ────────────────────────────

    async def sync_results_to_jira(self, case_ids: list[UUID], jira_config: dict) -> dict:
        """回写执行结果到 Jira/Xray。"""
        base_url = jira_config.get("base_url", "").rstrip("/")
        auth_token = jira_config.get("auth_token", "")
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        synced: list[dict] = []
        failed_count = 0

        results_q = (
            select(ExecutionResult)
            .where(
                ExecutionResult.test_case_id.in_(case_ids),
                ExecutionResult.deleted_at.is_(None),
            )
            .order_by(ExecutionResult.executed_at.desc())
        )
        result = await self.session.execute(results_q)
        execution_results = list(result.scalars().all())

        # 每个 case_id 只取最新的执行结果
        seen_cases: set[UUID] = set()
        latest_results: list[ExecutionResult] = []
        for er in execution_results:
            if er.test_case_id not in seen_cases:
                seen_cases.add(er.test_case_id)
                latest_results.append(er)

        status_map = {"passed": "PASS", "failed": "FAIL", "blocked": "BLOCKED", "skipped": "TODO"}

        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            for er in latest_results:
                jira_status = status_map.get(er.status, "TODO")
                payload = {
                    "status": jira_status,
                    "comment": er.actual_result or "",
                    "defects": [er.defect_id] if er.defect_id else [],
                    "environment": er.environment or "",
                    "executedBy": str(er.executor_id) if er.executor_id else "",
                }
                try:
                    # Xray REST API: update test run
                    resp = await client.put(
                        f"{base_url}/rest/raven/1.0/api/testrun/{er.test_case_id}/status",
                        json=payload,
                        headers=headers,
                    )
                    if resp.status_code in (200, 204):
                        synced.append({"test_case_id": str(er.test_case_id), "status": jira_status, "synced": True})
                    else:
                        logger.warning("Jira sync failed for %s: %s", er.test_case_id, resp.text[:200])
                        failed_count += 1
                except httpx.HTTPError as e:
                    logger.warning("Jira sync error for %s: %s", er.test_case_id, str(e))
                    failed_count += 1

        status = "completed" if failed_count == 0 else ("partial" if synced else "failed")
        return {
            "status": status,
            "synced_count": len(synced),
            "failed_count": failed_count,
            "results": synced,
            "error_message": None if failed_count == 0 else f"{failed_count} result(s) failed to sync",
        }
