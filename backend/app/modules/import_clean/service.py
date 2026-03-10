"""M02 历史数据导入清洗 — Service"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.import_clean.models import ImportJob, ImportRecord

logger = logging.getLogger(__name__)


class ImportJobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_job(
        self,
        *,
        file_name: str,
        file_type: str,
        product_id: UUID | None = None,
    ) -> ImportJob:
        """创建导入任务。"""
        job = ImportJob(
            file_name=file_name,
            file_type=file_type,
            product_id=product_id,
            status="pending",
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_job(self, job_id: UUID) -> ImportJob | None:
        """获取导入任务。"""
        result = await self.session.execute(
            select(ImportJob).where(
                ImportJob.id == job_id,
                ImportJob.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_jobs(self, product_id: UUID | None = None) -> list[ImportJob]:
        """列出导入任务。"""
        stmt = select(ImportJob).where(ImportJob.deleted_at.is_(None))
        if product_id:
            stmt = stmt.where(ImportJob.product_id == product_id)
        stmt = stmt.order_by(ImportJob.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete_job(self, job_id: UUID) -> None:
        """软删除导入任务。"""
        job = await self.session.get(ImportJob, job_id)
        if not job or job.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="导入任务不存在")
        job.deleted_at = datetime.now(UTC)
        await self.session.commit()

    # ── 文件解析 ──────────────────────────────────────────────────

    async def parse_file_content(self, job_id: UUID, data: bytes, file_type: str) -> int:
        """解析文件内容，写入 ImportRecord。"""
        if file_type == "csv":
            from app.engine.import_clean.csv_parser import parse_csv_bytes

            records = parse_csv_bytes(data)
        elif file_type == "excel":
            from app.engine.import_clean.excel_parser import parse_excel

            records = parse_excel(data)
        elif file_type == "markdown":
            from app.engine.import_clean.md_parser import parse_markdown_bytes

            records = parse_markdown_bytes(data)
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"不支持的文件类型: {file_type}")

        for record in records:
            row_num = record.pop("_row_number", 0)
            title = record.get("title") or record.get("标题") or record.get("用例标题", "")
            db_record = ImportRecord(
                job_id=job_id,
                row_number=row_num,
                raw_data=record,
                original_title=title or None,
                status="pending",
            )
            self.session.add(db_record)

        job = await self.session.get(ImportJob, job_id)
        if job:
            job.total_records = len(records)
            job.status = "mapping"
        await self.session.commit()
        return len(records)

    # ── 字段映射 ──────────────────────────────────────────────────

    async def auto_map_fields(self, job_id: UUID) -> dict[str, str | None]:
        """对导入任务执行 AI 字段语义映射。"""
        job = await self._require_job(job_id)

        # 取第一条记录的列名作为样本
        result = await self.session.execute(
            select(ImportRecord)
            .where(ImportRecord.job_id == job_id, ImportRecord.deleted_at.is_(None))
            .order_by(ImportRecord.row_number)
            .limit(1)
        )
        sample = result.scalar_one_or_none()
        if not sample:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "任务无记录，无法映射")

        columns = [k for k in sample.raw_data if not k.startswith("_")]

        from app.engine.import_clean.field_mapper import map_fields

        mapping = await map_fields(columns)

        job.field_mapping = mapping
        job.status = "cleaning"
        await self.session.commit()
        return mapping

    async def update_field_mapping(self, job_id: UUID, mapping: dict[str, str | None]) -> None:
        """手动更新字段映射。"""
        job = await self._require_job(job_id)
        job.field_mapping = mapping
        await self.session.commit()

    async def apply_field_mapping(self, job_id: UUID) -> int:
        """将字段映射应用到所有记录，生成 mapped_data。"""
        job = await self._require_job(job_id)
        if not job.field_mapping:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "尚未配置字段映射")

        result = await self.session.execute(
            select(ImportRecord).where(
                ImportRecord.job_id == job_id,
                ImportRecord.deleted_at.is_(None),
            )
        )
        records = list(result.scalars().all())

        mapping = job.field_mapping
        count = 0
        for record in records:
            mapped: dict = {}
            for src_col, target_field in mapping.items():
                if target_field and src_col in record.raw_data:
                    mapped[target_field] = record.raw_data[src_col]
            record.mapped_data = mapped
            record.mapped_title = mapped.get("title") or record.original_title
            record.status = "accepted"
            count += 1

        await self.session.commit()
        return count

    # ── 重复检测 ──────────────────────────────────────────────────

    async def detect_duplicates(self, job_id: UUID) -> int:
        """对导入记录执行重复检测。"""
        result = await self.session.execute(
            select(ImportRecord).where(
                ImportRecord.job_id == job_id,
                ImportRecord.deleted_at.is_(None),
            )
        )
        records = list(result.scalars().all())

        titles = [{"title": r.original_title or r.mapped_title or ""} for r in records]

        from app.engine.import_clean.deduplicator import detect_duplicates

        matches = detect_duplicates(titles, title_key="title")

        seen_targets: set[int] = set()
        dup_count = 0
        for match in matches:
            target_record = records[match.target_index]
            if match.target_index in seen_targets:
                continue
            seen_targets.add(match.target_index)
            target_record.status = "duplicate"
            target_record.match_score = match.score
            target_record.duplicate_of = records[match.source_index].id
            dup_count += 1

        # 更新 job 计数
        job = await self._require_job(job_id)
        job.duplicate_count = dup_count
        await self.session.commit()

        logger.info("重复检测完成: job_id=%s, duplicates=%d", job_id, dup_count)
        return dup_count

    # ── 健康报告 ──────────────────────────────────────────────────

    async def generate_health_report(self, job_id: UUID) -> dict:
        """生成导入健康报告。"""
        job = await self._require_job(job_id)

        result = await self.session.execute(
            select(ImportRecord).where(
                ImportRecord.job_id == job_id,
                ImportRecord.deleted_at.is_(None),
            )
        )
        records = list(result.scalars().all())

        total = len(records)
        error_count = sum(1 for r in records if r.status == "error")
        dup_count = sum(1 for r in records if r.status == "duplicate")
        valid_count = total - error_count - dup_count

        # 字段覆盖率分析
        field_coverage: dict[str, float] = {}
        if job.field_mapping:
            target_fields = [v for v in job.field_mapping.values() if v]
            for field in target_fields:
                filled = sum(1 for r in records if r.mapped_data and r.mapped_data.get(field))
                field_coverage[field] = round(filled / total * 100, 1) if total > 0 else 0.0

        # 问题收集
        issues: list[dict] = []
        if error_count > 0:
            issues.append({"type": "error", "message": f"{error_count} 条记录解析失败", "count": error_count})
        if dup_count > 0:
            issues.append({"type": "duplicate", "message": f"{dup_count} 条记录疑似重复", "count": dup_count})
        for field, cov in field_coverage.items():
            if cov < 50:
                issues.append({"type": "low_coverage", "message": f"字段 '{field}' 覆盖率仅 {cov}%", "field": field})

        summary_parts = [f"共 {total} 条记录"]
        if valid_count > 0:
            summary_parts.append(f"{valid_count} 条有效")
        if dup_count > 0:
            summary_parts.append(f"{dup_count} 条重复")
        if error_count > 0:
            summary_parts.append(f"{error_count} 条异常")

        report = {
            "job_id": str(job_id),
            "total_records": total,
            "valid_count": valid_count,
            "error_count": error_count,
            "duplicate_count": dup_count,
            "field_coverage": field_coverage,
            "issues": issues,
            "summary": "，".join(summary_parts),
        }

        job.health_report = report
        job.status = "reviewing"
        await self.session.commit()
        return report

    # ── 批量确认 ──────────────────────────────────────────────────

    async def batch_confirm(self, job_id: UUID, record_ids: list[UUID], action: str) -> int:
        """批量确认/跳过记录。"""
        result = await self.session.execute(
            select(ImportRecord).where(
                ImportRecord.id.in_(record_ids),
                ImportRecord.job_id == job_id,
                ImportRecord.deleted_at.is_(None),
            )
        )
        records = list(result.scalars().all())

        for record in records:
            if action == "import":
                record.status = "accepted"
            elif action == "skip":
                record.status = "rejected"
                record.error_message = "用户跳过"

        await self.session.commit()
        return len(records)

    async def complete_job(self, job_id: UUID) -> ImportJob:
        """完成导入任务，统计最终结果。"""
        job = await self._require_job(job_id)

        # 统计各状态
        result = await self.session.execute(
            select(ImportRecord.status, func.count(ImportRecord.id))
            .where(ImportRecord.job_id == job_id, ImportRecord.deleted_at.is_(None))
            .group_by(ImportRecord.status)
        )
        status_counts = {
            str(status): int(count)
            for status, count in result.all()
        }

        job.success_count = status_counts.get("accepted", 0) + status_counts.get("imported", 0)
        job.failed_count = status_counts.get("error", 0) + status_counts.get("rejected", 0)
        job.duplicate_count = status_counts.get("duplicate", 0)
        job.status = "completed"
        await self.session.commit()
        await self.session.refresh(job)
        return job

    # ── 辅助方法 ──────────────────────────────────────────────────

    async def _require_job(self, job_id: UUID) -> ImportJob:
        job = await self.get_job(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="导入任务不存在")
        return job


class ImportRecordService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_records(self, job_id: UUID, record_status: str | None = None) -> list[ImportRecord]:
        """列出导入记录。"""
        stmt = select(ImportRecord).where(
            ImportRecord.job_id == job_id,
            ImportRecord.deleted_at.is_(None),
        )
        if record_status:
            stmt = stmt.where(ImportRecord.status == record_status)
        stmt = stmt.order_by(ImportRecord.row_number)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def apply_action(
        self,
        record_id: UUID,
        *,
        action: str,
        merge_target_id: UUID | None = None,
    ) -> ImportRecord:
        """更新记录操作（导入/跳过/合并）。"""
        record = await self.session.get(ImportRecord, record_id)
        if not record or record.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在")

        if action == "import":
            record.status = "accepted"
        elif action == "skip":
            record.status = "rejected"
            record.error_message = "用户跳过"
        elif action == "merge" and merge_target_id:
            record.status = "merged"
            record.duplicate_of = merge_target_id

        await self.session.commit()
        await self.session.refresh(record)
        return record
