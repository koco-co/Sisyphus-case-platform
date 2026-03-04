"""测试向量管理 API"""

import pytest
from sqlalchemy import select
from app.tests.conftest import test_client_with_db
from app.database import async_session
from app.models.test_case import TestCase


@pytest.mark.asyncio
async def test_index_test_case(test_client_with_db):
    """测试为测试用例创建索引"""
    # 先创建测试用例
    case_response = await test_client_with_db.post(
        "/api/cases/",
        json={
            "project_id": 1,
            "title": "向量测试用例",
            "steps": "测试步骤",
            "expected_results": "预期结果"
        }
    )
    assert case_response.status_code == 201
    case_id = case_response.json()["id"]

    # 创建向量索引
    response = await test_client_with_db.post(f"/api/vectors/cases/{case_id}/index")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "向量索引创建成功"
    assert data["case_id"] == case_id


@pytest.mark.asyncio
async def test_batch_index_test_cases(test_client_with_db):
    """测试批量创建向量索引"""
    # 创建多个测试用例
    case_ids = []
    for i in range(3):
        case_response = await test_client_with_db.post(
            "/api/cases/",
            json={
                "project_id": 1,
                "title": f"批量索引测试用例 {i}",
                "steps": f"测试步骤 {i}",
                "expected_results": f"预期结果 {i}"
            }
        )
        case_ids.append(case_response.json()["id"])

    # 批量创建向量索引
    response = await test_client_with_db.post(
        "/api/vectors/cases/batch-index",
        json={"case_ids": case_ids}
    )
    assert response.status_code == 200
    data = response.json()
    assert "已为 3 条测试用例创建索引" in data["message"]
    assert data["count"] == 3


@pytest.mark.asyncio
async def test_search_similar_cases(test_client_with_db):
    """测试检索相似测试用例"""
    # 创建并索引测试用例
    case_response = await test_client_with_db.post(
        "/api/cases/",
        json={
            "project_id": 1,
            "title": "用户登录测试",
            "steps": "1. 打开登录页面\n2. 输入用户名和密码\n3. 点击登录按钮",
            "expected_results": "登录成功，跳转到首页"
        }
    )
    case_id = case_response.json()["id"]

    # 创建向量索引
    await test_client_with_db.post(f"/api/vectors/cases/{case_id}/index")

    # 检索相似用例 - 使用 pending 状态（默认状态）
    response = await test_client_with_db.post(
        "/api/vectors/search",
        json={
            "query": "测试用户登录功能",
            "top_k": 5,
            "status": "pending",  # 使用 pending 状态（默认状态）
            "min_similarity": 0.0  # 降低相似度阈值以确保返回结果
        }
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    assert results[0]["title"] == "用户登录测试"
    assert results[0]["similarity"] > 0.0


@pytest.mark.asyncio
async def test_index_nonexistent_case(test_client_with_db):
    """测试为不存在的用例创建索引"""
    response = await test_client_with_db.post("/api/vectors/cases/99999/index")
    assert response.status_code == 404
    assert "测试用例不存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_batch_index_nonexistent_cases(test_client_with_db):
    """测试批量索引不存在的用例"""
    response = await test_client_with_db.post(
        "/api/vectors/cases/batch-index",
        json={"case_ids": [99999, 99998]}
    )
    assert response.status_code == 404
    assert "没有找到测试用例" in response.json()["detail"]


@pytest.mark.asyncio
async def test_search_with_filters(test_client_with_db):
    """测试带过滤条件的检索"""
    # 创建不同项目的测试用例
    for project_id in [1, 2]:
        case_response = await test_client_with_db.post(
            "/api/cases/",
            json={
                "project_id": project_id,
                "title": f"项目{project_id}测试用例",
                "steps": "测试步骤",
                "expected_results": "预期结果"
            }
        )
        case_id = case_response.json()["id"]
        await test_client_with_db.post(f"/api/vectors/cases/{case_id}/index")

    # 按项目 ID 过滤 - 使用 pending 状态
    response = await test_client_with_db.post(
        "/api/vectors/search",
        json={
            "query": "测试用例",
            "top_k": 10,
            "status": "pending",  # 使用 pending 状态（默认状态）
            "project_id": 1,
            "min_similarity": 0.0
        }
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
