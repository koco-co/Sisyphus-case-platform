# 后端基础架构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 搭建 FastAPI 后端基础架构，包括数据库连接、项目结构、配置管理

**Architecture:**
- 使用 FastAPI 作为 Web 框架
- PostgreSQL + pgvector 作为数据存储
- SQLAlchemy 2.0 async 作为 ORM
- Pydantic v2 进行数据验证
- uv 作为依赖管理工具

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, uv, PostgreSQL, pgvector

---

## Task 1: 初始化后端项目结构

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/README.md`

**Step 1: 创建项目目录结构**

```bash
mkdir -p backend/app/{api,agents,plugins,rag,llm,models}
mkdir -p backend/app/tests
mkdir -p backend/skills
cd backend
```

**Step 2: 配置 uv 和 pyproject.toml**

创建 `backend/pyproject.toml`:

```toml
[project]
name = "sisyphus-backend"
version = "0.1.0"
description = "Sisyphus 测试用例生成平台 - 后端"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "asyncpg>=0.29.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
    "sentence-transformers>=2.3.1",
    "pypdf>=4.0.0",
    "openai>=1.10.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.26.0",
    "black>=23.12.0",
    "ruff>=0.1.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.26.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Step 3: 创建环境变量模板**

创建 `backend/.env.example`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://sisyphus:password@localhost:5432/sisyphus

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# JWT
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=30

# LLM (用户配置)
# 默认使用环境变量，用户可在界面中配置
DEFAULT_LLM_PROVIDER=glm
DEFAULT_LLM_API_KEY=your-api-key-here
```

**Step 4: 创建 README**

创建 `backend/README.md`:

```markdown
# Sisyphus Backend

测试用例生成平台后端服务。

## 开发环境设置

```bash
# 使用 uv 安装依赖
uv sync

# 复制环境变量
cp .env.example .env

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 运行测试

```bash
uv run pytest
```
```

**Step 5: 初始化 uv 项目**

```bash
cd backend
uv sync
```

**Step 6: Commit**

```bash
git add backend/
git commit -m "feat: 初始化后端项目结构和依赖配置"
```

---

## Task 2: 配置数据库连接

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/config.py`

**Step 1: Write failing test for database connection**

创建 `backend/app/tests/test_database.py`:

```python
import pytest
from app.database import get_db

@pytest.mark.asyncio
async def test_database_connection():
    """测试数据库连接是否正常"""
    async for db in get_db():
        result = await db.execute("SELECT 1")
        assert result.scalar() == 1
        break
```

**Step 2: Run test to verify it fails**

```bash
cd backend
uv run pytest app/tests/test_database.py::test_database_connection -v
```

Expected: FAIL with "module 'app.database' not found"

**Step 3: Implement database configuration**

创建 `backend/app/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://sisyphus:password@localhost:5432/sisyphus"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

创建 `backend/app/database.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session
```

**Step 4: Run test to verify it passes**

```bash
# 先启动 PostgreSQL (如果没有 Docker)
docker run -d --name sisyphus-db \
  -e POSTGRES_DB=sisyphus \
  -e POSTGRES_USER=sisyphus \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 等待数据库启动后运行测试
uv run pytest app/tests/test_database.py::test_database_connection -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/
git commit -m "feat: 配置数据库连接和设置管理"
```

---

## Task 3: 创建数据模型

**Files:**
- Create: `backend/app/models/project.py`
- Create: `backend/app/models/test_case.py`
- Create: `backend/app/models/user_config.py`

**Step 1: Write failing test for Project model**

创建 `backend/app/tests/test_models.py`:

```python
import pytest
from sqlalchemy import select
from app.models.project import Project
from app.database import async_session

@pytest.mark.asyncio
async def test_create_project():
    """测试创建项目"""
    async with async_session() as db:
        project = Project(name="登录模块", description="用户登录功能")
        db.add(project)
        await db.commit()
        await db.refresh(project)

        assert project.id is not None
        assert project.name == "登录模块"
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_models.py::test_create_project -v
```

Expected: FAIL with "module 'app.models.project' not found"

**Step 3: Implement Project model**

创建 `backend/app/models/__init__.py`:

```python
from app.models.project import Project
from app.models.test_case import TestCase
from app.models.user_config import UserConfig
```

创建 `backend/app/models/project.py`:

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    parent = relationship("Project", remote_side=[id], backref="children")
    test_cases = relationship("TestCase", back_populates="project")
```

**Step 4: Implement TestCase model**

创建 `backend/app/models/test_case.py`:

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    module = Column(String(255), nullable=True)
    title = Column(String(500), nullable=False)
    prerequisites = Column(Text, nullable=True)
    steps = Column(Text, nullable=False)
    expected_results = Column(Text, nullable=False)
    keywords = Column(Text, nullable=True)
    priority = Column(String(50), default="2")
    case_type = Column(String(50), default="功能测试")
    stage = Column(String(50), default="功能测试阶段")
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    project = relationship("Project", back_populates="test_cases")
```

