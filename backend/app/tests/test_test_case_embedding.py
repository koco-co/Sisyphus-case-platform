"""测试测试用例模型的向量存储支持"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.test_case import TestCase
from app.models.project import Project
from app.models import Base
from app.rag.embeddings import EmbeddingModel


# 使用 SQLite 测试数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    """创建测试数据库会话"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_save_test_case_with_embedding(db_session):
    """测试保存带向量的测试用例"""
    model = EmbeddingModel()
    embedding = await model.embed_text("测试用例内容")

    # 先创建项目
    project = Project(name="测试项目", description="测试描述")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    case = TestCase(
        project_id=project.id,
        title="测试用例",
        steps="测试步骤",
        expected_results="预期结果",
        embedding=embedding
    )
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)

    assert case.embedding is not None
    assert len(case.embedding) == 384
    assert all(isinstance(x, float) for x in case.embedding)


@pytest.mark.asyncio
async def test_save_test_case_without_embedding(db_session):
    """测试保存不带向量的测试用例（向后兼容）"""
    # 先创建项目
    project = Project(name="测试项目", description="测试描述")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    case = TestCase(
        project_id=project.id,
        title="测试用例",
        steps="测试步骤",
        expected_results="预期结果"
    )
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)

    assert case.embedding is None


@pytest.mark.asyncio
async def test_update_test_case_embedding(db_session):
    """测试更新测试用例的向量"""
    model = EmbeddingModel()

    # 先创建项目
    project = Project(name="测试项目", description="测试描述")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # 先创建不带向量的测试用例
    case = TestCase(
        project_id=project.id,
        title="测试用例",
        steps="测试步骤",
        expected_results="预期结果"
    )
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)

    assert case.embedding is None

    # 生成并保存向量
    embedding = await model.embed_text("更新后的测试用例内容")
    case.embedding = embedding
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)

    assert case.embedding is not None
    assert len(case.embedding) == 384
