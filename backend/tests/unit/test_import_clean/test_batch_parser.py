"""Tests for the CSV batch parser."""

from app.engine.import_clean.batch_parser import (
    _parse_expected_text,
    _parse_steps_text,
    detect_format,
    extract_module_from_path,
    normalize_csv_row,
)


class TestDetectFormat:
    def test_shuzhan(self):
        row = {"用例编号": "1", "所属产品": "P", "所属模块": "M", "用例标题": "T", "步骤": "S", "预期": "E"}
        assert detect_format(row) == "shuzhan"

    def test_xinyongzhonghe(self):
        row = {"所属模块": "M", "用例标题": "T", "步骤": "S", "预期": "E"}
        assert detect_format(row) == "xinyongzhonghe"

    def test_unknown(self):
        row = {"col1": "a", "col2": "b"}
        assert detect_format(row) == "unknown"


class TestExtractModuleFromPath:
    def test_standard_path(self):
        result = extract_module_from_path("/版本迭代测试用例/v6.4.8/【规则调度设置】任务时长限制(#10220)")
        assert result == "【规则调度设置】任务时长限制"

    def test_empty(self):
        assert extract_module_from_path("") == ""

    def test_simple_name(self):
        assert extract_module_from_path("公共组件") == "公共组件"

    def test_nested_path(self):
        result = extract_module_from_path("/a/b/c/模块名称(#123)")
        assert result == "模块名称"


class TestParseStepsText:
    def test_numbered_steps(self):
        text = "1. 打开页面\n2. 点击按钮\n3. 查看结果"
        steps = _parse_steps_text(text)
        assert len(steps) == 3
        assert steps[0]["action"] == "打开页面"
        assert steps[0]["no"] == 1

    def test_single_step(self):
        text = "打开页面并验证"
        steps = _parse_steps_text(text)
        assert len(steps) == 1
        assert steps[0]["action"] == "打开页面并验证"

    def test_empty(self):
        assert _parse_steps_text("") == []
        assert _parse_steps_text("无") == []

    def test_html_cleaned(self):
        text = "1. <b>打开</b>页面<br/>2. 点击按钮"
        steps = _parse_steps_text(text)
        assert len(steps) == 2
        assert "<b>" not in steps[0]["action"]


class TestParseExpectedText:
    def test_merge_with_steps(self):
        steps = [
            {"no": 1, "action": "打开页面", "expected_result": ""},
            {"no": 2, "action": "点击按钮", "expected_result": ""},
        ]
        result = _parse_expected_text("1. 页面显示\n2. 按钮响应", steps)
        assert result[0]["expected_result"] == "页面显示"
        assert result[1]["expected_result"] == "按钮响应"

    def test_no_expected(self):
        steps = [{"no": 1, "action": "test", "expected_result": ""}]
        result = _parse_expected_text("", steps)
        assert result[0]["expected_result"] == ""


class TestNormalizeCsvRow:
    def test_shuzhan_format(self):
        row = {
            "用例编号": "12345",
            "所属产品": "数据资产(#23)",
            "所属模块": "/测试/v6.4/【功能A】(#100)",
            "用例标题": "验证功能A正确",
            "前置条件": "系统已登录",
            "步骤": "1. 打开页面\n2. 点击按钮",
            "预期": "1. 页面正常\n2. 弹出提示",
            "优先级": "2",
            "用例类型": "功能测试",
            "关键词": "功能A,回归",
        }
        result = normalize_csv_row(row, "shuzhan")
        assert result["case_id"] == "12345"
        assert result["title"] == "验证功能A正确"
        assert result["priority"] == "P1"
        assert result["source"] == "imported"
        assert len(result["steps"]) == 2
        assert result["steps"][0]["expected_result"] == "页面正常"
        assert result["module_path"] == "【功能A】"
        assert "功能A" in result["tags"]
        assert result["original_raw"] is not None

    def test_xinyongzhonghe_format(self):
        row = {
            "所属模块": "流程中心",
            "用例标题": "验证流程列表",
            "前置条件": "无",
            "步骤": "检查列表",
            "预期": "列表正常显示",
            "优先级": "高",
            "用例类型": "",
            "关键词": "",
        }
        result = normalize_csv_row(row, "xinyongzhonghe")
        assert result["title"] == "验证流程列表"
        assert result["precondition"] == ""  # "无" normalized to ""
        assert result["priority"] == "P0"
        assert result["case_type"] == "functional"