**Step 5: Implement UserConfig model**

创建 `backend/app/models/user_config.py`:

```python
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class UserConfig(Base):
    __tablename__ = "user_configs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False)
    api_key_encrypted = Column(String(500), nullable=False)
    generator_model = Column(String(100), nullable=True)
    reviewer_model = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Step 6: Run tests**

```bash
uv run pytest app/tests/test_models.py -v
```

Expected: All PASS

**Step 7: Commit**

```bash
git add backend/app/models/
git commit -m "feat: 创建数据模型 (Project, TestCase, UserConfig)"
```

---

## Task 4: 创建数据库初始化脚本

**Files:**
- Create: `backend/app/init_db.py`

**Step 1: Create database initialization script**

创建 `backend/app/init_db.py`:

```python
import asyncio
from app.database import engine, Base
from app.models import Project, TestCase, UserConfig

async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        # 启用 pgvector 扩展
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

    print("✅ 数据库初始化完成")

if __name__ == "__main__":
    asyncio.run(init_db())
```

**Step 2: Test initialization**

```bash
cd backend
uv run python app/init_db.py
```

Expected: "✅ 数据库初始化完成"

**Step 3: Verify tables created**

```bash
# 连接数据库验证
psql postgresql://sisyphus:password@localhost:5432/sisyphus -c "\dt"
```

Expected output:
```
          List of relations
 Schema |     Name      | Type  |   Owner
--------+---------------+-------+----------
 public | projects      | table | sisyphus
 public | test_cases    | table | sisyphus
 public | user_configs  | table | sisyphus
```

**Step 4: Commit**

```bash
git add backend/app/init_db.py
git commit -m "feat: 添加数据库初始化脚本"
```

---

## Task 5: 创建 FastAPI 主应用

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/__init__.py`

**Step 1: Write failing test for API root**

创建 `backend/app/tests/test_main.py`:

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_api_root():
    """测试 API 根路径"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert "Sisyphus" in response.json()["message"]
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_main.py::test_api_root -v
```

Expected: FAIL with "module 'app.main' not found"

**Step 3: Implement FastAPI main application**

创建 `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title="Sisyphus API",
    description="测试用例生成平台 API",
    version="0.1.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Sisyphus 测试用例生成平台 API",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 4: Run tests**

```bash
uv run pytest app/tests/test_main.py::test_api_root -v
```

Expected: PASS

**Step 5: Test running the server**

```bash
# 新终端启动服务器
uvicorn app.main:app --reload

# 另一个终端测试
curl http://localhost:8000/
```

Expected: JSON response with "Sisyphus" in message

**Step 6: Commit**

```bash
git add backend/app/main.py backend/app/api/
git commit -m "feat: 创建 FastAPI 主应用和基础路由"
```

---

## Task 6: 创建项目 CRUD API

**Files:**
- Create: `backend/app/api/projects.py`
- Modify: `backend/app/main.py`

**Step 1: Write failing test for creating project**

创建 `backend/app/tests/test_projects_api.py`:

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_project():
    """测试创建项目"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
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
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_projects_api.py::test_create_project -v
```

Expected: FAIL with "404 Not Found"

**Step 3: Implement Projects API**

创建 `backend/app/api/projects.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.project import Project

