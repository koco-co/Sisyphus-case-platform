"""T-UNIT-05 — 场景地图测试点校验器单元测试（纯函数）"""

from __future__ import annotations

from app.engine.scene_map.validator import get_validation_summary, validate_test_points


class TestNameTooLongWarning:
    def test_name_too_long_warning(self):
        """标题超过 50 字应触发 '名称过长' 警告。"""
        points = [
            {
                "title": "A" * 51,
                "description": "测试描述，预期应返回正确结果",
                "group_name": "核心功能",
            }
        ]
        results = validate_test_points(points)
        warnings = results[0]["warnings"]

        rule_names = [w["rule"] for w in warnings]
        assert "名称过长" in rule_names

    def test_name_exactly_50_no_warning(self):
        """标题恰好 50 字不应触发 '名称过长' 警告。"""
        points = [
            {
                "title": "A" * 50,
                "description": "预期应验证数据完整性返回结果",
                "group_name": "核心功能",
            }
        ]
        results = validate_test_points(points)
        rule_names = [w["rule"] for w in results[0]["warnings"]]
        assert "名称过长" not in rule_names


class TestMissingExpectedResult:
    def test_missing_expected_result(self):
        """描述中缺少预期结果关键词应触发警告。"""
        points = [
            {
                "title": "创建同步任务",
                "description": "填写任务名称和配置信息",
                "group_name": "数据同步",
            }
        ]
        results = validate_test_points(points)
        rule_names = [w["rule"] for w in results[0]["warnings"]]
        assert "缺少预期结果" in rule_names

    def test_has_expected_result_keyword(self):
        """描述中包含预期结果关键词不应触发。"""
        points = [
            {
                "title": "创建任务",
                "description": "填写名称后，系统应返回成功状态",
                "group_name": "核心",
            }
        ]
        results = validate_test_points(points)
        rule_names = [w["rule"] for w in results[0]["warnings"]]
        assert "缺少预期结果" not in rule_names


class TestMultipleActionsWarning:
    def test_multiple_actions_warning(self):
        """标题包含多动作连接词应触发 '含多个动作' 警告。"""
        points = [
            {
                "title": "创建任务并且启动调度",
                "description": "预期应生成调度计划",
                "group_name": "调度",
            }
        ]
        results = validate_test_points(points)
        rule_names = [w["rule"] for w in results[0]["warnings"]]
        assert "含多个动作" in rule_names

    def test_multiple_actions_with_tongshi(self):
        """标题包含「同时」也应触发。"""
        points = [
            {
                "title": "同时修改多个字段配置",
                "description": "验证字段映射是否正确",
                "group_name": "字段",
            }
        ]
        results = validate_test_points(points)
        rule_names = [w["rule"] for w in results[0]["warnings"]]
        assert "含多个动作" in rule_names


class TestValidPointNoWarnings:
    def test_valid_point_no_warnings(self):
        """符合规范的测试点不应产生任何 warning。"""
        points = [
            {
                "title": "验证空值字段默认处理",
                "description": "当输入字段为空时，系统应返回默认值并显示提示信息",
                "group_name": "字段映射",
                "estimated_cases": 3,
            }
        ]
        results = validate_test_points(points)
        warning_rules = [w for w in results[0]["warnings"] if w["level"] == "warning"]
        assert warning_rules == []


class TestValidationSummary:
    def test_summary_all_pass(self):
        points = [
            {
                "title": "验证同步结果",
                "description": "执行同步后应返回成功状态",
                "group_name": "同步",
                "estimated_cases": 3,
            }
        ]
        validated = validate_test_points(points)
        summary = get_validation_summary(validated)

        assert summary["total_points"] == 1
        assert summary["pass_rate"] > 0

    def test_summary_with_warnings(self):
        points = [
            {"title": "A" * 60, "description": "短", "group_name": ""},
            {
                "title": "正常测试点",
                "description": "预期应验证数据正确性",
                "group_name": "核心",
                "estimated_cases": 2,
            },
        ]
        validated = validate_test_points(points)
        summary = get_validation_summary(validated)

        assert summary["total_points"] == 2
        assert summary["points_with_warnings"] >= 1
        assert "名称过长" in summary["rule_hit_counts"]

    def test_summary_empty_input(self):
        validated = validate_test_points([])
        summary = get_validation_summary(validated)
        assert summary["total_points"] == 0
        assert summary["pass_rate"] == 0
