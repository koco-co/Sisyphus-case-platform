"""测试用例 API 测试"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TestCaseNew, Requirement, Project


@pytest_asyncio.fixture(scope="function")
async def test_project(db_session: AsyncSession):
    """创建测试项目"""
    project = Project(name="测试项目", description="用于测试的项目")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture(scope="function")
async def test_requirement(db_session: AsyncSession, test_project: Project):
    """创建测试需求"""
    requirement = Requirement(
        project_id=test_project.id,
        title="测试需求",
        content={"modules": []},
    )
    db_session.add(requirement)
    await db_session.commit()
    await db_session.refresh(requirement)
    return requirement


@pytest.mark.asyncio
async def test_create_testcases(
    test_client_with_db: AsyncClient,
    test_requirement: Requirement,
):
    """测试批量创建测试用例"""
    response = await test_client_with_db.post(
        "/api/testcases/",
        json={
            "requirement_id": str(test_requirement.id),
            "test_cases": [
                {
                    "title": "登录功能测试",
                    "priority": "P1",
                    "preconditions": "用户已注册",
                    "steps": [
                        {"step": 1, "action": "打开登录页面", "expected": "显示登录表单"},
                        {"step": 2, "action": "输入用户名和密码", "expected": "输入框显示内容"},
                        {"step": 3, "action": "点击登录按钮", "expected": "登录成功"},
                    ],
                    "tags": ["登录", "冒烟测试"],
                },
                {
                    "title": "注册功能测试",
                    "priority": "P2",
                    "preconditions": None,
                    "steps": [
                        {"step": 1, "action": "打开注册页面", "expected": "显示注册表单"},
                    ],
                    "tags": [],
                },
            ],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "登录功能测试"
    assert data[0]["priority"] == "P1"
    assert len(data[0]["steps"]) == 3
    assert "登录" in data[0]["tags"]
    assert data[1]["title"] == "注册功能测试"


@pytest.mark.asyncio
async def test_create_testcases_invalid_requirement_id(
    test_client_with_db: AsyncClient,
):
    """测试无效的需求 ID"""
    response = await test_client_with_db.post(
        "/api/testcases/",
        json={
            "requirement_id": "invalid-uuid",
            "test_cases": [
                {
                    "title": "测试用例",
                    "priority": "P2",
                    "steps": [],
                    "tags": [],
                }
            ],
        },
    )

    assert response.status_code == 400
    assert "无效的需求 ID" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_testcases_by_requirement(
    test_client_with_db: AsyncClient,
    db_session: AsyncSession,
    test_requirement: Requirement,
):
    """测试获取需求关联的测试用例列表"""
    # 先创建一些测试用例
    tc1 = TestCaseNew(
        requirement_id=test_requirement.id,
        title="用例1",
        priority="P1",
        steps=[{"step": 1, "action": "操作1", "expected": "结果1"}],
        tags=[],
    )
    tc2 = TestCaseNew(
        requirement_id=test_requirement.id,
        title="用例2",
        priority="P2",
        steps=[],
        tags=[],
    )
    db_session.add_all([tc1, tc2])
    await db_session.commit()

    response = await test_client_with_db.get(
        f"/api/testcases/requirement/{test_requirement.id}"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    titles = [tc["title"] for tc in data]
    assert "用例1" in titles
    assert "用例2" in titles


@pytest.mark.asyncio
async def test_get_testcase(
    test_client_with_db: AsyncClient,
    db_session: AsyncSession,
    test_requirement: Requirement,
):
    """测试获取测试用例详情"""
    tc = TestCaseNew(
        requirement_id=test_requirement.id,
        title="详细测试用例",
        priority="P1",
        preconditions="前置条件说明",
        steps=[
            {"step": 1, "action": "步骤1", "expected": "预期1"},
            {"step": 2, "action": "步骤2", "expected": "预期2"},
        ],
        tags=["标签1", "标签2"],
    )
    db_session.add(tc)
    await db_session.commit()
    await db_session.refresh(tc)

    response = await test_client_with_db.get(f"/api/testcases/{tc.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "详细测试用例"
    assert data["priority"] == "P1"
    assert data["preconditions"] == "前置条件说明"
    assert len(data["steps"]) == 2
    assert data["steps"][0]["action"] == "步骤1"
    assert "标签1" in data["tags"]


@pytest.mark.asyncio
async def test_get_testcase_not_found(
    test_client_with_db: AsyncClient,
):
    """测试获取不存在的测试用例"""
    response = await test_client_with_db.get(
        "/api/testcases/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_testcases_empty_list(
    test_client_with_db: AsyncClient,
    test_requirement: Requirement,
):
    """测试创建空的测试用例列表"""
    response = await test_client_with_db.post(
        "/api/testcases/",
        json={
            "requirement_id": str(test_requirement.id),
            "test_cases": [],
        },
    )

    # 应该成功，但返回空列表
    assert response.status_code == 201
    assert response.json() == []
