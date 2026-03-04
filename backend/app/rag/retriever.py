"""向量检索器"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database import async_session
from app.models.test_case import TestCase
from app.rag.embeddings import EmbeddingModel
import numpy as np


class VectorRetriever:
    """向量检索器"""

    def __init__(self):
        self.embedding_model = EmbeddingModel()

    async def search_similar_cases(
        self,
        query: str,
        top_k: int = 5,
        status: str = "approved",
        project_id: Optional[int] = None,
        min_similarity: float = 0.5,
        db: Optional[AsyncSession] = None
    ) -> List[TestCase]:
        """
        检索相似的测试用例

        Args:
            query: 查询文本
            top_k: 返回前 K 个结果
            status: 用例状态过滤
            project_id: 项目 ID 过滤
            min_similarity: 最小相似度阈值
            db: 数据库会话（可选）

        Returns:
            相似测试用例列表
        """
        # 生成查询向量
        query_vector = await self.embedding_model.embed_text(query)

        # 构建基本查询条件
        conditions = [TestCase.status == status]
        if project_id:
            conditions.append(TestCase.project_id == project_id)

        # 使用 SQLAlchemy 查询（兼容 SQLite 和 PostgreSQL）
        stmt = select(TestCase).where(*conditions)

        # 执行查询
        if db is None:
            async with async_session() as session:
                result = await session.execute(stmt)
                all_cases = result.scalars().all()
        else:
            result = await db.execute(stmt)
            all_cases = result.scalars().all()

        # 计算余弦相似度（Python 实现，兼容 SQLite）
        cases_with_similarity = []
        for case in all_cases:
            if case.embedding:
                similarity = self._cosine_similarity(query_vector, case.embedding)
                if similarity >= min_similarity:
                    case.similarity = similarity
                    cases_with_similarity.append(case)

        # 按相似度排序并返回前 K 个
        cases_with_similarity.sort(key=lambda c: c.similarity, reverse=True)
        return cases_with_similarity[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            相似度分数 (0-1)
        """
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)

        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    async def index_test_case(
        self,
        case: TestCase,
        db: Optional[AsyncSession] = None
    ):
        """
        为测试用例创建向量索引

        Args:
            case: 测试用例对象
            db: 数据库会话（可选）
        """
        # 组合文本字段
        text = f"{case.title} {case.steps} {case.expected_results}"

        # 生成向量
        embedding = await self.embedding_model.embed_text(text)

        # 保存到数据库
        case.embedding = embedding

        if db:
            db.add(case)
            await db.commit()
        else:
            async with async_session() as session:
                session.add(case)
                await session.commit()

    async def index_batch(
        self,
        cases: List[TestCase],
        db: Optional[AsyncSession] = None
    ):
        """
        批量创建向量索引

        Args:
            cases: 测试用例列表
            db: 数据库会话（可选）
        """
        texts = [
            f"{case.title} {case.steps} {case.expected_results}"
            for case in cases
        ]

        embeddings = await self.embedding_model.embed_batch(texts)

        for case, embedding in zip(cases, embeddings):
            case.embedding = embedding

        if db:
            for case in cases:
                db.add(case)
            await db.commit()
        else:
            async with async_session() as session:
                for case in cases:
                    session.add(case)
                await session.commit()
