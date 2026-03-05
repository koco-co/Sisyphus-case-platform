"""用例导出服务"""

import csv
import io
import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExportTemplate, TestCaseNew


class ExportService:
    """用例导出服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_templates(self) -> List[ExportTemplate]:
        """获取所有模板"""
        result = await self.db.execute(
            select(ExportTemplate).order_by(ExportTemplate.is_default.desc(), ExportTemplate.name)
        )
        return list(result.scalars().all())

    async def create_template(self, data: dict) -> ExportTemplate:
        """创建模板"""
        template = ExportTemplate(**data)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def export_csv(
        self,
        test_case_ids: List[UUID],
        template: ExportTemplate,
    ) -> str:
        """导出为 CSV 格式"""
        # 获取用例
        result = await self.db.execute(
            select(TestCaseNew).where(TestCaseNew.id.in_(test_case_ids))
        )
        test_cases = result.scalars().all()

        # 应用过滤条件
        filter_config = template.filter_config or {}
        if filter_config.get("priority"):
            priorities = filter_config["priority"]
            test_cases = [tc for tc in test_cases if tc.priority in priorities]

        # 获取字段配置
        field_config = template.field_config or {}
        fields = field_config.get("fields", ["title", "priority", "preconditions", "steps"])

        # 获取格式配置
        format_config = template.format_config or {}
        delimiter = format_config.get("delimiter", ",")
        include_headers = format_config.get("include_headers", True)

        # 字段标签映射
        field_labels = {
            "title": "用例标题",
            "priority": "优先级",
            "preconditions": "前置条件",
            "steps": "测试步骤",
            "tags": "标签",
            "requirement_id": "关联需求ID",
            "created_at": "创建时间",
            "updated_at": "更新时间",
        }

        # 生成 CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)

        # 写入表头
        if include_headers:
            headers = [field_labels.get(f, f) for f in fields]
            writer.writerow(headers)

        # 写入数据
        for tc in test_cases:
            row = []
            for field in fields:
                value = self._get_field_value(tc, field)
                row.append(value)
            writer.writerow(row)

        return output.getvalue()

    async def export_json(
        self,
        test_case_ids: List[UUID],
        template: ExportTemplate,
    ) -> dict:
        """导出为 JSON 格式"""
        # 获取用例
        result = await self.db.execute(
            select(TestCaseNew).where(TestCaseNew.id.in_(test_case_ids))
        )
        test_cases = result.scalars().all()

        # 应用过滤条件
        filter_config = template.filter_config or {}
        if filter_config.get("priority"):
            priorities = filter_config["priority"]
            test_cases = [tc for tc in test_cases if tc.priority in priorities]

        # 获取字段配置
        field_config = template.field_config or {}
        fields = field_config.get("fields", ["title", "priority", "preconditions", "steps"])

        # 构建导出数据
        exported_cases = []
        for tc in test_cases:
            case_data = {}
            for field in fields:
                case_data[field] = self._get_field_value(tc, field)
            case_data["id"] = str(tc.id)
            exported_cases.append(case_data)

        return {
            "export_info": {
                "exported_at": datetime.utcnow().isoformat(),
                "total_count": len(exported_cases),
                "template": template.name if template else "默认模板",
            },
            "test_cases": exported_cases,
        }

    def _get_field_value(self, tc: TestCaseNew, field: str) -> str:
        """获取字段值"""
        if field == "steps":
            return json.dumps(tc.steps, ensure_ascii=False) if tc.steps else ""
        elif field == "tags":
            return ", ".join(tc.tags) if tc.tags else ""
        elif field in ("created_at", "updated_at"):
            value = getattr(tc, field, None)
            return value.isoformat() if value else ""
        elif field == "requirement_id":
            return str(tc.requirement_id) if tc.requirement_id else ""
        else:
            return str(getattr(tc, field, "") or "")
