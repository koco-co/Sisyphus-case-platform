"""集成测试桩 — 诊断 + 场景地图 + 用例生成 AI 流程

NOTE: 需要 Docker 环境运行（PostgreSQL + Redis）+ LLM API Key。
      运行前请确保：docker compose -f docker/docker-compose.yml up -d
"""

from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
]


async def test_diagnosis_scan_flow():
    """T-INT-04: 需求诊断扫描 → 生成风险清单 → 持久化验证。"""
    pytest.skip("需要 Docker + LLM API 环境，请在集成测试环境中运行")


async def test_scene_map_generation():
    """场景地图生成 → 测试点提取 → 节点状态验证。"""
    pytest.skip("需要 Docker + LLM API 环境，请在集成测试环境中运行")


async def test_case_generation_sse():
    """T-INT-05: 用例生成 SSE 流 → 流式接收 → 解析 → TestCase 持久化。"""
    pytest.skip("需要 Docker + LLM API 环境，请在集成测试环境中运行")


async def test_case_generation_with_fallback():
    """主模型失败 → 自动降级 → 仍然生成用例。"""
    pytest.skip("需要 Docker + LLM API 环境，请在集成测试环境中运行")
