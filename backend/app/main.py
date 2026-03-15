import importlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.audit_middleware import audit_logging_middleware
from app.core.config import settings
from app.core.middleware import request_logging_middleware
from app.core.rate_limiter import rate_limit_middleware

logger = logging.getLogger(__name__)

_MODULE_NAMES = [
    "auth",
    "products",
    "uda",
    "import_clean",
    "diagnosis",
    "scene_map",
    "generation",
    "testcases",
    "diff",
    "coverage",
    "templates",
    "knowledge",
    "export",
    "execution",
    "analytics",
    "search",
    "dashboard",
    "audit",
    "recycle",
    "ai_config",
    "tasks",
]


def _collect_routers() -> list:
    """Import each module router with error handling for modules not yet ready."""
    routers = []
    for name in _MODULE_NAMES:
        module_path = f"app.modules.{name}.router"
        try:
            mod = importlib.import_module(module_path)
            routers.append(mod.router)
        except Exception:
            logger.warning("Failed to load router from %s — skipping", module_path, exc_info=True)
    return routers


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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(request_logging_middleware)
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(audit_logging_middleware)

for _r in _collect_routers():
    app.include_router(_r, prefix="/api")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
