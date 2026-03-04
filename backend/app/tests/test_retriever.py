"""测试向量检索器"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.retriever import VectorRetriever
from app.models.test_case import TestCase


@pytest.mark.asyncio
async def test_vector_retrieval(db_session: AsyncSession):
    """测试向量检索"""
    retriever = VectorRetriever()

    # 先创建一些测试用例
    case1 = TestCase(
        project_id=1,
        title="用户登录测试",
        steps="输入用户名密码",
        expected_results="登录成功",
        status="approved"
    )
    case2 = TestCase(
        project_id=1,
        title="用户注册测试",
        steps="填写注册信息",
        expected_results="注册成功",
        status="approved"
    )
    db_session.add_all([case1, case2])
    await db_session.commit()

    # 为用例创建向量索引
    await retriever.index_test_case(case1, db=db_session)
    await retriever.index_test_case(case2, db=db_session)

    # 检索相似用例
    results = await retriever.search_similar_cases(
        query="测试用户登录功能",
        top_k=2,
        status="approved",
        db=db_session
    )

    assert len(results) > 0
    assert results[0].title == "用户登录测试"  # 最相似的结果


@pytest.mark.asyncio
async def test_index_batch(db_session: AsyncSession):
    """测试批量索引"""
    retriever = VectorRetriever()

    cases = [
        TestCase(
            project_id=1,
            title=f"测试用例 {i}",
            steps=f"步骤 {i}",
            expected_results=f"结果 {i}",
            status="approved"
        )
        for i in range(3)
    ]
    db_session.add_all(cases)
    await db_session.commit()

    # 批量创建索引
    await retriever.index_batch(cases, db=db_session)

    # 验证索引已创建
    for case in cases:
        assert case.embedding is not None
        assert len(case.embedding) == 384


@pytest.mark.asyncio
async def test_search_with_min_similarity(db_session: AsyncSession):
    """测试最小相似度过滤"""
    retriever = VectorRetriever()

    case = TestCase(
        project_id=1,
        title="用户登录测试",
        steps="输入用户名密码",
        expected_results="登录成功",
        status="approved"
    )
    db_session.add(case)
    await db_session.commit()
    await retriever.index_test_case(case, db=db_session)

    # 搜索相似用例，设置合理的相似度阈值
    results = await retriever.search_similar_cases(
        query="用户登录功能",
        top_k=5,
        status="approved",
        min_similarity=0.3,
        db=db_session
    )

    # 应该能找到相似的用例
    assert len(results) > 0
    # 验证相似度分数
    for result in results:
        assert hasattr(result, 'similarity')
        assert result.similarity >= 0.3
