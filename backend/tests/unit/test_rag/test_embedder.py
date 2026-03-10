"""T-UNIT-10 — RAG 嵌入器客户端配置测试。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import ANY, MagicMock, patch

from app.engine.rag.embedder import _embed_zhipu


async def test_embed_zhipu_disables_env_proxy():
    """智谱嵌入客户端应显式禁用系统代理。"""
    http_client = MagicMock()
    zhipu_client = MagicMock()
    zhipu_client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3])]
    )

    with (
        patch("app.engine.rag.embedder.httpx.Client", return_value=http_client) as httpx_client,
        patch("zhipuai.ZhipuAI", return_value=zhipu_client) as zhipu_ai,
    ):
        result = await _embed_zhipu(["hello"])

    httpx_client.assert_called_once_with(proxy=None, trust_env=False)
    zhipu_ai.assert_called_once_with(
        api_key=ANY,
        http_client=http_client,
    )
    assert result == [[0.1, 0.2, 0.3]]
