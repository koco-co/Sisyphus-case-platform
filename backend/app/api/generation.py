"""用例生成 API (WebSocket 流式输出)"""

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.agents.orchestrator import AgentOrchestrator
from app.database import get_db
from app.llm.factory import create_llm_provider
from app.models.user_config import UserConfig
from app.rag.retriever import VectorRetriever

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/generate", tags=["generation"])


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_progress(self, websocket: WebSocket, message: Dict[str, Any]):
        await websocket.send_text(json.dumps(message, ensure_ascii=False))


manager = ConnectionManager()


@router.websocket("/ws")
async def generate_test_cases_websocket(websocket: WebSocket):
    """
    WebSocket 端点，用于流式生成测试用例。

    客户端发送:
    {
        "requirement": "需求文档",
        "test_points": ["测试点1", "测试点2"],
        "project_id": 项目ID (可选),
        "use_rag": 是否使用 RAG 检索历史用例
    }

    服务器发送进度消息:
    {
        "stage": "analyzing",  // analyzing, generating, reviewing, completed
        "message": "正在分析需求...",
        "progress": 30
    }

    服务器发送用例:
    {
        "stage": "completed",
        "test_cases": [...],
        "review_passed": true
    }
    """
    await manager.connect(websocket)

    try:
        # 接收初始消息
        data = await websocket.receive_text()
        request = json.loads(data)

        requirement = request.get("requirement")
        test_points = request.get("test_points", [])
        project_id = request.get("project_id")
        use_rag = request.get("use_rag", True)

        if not requirement:
            await manager.send_progress(
                websocket,
                {"stage": "error", "message": "缺少需求文档"},
            )
            return

        # 获取激活的 LLM 配置
        config = None
        async for db in get_db():
            result = await db.execute(
                select(UserConfig).where(UserConfig.is_active == True)
            )
            config = result.scalar_one_or_none()
            break

        if not config:
            await manager.send_progress(
                websocket,
                {"stage": "error", "message": "请先配置 LLM 提供商"},
            )
            return

        # 创建 LLM 实例
        llm = create_llm_provider(
            provider=config.provider,
            api_key=config.api_key_encrypted,
        )

        # 向量检索历史用例
        examples = []
        if use_rag:
            await manager.send_progress(
                websocket,
                {
                    "stage": "retrieving",
                    "message": "正在检索相似的历史用例...",
                    "progress": 10,
                },
            )

            retriever = VectorRetriever()
            similar_cases = await retriever.search_similar_cases(
                query=requirement,
                top_k=5,
                project_id=project_id,
            )

            examples = [
                {
                    "module": case.module,
                    "title": case.title,
                    "prerequisites": case.prerequisites,
                    "steps": case.steps,
                    "expected_results": case.expected_results,
                    "priority": case.priority,
                }
                for case in similar_cases
            ]

        # 创建编排器
        orchestrator = AgentOrchestrator(
            generator_llm=llm,
            reviewer_llm=llm,
            max_retries=3,
        )

        # 进度回调函数
        async def progress_callback(stage: str, message: str):
            progress_map = {
                "retrieving": 10,
                "generating": 30,
                "reviewing": 70,
                "completed": 100,
                "error": 0,
            }
            await manager.send_progress(
                websocket,
                {
                    "stage": stage,
                    "message": message,
                    "progress": progress_map.get(stage, 50),
                },
            )

        # 开始生成
        await progress_callback("generating", "正在生成测试用例...")

        result = await orchestrator.generate_with_review(
            {
                "requirement": requirement,
                "test_points": test_points,
                "examples": examples,
                "project_id": project_id,
                "use_rag": use_rag,
            },
            progress_callback=progress_callback,
        )

        if result["success"]:
            # 发送最终结果
            await manager.send_progress(
                websocket,
                {
                    "stage": "completed",
                    "message": "生成完成!",
                    "progress": 100,
                    "test_cases": result["test_cases"],
                    "review_passed": result.get("review_passed", False),
                    "attempts": result.get("attempts", 1),
                    "review": result.get("review", {}),
                },
            )
        else:
            await manager.send_progress(
                websocket,
                {
                    "stage": "error",
                    "message": result.get("error", "生成失败"),
                },
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 生成失败: {e}")
        await manager.send_progress(
            websocket,
            {"stage": "error", "message": f"错误: {str(e)}"},
        )
        manager.disconnect(websocket)


@router.post("/")
async def simple_generate(request: Dict[str, Any]):
    """简单的生成端点 (不需要 WebSocket)

    Returns:
        生成结果
    """
    requirement = request.get("requirement")
    test_points = request.get("test_points", [])
    project_id = request.get("project_id")
    use_rag = request.get("use_rag", True)

    if not requirement:
        return {"success": False, "error": "缺少需求文档"}

    # 获取激活的 LLM 配置
    config = None
    async for db in get_db():
        result = await db.execute(
            select(UserConfig).where(UserConfig.is_active == True)
        )
        config = result.scalar_one_or_none()
        break

    if not config:
        return {"success": False, "error": "请先配置 LLM 提供商"}

    # 创建 LLM 实例
    llm = create_llm_provider(
        provider=config.provider,
        api_key=config.api_key_encrypted,
    )

    # 向量检索历史用例
    examples = []
    if use_rag:
        retriever = VectorRetriever()
        similar_cases = await retriever.search_similar_cases(
            query=requirement,
            top_k=5,
            project_id=project_id,
        )
        examples = [
            {
                "module": case.module,
                "title": case.title,
                "prerequisites": case.prerequisites,
                "steps": case.steps,
                "expected_results": case.expected_results,
                "priority": case.priority,
            }
            for case in similar_cases
        ]

    # 创建编排器
    orchestrator = AgentOrchestrator(
        generator_llm=llm,
        reviewer_llm=llm,
        max_retries=3,
    )

    # 执行生成
    result = await orchestrator.generate_with_review(
        {
            "requirement": requirement,
            "test_points": test_points,
            "examples": examples,
            "project_id": project_id,
            "use_rag": use_rag,
        }
    )

    return result
