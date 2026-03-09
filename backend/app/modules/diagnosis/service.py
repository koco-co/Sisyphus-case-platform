import json
import logging
import re
from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import assemble_prompt
from app.ai.stream_adapter import get_thinking_stream
from app.modules.diagnosis.models import DiagnosisChatMessage, DiagnosisReport, DiagnosisRisk
from app.modules.diagnosis.schemas import DiagnosisRiskUpdate
from app.modules.products.models import Requirement

logger = logging.getLogger(__name__)


class DiagnosisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── 查询方法 ──────────────────────────────────────────────────────

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

    # ── 流式诊断 ──────────────────────────────────────────────────────

    async def run_stream(self, requirement_id: UUID) -> AsyncIterator[str]:
        req = await self.session.get(Requirement, requirement_id)
        content = json.dumps(req.content_ast, ensure_ascii=False) if req else ""
        title = req.title if req else ""

        # 注入行业清单匹配结果到 Prompt
        from app.engine.diagnosis.checklist import get_checklist_summary

        checklist_hint = get_checklist_summary(content)

        user_content = (
            f"请对以下需求进行健康诊断：\n\n"
            f"需求标题：{title}\n\n需求内容：\n{content}\n\n"
            f"---\n行业清单参考：\n{checklist_hint}"
        )
        task_instruction = "对用户提供的需求文档进行全面的测试健康诊断，按 6 个维度逐一扫描并给出评分。"
        system = assemble_prompt("diagnosis", task_instruction)
        messages = [{"role": "user", "content": user_content}]
        return await get_thinking_stream(messages, system=system)

    # ── 报告管理 ──────────────────────────────────────────────────────

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
        risk_count_industry: int = 0,
        overall_score: float | None = None,
    ) -> DiagnosisReport | None:
        report = await self.session.get(DiagnosisReport, report_id)
        if report:
            report.status = "completed"
            report.summary = summary
            report.risk_count_high = risk_count_high
            report.risk_count_medium = risk_count_medium
            report.risk_count_industry = risk_count_industry
            if overall_score is not None:
                report.overall_score = overall_score
            await self.session.commit()
            await self.session.refresh(report)
        return report

    # ── 消息管理 ──────────────────────────────────────────────────────

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

    async def get_current_round(self, report_id: UUID) -> int:
        """获取当前对话轮次编号。"""
        q = select(func.max(DiagnosisChatMessage.round_num)).where(
            DiagnosisChatMessage.report_id == report_id,
            DiagnosisChatMessage.deleted_at.is_(None),
        )
        result = await self.session.execute(q)
        max_round = result.scalar_one_or_none()
        return (max_round or 0) + 1

    # ── 追问式对话 ────────────────────────────────────────────────────

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

    # ── AI 响应自动解析与持久化 ────────────────────────────────────────

    async def persist_ai_response(
        self,
        report_id: UUID,
        ai_content: str,
        round_num: int = 1,
    ) -> list[DiagnosisRisk]:
        """将 AI 诊断响应持久化：保存消息 + 解析风险项。

        1. 保存聊天消息到 DiagnosisChatMessage（role=assistant）
        2. 从 AI 内容中安全提取 JSON 风险项数组
        3. 写入 DiagnosisRisk 表
        4. 更新 DiagnosisReport 的风险计数和评分
        """
        # 1. 保存 assistant 消息
        msg = DiagnosisChatMessage(
            report_id=report_id,
            role="assistant",
            content=ai_content,
            round_num=round_num,
        )
        self.session.add(msg)

        # 2. 安全提取 JSON 风险项
        risks: list[DiagnosisRisk] = []
        match = re.search(r"\[.*\]", ai_content, re.DOTALL)
        if match:
            try:
                risk_data = json.loads(match.group())
                for item in risk_data:
                    if not isinstance(item, dict):
                        continue
                    level = item.get("risk_level") or item.get("level") or item.get("severity", "medium")
                    title = item.get("title", "")
                    if not title:
                        continue
                    risk = DiagnosisRisk(
                        report_id=report_id,
                        level=level,
                        title=title,
                        description=item.get("description", ""),
                    )
                    self.session.add(risk)
                    risks.append(risk)
            except (json.JSONDecodeError, TypeError):
                logger.debug("AI 响应非结构化，仅保存消息（report_id=%s）", report_id)

        await self.session.flush()

        # 3. 更新报告的风险计数
        if risks:
            high = sum(1 for r in risks if r.level == "high")
            medium = sum(1 for r in risks if r.level == "medium")
            report = await self.session.get(DiagnosisReport, report_id)
            if report:
                report.risk_count_high = high
                report.risk_count_medium = medium

        # 4. 尝试从内容中提取总分
        score_match = re.search(r"(?:总体|总分|健康评分|overall)[：:\s]*(\d{1,3})", ai_content)
        if score_match:
            score = min(int(score_match.group(1)), 100)
            report = await self.session.get(DiagnosisReport, report_id)
            if report:
                report.overall_score = float(score)

        await self.session.commit()
        logger.info("AI 响应已持久化: report_id=%s, risks=%d", report_id, len(risks))
        return risks

    # ── 完整诊断流程（引擎整合） ───────────────────────────────────────

    async def run_full_diagnosis(
        self,
        requirement_id: UUID,
        requirement_text: str,
    ) -> dict:
        """运行完整诊断流程：扫描 → 清单匹配 → 质量评估 → 生成报告。

        Returns:
            dict: {
                "report_id": UUID,
                "scan_risks": [...],
                "checklist": {"matched": [...], "unmatched": [...], ...},
                "quality": {"scores": {...}, "overall": int, ...},
            }
        """
        from app.engine.diagnosis.checklist import match_checklist
        from app.engine.diagnosis.quality_evaluator import evaluate_requirement_quality
        from app.engine.diagnosis.scanner import scan_requirement

        report = await self.create_or_get_report(requirement_id)
        report_id = report.id

        # 1. 广度扫描
        scan_risks = await scan_requirement(requirement_text)

        # 2. 清单匹配
        checklist_result = match_checklist(requirement_text)

        # 3. 质量评估
        try:
            quality = await evaluate_requirement_quality(requirement_text)
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning("质量评估失败: %s", e)
            quality = {"scores": {}, "issues": [], "overall": 0}

        # 4. 持久化风险项
        for item in scan_risks:
            risk = DiagnosisRisk(
                report_id=report_id,
                level=item.get("risk_level", "medium"),
                title=item.get("title", ""),
                description=item.get("description", ""),
            )
            self.session.add(risk)

        # 5. 补充行业清单未覆盖项为风险
        industry_count = 0
        for item in checklist_result.get("unmatched", []):
            risk = DiagnosisRisk(
                report_id=report_id,
                level="medium",
                title=f"[行业清单] {item['title']}",
                description=item.get("description", ""),
            )
            self.session.add(risk)
            industry_count += 1

        # 6. 更新报告
        high_count = sum(1 for r in scan_risks if r.get("risk_level") == "high")
        medium_count = sum(1 for r in scan_risks if r.get("risk_level") == "medium")

        summary_parts = [
            f"广度扫描发现 {len(scan_risks)} 个风险项",
            f"行业清单覆盖率 {checklist_result.get('coverage_rate', 0):.0%}",
            f"质量总分 {quality.get('overall', 0)} 分",
        ]

        await self.complete_report(
            report_id=report_id,
            summary="；".join(summary_parts),
            risk_count_high=high_count,
            risk_count_medium=medium_count,
            risk_count_industry=industry_count,
            overall_score=float(quality.get("overall", 0)),
        )

        return {
            "report_id": report_id,
            "scan_risks": scan_risks,
            "checklist": checklist_result,
            "quality": quality,
        }
