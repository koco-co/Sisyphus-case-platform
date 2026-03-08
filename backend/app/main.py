from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import request_logging_middleware
from app.modules.analytics.router import router as analytics_router
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.collaboration.router import router as collaboration_router
from app.modules.coverage.router import router as coverage_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.diagnosis.router import router as diagnosis_router
from app.modules.diff.router import router as diff_router
from app.modules.execution.router import router as execution_router
from app.modules.export.router import router as export_router
from app.modules.generation.router import router as generation_router
from app.modules.import_clean.router import router as import_clean_router
from app.modules.knowledge.router import router as knowledge_router
from app.modules.notification.router import router as notification_router
from app.modules.products.router import router as products_router
from app.modules.recycle.router import router as recycle_router
from app.modules.scene_map.router import router as scene_map_router
from app.modules.search.router import router as search_router
from app.modules.templates.router import router as templates_router
from app.modules.test_plan.router import router as test_plan_router
from app.modules.testcases.router import router as testcases_router
from app.modules.uda.router import router as uda_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="Sisyphus Case Platform",
    description="AI-driven enterprise test case generation platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(request_logging_middleware)

_routers = [
    auth_router,
    products_router,
    uda_router,
    import_clean_router,
    diagnosis_router,
    scene_map_router,
    generation_router,
    testcases_router,
    diff_router,
    coverage_router,
    test_plan_router,
    templates_router,
    knowledge_router,
    export_router,
    execution_router,
    analytics_router,
    notification_router,
    search_router,
    collaboration_router,
    dashboard_router,
    audit_router,
    recycle_router,
]

for r in _routers:
    app.include_router(r, prefix="/api")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
