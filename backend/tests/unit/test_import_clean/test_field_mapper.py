"""字段映射器单元测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from app.engine.import_clean.field_mapper import _rule_based_mapping, map_fields


class TestRuleBasedMapping:
    def test_rule_based_mapping_maps_common_columns(self):
        mapping = _rule_based_mapping(["用例标题", "测试步骤", "预期结果", "优先级", "备注"])

        assert mapping == {
            "用例标题": "title",
            "测试步骤": "steps",
            "预期结果": "expected_result",
            "优先级": "priority",
            "备注": "description",
        }


class TestMapFields:
    async def test_map_fields_uses_ai_for_unmapped_columns_only(self):
        with patch(
            "app.engine.import_clean.field_mapper._ai_mapping",
            AsyncMock(return_value={"业务域": "module", "标签列": "tags", "用例标题": "title"}),
        ) as ai_mapping:
            mapping = await map_fields(["用例标题", "业务域", "标签列"])

        assert mapping == {
            "用例标题": "title",
            "业务域": "module",
            "标签列": "tags",
        }
        ai_mapping.assert_awaited_once_with(["用例标题", "业务域", "标签列"])

    async def test_map_fields_falls_back_to_rule_mapping_when_ai_fails(self):
        with patch(
            "app.engine.import_clean.field_mapper._ai_mapping",
            AsyncMock(side_effect=RuntimeError("llm down")),
        ):
            mapping = await map_fields(["用例标题", "未知列"])

        assert mapping == {
            "用例标题": "title",
            "未知列": None,
        }
