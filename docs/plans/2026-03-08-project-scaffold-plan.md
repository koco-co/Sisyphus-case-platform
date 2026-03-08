# Project Scaffold Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Scaffold the complete Sisyphus-case-platform project with backend (FastAPI + DDD), frontend (Next.js 14), toolchain, CI/CD, and dev environment.

**Architecture:** FastAPI backend with DDD modular architecture (21 business modules), Next.js 14 App Router frontend, uv + ruff + pyright + Biome toolchain, Docker Compose infrastructure, GitHub Actions CI.

**Tech Stack:** Python 3.12 (uv), FastAPI, SQLAlchemy 2.0, Alembic, Celery, Next.js 14 (bun), Ant Design, Tailwind CSS, Biome, PostgreSQL, Redis, Qdrant, MinIO.

---

### Task 1: Root configuration files

**Files:**
- Modify: `.gitignore`
- Create: `.editorconfig`
- Create: `.env.example`

**Step 1: Update .gitignore to cover full-stack project**

Add Node.js/Next.js entries and project-specific ignores to the existing Python .gitignore:

```gitignore
# --- Append to existing .gitignore ---

# Node.js
node_modules/
.next/
out/
bun.lock

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project
*.local
.env*.local
docker/data/
```

**Step 2: Create .editorconfig**

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space

[*.py]
indent_size = 4

[*.{ts,tsx,js,jsx,json,yml,yaml,md}]
indent_size = 2
```

**Step 3: Create .env.example**

```bash
# LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
# OLLAMA_BASE_URL=http://localhost:11434

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sisyphus
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/sisyphus

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=sisyphus

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# App
APP_ENV=development
APP_DEBUG=true
```

**Step 4: Commit**

```bash
git add .gitignore .editorconfig .env.example
git commit -m "chore: add root configuration files"
```

---

### Task 2: Backend project initialization with uv

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`

**Step 1: Initialize backend with uv**

```bash
cd backend
uv init --no-readme
```

Then replace the generated `pyproject.toml` with the full config.

**Step 2: Write pyproject.toml**

```toml
[project]
name = "sisyphus-case-platform"
version = "0.1.0"
description = "AI-driven enterprise test case generation platform"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "sqlalchemy[asyncio]>=2.0",
    "alembic>=1.14",
    "asyncpg>=0.30",
    "pydantic-settings>=2.7",
    "celery[redis]>=5.4",
    "redis>=5.2",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "httpx>=0.28",
    "python-multipart>=0.0.18",
    "minio>=7.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-cov>=6.0",
    "httpx>=0.28",
    "factory-boy>=3.3",
    "ruff>=0.8",
    "pyright>=1.1",
]

[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = [
    "E", "W",
    "F",
    "I",
    "N",
    "UP",
    "B",
    "SIM",
    "ASYNC",
]

[tool.ruff.lint.isort]
known-first-party = ["app"]

[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "standard"
venvPath = "."
venv = ".venv"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Step 3: Create app package**

```python
# backend/app/__init__.py
```

(Empty file, just marks the package.)

**Step 4: Install dependencies**

```bash
cd backend && uv sync --all-extras
```

Expected: Lock file created, dependencies installed.

**Step 5: Verify toolchain**

```bash
cd backend && uv run ruff check . && uv run pyright --version
```

Expected: No errors (empty project), pyright version prints.

**Step 6: Commit**

```bash
git add backend/
git commit -m "chore: initialize backend with uv, ruff, pyright"
```

---

### Task 3: Backend core infrastructure

**Files:**
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`
- Create: `backend/app/core/security.py`
- Create: `backend/app/core/dependencies.py`
- Create: `backend/app/core/exceptions.py`
- Create: `backend/app/core/middleware.py`

**Step 1: Create core/__init__.py**

```python
# backend/app/core/__init__.py
```

**Step 2: Create config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sisyphus"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/sisyphus"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "sisyphus"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # LLM
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    ollama_base_url: str = "http://localhost:11434"


settings = Settings()
```

**Step 3: Create database.py**

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
```

**Step 4: Create security.py**

```python
from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
```

**Step 5: Create dependencies.py**

```python
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
```

**Step 6: Create exceptions.py**

```python
from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictError(HTTPException):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
```

**Step 7: Create middleware.py**

```python
import time
import logging

from fastapi import Request

logger = logging.getLogger(__name__)


async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    logger.info("%s %s %s %.3fs", request.method, request.url.path, response.status_code, elapsed)
    return response
```

**Step 8: Run ruff + pyright**

```bash
cd backend && uv run ruff check app/core/ && uv run ruff format --check app/core/ && uv run pyright app/core/
```

Expected: All pass.

