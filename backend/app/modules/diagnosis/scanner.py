"""广度扫描器 — 识别需求文档中 6 类遗漏"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScanFinding:
    """扫描发现项。"""

    category: str  # 遗漏类别
    severity: str  # high / medium / low
    title: str
    description: str
    suggestion: str


# 6 类遗漏检查
SCAN_CATEGORIES = [
    "boundary_missing",  # 边界条件缺失
    "exception_missing",  # 异常处理缺失
    "permission_missing",  # 权限控制缺失
    "performance_missing",  # 性能约束缺失
    "data_format_missing",  # 数据格式缺失
    "dependency_missing",  # 依赖关系缺失
]


def scan_requirement_text(text: str) -> list[ScanFinding]:
    """对需求文本进行广度扫描，识别潜在遗漏。

    注意：此函数做基于关键词的快速扫描，
    深度分析由 AI 引擎的诊断 Prompt 完成。
    """
    findings: list[ScanFinding] = []

    # 边界条件检查
    boundary_keywords = ["最大", "最小", "上限", "下限", "范围", "区间", "阈值"]
    if not any(kw in text for kw in boundary_keywords):
        findings.append(
            ScanFinding(
                category="boundary_missing",
                severity="high",
                title="未定义边界条件",
                description="需求文档中未提及数值边界、范围限制等约束条件",
                suggestion="建议补充字段长度限制、数值范围、列表最大条目数等边界规则",
            )
        )

    # 异常处理检查
    exception_keywords = ["异常", "错误", "失败", "超时", "重试", "回滚", "降级"]
    if not any(kw in text for kw in exception_keywords):
        findings.append(
            ScanFinding(
                category="exception_missing",
                severity="high",
                title="未定义异常处理",
                description="需求文档中未描述异常场景的处理策略",
                suggestion="建议补充网络超时、数据校验失败、并发冲突等异常场景的处理方式",
            )
        )

    # 权限控制检查
    permission_keywords = ["权限", "角色", "鉴权", "授权", "RBAC", "访问控制"]
    if not any(kw in text for kw in permission_keywords):
        findings.append(
            ScanFinding(
                category="permission_missing",
                severity="medium",
                title="未定义权限控制",
                description="需求文档中未提及用户角色与权限规则",
                suggestion="建议明确不同角色（管理员/测试员/开发者）的功能权限",
            )
        )

    # 性能约束检查
    perf_keywords = ["性能", "响应时间", "并发", "吞吐", "延迟", "QPS", "TPS"]
    if not any(kw in text for kw in perf_keywords):
        findings.append(
            ScanFinding(
                category="performance_missing",
                severity="medium",
                title="未定义性能约束",
                description="需求文档中未给出性能指标要求",
                suggestion="建议补充接口响应时间、并发用户数、数据量级等性能指标",
            )
        )

    # 数据格式检查
    format_keywords = ["格式", "类型", "编码", "正则", "校验规则", "字段长度"]
    if not any(kw in text for kw in format_keywords):
        findings.append(
            ScanFinding(
                category="data_format_missing",
                severity="medium",
                title="未定义数据格式",
                description="需求文档中未明确数据格式与校验规则",
                suggestion="建议补充输入字段的类型、长度、格式（如日期格式、手机号格式）",
            )
        )

    # 依赖关系检查
    dep_keywords = ["依赖", "前置条件", "关联", "触发", "上游", "下游"]
    if not any(kw in text for kw in dep_keywords):
        findings.append(
            ScanFinding(
                category="dependency_missing",
                severity="low",
                title="未定义依赖关系",
                description="需求文档中未说明与其他模块/系统的依赖关系",
                suggestion="建议补充上下游系统依赖、接口调用关系、数据流向",
            )
        )

    return findings
