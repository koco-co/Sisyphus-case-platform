"""行业必问清单 — 数据中台场景 32 条内置检查项"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChecklistItem:
    """清单检查项。"""

    id: str
    category: str
    question: str
    risk_if_missing: str
    priority: str  # high / medium / low


# 数据中台行业必问清单（内置 32 条，不可删除，用户可追加自定义）
BUILTIN_CHECKLIST: list[ChecklistItem] = [
    # ── 数据同步 (4) ──
    ChecklistItem("CK-01", "数据同步", "全量同步与增量同步的触发条件和切换策略是否明确?", "数据不一致", "high"),
    ChecklistItem("CK-02", "数据同步", "同步失败时的重试机制和告警通知是否定义?", "数据丢失", "high"),
    ChecklistItem("CK-03", "数据同步", "同步延迟的容忍阈值是否明确(如 T+1, 实时)?", "业务决策延迟", "medium"),
    ChecklistItem("CK-04", "数据同步", "数据源变更(加字段/改类型)时的兼容处理是否考虑?", "同步中断", "high"),
    # ── 调度任务 (4) ──
    ChecklistItem("CK-05", "调度任务", "任务调度的 CRON 表达式和时区是否明确?", "执行时间错误", "medium"),
    ChecklistItem("CK-06", "调度任务", "任务依赖链(DAG)和失败传播策略是否定义?", "级联失败", "high"),
    ChecklistItem("CK-07", "调度任务", "任务超时处理和资源回收策略是否明确?", "资源泄漏", "high"),
    ChecklistItem("CK-08", "调度任务", "任务重跑(backfill)和幂等性是否保证?", "数据重复", "high"),
    # ── 字段映射 (4) ──
    ChecklistItem("CK-09", "字段映射", "源表与目标表的字段映射关系是否完整?", "字段遗漏", "high"),
    ChecklistItem("CK-10", "字段映射", "字段类型转换规则(如 varchar→int)是否明确?", "类型转换异常", "medium"),
    ChecklistItem("CK-11", "字段映射", "NULL 值和默认值的处理策略是否定义?", "空指针异常", "medium"),
    ChecklistItem("CK-12", "字段映射", "枚举值映射表(如状态码转换)是否维护?", "映射错误", "medium"),
    # ── 大表分页 (4) ──
    ChecklistItem("CK-13", "大表分页", "分页查询是否强制使用游标/Keyset 分页?", "深度分页性能", "high"),
    ChecklistItem("CK-14", "大表分页", "单页最大条目数限制是否设置(如 max=100)?", "内存溢出", "medium"),
    ChecklistItem("CK-15", "大表分页", "总数查询是否有 COUNT 优化(估算/缓存)?", "查询超时", "medium"),
    ChecklistItem("CK-16", "大表分页", "导出全量数据时的流式处理是否实现?", "OOM", "high"),
    # ── 权限隔离 (4) ──
    ChecklistItem("CK-17", "权限隔离", "数据行级权限(RLS)隔离策略是否设计?", "数据越权", "high"),
    ChecklistItem("CK-18", "权限隔离", "跨租户数据访问的拦截机制是否到位?", "数据泄漏", "high"),
    ChecklistItem("CK-19", "权限隔离", "敏感字段(手机号/身份证)的脱敏规则是否定义?", "隐私泄漏", "high"),
    ChecklistItem("CK-20", "权限隔离", "API 接口的鉴权和频率限制是否配置?", "安全风险", "medium"),
    # ── 审计日志 (4) ──
    ChecklistItem("CK-21", "审计日志", "关键操作(删除/修改/导出)是否记录审计日志?", "无法追溯", "high"),
    ChecklistItem("CK-22", "审计日志", "审计日志的保留周期和归档策略是否明确?", "存储膨胀", "medium"),
    ChecklistItem("CK-23", "审计日志", "日志中是否脱敏了敏感信息?", "隐私合规", "medium"),
    ChecklistItem("CK-24", "审计日志", "审计日志是否支持按操作人/时间/资源检索?", "排查效率低", "low"),
    # ── 数据血缘 (4) ──
    ChecklistItem("CK-25", "数据血缘", "表级和字段级血缘是否可追溯?", "影响分析困难", "medium"),
    ChecklistItem("CK-26", "数据血缘", "血缘关系在 DDL 变更时是否自动更新?", "血缘失效", "medium"),
    ChecklistItem("CK-27", "数据血缘", "跨系统数据流转的血缘是否记录?", "端到端不可控", "low"),
    ChecklistItem("CK-28", "数据血缘", "血缘图的可视化和导出是否支持?", "可维护性差", "low"),
    # ── 质量规则 (4) ──
    ChecklistItem("CK-29", "质量规则", "数据质量规则(唯一性/完整性/一致性)是否定义?", "脏数据流入", "high"),
    ChecklistItem("CK-30", "质量规则", "质量检查失败时的阻断/告警策略是否配置?", "问题扩散", "high"),
    ChecklistItem("CK-31", "质量规则", "质量分数的计算公式和阈值是否明确?", "标准模糊", "medium"),
    ChecklistItem("CK-32", "质量规则", "质量趋势报表和异常波动告警是否实现?", "问题发现滞后", "medium"),
]


def get_builtin_checklist() -> list[ChecklistItem]:
    """返回内置必问清单（只读副本）。"""
    return list(BUILTIN_CHECKLIST)


def get_checklist_by_category(category: str) -> list[ChecklistItem]:
    """按类别筛选清单项。"""
    return [item for item in BUILTIN_CHECKLIST if item.category == category]


def get_categories() -> list[str]:
    """返回所有清单类别。"""
    seen: set[str] = set()
    result: list[str] = []
    for item in BUILTIN_CHECKLIST:
        if item.category not in seen:
            seen.add(item.category)
            result.append(item.category)
    return result