**Step 9: Commit**

```bash
git add backend/app/core/
git commit -m "feat: add backend core infrastructure (config, db, security, middleware)"
```

---

### Task 4: Backend shared utilities

**Files:**
- Create: `backend/app/shared/__init__.py`
- Create: `backend/app/shared/base_model.py`
- Create: `backend/app/shared/base_schema.py`
- Create: `backend/app/shared/pagination.py`
- Create: `backend/app/shared/enums.py`

**Step 1: Create shared/__init__.py**

```python
# backend/app/shared/__init__.py
```

**Step 2: Create base_model.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
```

**Step 3: Create base_schema.py**

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseResponse(BaseSchema):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
```

**Step 4: Create pagination.py**

```python
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
```

**Step 5: Create enums.py**

```python
from enum import StrEnum


class RequirementStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    DIAGNOSED = "diagnosed"
    GENERATING = "generating"
    COMPLETED = "completed"


class ScenarioType(StrEnum):
    NORMAL = "normal"
    EXCEPTION = "exception"
    BOUNDARY = "boundary"
    CONCURRENT = "concurrent"
    PERMISSION = "permission"


class SceneNodeSource(StrEnum):
    DOCUMENT = "document"
    AI_DETECTED = "ai_detected"
    USER_ADDED = "user_added"


class SceneNodeStatus(StrEnum):
    COVERED = "covered"
    SUPPLEMENTED = "supplemented"
    MISSING = "missing"
    PENDING = "pending"
    CONFIRMED = "confirmed"


class Priority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class TestCaseStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
```

**Step 6: Run checks**

```bash
cd backend && uv run ruff check app/shared/ && uv run pyright app/shared/
```

Expected: All pass.

**Step 7: Commit**

```bash
git add backend/app/shared/
git commit -m "feat: add backend shared utilities (base model, schemas, pagination, enums)"
```

---

### Task 5: Backend business modules — P0 core modules (auth, products, diagnosis, scene_map, generation, testcases, diff)

**Files:** Create `__init__.py`, `router.py`, `models.py`, `schemas.py`, `service.py` for each P0 module.

Each module follows the same skeleton pattern. Below shows the detailed content for `auth` and `products` as reference; the remaining P0 modules use the same skeleton with module-appropriate placeholders.

**Step 1: Create auth module**

`backend/app/modules/__init__.py`:
```python
```

`backend/app/modules/auth/__init__.py`:
```python
```

`backend/app/modules/auth/models.py`:
```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(default=True)
    role: Mapped[str] = mapped_column(String(20), default="member")
```

`backend/app/modules/auth/schemas.py`:
```python
from app.shared.base_schema import BaseResponse, BaseSchema


class UserCreate(BaseSchema):
    email: str
    username: str
    password: str
    full_name: str | None = None


class UserLogin(BaseSchema):
    username: str
    password: str


class UserResponse(BaseResponse):
    email: str
    username: str
    full_name: str | None
    is_active: bool
    role: str


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
```

`backend/app/modules/auth/service.py`:
```python
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.modules.auth.models import User
from app.modules.auth.schemas import TokenResponse, UserCreate


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(self, data: UserCreate) -> User:
        user = User(
            email=data.email,
            username=data.username,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate(self, username: str, password: str) -> TokenResponse | None:
        stmt = select(User).where(User.username == username, User.is_active.is_(True))
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            return None
        token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=token)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)
```

`backend/app/modules/auth/router.py`:
```python
from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import AsyncSessionDep
from app.modules.auth.schemas import TokenResponse, UserCreate, UserLogin, UserResponse
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, session: AsyncSessionDep):
    service = AuthService(session)
    user = await service.register(data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, session: AsyncSessionDep):
    service = AuthService(session)
    result = await service.authenticate(data.username, data.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return result
```

**Step 2: Create products module**

`backend/app/modules/products/__init__.py`:
```python
```

`backend/app/modules/products/models.py`:
```python
import uuid

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class Product(BaseModel):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(Text)


class Iteration(BaseModel):
    __tablename__ = "iterations"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    name: Mapped[str] = mapped_column(String(100))
    start_date: Mapped[str | None] = mapped_column(Date)
    end_date: Mapped[str | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")


class Requirement(BaseModel):
    __tablename__ = "requirements"

    iteration_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("iterations.id"))
    req_id: Mapped[str] = mapped_column(String(50), unique=True)
    title: Mapped[str] = mapped_column(Text)
    content_ast: Mapped[dict] = mapped_column(JSONB, default=dict)
    frontmatter: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)


class RequirementVersion(BaseModel):
    __tablename__ = "requirement_versions"

    requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("requirements.id"))
    version: Mapped[int] = mapped_column(Integer)
    content_ast: Mapped[dict] = mapped_column(JSONB)
    change_summary: Mapped[str | None] = mapped_column(Text)
```

