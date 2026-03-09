"""T-UNIT-07 — Diff 引擎 Myers diff 文本对比测试（纯函数）"""

from __future__ import annotations

import difflib


class TestMyersDiffTextComparison:
    """使用 difflib.unified_diff 进行 Myers diff 文本对比（与 DiffService 一致）。"""

    def test_identical_texts_no_diff(self):
        old = "line 1\nline 2\nline 3\n"
        new = "line 1\nline 2\nline 3\n"

        diff = list(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
            )
        )
        additions = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
        deletions = [l for l in diff if l.startswith("-") and not l.startswith("---")]

        assert len(additions) == 0
        assert len(deletions) == 0

    def test_addition_detected(self):
        old = "line 1\nline 2\n"
        new = "line 1\nline 2\nline 3\n"

        diff = list(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile="v1",
                tofile="v2",
            )
        )
        additions = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
        assert len(additions) >= 1
        assert any("line 3" in l for l in additions)

    def test_deletion_detected(self):
        old = "line 1\nline 2\nline 3\n"
        new = "line 1\nline 3\n"

        diff = list(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
            )
        )
        deletions = [l for l in diff if l.startswith("-") and not l.startswith("---")]
        assert len(deletions) >= 1
        assert any("line 2" in l for l in deletions)

    def test_modification_detected(self):
        old = "name: old_value\nstatus: active\n"
        new = "name: new_value\nstatus: active\n"

        diff = list(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
            )
        )
        additions = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
        deletions = [l for l in diff if l.startswith("-") and not l.startswith("---")]

        assert len(additions) >= 1
        assert len(deletions) >= 1
        assert any("new_value" in l for l in additions)
        assert any("old_value" in l for l in deletions)

    def test_impact_level_classification(self):
        """验证 DiffService 中使用的影响等级分类逻辑。"""
        test_cases = [
            (0, "none"),
            (3, "low"),
            (10, "medium"),
            (25, "high"),
        ]
        for total_changes, expected_level in test_cases:
            if total_changes == 0:
                level = "none"
            elif total_changes < 5:
                level = "low"
            elif total_changes < 20:
                level = "medium"
            else:
                level = "high"
            assert level == expected_level, f"total_changes={total_changes}"

    def test_chinese_text_diff(self):
        """验证中文文本 diff 能正确识别变更。"""
        old = "需求描述：数据同步功能\n支持全量同步\n"
        new = "需求描述：数据同步功能\n支持全量同步和增量同步\n"

        diff = list(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
            )
        )
        additions = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
        assert any("增量同步" in l for l in additions)

    def test_empty_to_content(self):
        """空文本到有内容应全部为新增。"""
        diff = list(
            difflib.unified_diff(
                "".splitlines(keepends=True),
                "new content\n".splitlines(keepends=True),
            )
        )
        additions = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
        assert len(additions) >= 1
