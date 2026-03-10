"""重复检测器单元测试。"""

from __future__ import annotations

from app.engine.import_clean.deduplicator import detect_duplicates, detect_duplicates_against_existing


class TestDetectDuplicates:
    def test_detect_duplicates_returns_similar_pairs(self):
        matches = detect_duplicates(
            [
                {"title": "Login success"},
                {"title": " login success "},
                {"title": "Create order"},
            ]
        )

        assert len(matches) == 1
        assert matches[0].source_index == 0
        assert matches[0].target_index == 1
        assert matches[0].score >= 0.99

    def test_detect_duplicates_against_existing_returns_best_match(self):
        matches = detect_duplicates_against_existing(
            [
                {"title": "Create order"},
                {"title": "Cancel order"},
                {"title": ""},
            ],
            ["create order", "refund order"],
        )

        assert matches == {
            0: ("create order", 1.0),
        }
