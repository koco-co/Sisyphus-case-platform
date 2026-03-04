"""文本向量化模型"""

from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np


class EmbeddingModel:
    """文本向量化模型"""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        初始化嵌入模型

        Args:
            model_name: 模型名称，默认使用多语言 MiniLM
        """
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    async def embed_text(self, text: str) -> List[float]:
        """
        将文本向量化

        Args:
            text: 输入文本

        Returns:
            向量列表
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def normalize(self, embedding: List[float]) -> List[float]:
        """
        归一化向量（用于余弦相似度计算）

        Args:
            embedding: 原始向量

        Returns:
            归一化后的向量
        """
        arr = np.array(embedding)
        norm = np.linalg.norm(arr)
        if norm == 0:
            return arr.tolist()
        return (arr / norm).tolist()
