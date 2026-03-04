"""测试文本向量化模型"""

import pytest
from app.rag.embeddings import EmbeddingModel


@pytest.mark.asyncio
async def test_embedding_model():
    """测试向量化模型"""
    model = EmbeddingModel()
    text = "这是一个测试句子"
    embedding = await model.embed_text(text)

    assert len(embedding) == 384  # MiniLM 模型输出维度
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_embedding_batch():
    """测试批量向量化"""
    model = EmbeddingModel()
    texts = ["第一个句子", "第二个句子", "第三个句子"]
    embeddings = await model.embed_batch(texts)

    assert len(embeddings) == 3
    assert all(len(emb) == 384 for emb in embeddings)
    assert all(all(isinstance(x, float) for x in emb) for emb in embeddings)


@pytest.mark.asyncio
async def test_normalize():
    """测试向量归一化"""
    model = EmbeddingModel()
    text = "测试归一化"
    embedding = await model.embed_text(text)
    normalized = model.normalize(embedding)

    # 验证归一化后的向量范数为 1
    import numpy as np
    norm = np.linalg.norm(np.array(normalized))
    assert abs(norm - 1.0) < 1e-6  # 允许浮点误差