`backend/app/modules/products/schemas.py`:
```python
import uuid

from app.shared.base_schema import BaseResponse, BaseSchema


class ProductCreate(BaseSchema):
    name: str
    slug: str
    description: str | None = None


class ProductResponse(BaseResponse):
    name: str
    slug: str
    description: str | None


class IterationCreate(BaseSchema):
    product_id: uuid.UUID
    name: str
    start_date: str | None = None
    end_date: str | None = None


class IterationResponse(BaseResponse):
    product_id: uuid.UUID
    name: str
    start_date: str | None
    end_date: str | None
    status: str


class RequirementCreate(BaseSchema):
    iteration_id: uuid.UUID
    req_id: str
    title: str
    content_ast: dict | None = None
    frontmatter: dict | None = None


class RequirementResponse(BaseResponse):
    iteration_id: uuid.UUID
    req_id: str
    title: str
    status: str
    version: int
```

`backend/app/modules/products/service.py`:
```python
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.models import Iteration, Product, Requirement
from app.modules.products.schemas import IterationCreate, ProductCreate, RequirementCreate


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_product(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def list_products(self) -> list[Product]:
        result = await self.session.execute(select(Product).where(Product.deleted_at.is_(None)))
        return list(result.scalars().all())

    async def get_product(self, product_id: UUID) -> Product | None:
        return await self.session.get(Product, product_id)


class IterationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_iteration(self, data: IterationCreate) -> Iteration:
        iteration = Iteration(**data.model_dump())
        self.session.add(iteration)
        await self.session.commit()
        await self.session.refresh(iteration)
        return iteration

    async def list_by_product(self, product_id: UUID) -> list[Iteration]:
        result = await self.session.execute(
            select(Iteration).where(Iteration.product_id == product_id, Iteration.deleted_at.is_(None))
        )
        return list(result.scalars().all())


class RequirementService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_requirement(self, data: RequirementCreate) -> Requirement:
        requirement = Requirement(**data.model_dump(exclude_none=True))
        self.session.add(requirement)
        await self.session.commit()
        await self.session.refresh(requirement)
        return requirement

    async def list_by_iteration(self, iteration_id: UUID) -> list[Requirement]:
        result = await self.session.execute(
            select(Requirement).where(Requirement.iteration_id == iteration_id, Requirement.deleted_at.is_(None))
        )
        return list(result.scalars().all())
```

`backend/app/modules/products/router.py`:
```python
import uuid

from fastapi import APIRouter, status

from app.core.dependencies import AsyncSessionDep
from app.modules.products.schemas import (
    IterationCreate,
    IterationResponse,
    ProductCreate,
    ProductResponse,
    RequirementCreate,
    RequirementResponse,
)
from app.modules.products.service import IterationService, ProductService, RequirementService

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, session: AsyncSessionDep):
    service = ProductService(session)
    return await service.create_product(data)


@router.get("", response_model=list[ProductResponse])
async def list_products(session: AsyncSessionDep):
    service = ProductService(session)
    return await service.list_products()


@router.post("/{product_id}/iterations", response_model=IterationResponse, status_code=status.HTTP_201_CREATED)
async def create_iteration(product_id: uuid.UUID, data: IterationCreate, session: AsyncSessionDep):
    data.product_id = product_id
    service = IterationService(session)
    return await service.create_iteration(data)


@router.get("/{product_id}/iterations", response_model=list[IterationResponse])
async def list_iterations(product_id: uuid.UUID, session: AsyncSessionDep):
    service = IterationService(session)
    return await service.list_by_product(product_id)


@router.post("/{product_id}/iterations/{iteration_id}/requirements", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(data: RequirementCreate, session: AsyncSessionDep):
    service = RequirementService(session)
    return await service.create_requirement(data)
```

**Step 3: Create remaining P0 module skeletons**

For each of these modules, create `__init__.py`, `router.py`, `models.py`, `schemas.py`, `service.py` with minimal skeleton content:

- `backend/app/modules/uda/` — UDA document abstraction, plus `parsers/` and `renderers/` subdirs
- `backend/app/modules/diagnosis/` — health diagnosis, plus `checklists/default.yml`
- `backend/app/modules/scene_map/` — test point & scene map
- `backend/app/modules/generation/` — test case generation
- `backend/app/modules/testcases/` — test case management
- `backend/app/modules/diff/` — requirement diff & impact analysis

Each skeleton `router.py`:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/<module-kebab>", tags=["<module>"])


