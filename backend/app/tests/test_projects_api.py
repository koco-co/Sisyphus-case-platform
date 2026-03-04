import pytest
from app.tests.conftest import test_client_with_db


@pytest.mark.asyncio
async def test_create_project(test_client_with_db):
    """测试创建项目"""
    response = await test_client_with_db.post(
        "/api/projects/",
        json={
            "name": "登录模块",
            "description": "用户登录功能测试",
            "parent_id": None
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "登录模块"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects(test_client_with_db):
    """测试获取项目列表"""
    # 先创建一个项目
    await test_client_with_db.post(
        "/api/projects/",
        json={
            "name": "测试项目",
            "description": "测试描述",
        }
    )

    # 获取列表
    response = await test_client_with_db.get("/api/projects/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_project(test_client_with_db):
    """测试获取项目详情"""
    # 先创建一个项目
    create_response = await test_client_with_db.post(
        "/api/projects/",
        json={
            "name": "详情测试",
            "description": "测试获取详情",
        }
    )
    project_id = create_response.json()["id"]

    # 获取详情
    response = await test_client_with_db.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "详情测试"


@pytest.mark.asyncio
async def test_get_project_not_found(test_client_with_db):
    """测试获取不存在项目"""
    response = await test_client_with_db.get("/api/projects/99999")
    assert response.status_code == 404
