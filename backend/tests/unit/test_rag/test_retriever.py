"""T-UNIT-09 — RAG 检索器客户端配置测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.engine.rag import retriever


class TestQdrantClientConfig:
    def teardown_method(self):
        retriever._client = None

    def test_get_client_disables_env_proxy(self):
        """Qdrant 客户端应禁用 trust_env，避免被系统代理污染。"""
        client = MagicMock()

        with patch("app.engine.rag.retriever.QdrantClient", return_value=client) as qdrant_client:
            retriever._client = None
            result = retriever._get_client()

        qdrant_client.assert_called_once_with(
            url=retriever.settings.qdrant_url,
            timeout=30,
            trust_env=False,
        )
        assert result is client

    def test_get_client_reuses_cached_instance(self):
        """重复获取客户端时应复用缓存实例。"""
        client = MagicMock()

        with patch("app.engine.rag.retriever.QdrantClient", return_value=client) as qdrant_client:
            retriever._client = None
            first = retriever._get_client()
            second = retriever._get_client()

        qdrant_client.assert_called_once()
        assert first is second