# TODO: implement endpoints
```

Each skeleton `models.py`:
```python
# TODO: implement models
```

Each skeleton `schemas.py`:
```python
# TODO: implement schemas
```

Each skeleton `service.py`:
```python
# TODO: implement service
```

**Step 4: Run checks**

```bash
cd backend && uv run ruff check app/modules/ && uv run pyright app/modules/
```

Expected: All pass.

**Step 5: Commit**

```bash
git add backend/app/modules/
git commit -m "feat: add backend business modules — auth, products (full), P0 skeletons"
```

---

### Task 6: Backend business modules — P1/P2 module skeletons

**Files:** Create skeleton `__init__.py`, `router.py`, `models.py`, `schemas.py`, `service.py` for each module.

Modules:
- `backend/app/modules/import_clean/` (M02)
- `backend/app/modules/coverage/` (M08)
- `backend/app/modules/test_plan/` (M09)
- `backend/app/modules/templates/` (M10)
- `backend/app/modules/knowledge/` (M11)
- `backend/app/modules/export/` (M12)
- `backend/app/modules/execution/` (M13)
- `backend/app/modules/analytics/` (M14)
- `backend/app/modules/notification/` (M16)
- `backend/app/modules/search/` (M17)
- `backend/app/modules/collaboration/` (M18)
- `backend/app/modules/dashboard/` (M19)
- `backend/app/modules/audit/` (M20) — includes full `AuditLog` model
- `backend/app/modules/recycle/` (M21)

**Step 1: Create all skeletons (same pattern as Task 5 Step 3)**

**Step 2: Create audit/models.py with full AuditLog model**

```python
import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(50))
    resource: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    detail: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(Text)
```

**Step 3: Create notification/models.py with full Notification model**

```python
import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    ref_type: Mapped[str | None] = mapped_column(String(50))
    ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
```

**Step 4: Run checks and commit**

```bash
cd backend && uv run ruff check app/modules/ && uv run pyright app/modules/
git add backend/app/modules/
git commit -m "feat: add P1/P2 module skeletons with audit and notification models"
```

---

### Task 7: Backend Celery worker setup

**Files:**
- Create: `backend/app/worker/__init__.py`
- Create: `backend/app/worker/celery_app.py`
- Create: `backend/app/worker/tasks/__init__.py`
- Create: `backend/app/worker/tasks/parse_tasks.py`
- Create: `backend/app/worker/tasks/diagnosis_tasks.py`
- Create: `backend/app/worker/tasks/diff_tasks.py`
- Create: `backend/app/worker/tasks/generation_tasks.py`

**Step 1: Create celery_app.py**

```python
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "sisyphus",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

celery_app.autodiscover_tasks(["app.worker.tasks"])
```

**Step 2: Create task skeletons**

Each task file follows:

```python
from app.worker.celery_app import celery_app


@celery_app.task(name="<module>.<task_name>")
def task_name():
    """TODO: implement"""
```

**Step 3: Run checks and commit**

```bash
cd backend && uv run ruff check app/worker/ && uv run pyright app/worker/
git add backend/app/worker/
git commit -m "feat: add Celery worker setup with task skeletons"
```

---

### Task 8: Backend main.py — FastAPI app entry point

**Files:**
- Create: `backend/app/main.py`

**Step 1: Create main.py**

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import request_logging_middleware
from app.modules.auth.router import router as auth_router
from app.modules.products.router import router as products_router
from app.modules.uda.router import router as uda_router
from app.modules.diagnosis.router import router as diagnosis_router
from app.modules.scene_map.router import router as scene_map_router
from app.modules.generation.router import router as generation_router
from app.modules.testcases.router import router as testcases_router
from app.modules.diff.router import router as diff_router
from app.modules.coverage.router import router as coverage_router
from app.modules.test_plan.router import router as test_plan_router
from app.modules.templates.router import router as templates_router
from app.modules.knowledge.router import router as knowledge_router
from app.modules.export.router import router as export_router
from app.modules.execution.router import router as execution_router
from app.modules.analytics.router import router as analytics_router
from app.modules.notification.router import router as notification_router
from app.modules.search.router import router as search_router
from app.modules.collaboration.router import router as collaboration_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.audit.router import router as audit_router
from app.modules.recycle.router import router as recycle_router


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

# Mount all routers
for r in [
    auth_router,
    products_router,
    uda_router,
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
]:
    app.include_router(r, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

**Step 2: Write a smoke test**

Create `backend/tests/__init__.py` and `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 3: Run test**

```bash
cd backend && uv run pytest tests/test_health.py -v
```

Expected: PASS

**Step 4: Run full checks**

```bash
cd backend && uv run ruff check . && uv run pyright app/ && uv run pytest
```