router = APIRouter(prefix="/api/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建项目"""
    db_project = Project(**project.dict())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project

@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取项目列表"""
    result = await db.execute(
        select(Project).offset(skip).limit(limit)
    )
    projects = result.scalars().all()
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取项目详情"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project
```

**Step 4: Register router in main app**

修改 `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import projects  # 添加这行

app = FastAPI(
    title="Sisyphus API",
    description="测试用例生成平台 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)  # 添加这行

@app.get("/")
async def root():
    return {
        "message": "Sisyphus 测试用例生成平台 API",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 5: Run tests**

```bash
uv run pytest app/tests/test_projects_api.py -v
```

Expected: All PASS

**Step 6: Commit**

```bash
git add backend/app/api/projects.py backend/app/main.py
git commit -m "feat: 实现项目 CRUD API"
```

---

## Task 7: 创建测试用例 CRUD API

**Files:**
- Create: `backend/app/api/cases.py`
- Modify: `backend/app/main.py`

**Step 1: Write failing test for creating test case**

创建 `backend/app/tests/test_cases_api.py`:

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_test_case():
    """测试创建测试用例"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 先创建项目
        project_response = await ac.post(
            "/api/projects/",
            json={"name": "登录模块"}
        )
        project_id = project_response.json()["id"]

        # 创建测试用例
        response = await ac.post(
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
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "测试用户名密码登录"
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_cases_api.py::test_create_test_case -v
```

Expected: FAIL with "404 Not Found"

**Step 3: Implement Test Cases API**

创建 `backend/app/api/cases.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.test_case import TestCase

router = APIRouter(prefix="/api/cases", tags=["cases"])

class TestCaseCreate(BaseModel):
    project_id: int
    module: Optional[str] = None
    title: str
    prerequisites: Optional[str] = None
    steps: str
    expected_results: str
    keywords: Optional[str] = None
    priority: str = "2"
    case_type: str = "功能测试"
    stage: str = "功能测试阶段"

class TestCaseResponse(BaseModel):
    id: int
    project_id: int
    module: Optional[str]
    title: str
    prerequisites: Optional[str]
    steps: str
    expected_results: str
    keywords: Optional[str]
    priority: str
    case_type: str
    stage: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=TestCaseResponse)
async def create_test_case(
    case: TestCaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建测试用例"""
    db_case = TestCase(**case.dict())
    db.add(db_case)
    await db.commit()
    await db.refresh(db_case)
    return db_case

@router.get("/", response_model=list[TestCaseResponse])
async def list_test_cases(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取测试用例列表"""
    query = select(TestCase)
    if project_id:
        query = query.where(TestCase.project_id == project_id)
    if status:
        query = query.where(TestCase.status == status)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    cases = result.scalars().all()
    return cases

@router.get("/{case_id}", response_model=TestCaseResponse)
async def get_test_case(
    case_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取测试用例详情"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    return case

@router.put("/{case_id}", response_model=TestCaseResponse)
async def update_test_case(
    case_id: int,
    case_update: TestCaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """更新测试用例"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id)
    )
    db_case = result.scalar_one_or_none()
    if not db_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")

    for key, value in case_update.dict().items():
        setattr(db_case, key, value)

    await db.commit()
    await db.refresh(db_case)
    return db_case

@router.patch("/{case_id}/status")
async def update_case_status(
    case_id: int,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """更新测试用例状态（审批通过/拒绝）"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id)
    )
    db_case = result.scalar_one_or_none()
    if not db_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")

    if status not in ["pending", "approved", "rejected"]:
        raise HTTPException(status_code=400, detail="无效的状态值")

    db_case.status = status
    await db.commit()
    return {"message": f"测试用例状态已更新为 {status}"}
```

**Step 4: Register router in main app**

修改 `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import projects, cases  # 添加 cases

app = FastAPI(
    title="Sisyphus API",
    description="测试用例生成平台 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(cases.router)  # 添加这行

@app.get("/")
async def root():
    return {
        "message": "Sisyphus 测试用例生成平台 API",
        "version": "0.1.0",
        "status": "running"
    }
```

**Step 5: Run tests**

```bash
uv run pytest app/tests/test_cases_api.py -v
```

Expected: All PASS

**Step 6: Commit**

```bash
git add backend/app/api/cases.py backend/app/main.py
git commit -m "feat: 实现测试用例 CRUD API"
```

---

## Task 8: 添加 Docker 配置

**Files:**
- Create: `backend/Dockerfile`
- Create: `docker-compose.yml`
- Modify: `backend/.gitignore`

**Step 1: Create backend Dockerfile**

创建 `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 复制依赖文件
COPY pyproject.toml ./

# 安装依赖
RUN uv sync --frozen

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Create docker-compose.yml**

在项目根目录创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: sisyphus-db
    environment:
      POSTGRES_DB: sisyphus
      POSTGRES_USER: sisyphus
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sisyphus"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: sisyphus-backend
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://sisyphus:password@postgres:5432/sisyphus
      API_HOST: 0.0.0.0
      API_PORT: 8000
      DEBUG: "True"
    ports:
      - "8000:8000"
    volumes:
      - ./backend/skills:/app/skills

volumes:
  postgres_data:
```

**Step 3: Add .gitignore**

创建 `backend/.gitignore`:

```
__pycache__/
*.pyc
.env
.venv/
.pytest_cache/
.coverage
dist/
```

**Step 4: Test Docker build**

```bash
docker-compose up backend
```

Expected: Backend starts successfully and connects to database

**Step 5: Commit**

```bash
git add backend/Dockerfile docker-compose.yml backend/.gitignore
git commit -m "feat: 添加 Docker 配置"
```

---

## 完成检查清单

- [ ] 所有测试通过
- [ ] 数据库表创建成功
- [ ] API 端点正常工作
- [ ] Docker 构建成功
- [ ] 代码符合项目规范（使用 ruff 和 black）

## 下一步

继续实施：
- `2026-03-04-02-llm-integration.md` - LLM 接入层
- `2026-03-04-03-vector-rag.md` - 向量检索和 RAG
- `2026-03-04-04-agent-system.md` - Agent 系统
- `2026-03-04-05-document-parsers.md` - 文档解析插件
