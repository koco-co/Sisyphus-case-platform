import uuid
from datetime import date, timedelta
from typing import cast

from sqlalchemy import BinaryExpression, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import AnalyticsSnapshot
from app.modules.execution.models import ExecutionResult
from app.modules.products.models import Iteration, Product, Requirement
from app.modules.testcases.models import TestCase


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _iteration_case_filter(self, iteration_id: uuid.UUID | None):
        conditions: list[BinaryExpression[bool]] = [
            TestCase.deleted_at.is_(None),
            Requirement.deleted_at.is_(None),
        ]
        if iteration_id is not None:
            conditions.append(cast(BinaryExpression[bool], Requirement.iteration_id == iteration_id))
        return conditions

    def _case_ids_subquery(self, iteration_id: uuid.UUID | None):
        return (
            select(TestCase.id)
            .join(Requirement, TestCase.requirement_id == Requirement.id)
            .where(*self._iteration_case_filter(iteration_id))
            .subquery()
        )

    def _snapshot_query(self, iteration_id: uuid.UUID | None, since: date):
        q = (
            select(AnalyticsSnapshot)
            .where(
                AnalyticsSnapshot.deleted_at.is_(None),
                AnalyticsSnapshot.snapshot_date >= since,
            )
            .order_by(AnalyticsSnapshot.snapshot_date)
        )
        if iteration_id is not None:
            q = q.where(AnalyticsSnapshot.iteration_id == iteration_id)
        return q

    async def _count_cases(self, iteration_id: uuid.UUID | None = None) -> int:
        q = (
            select(func.count())
            .select_from(TestCase)
            .join(Requirement, TestCase.requirement_id == Requirement.id)
            .where(*self._iteration_case_filter(iteration_id))
        )
        return (await self.session.execute(q)).scalar() or 0

    async def _get_executed_case_count(self, iteration_id: uuid.UUID | None = None) -> int:
        case_ids_subq = self._case_ids_subquery(iteration_id)
        return (
            await self.session.execute(
                select(func.count(func.distinct(ExecutionResult.test_case_id))).where(
                    ExecutionResult.deleted_at.is_(None),
                    ExecutionResult.test_case_id.in_(select(case_ids_subq.c.id)),
                )
            )
        ).scalar() or 0

    async def _get_ai_generated_case_count(self, iteration_id: uuid.UUID | None = None) -> int:
        q = (
            select(func.count())
            .select_from(TestCase)
            .join(Requirement, TestCase.requirement_id == Requirement.id)
            .where(
                *self._iteration_case_filter(iteration_id),
                TestCase.source == "ai_generated",
            )
        )
        return (await self.session.execute(q)).scalar() or 0

    def _calculate_overview_metrics(
        self,
        total_cases: int,
        exec_counts: dict[str, int],
        executed_cases: int,
        ai_generated_cases: int,
    ) -> dict[str, float]:
        total_executed = sum(exec_counts.values())
        passed = exec_counts.get("passed", 0)
        failed = exec_counts.get("failed", 0)

        pass_rate = round((passed / total_executed * 100) if total_executed > 0 else 0.0, 2)
        coverage_rate = round((executed_cases / total_cases * 100) if total_cases > 0 else 0.0, 2)
        defect_density = round((failed / total_cases) if total_cases > 0 else 0.0, 2)
        automation_rate = round((ai_generated_cases / total_cases * 100) if total_cases > 0 else 0.0, 2)
        quality_score = round(
            min(
                100.0,
                max(
                    0.0,
                    pass_rate * 0.4
                    + coverage_rate * 0.4
                    + max(0.0, 100 - defect_density * 10) * 0.2,
                ),
            ),
            2,
        )

        return {
            "pass_rate": pass_rate,
            "coverage_rate": coverage_rate,
            "defect_density": defect_density,
            "automation_rate": automation_rate,
            "quality_score": quality_score,
        }

    async def get_quality_overview(self, iteration_id: uuid.UUID | None = None) -> dict:
        product_count = (
            await self.session.execute(select(func.count()).select_from(Product).where(Product.deleted_at.is_(None)))
        ).scalar() or 0

        iteration_count = (
            await self.session.execute(
                select(func.count()).select_from(Iteration).where(Iteration.deleted_at.is_(None))
            )
        ).scalar() or 0

        req_q = select(func.count()).select_from(Requirement).where(Requirement.deleted_at.is_(None))
        if iteration_id is not None:
            req_q = req_q.where(Requirement.iteration_id == iteration_id)
        requirement_count = (await self.session.execute(req_q)).scalar() or 0

        testcase_count = await self._count_cases(iteration_id)
        exec_counts = await self._get_execution_counts(iteration_id)
        executed_cases = await self._get_executed_case_count(iteration_id)
        ai_generated_cases = await self._get_ai_generated_case_count(iteration_id)
        metrics = self._calculate_overview_metrics(
            total_cases=testcase_count,
            exec_counts=exec_counts,
            executed_cases=executed_cases,
            ai_generated_cases=ai_generated_cases,
        )

        return {
            "product_count": product_count,
            "iteration_count": iteration_count,
            "requirement_count": requirement_count,
            "testcase_count": testcase_count,
            **metrics,
        }

    async def get_priority_distribution(self, iteration_id: uuid.UUID | None = None) -> list[dict]:
        q = (
            select(TestCase.priority, func.count())
            .join(Requirement, TestCase.requirement_id == Requirement.id)
            .where(*self._iteration_case_filter(iteration_id))
            .group_by(TestCase.priority)
        )
        result = await self.session.execute(q)
        return [{"priority": row[0], "count": row[1]} for row in result.all()]

    async def get_status_distribution(self, iteration_id: uuid.UUID | None = None) -> list[dict]:
        q = (
            select(TestCase.status, func.count())
            .join(Requirement, TestCase.requirement_id == Requirement.id)
            .where(*self._iteration_case_filter(iteration_id))
            .group_by(TestCase.status)
        )
        result = await self.session.execute(q)
        return [{"status": row[0], "count": row[1]} for row in result.all()]

    async def get_source_distribution(self, iteration_id: uuid.UUID | None = None) -> list[dict]:
        q = (
            select(TestCase.source, func.count())
            .join(Requirement, TestCase.requirement_id == Requirement.id)
            .where(*self._iteration_case_filter(iteration_id))
            .group_by(TestCase.source)
        )
        result = await self.session.execute(q)
        return [{"source": row[0], "count": row[1]} for row in result.all()]

    async def _count_cases_for_iteration(self, iteration_id: uuid.UUID) -> int:
        return await self._count_cases(iteration_id)

    async def _get_execution_counts(self, iteration_id: uuid.UUID | None = None) -> dict[str, int]:
        case_ids_subq = self._case_ids_subquery(iteration_id)
        q = (
            select(ExecutionResult.status, func.count())
            .where(
                ExecutionResult.deleted_at.is_(None),
                ExecutionResult.test_case_id.in_(select(case_ids_subq.c.id)),
            )
            .group_by(ExecutionResult.status)
        )
        result = await self.session.execute(q)
        counts: dict[str, int] = {}
        for row in result.all():
            counts[row[0]] = row[1]
        return counts

    async def take_snapshot(self, iteration_id: uuid.UUID) -> AnalyticsSnapshot:
        total_cases = await self._count_cases_for_iteration(iteration_id)
        exec_counts = await self._get_execution_counts(iteration_id)
        executed_cases = await self._get_executed_case_count(iteration_id)
        ai_generated_cases = await self._get_ai_generated_case_count(iteration_id)
        metrics = self._calculate_overview_metrics(
            total_cases=total_cases,
            exec_counts=exec_counts,
            executed_cases=executed_cases,
            ai_generated_cases=ai_generated_cases,
        )
        reuse_rate = 0.0

        snapshot_metrics = {
            "total_cases": total_cases,
            "passed": exec_counts.get("passed", 0),
            "failed": exec_counts.get("failed", 0),
            "blocked": exec_counts.get("blocked", 0),
            "reuse_rate": reuse_rate,
            **metrics,
        }

        today = date.today()
        existing = (
            await self.session.execute(
                select(AnalyticsSnapshot).where(
                    AnalyticsSnapshot.deleted_at.is_(None),
                    AnalyticsSnapshot.iteration_id == iteration_id,
                    AnalyticsSnapshot.snapshot_date == today,
                )
            )
        ).scalar_one_or_none()

        if existing:
            existing.metrics = snapshot_metrics
            existing.trends = None
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        snapshot = AnalyticsSnapshot(
            iteration_id=iteration_id,
            snapshot_date=today,
            metrics=snapshot_metrics,
        )
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot

    async def get_dashboard_data(self, iteration_id: uuid.UUID) -> dict:
        total_cases = await self._count_cases_for_iteration(iteration_id)
        exec_counts = await self._get_execution_counts(iteration_id)
        executed_cases = await self._get_executed_case_count(iteration_id)
        ai_generated_cases = await self._get_ai_generated_case_count(iteration_id)
        metrics = self._calculate_overview_metrics(
            total_cases=total_cases,
            exec_counts=exec_counts,
            executed_cases=executed_cases,
            ai_generated_cases=ai_generated_cases,
        )

        total_executed = sum(exec_counts.values())
        failed = exec_counts.get("failed", 0)

        pass_rate = metrics["pass_rate"]
        fail_rate = round((failed / total_executed * 100) if total_executed > 0 else 0.0, 2)

        priority_dist = await self.get_priority_distribution(iteration_id)
        status_dist = await self.get_status_distribution(iteration_id)
        source_dist = await self.get_source_distribution(iteration_id)

        return {
            "overview": {
                "total_cases": total_cases,
                "total_executed": total_executed,
                "pass_rate": pass_rate,
                "fail_rate": fail_rate,
            },
            "priority_distribution": priority_dist,
            "status_distribution": status_dist,
            "source_distribution": source_dist,
            "execution_summary": {
                "passed": exec_counts.get("passed", 0),
                "failed": failed,
                "blocked": exec_counts.get("blocked", 0),
                "skipped": exec_counts.get("skipped", 0),
            },
        }

    async def get_trend_data(self, iteration_id: uuid.UUID, days: int = 30) -> dict:
        since = date.today() - timedelta(days=days)
        result = await self.session.execute(self._snapshot_query(iteration_id, since))
        snapshots = result.scalars().all()

        dates: list[str] = []
        metrics_data: dict[str, list] = {
            "total_cases": [],
            "passed": [],
            "failed": [],
            "blocked": [],
            "coverage_rate": [],
            "defect_density": [],
        }

        for snap in snapshots:
            dates.append(snap.snapshot_date.isoformat())
            m = snap.metrics or {}
            for key in metrics_data:
                metrics_data[key].append(m.get(key, 0))

        return {"dates": dates, "metrics": metrics_data}

    async def get_frontend_trends(self, iteration_id: uuid.UUID | None = None, days: int = 30) -> dict:
        since = date.today() - timedelta(days=days)
        result = await self.session.execute(self._snapshot_query(iteration_id, since))
        snapshots = result.scalars().all()

        aggregated: dict[str, dict[str, float]] = {}
        for snap in snapshots:
            date_key = snap.snapshot_date.strftime("%m/%d")
            bucket = aggregated.setdefault(
                date_key,
                {"total_cases": 0.0, "passed": 0.0, "failed": 0.0, "blocked": 0.0},
            )
            metrics = snap.metrics or {}
            bucket["total_cases"] += float(metrics.get("total_cases", 0))
            bucket["passed"] += float(metrics.get("passed", 0))
            bucket["failed"] += float(metrics.get("failed", 0))
            bucket["blocked"] += float(metrics.get("blocked", 0))

        case_count_trend: list[dict[str, float | str]] = []
        pass_rate_trend: list[dict[str, float | str]] = []
        for date_key, bucket in aggregated.items():
            total_executed = bucket["passed"] + bucket["failed"] + bucket["blocked"]
            pass_rate = round((bucket["passed"] / total_executed * 100) if total_executed > 0 else 0.0, 2)
            case_count_trend.append({"date": date_key, "value": round(bucket["total_cases"])})
            pass_rate_trend.append({"date": date_key, "value": pass_rate})

        return {
            "case_count_trend": case_count_trend,
            "pass_rate_trend": pass_rate_trend,
        }

    async def get_quality_score(self, iteration_id: uuid.UUID) -> dict:
        total_cases = await self._count_cases_for_iteration(iteration_id)
        exec_counts = await self._get_execution_counts(iteration_id)

        total_executed = sum(exec_counts.values())
        passed = exec_counts.get("passed", 0)

        pass_rate = (passed / total_executed) if total_executed > 0 else 0.0

        case_ids_subq = (
            select(TestCase.id)
            .join(Requirement, TestCase.requirement_id == Requirement.id)
            .where(*self._iteration_case_filter(iteration_id))
            .subquery()
        )
        executed_cases = (
            await self.session.execute(
                select(func.count(func.distinct(ExecutionResult.test_case_id))).where(
                    ExecutionResult.deleted_at.is_(None),
                    ExecutionResult.test_case_id.in_(select(case_ids_subq.c.id)),
                )
            )
        ).scalar() or 0

        coverage_rate = (executed_cases / total_cases) if total_cases > 0 else 0.0
        defect_density = 0.0

        pass_rate_score = min(40.0, round(pass_rate * 40, 2))
        coverage_score = min(30.0, round(coverage_rate * 30, 2))
        defect_score = min(20.0, round(max(0, 20 - defect_density * 100), 2))
        case_completeness = min(10.0, round(total_cases / 10, 2)) if total_cases > 0 else 0.0

        total_score = round(pass_rate_score + coverage_score + defect_score + case_completeness, 2)

        if total_score >= 90:
            grade = "A"
        elif total_score >= 80:
            grade = "B"
        elif total_score >= 70:
            grade = "C"
        elif total_score >= 60:
            grade = "D"
        else:
            grade = "F"

        return {
            "iteration_id": iteration_id,
            "score": total_score,
            "breakdown": {
                "pass_rate_score": pass_rate_score,
                "coverage_score": coverage_score,
                "defect_score": defect_score,
                "case_completeness": case_completeness,
            },
            "grade": grade,
        }

    async def get_ai_usage_stats(self, iteration_id: uuid.UUID | None = None) -> dict:
        """Get AI call statistics: session count, message count, model usage."""
        from app.modules.generation.models import GenerationMessage, GenerationSession

        session_q = (
            select(func.count())
            .select_from(GenerationSession)
            .where(
                GenerationSession.deleted_at.is_(None),
            )
        )
        msg_q = (
            select(func.count())
            .select_from(GenerationMessage)
            .where(
                GenerationMessage.deleted_at.is_(None),
            )
        )
        token_q = select(func.coalesce(func.sum(GenerationMessage.token_count), 0)).where(
            GenerationMessage.deleted_at.is_(None),
        )
        model_q = (
            select(GenerationSession.model_used, func.count())
            .where(GenerationSession.deleted_at.is_(None))
            .group_by(GenerationSession.model_used)
        )

        if iteration_id:
            req_ids_subq = (
                select(Requirement.id)
                .where(
                    Requirement.iteration_id == iteration_id,
                    Requirement.deleted_at.is_(None),
                )
                .subquery()
            )
            session_q = session_q.where(
                GenerationSession.requirement_id.in_(select(req_ids_subq.c.id)),
            )
            session_ids_subq = (
                select(GenerationSession.id)
                .where(
                    GenerationSession.requirement_id.in_(select(req_ids_subq.c.id)),
                    GenerationSession.deleted_at.is_(None),
                )
                .subquery()
            )
            msg_q = msg_q.where(GenerationMessage.session_id.in_(select(session_ids_subq.c.id)))
            token_q = token_q.where(GenerationMessage.session_id.in_(select(session_ids_subq.c.id)))
            model_q = model_q.where(
                GenerationSession.requirement_id.in_(select(req_ids_subq.c.id)),
            )

        total_sessions = (await self.session.execute(session_q)).scalar() or 0
        total_messages = (await self.session.execute(msg_q)).scalar() or 0
        total_tokens = (await self.session.execute(token_q)).scalar() or 0

        model_result = await self.session.execute(model_q)
        model_usage = [{"model": row[0], "count": row[1]} for row in model_result.all()]

        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "model_usage": model_usage,
        }