Expected: All pass.

**Step 5: Commit**

```bash
git add backend/app/main.py backend/tests/
git commit -m "feat: add FastAPI app entry point with all routers mounted"
```

---

### Task 9: Alembic setup

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/` (directory)

**Step 1: Initialize alembic**

```bash
cd backend && uv run alembic init alembic
```

**Step 2: Edit alembic.ini — set sqlalchemy.url placeholder**

In `alembic.ini`, set:
```ini
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/sisyphus
```

**Step 3: Edit alembic/env.py to import all models and use async**

Replace `alembic/env.py` with:

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.shared.base_model import Base

# Import all models so Alembic detects them
from app.modules.auth.models import User  # noqa: F401
from app.modules.products.models import Product, Iteration, Requirement, RequirementVersion  # noqa: F401
from app.modules.audit.models import AuditLog  # noqa: F401
from app.modules.notification.models import Notification  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import engine_from_config
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 4: Create scripts/seed.py**

```python
"""Seed initial data: default admin user, checklist templates."""

import asyncio


async def seed():
    print("Seeding database...")
    # TODO: Add seed data (admin user, checklists, templates)
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
```

**Step 5: Commit**

```bash
git add backend/alembic/ backend/alembic.ini backend/scripts/
git commit -m "feat: add Alembic migration setup and seed script"
```

---

### Task 10: Backend test structure

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/unit/__init__.py`
- Create: `backend/tests/integration/__init__.py`

**Step 1: Create conftest.py**

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)
```

**Step 2: Create directory markers**

```python
# backend/tests/unit/__init__.py
# backend/tests/integration/__init__.py
```

**Step 3: Run pytest to verify structure**

```bash
cd backend && uv run pytest -v
```

Expected: 1 test passes (health check from Task 8).

**Step 4: Commit**

```bash
git add backend/tests/
git commit -m "feat: add backend test structure with conftest"
```

---

### Task 11: Frontend initialization with bun

**Files:**
- Create: `frontend/` — full Next.js project

**Step 1: Create Next.js project with bun**

```bash
cd /Users/aa/WorkSpace/Projects/Sisyphus-case-platform
bunx create-next-app@latest frontend --typescript --tailwind --eslint=false --app --src-dir --import-alias="@/*" --use-bun
```

**Step 2: Remove default ESLint config (we use Biome)**

```bash
rm -f frontend/.eslintrc.json frontend/eslint.config.mjs
```

**Step 3: Install additional dependencies**

```bash
cd frontend && bun add antd @ant-design/icons zustand @tanstack/react-query
```

**Step 4: Install Biome as dev dependency**

```bash
cd frontend && bun add -d @biomejs/biome
```

**Step 5: Create biome.json**

```json
{
  "$schema": "https://biomejs.dev/schemas/2.0.0/schema.json",
  "organizeImports": { "enabled": true },
  "linter": {
    "enabled": true,
    "rules": { "recommended": true }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": { "quoteStyle": "single", "semicolons": "always" }
  }
}
```

**Step 6: Verify**

```bash
cd frontend && bunx biome check . && bun run build
```

Expected: Build succeeds.

**Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: initialize frontend with Next.js 14, Tailwind, Ant Design, Biome"
```

---

### Task 12: Frontend app structure — layouts and page skeletons

**Files:**
- Create/Modify: `frontend/src/app/layout.tsx` (root layout)
- Create: `frontend/src/app/(auth)/login/page.tsx`
- Create: `frontend/src/app/(main)/layout.tsx`
- Create: `frontend/src/app/(main)/products/page.tsx`
- Create: All other page skeletons under `(main)/`

**Step 1: Update root layout.tsx**

```tsx
import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Sisyphus Case Platform',
  description: 'AI-driven enterprise test case generation platform',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
```

**Step 2: Create auth pages**

`frontend/src/app/(auth)/login/page.tsx`:
```tsx
export default function LoginPage() {
  return <div>Login</div>;
}
```

**Step 3: Create main layout**

`frontend/src/app/(main)/layout.tsx`:
```tsx
export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside style={{ width: 240, borderRight: '1px solid #f0f0f0' }}>Sidebar</aside>
      <main style={{ flex: 1, padding: 24 }}>{children}</main>
    </div>
  );
}
```

**Step 4: Create all page skeletons**

For each page, create a minimal `page.tsx`:

```tsx
export default function <PageName>Page() {
  return <div><PageName></div>;
}
```

