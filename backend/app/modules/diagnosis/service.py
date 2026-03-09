import json
from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import assemble_prompt
from app.ai.stream_adapter import get_thinking_stream
from app.modules.diagnosis.models import DiagnosisChatMessage, DiagnosisReport, DiagnosisRisk
from app.modules.diagnosis.schemas import DiagnosisRiskUpdate
from app.modules.products.models import Requirement


class DiagnosisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_report(self, requirement_id: UUID) -> DiagnosisReport | None:
        q = select(DiagnosisReport).where(
            DiagnosisReport.requirement_id == requirement_id,
            DiagnosisReport.deleted_at.is_(None),
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def list_risks(self, report_id: UUID) -> list[DiagnosisRisk]:
        q = select(DiagnosisRisk).where(
            DiagnosisRisk.report_id == report_id,
            DiagnosisRisk.deleted_at.is_(None),
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_risk(self, risk_id: UUID) -> DiagnosisRisk | None:
        q = select(DiagnosisRisk).where(
            DiagnosisRisk.id == risk_id,
            DiagnosisRisk.deleted_at.is_(None),
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def update_risk_status(self, risk: DiagnosisRisk, data: DiagnosisRiskUpdate) -> DiagnosisRisk:
        risk.risk_status = data.risk_status
        await self.session.commit()
        await self.session.refresh(risk)
        return risk

    async def run_stream(self, requirement_id: UUID) -> AsyncIterator[str]:
        req = await self.session.get(Requirement, requirement_id)
        content = json.dumps(req.content_ast, ensure_ascii=False) if req else ""
        title = req.title if req else ""
        user_content = f"请对以下需求进行健康诊断：\n\n需求标题：{title}\n\n需求内容：\n{content}"
        task_instruction = "对用户提供的需求文档进行全面的测试健康诊断，按 6 个维度逐一扫描并给出评分。"
        system = assemble_prompt("diagnosis", task_instruction)
        messages = [{"role": "user", "content": user_content}]
        return await get_thinking_stream(messages, system=system)

    async def create_or_get_report(self, requirement_id: UUID) -> DiagnosisReport:
        report = await self.get_report(requirement_id)
        if report:
            return report
        report = DiagnosisReport(
            requirement_id=requirement_id,
            status="running",
        )
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def complete_report(
        self,
        report_id: UUID,
        summary: str,
        risk_count_high: int = 0,
        risk_count_medium: int = 0,
    ) -> DiagnosisReport | None:
        report = await self.session.get(DiagnosisReport, report_id)
        if report:
            report.status = "completed"
            report.summary = summary
            report.risk_count_high = risk_count_high
            report.risk_count_medium = risk_count_medium
            await self.session.commit()
            await self.session.refresh(report)
        return report

    async def save_message(self, report_id: UUID, role: str, content: str, round_num: int = 1) -> DiagnosisChatMessage:
        msg = DiagnosisChatMessage(
            report_id=report_id,
            role=role,
            content=content,
            round_num=round_num,
        )
        self.session.add(msg)
        await self.session.commit()
        return msg

    async def list_messages(self, report_id: UUID) -> list[DiagnosisChatMessage]:
        q = (
            select(DiagnosisChatMessage)
            .where(
                DiagnosisChatMessage.report_id == report_id,
                DiagnosisChatMessage.deleted_at.is_(None),
            )
            .order_by(DiagnosisChatMessage.created_at)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def chat_stream(self, requirement_id: UUID, user_message: str) -> AsyncIterator[str]:
        report = await self.get_report(requirement_id)
        history: list[dict] = []
        if report:
            q = (
                select(DiagnosisChatMessage)
                .where(
                    DiagnosisChatMessage.report_id == report.id,
                    DiagnosisChatMessage.deleted_at.is_(None),
                )
                .order_by(DiagnosisChatMessage.created_at)
            )
            result = await self.session.execute(q)
            for msg in result.scalars().all():
                history.append({"role": msg.role, "content": msg.content})

        history.append({"role": "user", "content": user_message})
        task_instruction = "针对上一轮对话中发现的风险点进行苏格拉底式追问，深入挖掘需求盲区。"
        system = assemble_prompt("diagnosis_followup", task_instruction)
        return await get_thinking_stream(history, system=system)
