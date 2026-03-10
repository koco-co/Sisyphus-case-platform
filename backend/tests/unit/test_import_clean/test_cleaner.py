"""Tests for the data cleaning engine."""

from app.engine.import_clean.cleaner import (
    normalize_empty_values,
    score_test_case,
    strip_html_tags,
)


class TestStripHtmlTags:
    def test_basic_tags(self):
        assert strip_html_tags("<b>bold</b>") == "bold"

    def test_br_to_newline(self):
        assert strip_html_tags("line1<br/>line2") == "line1\nline2"

    def test_p_tags(self):
        assert strip_html_tags("<p>paragraph</p>") == "paragraph"

    def test_entities(self):
        assert strip_html_tags("&amp; &lt; &gt; &nbsp;") == "& < >"

    def test_empty(self):
        assert strip_html_tags("") == ""
        assert strip_html_tags(None) == ""

    def test_no_html(self):
        assert strip_html_tags("plain text") == "plain text"

    def test_nested(self):
        result = strip_html_tags("<div><p>hello <b>world</b></p></div>")
        assert result == "hello world"


class TestNormalizeEmptyValues:
    def test_none(self):
        assert normalize_empty_values(None) == ""

    def test_empty_string(self):
        assert normalize_empty_values("") == ""

    def test_dash(self):
        assert normalize_empty_values("-") == ""

    def test_na(self):
        assert normalize_empty_values("N/A") == ""
        assert normalize_empty_values("n/a") == ""

    def test_chinese_wu(self):
        assert normalize_empty_values("无") == ""
        assert normalize_empty_values("无。") == ""

    def test_null(self):
        assert normalize_empty_values("null") == ""
        assert normalize_empty_values("NULL") == ""

    def test_real_value(self):
        assert normalize_empty_values("有效数据") == "有效数据"

    def test_whitespace(self):
        assert normalize_empty_values("  ") == ""


class TestScoreTestCase:
    def test_perfect_case(self):
        case = {
            "title": "验证用户登录功能在正确账号密码下的成功场景",
            "precondition": "系统已部署，数据库已初始化",
            "priority": "P1",
            "steps": [
                {"no": 1, "action": "打开登录页面", "expected_result": "登录页面展示正确"},
                {"no": 2, "action": "输入账号密码", "expected_result": "输入成功"},
                {"no": 3, "action": "点击登录", "expected_result": "跳转到首页"},
            ],
        }
        score = score_test_case(case)
        assert score >= 80.0

    def test_empty_case(self):
        score = score_test_case({})
        # Empty case still gets HTML-free bonus (no content = no HTML)
        assert score <= 10.0

    def test_title_only(self):
        case = {"title": "简单标题"}
        score = score_test_case(case)
        assert 10.0 <= score <= 30.0

    def test_html_in_content(self):
        case = {
            "title": "标题",
            "steps": [{"no": 1, "action": "<b>step</b>", "expected_result": "ok"}],
        }
        score = score_test_case(case)
        # Should not get the HTML-free bonus
        assert score < 80.0

    def test_missing_expected_results(self):
        case = {
            "title": "验证用户登录功能正确",
            "steps": [
                {"no": 1, "action": "打开页面", "expected_result": ""},
                {"no": 2, "action": "点击按钮", "expected_result": ""},
            ],
        }
        score = score_test_case(case)
        assert score < 70.0