Pages to create:
- `(main)/products/page.tsx`
- `(main)/iterations/page.tsx`
- `(main)/requirements/page.tsx`
- `(main)/diagnosis/page.tsx`
- `(main)/scene-map/page.tsx`
- `(main)/workbench/page.tsx`
- `(main)/testcases/page.tsx`
- `(main)/diff/page.tsx`
- `(main)/coverage/page.tsx`
- `(main)/knowledge/page.tsx`
- `(main)/analytics/page.tsx`
- `(main)/settings/page.tsx`

**Step 5: Verify build**

```bash
cd frontend && bun run build
```

Expected: Build succeeds.

**Step 6: Commit**

```bash
git add frontend/src/app/
git commit -m "feat: add frontend page structure with layouts and skeletons"
```

---

### Task 13: Frontend shared infrastructure (components, hooks, lib, stores, types)

**Files:**
- Create: `frontend/src/components/ui/.gitkeep`
- Create: `frontend/src/components/layout/.gitkeep`
- Create: `frontend/src/components/editor/.gitkeep`
- Create: `frontend/src/components/scene-map/.gitkeep`
- Create: `frontend/src/components/diff-viewer/.gitkeep`
- Create: `frontend/src/hooks/use-sse.ts`
- Create: `frontend/src/lib/api-client.ts`
- Create: `frontend/src/lib/constants.ts`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/stores/auth-store.ts`
- Create: `frontend/src/stores/workspace-store.ts`
- Create: `frontend/src/types/api.ts`
- Create: `frontend/src/types/models.ts`

**Step 1: Create lib/api-client.ts**

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api';

export async function apiClient<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
```

**Step 2: Create lib/constants.ts**

```typescript
export const APP_NAME = 'Sisyphus Case Platform';
```

**Step 3: Create lib/utils.ts**

```typescript
export function cn(...classes: (string | undefined | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
```

**Step 4: Create hooks/use-sse.ts**

```typescript
'use client';

import { useCallback, useRef, useState } from 'react';

export function useSSE<T>() {
  const [data, setData] = useState<T[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);

  const start = useCallback((url: string) => {
    setIsStreaming(true);
    setData([]);
    const source = new EventSource(url);
    sourceRef.current = source;
    source.onmessage = (event) => {
      const parsed = JSON.parse(event.data) as T;
      setData((prev) => [...prev, parsed]);
    };
    source.onerror = () => {
      source.close();
      setIsStreaming(false);
    };
  }, []);

  const stop = useCallback(() => {
    sourceRef.current?.close();
    setIsStreaming(false);
  }, []);

  return { data, isStreaming, start, stop };
}
```

**Step 5: Create stores/auth-store.ts**

```typescript
import { create } from 'zustand';

interface AuthState {
  token: string | null;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  setToken: (token) => set({ token }),
  logout: () => set({ token: null }),
}));
```

**Step 6: Create stores/workspace-store.ts**

```typescript
import { create } from 'zustand';

interface WorkspaceState {
  selectedProductId: string | null;
  selectedIterationId: string | null;
  setProduct: (id: string | null) => void;
  setIteration: (id: string | null) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  selectedProductId: null,
  selectedIterationId: null,
  setProduct: (id) => set({ selectedProductId: id }),
  setIteration: (id) => set({ selectedIterationId: id }),
}));
```

**Step 7: Create types/models.ts**

```typescript
export interface Product {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Iteration {
  id: string;
  product_id: string;
  name: string;
  start_date: string | null;
  end_date: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Requirement {
  id: string;
  iteration_id: string;
  req_id: string;
  title: string;
  status: string;
  version: number;
  created_at: string;
  updated_at: string;
}
```

**Step 8: Create types/api.ts**

```typescript
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
}
```

**Step 9: Create .gitkeep files for component directories**

```bash
mkdir -p frontend/src/components/{ui,layout,editor,scene-map,diff-viewer}
touch frontend/src/components/{ui,layout,editor,scene-map,diff-viewer}/.gitkeep
```

**Step 10: Verify**

```bash
cd frontend && bunx biome check src/ && bun run build
```

Expected: Pass.

**Step 11: Commit**

```bash
git add frontend/src/
git commit -m "feat: add frontend shared infrastructure (hooks, lib, stores, types, components)"
```

---

### Task 14: Docker Compose setup

**Files:**
- Create: `docker/docker-compose.yml`
- Create: `docker/Dockerfile.backend`

**Step 1: Create docker-compose.yml**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: sisyphus
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:6333/readyz || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  minio_data:
```

**Step 2: Create Dockerfile.backend**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 3: Commit**

```bash
git add docker/
git commit -m "feat: add Docker Compose (postgres, redis, qdrant, minio) and backend Dockerfile"
```

---

### Task 15: GitHub Actions CI workflows

**Files:**
- Create: `.github/workflows/ci-backend.yml`
- Create: `.github/workflows/ci-frontend.yml`
- Create: `.github/workflows/ci-docs.yml`

**Step 1: Create ci-backend.yml**

```yaml
name: CI Backend

