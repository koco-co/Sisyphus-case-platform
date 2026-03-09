"""T-UNIT-04 — 需求扫描器单元测试（纯函数，不依赖 LLM/DB）"""

from __future__ import annotations

from app.modules.diagnosis.scanner import ScanFinding, scan_requirement_text


class TestScanFindsIssues:
    def test_scan_finds_missing_boundary(self):
        """缺少边界条件关键词时应报告 boundary_missing。"""
        text = "用户可以创建数据同步任务，填写名称和描述后提交。"
        findings = scan_requirement_text(text)

        categories = [f.category for f in findings]
        assert "boundary_missing" in categories

        boundary_finding = next(f for f in findings if f.category == "boundary_missing")
        assert boundary_finding.severity == "high"
        assert "边界" in boundary_finding.title

    def test_scan_finds_missing_permission(self):
        """缺少权限相关关键词时应报告 permission_missing。"""
        text = "系统支持数据导入功能，最大文件大小为 100MB，超时后重试。"
        findings = scan_requirement_text(text)

        categories = [f.category for f in findings]
        assert "permission_missing" in categories

        perm_finding = next(f for f in findings if f.category == "permission_missing")
        assert perm_finding.severity == "medium"

    def test_scan_clean_requirement(self):
        """需求文本覆盖所有关键词时不应有发现项。"""
        text = (
            "用户可以创建数据同步任务。最大支持 100 个字段，最小 1 个字段。"
            "超时后自动重试，失败时回滚。"
            "管理员角色具有 RBAC 权限控制。"
            "系统支持 1000 QPS 并发。"
            "字段格式校验规则：手机号正则匹配。"
            "上游系统触发时启动任务。"
        )
        findings = scan_requirement_text(text)
        assert len(findings) == 0

    def test_scan_returns_scan_finding_type(self):
        text = "简单的需求描述。"
        findings = scan_requirement_text(text)
        for f in findings:
            assert isinstance(f, ScanFinding)

    def test_scan_partial_coverage(self):
        """包含部分关键词时，只报告未覆盖的维度。"""
        text = "系统最大处理 10000 条记录。失败时自动重试。管理员具有权限管理功能。"
        findings = scan_requirement_text(text)

        categories = {f.category for f in findings}
        # 边界(最大)、异常(失败/重试)、权限(权限/管理员) 已覆盖
        assert "boundary_missing" not in categories
        assert "exception_missing" not in categories
        assert "permission_missing" not in categories
        # 性能、格式、依赖 未覆盖
        assert "performance_missing" in categories
        assert "data_format_missing" in categories
        assert "dependency_missing" in categories
