"""集成测试桩 — 知识库 RAG + 用例导出

NOTE: 需要 Docker 环境运行（PostgreSQL + Redis + Qdrant + MinIO）。
      运行前请确保：docker compose -f docker/docker-compose.yml up -d
"""

from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
]


async def test_knowledge_upload_and_embed():
    """知识库上传文档 → 分块 → 向量嵌入 → Qdrant 存储。"""
    pytest.skip("需要 Docker 环境（PG/Redis/Qdrant/MinIO），请在集成测试环境中运行")


async def test_semantic_search():
    """语义搜索 → 向量检索 → 结果排序。"""
    pytest.skip("需要 Docker 环境（PG/Redis/Qdrant），请在集成测试环境中运行")


async def test_export_testcases():
    """用例导出 → 生成 Excel → MinIO 存储 → 下载链接。"""
    pytest.skip("需要 Docker 环境（PG/Redis/MinIO），请在集成测试环境中运行")
