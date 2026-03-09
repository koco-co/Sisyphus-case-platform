"""T-UNIT-04 — 行业必问清单单元测试（纯函数，不依赖 LLM/DB）"""

from __future__ import annotations

from app.modules.diagnosis.checklist import (
    BUILTIN_CHECKLIST,
    ChecklistItem,
    get_builtin_checklist,
    get_categories,
    get_checklist_by_category,
)


class TestChecklistItemsLoaded:
    def test_builtin_checklist_has_items(self):
        """内置清单应包含 32 条检查项。"""
        checklist = get_builtin_checklist()
        assert len(checklist) == 32

    def test_checklist_items_are_dataclass(self):
        checklist = get_builtin_checklist()
        for item in checklist:
            assert isinstance(item, ChecklistItem)

    def test_checklist_ids_unique(self):
        """所有检查项 ID 必须唯一。"""
        checklist = get_builtin_checklist()
        ids = [item.id for item in checklist]
        assert len(ids) == len(set(ids))

    def test_checklist_categories_valid(self):
        """所有检查项必须属于已知类别。"""
        expected_categories = {"数据同步", "调度任务", "字段映射", "大表分页", "权限隔离", "审计日志", "数据血缘", "质量规则"}
        checklist = get_builtin_checklist()
        actual_categories = {item.category for item in checklist}
        assert actual_categories == expected_categories

    def test_get_categories_returns_8(self):
        categories = get_categories()
        assert len(categories) == 8

    def test_get_checklist_by_category(self):
        items = get_checklist_by_category("数据同步")
        assert len(items) == 4
        assert all(item.category == "数据同步" for item in items)

    def test_checklist_priority_valid(self):
        """优先级只允许 high / medium / low。"""
        checklist = get_builtin_checklist()
        valid_priorities = {"high", "medium", "low"}
        for item in checklist:
            assert item.priority in valid_priorities, f"{item.id} has invalid priority: {item.priority}"


class TestUnmatchedItems:
    def test_unmatched_returns_nonexistent_category(self):
        """查询不存在的类别应返回空列表。"""
        items = get_checklist_by_category("不存在的类别")
        assert items == []

    def test_builtin_checklist_is_copy(self):
        """get_builtin_checklist 应返回副本，不影响原始数据。"""
        copy1 = get_builtin_checklist()
        copy2 = get_builtin_checklist()
        # 修改 copy1 不影响 copy2
        copy1.pop()
        assert len(copy2) == 32
        assert len(BUILTIN_CHECKLIST) == 32
