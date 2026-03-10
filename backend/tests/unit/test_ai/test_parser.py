"""AI 输出解析器回归测试。"""

from __future__ import annotations

from app.ai.parser import parse_test_cases


class TestParseTestCases:
    def test_parse_test_cases_from_keyed_json_object(self):
        """带用例编号键名的 JSON 对象应被解析为结构化用例。"""
        text = """```json
{
  "用例: TC-迭代16-001": {
    "title": "[P0]-数据目录发布流程-数据目录发布流程审批通过",
    "priority": "P0",
    "case_type": "normal",
    "steps": [
      {
        "step": "1. 登录系统，进入数据目录发布流程页面",
        "expect": "系统显示数据目录发布流程页面"
      },
      {
        "step": "2. 选择L2目录，填写其他必填项",
        "expect": "系统根据选择的L2目录内容回显其他所有必填项"
      }
    ]
  }
}
```"""

        cases = parse_test_cases(text)

        assert len(cases) == 1
        assert cases[0]["title"] == "[P0]-数据目录发布流程-数据目录发布流程审批通过"
        assert cases[0]["priority"] == "P0"
        assert cases[0]["case_type"] == "normal"
        assert cases[0]["steps"] == [
            {
                "step_num": 1,
                "action": "1. 登录系统，进入数据目录发布流程页面",
                "expected_result": "系统显示数据目录发布流程页面",
            },
            {
                "step_num": 2,
                "action": "2. 选择L2目录，填写其他必填项",
                "expected_result": "系统根据选择的L2目录内容回显其他所有必填项",
            },
        ]
