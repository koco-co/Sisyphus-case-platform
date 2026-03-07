import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import app.models.test_case as test_case_model
import app.models.test_case_package_version as test_case_package_version_model
import app.models.test_point_version as test_point_version_model
from app.models.project import Project
from app.models.requirement_task import RequirementTask
from app.models.source_document import SourceDocument
from app.models.structured_requirement_version import StructuredRequirementVersion
from app.models.review_record import ReviewRecord
from app.models.job import Job
from app.models.user_config import UserConfig
from app.models import Base


# 使用 SQLite 测试数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

TEST_TABLES = [
    Project.__table__,
    test_case_model.TestCase.__table__,
    UserConfig.__table__,
    RequirementTask.__table__,
    SourceDocument.__table__,
    StructuredRequirementVersion.__table__,
    test_point_version_model.TestPointVersion.__table__,
    test_case_package_version_model.TestCasePackageVersion.__table__,
    ReviewRecord.__table__,
    Job.__table__,
]


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=TEST_TABLES))

    yield engine

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, tables=TEST_TABLES))

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
    test_case = test_case_model.TestCase(
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


@pytest.mark.asyncio
async def test_create_requirement_task_with_versions(db_session):
    """测试任务主模型和版本模型"""
    project = Project(name="结算平台", description="复杂结算业务")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    task = RequirementTask(
        project_id=project.id,
        title="结算规则需求",
        source_type="pdf",
        current_stage="intake",
        task_status="created",
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    document = SourceDocument(
        task_id=task.id,
        file_name="requirement.pdf",
        file_type="application/pdf",
        storage_path="/tmp/requirement.pdf",
    )
    structured = StructuredRequirementVersion(
        task_id=task.id,
        version_no=1,
        status="draft",
        content_json={"modules": [{"name": "清结算"}]},
    )
    test_points = test_point_version_model.TestPointVersion(
        task_id=task.id,
        version_no=1,
        status="draft",
        content_json={"points": [{"name": "主流程"}]},
    )
    case_package = test_case_package_version_model.TestCasePackageVersion(
        task_id=task.id,
        version_no=1,
        status="draft",
        content_json={"cases": [{"title": "正常结算"}]},
    )
    review = ReviewRecord(
        task_id=task.id,
        target_type="structured_requirement_version",
        target_version_id=1,
        stage="structuring",
        review_result="approved",
    )
    job = Job(
        job_type="structuring",
        target_type="requirement_task",
        target_id=task.id,
        status="queued",
        progress=0,
    )

    db_session.add_all([document, structured, test_points, case_package, review, job])
    await db_session.commit()

    assert task.id is not None
    assert task.current_stage == "intake"
    assert task.task_status == "created"
    assert document.id is not None
    assert structured.version_no == 1
    assert structured.content_json["modules"][0]["name"] == "清结算"
    assert test_points.content_json["points"][0]["name"] == "主流程"
    assert case_package.content_json["cases"][0]["title"] == "正常结算"
    assert review.review_result == "approved"
    assert job.status == "queued"