on:
  push:
    paths: ["backend/**"]
  pull_request:
    paths: ["backend/**"]

defaults:
  run:
    working-directory: backend

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Ruff lint
        run: uv run ruff check .

      - name: Ruff format check
        run: uv run ruff format --check .

      - name: Pyright type check
        run: uv run pyright app/

      - name: Run tests
        run: uv run pytest --cov=app --cov-report=term-missing -v
```

**Step 2: Create ci-frontend.yml**

```yaml
name: CI Frontend

on:
  push:
    paths: ["frontend/**"]
  pull_request:
    paths: ["frontend/**"]

defaults:
  run:
    working-directory: frontend

jobs:
  lint-and-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest

      - name: Install dependencies
        run: bun install --frozen-lockfile

      - name: Biome check
        run: bunx biome check .

      - name: TypeScript check
        run: bun run tsc --noEmit

      - name: Build
        run: bun run build
```

**Step 3: Create ci-docs.yml**

```yaml
name: CI Docs

on:
  pull_request:
    branches: [main]

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check documentation updates
        run: |
          CHANGED=$(git diff --name-only origin/main...HEAD)
          HAS_CODE=$(echo "$CHANGED" | grep -E '^(backend|frontend)/' || true)
          HAS_DOCS=$(echo "$CHANGED" | grep -E '^(docs/|README\.md|CHANGELOG\.md)' || true)

          if [ -n "$HAS_CODE" ] && [ -z "$HAS_DOCS" ]; then
            echo "::warning::Code changes detected but no documentation updated. Consider updating docs/, README.md, or CHANGELOG.md."
          fi

      - uses: DavidAnson/markdownlint-cli2-action@v19
        with:
          globs: |
            README.md
            CHANGELOG.md
            docs/**/*.md
```

**Step 4: Commit**

```bash
git add .github/
git commit -m "ci: add GitHub Actions workflows for backend, frontend, and docs"
```

---

### Task 16: CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

**Step 1: Create CLAUDE.md**

(Content as designed in Part 5 of the design document — full project context + development standards + common commands.)

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md with project context and development guidelines"
```

---

### Task 17: CHANGELOG.md

**Files:**
- Create: `CHANGELOG.md`

**Step 1: Create CHANGELOG.md**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Project scaffolding: backend (FastAPI + DDD modules) and frontend (Next.js 14)
- Development toolchain: uv, ruff, pyright, Biome
- Docker Compose for local infrastructure (PostgreSQL, Redis, Qdrant, MinIO)
- GitHub Actions CI: backend, frontend, docs workflows
- CLAUDE.md development guidelines
- init.sh one-click development environment setup
```

**Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add CHANGELOG.md"
```

---

### Task 18: init.sh

**Files:**
- Create: `init.sh`

**Step 1: Create init.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ─── 1. Check dependencies ───────────────────────────────────────
info "Checking dependencies..."

command -v uv    >/dev/null 2>&1 || error "uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
command -v bun   >/dev/null 2>&1 || error "bun not found. Install: curl -fsSL https://bun.sh/install | bash"
command -v docker >/dev/null 2>&1 || error "docker not found. Install Docker Desktop."
docker compose version >/dev/null 2>&1 || error "docker compose not found."

info "All dependencies found."

# ─── 2. Check ports ──────────────────────────────────────────────
for port in 5432 6379 6333 9000 8000 3000; do
  if lsof -i :"$port" >/dev/null 2>&1; then
    warn "Port $port is already in use."
  fi
done

# ─── 3. Environment config ───────────────────────────────────────
if [ ! -f "$PROJECT_DIR/.env" ]; then
  info "Creating .env from .env.example..."
  cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
  warn "Please edit .env to set your OPENAI_API_KEY (optional for Ollama mode)."
fi

# ─── 4. Install dependencies ─────────────────────────────────────
info "Installing backend dependencies..."
cd "$PROJECT_DIR/backend" && uv sync --all-extras

info "Installing frontend dependencies..."
cd "$PROJECT_DIR/frontend" && bun install

# ─── 5. Start infrastructure ─────────────────────────────────────
info "Starting Docker services..."
cd "$PROJECT_DIR"
docker compose -f docker/docker-compose.yml up -d

info "Waiting for services to be healthy..."
sleep 5

# Wait for PostgreSQL
until docker compose -f docker/docker-compose.yml exec -T postgres pg_isready -U postgres >/dev/null 2>&1; do
  sleep 1
done
info "PostgreSQL is ready."

