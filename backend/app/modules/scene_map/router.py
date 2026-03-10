import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, StreamingResponse

from app.core.dependencies import AsyncSessionDep
from app.modules.scene_map.schemas import (
    BatchUpdateRequest,
    ReorderRequest,
    SceneMapResponse,
    TestPointCreate,
    TestPointResponse,
    TestPointUpdate,
)
from app.modules.scene_map.service import SceneMapService

router = APIRouter(prefix="/scene-map", tags=["scene-map"])


@router.get("/{requirement_id}", response_model=SceneMapResponse)
async def get_scene_map(requirement_id: uuid.UUID, session: AsyncSessionDep) -> SceneMapResponse:
    svc = SceneMapService(session)
    scene_map = await svc.get_map(requirement_id)
    if not scene_map:
        raise HTTPException(status_code=404, detail="Scene map not found")
    test_points = await svc.list_test_points(scene_map.id)
    resp = SceneMapResponse.model_validate(scene_map)
    resp.test_points = [TestPointResponse.model_validate(tp) for tp in test_points]
    return resp


@router.post("/{requirement_id}/generate")
async def generate_scene_map(requirement_id: uuid.UUID, session: AsyncSessionDep) -> StreamingResponse:
    svc = SceneMapService(session)
    collector = await svc.generate_stream_with_persistence(requirement_id)
    return StreamingResponse(collector, media_type="text/event-stream")


@router.post("/{requirement_id}/test-points", response_model=TestPointResponse)
async def add_test_point(
    requirement_id: uuid.UUID,
    data: TestPointCreate,
    session: AsyncSessionDep,
) -> TestPointResponse:
    svc = SceneMapService(session)
    scene_map = await svc.get_or_create(requirement_id)
    tp = await svc.add_test_point(scene_map.id, data)
    return TestPointResponse.model_validate(tp)


@router.get("/{requirement_id}/test-points", response_model=list[TestPointResponse])
async def list_test_points(requirement_id: uuid.UUID, session: AsyncSessionDep) -> list[TestPointResponse]:
    svc = SceneMapService(session)
    scene_map = await svc.get_map(requirement_id)
    if not scene_map:
        return []
    points = await svc.list_test_points(scene_map.id)
    return [TestPointResponse.model_validate(tp) for tp in points]


@router.patch("/test-points/{test_point_id}", response_model=TestPointResponse)
async def update_test_point(
    test_point_id: uuid.UUID,
    data: TestPointUpdate,
    session: AsyncSessionDep,
) -> TestPointResponse:
    svc = SceneMapService(session)
    tp = await svc.update_test_point(test_point_id, data)
    if not tp:
        raise HTTPException(status_code=404, detail="Test point not found")
    return TestPointResponse.model_validate(tp)


@router.post("/test-points/{test_point_id}/confirm", response_model=TestPointResponse)
async def confirm_test_point(test_point_id: uuid.UUID, session: AsyncSessionDep) -> TestPointResponse:
    svc = SceneMapService(session)
    tp = await svc.confirm_test_point(test_point_id)
    if not tp:
        raise HTTPException(status_code=404, detail="Test point not found")
    return TestPointResponse.model_validate(tp)


@router.delete("/test-points/{test_point_id}")
async def delete_test_point(test_point_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = SceneMapService(session)
    success = await svc.soft_delete_test_point(test_point_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test point not found")
    return {"ok": True}


@router.post("/{requirement_id}/confirm", response_model=SceneMapResponse)
async def confirm_scene_map(requirement_id: uuid.UUID, session: AsyncSessionDep) -> SceneMapResponse:
    svc = SceneMapService(session)
    scene_map = await svc.get_map(requirement_id)
    if not scene_map:
        raise HTTPException(status_code=404, detail="Scene map not found")
    scene_map = await svc.confirm_all(scene_map.id)
    if not scene_map:
        raise HTTPException(status_code=404, detail="Scene map not found")
    test_points = await svc.list_test_points(scene_map.id)
    resp = SceneMapResponse.model_validate(scene_map)
    resp.test_points = [TestPointResponse.model_validate(tp) for tp in test_points]
    return resp


# ── Batch operations (B-M04-09) ───────────────────────────────────


@router.post("/{requirement_id}/test-points/batch-update", response_model=list[TestPointResponse])
async def batch_update_points(
    requirement_id: uuid.UUID,
    data: BatchUpdateRequest,
    session: AsyncSessionDep,
) -> list[TestPointResponse]:
    svc = SceneMapService(session)
    scene_map = await svc.get_map(requirement_id)
    if not scene_map:
        raise HTTPException(status_code=404, detail="Scene map not found")
    updated = await svc.batch_update_points(data.updates)
    return [TestPointResponse.model_validate(tp) for tp in updated]


@router.post("/{requirement_id}/test-points/reorder", response_model=list[TestPointResponse])
async def reorder_points(
    requirement_id: uuid.UUID,
    data: ReorderRequest,
    session: AsyncSessionDep,
) -> list[TestPointResponse]:
    svc = SceneMapService(session)
    scene_map = await svc.get_map(requirement_id)
    if not scene_map:
        raise HTTPException(status_code=404, detail="Scene map not found")
    points = await svc.reorder_points(scene_map.id, data.order)
    return [TestPointResponse.model_validate(tp) for tp in points]


# ── Export (B-M04-10) ─────────────────────────────────────────────


@router.get("/{requirement_id}/export", response_model=None)
async def export_scene_map(
    requirement_id: uuid.UUID,
    session: AsyncSessionDep,
    fmt: Literal["json", "md"] = Query("json", alias="format"),
) -> dict | PlainTextResponse:
    svc = SceneMapService(session)
    scene_map = await svc.get_map(requirement_id)
    if not scene_map:
        raise HTTPException(status_code=404, detail="Scene map not found")
    result = await svc.export_scene_map(scene_map.id, fmt)
    if isinstance(result, str):
        return PlainTextResponse(content=result, media_type="text/markdown")
    return result
