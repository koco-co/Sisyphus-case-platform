import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.project import Project
from app.models.test_case import TestCase
from app.models.user_config import UserConfig
from app.models import Base


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
async def test_create_project(db_session):
    """测试创建项目"""
    project = Project(name="登录模块", description="用户登录功能")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    assert project.id is not None
    assert project.name == "登录模块"
    assert project.description == "用户登录功能"


@pytest.mark.asyncio
async def test_create_test_case(db_session):
    """测试创建测试用例"""
    # 先创建项目
    project = Project(name="登录模块", description="用户登录功能")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # 创建测试用例
    test_case = TestCase(
        project_id=project.id,
        module="登录",
        title="正常登录测试",
        prerequisites="用户已注册",
        steps="1. 打开登录页面\n2. 输入用户名和密码\n3. 点击登录按钮",
        expected_results="成功登录，跳转到首页",
        priority="1",
        case_type="功能测试",
        stage="功能测试阶段"
    )
    db_session.add(test_case)
    await db_session.commit()
    await db_session.refresh(test_case)

    assert test_case.id is not None
    assert test_case.project_id == project.id
    assert test_case.title == "正常登录测试"
    assert test_case.priority == "1"


@pytest.mark.asyncio
async def test_create_user_config(db_session):
    """测试创建用户配置"""
    user_config = UserConfig(
        provider="openai",
        api_key_encrypted="encrypted_key_here",
        generator_model="gpt-4",
        reviewer_model="gpt-4",
        is_active=True
    )
    db_session.add(user_config)
    await db_session.commit()
    await db_session.refresh(user_config)

    assert user_config.id is not None
    assert user_config.provider == "openai"
    assert user_config.generator_model == "gpt-4"
    assert user_config.is_active is True
