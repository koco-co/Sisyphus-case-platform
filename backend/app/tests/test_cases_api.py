import pytest
from app.tests.conftest import test_client_with_db


@pytest.mark.asyncio
async def test_create_test_case(test_client_with_db):
    """测试创建测试用例"""
    # 先创建项目
    project_response = await test_client_with_db.post(
        "/api/projects/",
        json={"name": "登录模块"}
    )
    project_id = project_response.json()["id"]

    # 创建测试用例
    response = await test_client_with_db.post(
        "/api/cases/",
        json={
            "project_id": project_id,
            "module": "用户登录",
            "title": "测试用户名密码登录",
            "prerequisites": "1) 用户已注册\n2) 用户知道账号密码",
            "steps": "1. 打开登录页面\n2. 输入用户名和密码\n3. 点击登录按钮",
            "expected_results": "1. 登录成功\n2. 跳转到首页",
            "priority": "1",
            "case_type": "功能测试",
            "stage": "功能测试阶段"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "测试用户名密码登录"
    assert data["project_id"] == project_id
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_test_cases(test_client_with_db):
    """测试获取测试用例列表"""
    # 先创建项目和测试用例
    project_response = await test_client_with_db.post(
        "/api/projects/",
        json={"name": "测试项目"}
    )
    project_id = project_response.json()["id"]

    await test_client_with_db.post(
        "/api/cases/",
        json={
            "project_id": project_id,
            "title": "测试用例1",
            "steps": "步骤1",
            "expected_results": "预期结果1"
        }
    )

    # 获取列表
    response = await test_client_with_db.get("/api/cases/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_test_cases_by_project(test_client_with_db):
    """测试按项目筛选测试用例"""
    # 创建两个项目
    project1_response = await test_client_with_db.post(
        "/api/projects/",
        json={"name": "项目1"}
    )
    project1_id = project1_response.json()["id"]

    project2_response = await test_client_with_db.post(
        "/api/projects/",
        json={"name": "项目2"}
    )
    project2_id = project2_response.json()["id"]

    # 为项目1创建测试用例
    await test_client_with_db.post(
        "/api/cases/",
        json={
            "project_id": project1_id,
            "title": "项目1的测试用例",
            "steps": "步骤",
            "expected_results": "结果"
        }
    )

    # 为项目2创建测试用例
    await test_client_with_db.post(
        "/api/cases/",
        json={
            "project_id": project2_id,
            "title": "项目2的测试用例",
            "steps": "步骤",
            "expected_results": "结果"
        }
    )

    # 筛选项目1的测试用例
    response = await test_client_with_db.get(f"/api/cases/?project_id={project1_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["project_id"] == project1_id


@pytest.mark.asyncio
async def test_get_test_case(test_client_with_db):
    """测试获取测试用例详情"""
    # 先创建项目和测试用例
    project_response = await test_client_with_db.post(
        "/api/projects/",
        json={"name": "测试项目"}
    )
    project_id = project_response.json()["id"]

    case_response = await test_client_with_db.post(
        "/api/cases/",
        json={
            "project_id": project_id,
            "module": "用户管理",
            "title": "测试详情获取",
            "steps": "测试步骤",
            "expected_results": "预期结果"
        }
    )
    case_id = case_response.json()["id"]

    # 获取详情
    response = await test_client_with_db.get(f"/api/cases/{case_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == case_id
    assert data["title"] == "测试详情获取"
    assert data["module"] == "用户管理"


@pytest.mark.asyncio
async def test_get_test_case_not_found(test_client_with_db):
    """测试获取不存在的测试用例"""
    response = await test_client_with_db.get("/api/cases/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "测试用例不存在"


@pytest.mark.asyncio
async def test_update_test_case(test_client_with_db):
    """测试更新测试用例"""
    # 先创建项目和测试用例
    project_response = await test_client_with_db.post(
        "/api/projects/",
        json={"name": "测试项目"}
    )
    project_id = project_response.json()["id"]

    case_response = await test_client_with_db.post(
        "/api/cases/",
        json={
            "project_id": project_id,
            "title": "原标题",
            "steps": "原步骤",
            "expected_results": "原结果"
        }
    )
    case_id = case_response.json()["id"]

    # 更新测试用例
    update_response = await test_client_with_db.put(
        f"/api/cases/{case_id}",
        json={
            "project_id": project_id,
            "title": "更新后的标题",
            "steps": "更新后的步骤",
            "expected_results": "更新后的结果",
            "priority": "1"
        }
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["title"] == "更新后的标题"
    assert data["priority"] == "1"


@pytest.mark.asyncio
async def test_update_test_case_not_found(test_client_with_db):
    """测试更新不存在的测试用例"""
    response = await test_client_with_db.put(
        "/api/cases/99999",
        json={
            "project_id": 1,
            "title": "标题",
            "steps": "步骤",
            "expected_results": "结果"
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "测试用例不存在"


@pytest.mark.asyncio
async def test_update_case_status(test_client_with_db):
    """测试更新测试用例状态"""
    # 先创建项目和测试用例
    project_response = await test_client_with_db.post(
        "/api/projects/",
        json={"name": "测试项目"}
    )
    project_id = project_response.json()["id"]

    case_response = await test_client_with_db.post(
        "/api/cases/",
        json={
            "project_id": project_id,
            "title": "待审批测试用例",
            "steps": "步骤",
            "expected_results": "结果"
        }
    )
    case_id = case_response.json()["id"]

    # 更新状态为 approved
    response = await test_client_with_db.patch(
        f"/api/cases/{case_id}/status?status=approved"
    )
    assert response.status_code == 200
    data = response.json()
    assert "已更新为 approved" in data["message"]


@pytest.mark.asyncio
async def test_update_case_status_invalid(test_client_with_db):
    """测试更新为无效状态"""
    # 先创建项目和测试用例
    project_response = await test_client_with_db.post(
        "/api/projects/",
        json={"name": "测试项目"}
    )
    project_id = project_response.json()["id"]

    case_response = await test_client_with_db.post(
        "/api/cases/",
        json={
            "project_id": project_id,
            "title": "测试用例",
            "steps": "步骤",
            "expected_results": "结果"
        }
    )
    case_id = case_response.json()["id"]

    # 尝试更新为无效状态
    response = await test_client_with_db.patch(
        f"/api/cases/{case_id}/status?status=invalid_status"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "无效的状态值"


@pytest.mark.asyncio
async def test_update_case_status_not_found(test_client_with_db):
    """测试更新不存在测试用例的状态"""
    response = await test_client_with_db.patch(
        "/api/cases/99999/status?status=approved"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "测试用例不存在"
