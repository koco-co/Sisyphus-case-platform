"""Seed initial data: default admin user, demo product/iteration/requirement."""

import asyncio
import hashlib
import json
import os
import sys
import uuid
from datetime import date, datetime

# Ensure the backend directory is on sys.path so `app` package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_factory


def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# 详细的测试用需求文档 —— 用于验证 AI 链路
_REQUIREMENT_CONTENT = """# 数据源接入管理模块

## 1. 功能概述

本模块负责企业数据中台的多种异构数据源统一接入与生命周期管理。
支持关系型数据库（MySQL 5.7+、PostgreSQL 12+、Oracle 19c+）、
NoSQL 数据库（MongoDB 4.4+、Redis 6+）、消息队列（Kafka 2.8+）、
以及 RESTful API / GraphQL 外部接口的注册、连接测试、元数据采集与健康监控。

## 2. 用户角色

| 角色 | 权限 |
|------|------|
| 数据管理员 | 增删改查所有数据源，执行连接测试，配置采集策略 |
| 数据开发者 | 查看数据源列表，浏览元数据，申请数据源访问权 |
| 系统管理员 | 管理数据源类型字典，配置全局连接池参数 |
| 审计员 | 查看数据源操作日志，导出审计报告 |

## 3. 功能需求

### 3.1 数据源注册

- **FR-001**: 支持通过向导式表单创建数据源，必填项：名称（2-50字符）、类型、连接地址、端口、认证方式
- **FR-002**: 名称唯一性校验，不允许特殊字符（仅中英文、数字、下划线、中划线）
- **FR-003**: 密码字段使用 AES-256 加密存储，界面回显时脱敏显示（仅显示前2后2位）
- **FR-004**: 支持批量导入数据源配置（Excel/CSV格式），单次最多100条
- **FR-005**: 创建时自动触发连接测试，测试失败仍可保存（状态标记为"未验证"）

### 3.2 连接测试

- **FR-006**: 点击"测试连接"按钮后，30秒超时，期间显示进度动画
- **FR-007**: 测试结果包含：连接状态（成功/失败/超时）、延迟（ms）、数据库版本、字符集
- **FR-008**: 连接失败时返回可读的错误信息（如"认证失败"、"网络不可达"、"端口拒绝"）
- **FR-009**: 支持使用 SSH 隧道连接（需配置跳板机IP/端口/密钥）

### 3.3 元数据采集

- **FR-010**: 手动触发或定时（Cron 表达式）自动采集数据库的库/表/字段/索引/分区信息
- **FR-011**: 增量采集：仅同步变更的表结构，通过对比 information_schema 实现
- **FR-012**: 采集结果存储到元数据仓库，支持版本对比（字段新增/删除/类型变更）
- **FR-013**: 单次采集超时上限 10 分钟，可中断

### 3.4 健康监控

- **FR-014**: 每5分钟自动心跳检测所有已启用的数据源
- **FR-015**: 连续3次心跳失败触发告警通知（邮件+站内信）
- **FR-016**: 仪表盘展示：在线数量、离线数量、平均延迟、告警趋势图

### 3.5 数据源停用与删除

- **FR-017**: 停用数据源前检查是否有正在运行的采集任务或依赖的下游 ETL 任务
- **FR-018**: 删除采用软删除，保留30天可恢复
- **FR-019**: 有下游依赖时禁止删除，需先解除依赖关系

## 4. 非功能需求

- **NFR-001**: 连接测试接口响应 < 5秒（不含网络延迟）
- **NFR-002**: 支持同时管理不少于500个数据源
- **NFR-003**: 密码等敏感信息传输使用 TLS 1.2+
- **NFR-004**: 操作日志保留180天
- **NFR-005**: 元数据采集任务支持并发（最大并行度可配置，默认5）

## 5. 业务规则

- BR-001: 同一类型的数据源，连接地址+端口+库名组合必须唯一
- BR-002: SSH 隧道连接仅管理员角色可配置
- BR-003: 批量导入时，重复项跳过并记录到导入报告
- BR-004: 定时采集的 Cron 表达式最小间隔不得低于 5 分钟
"""


def _build_content_ast(raw_text: str) -> dict:
    """将 Markdown 原文解析为 sections 结构的 content_ast。"""
    sections = []
    current_heading = ""
    current_body: list[str] = []

    for line in raw_text.strip().splitlines():
        if line.startswith("#"):
            if current_heading or current_body:
                sections.append(
                    {
                        "heading": current_heading,
                        "body": "\n".join(current_body).strip(),
                    }
                )
            current_heading = line.lstrip("#").strip()
            current_body = []
        else:
            current_body.append(line)

    if current_heading or current_body:
        sections.append(
            {
                "heading": current_heading,
                "body": "\n".join(current_body).strip(),
            }
        )

    return {"raw_text": raw_text.strip(), "sections": sections}


async def seed() -> None:
    print("Seeding database...")
    factory = get_session_factory()
    async with factory() as session:
        session: AsyncSession

        # Check if admin already exists
        result = await session.execute(text("SELECT id FROM users WHERE username = 'admin' LIMIT 1"))
        if result.scalar():
            print("Admin user already exists — skipping seed.")
            return

        now = datetime.utcnow()
        admin_id = uuid.uuid4()
        product_id = uuid.uuid4()
        iteration_id = uuid.uuid4()
        req_id = uuid.uuid4()

        # Admin user
        await session.execute(
            text(
                "INSERT INTO users (id, email, username, hashed_password, "
                "full_name, is_active, role, created_at, updated_at) "
                "VALUES (:id, :email, :username, :pw, :name, true, 'admin', :now, :now)"
            ),
            {
                "id": admin_id,
                "email": "admin@sisyphus.dev",
                "username": "admin",
                "pw": _hash_pw("admin123"),
                "name": "系统管理员",
                "now": now,
            },
        )

        # Demo product
        await session.execute(
            text(
                "INSERT INTO products (id, name, slug, description, created_at, updated_at) "
                "VALUES (:id, :name, :slug, :desc, :now, :now)"
            ),
            {
                "id": product_id,
                "name": "数据中台",
                "slug": "data-platform",
                "desc": "企业级数据中台核心系统",
                "now": now,
            },
        )

        # Demo iteration
        await session.execute(
            text(
                "INSERT INTO iterations (id, product_id, name, start_date, end_date, status, created_at, updated_at) "
                "VALUES (:id, :pid, :name, :start, :end, 'active', :now, :now)"
            ),
            {
                "id": iteration_id,
                "pid": product_id,
                "name": "Sprint 2025-Q1",
                "start": date(2025, 1, 1),
                "end": date(2025, 3, 31),
                "now": now,
            },
        )

        # Demo requirement — 详细的数据源接入管理需求
        content_ast = _build_content_ast(_REQUIREMENT_CONTENT)
        await session.execute(
            text(
                "INSERT INTO requirements (id, iteration_id, req_id, title, "
                "content_ast, status, version, created_at, updated_at) "
                "VALUES (:id, :iid, :rid, :title, :ast, 'draft', 1, :now, :now)"
            ),
            {
                "id": req_id,
                "iid": iteration_id,
                "rid": "REQ-001",
                "title": "数据源接入管理模块",
                "ast": json.dumps(content_ast, ensure_ascii=False),
                "now": now,
            },
        )

        await session.commit()
        print(f"Seed complete — admin (admin/admin123), product={product_id}, requirement={req_id}")


if __name__ == "__main__":
    asyncio.run(seed())