# ─── 6. Initialize database ──────────────────────────────────────
info "Running database migrations..."
cd "$PROJECT_DIR/backend" && uv run alembic upgrade head

info "Seeding database..."
cd "$PROJECT_DIR/backend" && uv run python scripts/seed.py

# ─── 7. Start dev servers ────────────────────────────────────────
info "Starting backend server..."
cd "$PROJECT_DIR/backend" && uv run uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

info "Starting Celery worker..."
cd "$PROJECT_DIR/backend" && uv run celery -A app.worker.celery_app worker --loglevel=info &
CELERY_PID=$!

# Cleanup on exit
cleanup() {
  info "Shutting down..."
  kill "$BACKEND_PID" "$CELERY_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo ""
info "==================================="
info "  Sisyphus Case Platform is ready!"
info "==================================="
info "  Frontend:  http://localhost:3000"
info "  Backend:   http://localhost:8000"
info "  API Docs:  http://localhost:8000/docs"
info "  MinIO:     http://localhost:9001"
info "==================================="
echo ""

info "Starting frontend (Ctrl+C to stop all)..."
cd "$PROJECT_DIR/frontend" && bun dev
```

**Step 2: Make executable**

```bash
chmod +x init.sh
```

**Step 3: Commit**

```bash
git add init.sh
git commit -m "feat: add init.sh one-click development environment setup"
```

---

### Task 19: Update README.md

**Files:**
- Modify: `README.md`

**Step 1: Add new modules to the module table (M16-M21)**

Insert after M15 row:

```markdown
| **M16** | 通知系统 | 站内信、邮件、钉钉/飞书 Webhook 通知推送 | `P1` |
| **M17** | 全局搜索 | 跨需求/测试点/用例全文检索（PostgreSQL FTS + Qdrant 语义搜索） | `P1` |
| **M18** | 协作功能 | 评论、@提及、测试点多人评审 | `P2` |
| **M19** | 首页仪表盘 | 迭代概览、待办事项、生成质量趋势 | `P1` |
| **M20** | 操作审计日志 | 全局操作记录、数据变更追踪 | `P1` |
| **M21** | 回收站 | 软删除、误删恢复、定期清理 | `P2` |
```

**Step 2: Update tech stack — add toolchain section**

In the backend tech table, add:

```markdown
| **uv** | latest | Python 环境与依赖管理 |
| **ruff** | 0.8+ | Lint + Format（替代 flake8/black/isort） |
| **pyright** | 1.1+ | 静态类型检查（standard 模式） |
```

In the frontend tech table, add:

```markdown
| **Biome** | 2+ | Lint + Format（替代 ESLint + Prettier） |
| **bun** | latest | 包管理 + 运行时 |
```

**Step 3: Update Python badge to 3.12+**

Change the Python badge from `3.12+` (already correct) and fix the quick start section.

**Step 4: Update quick start section**

Replace `pip install -r requirements.txt` with:
```bash
cd backend && uv sync --all-extras
```

Replace `npm install && npm run dev` with:
```bash
cd frontend && bun install && bun dev
```

**Step 5: Add audit_logs and notifications to data model section**

Add the `audit_logs` and `notifications` CREATE TABLE statements.

Add `deleted_at TIMESTAMPTZ DEFAULT NULL` comment noting all tables support soft delete.

**Step 6: Commit**

```bash
git add README.md
git commit -m "docs: update README with new modules (M16-M21), toolchain, and data models"
```

---

### Task 20: Create docs directory structure

**Files:**
- Create: `docs/api/.gitkeep`
- Create: `docs/architecture/.gitkeep`
- Create: `tests/.gitkeep` (root E2E tests)

**Step 1: Create directories**

```bash
mkdir -p docs/api docs/architecture tests
touch docs/api/.gitkeep docs/architecture/.gitkeep tests/.gitkeep
```

**Step 2: Commit**

```bash
git add docs/ tests/.gitkeep
git commit -m "docs: add docs and tests directory structure"
```

---

### Task 21: Final verification

**Step 1: Run full backend checks**

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run pyright app/ && uv run pytest -v
```

Expected: All pass.

**Step 2: Run full frontend checks**

```bash
cd frontend && bunx biome check . && bun run tsc --noEmit && bun run build
```

Expected: All pass.

**Step 3: Verify project structure**

```bash
find . -type f -not -path './.git/*' -not -path './backend/.venv/*' -not -path './frontend/node_modules/*' -not -path './frontend/.next/*' | sort
```

Verify all expected files exist.

**Step 4: Final commit (if any remaining changes)**

```bash
git status
# If clean, done. If changes remain:
git add -A && git commit -m "chore: final scaffold cleanup"
```
