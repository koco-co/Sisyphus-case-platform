# 前端重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将测试用例平台重构为 Gemini/DeepSeek 风格的聊天式交互界面

**Architecture:** 单页应用 + 路由下钻结构。左侧项目树导航，右侧聊天区。保留后端核心逻辑（Agent、RAG、解析器），重构 API 层和数据模型。

**Tech Stack:** React 18 + Vite + TypeScript + Ant Design + TailwindCSS (前端), FastAPI + SQLAlchemy (后端), PostgreSQL + pgvector (数据库)

---

## Phase 1: 基础架构重构

### Task 1: 数据库迁移 - 新表结构

**Files:**
- Create: `backend/app/migrations/versions/001_redesign_schema.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: 创建迁移脚本**

```python
# backend/app/migrations/versions/001_redesign_schema.py
"""redesign schema

Revision ID: 001_redesign
Revises:
Create Date: 2026-03-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_redesign'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 文件表
    op.create_table(
        'files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_name', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('size', sa.BigInteger),
        sa.Column('storage_type', sa.String(20), server_default='local'),
        sa.Column('storage_path', sa.String(500)),
        sa.Column('parsed_content', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # 需求表
    op.create_table(
        'requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', postgresql.JSONB, server_default='{}'),
        sa.Column('source_file_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('files.id')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # 测试用例表（重构）
    op.create_table(
        'test_cases_new',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('requirements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('priority', sa.String(10), server_default='P2'),
        sa.Column('preconditions', sa.Text),
        sa.Column('steps', postgresql.JSONB, server_default='[]'),
        sa.Column('tags', postgresql.ARRAY(sa.Text), server_default='{}'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # 导出模板表
    op.create_table(
        'export_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('field_config', postgresql.JSONB, server_default='{}'),
        sa.Column('format_config', postgresql.JSONB, server_default='{}'),
        sa.Column('filter_config', postgresql.JSONB, server_default='{}'),
        sa.Column('is_default', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # 对话历史表
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('requirements.id', ondelete='CASCADE')),
        sa.Column('messages', postgresql.JSONB, server_default='[]'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # 用户配置表
    op.create_table(
        'user_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('llm_config', postgresql.JSONB, server_default='{}'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('user_configs')
    op.drop_table('conversations')
    op.drop_table('export_templates')
    op.drop_table('test_cases_new')
    op.drop_table('requirements')
    op.drop_table('files')
```

**Step 2: 运行迁移**

```bash
cd backend && alembic upgrade head
```

**Step 3: 验证表结构**

```bash
psql -U postgres -d sisyphus -c "\dt"
```

预期输出应包含：files, requirements, test_cases_new, export_templates, conversations, user_configs

---

### Task 2: 数据模型定义

**Files:**
- Create: `backend/app/models/file.py`
- Create: `backend/app/models/requirement.py`
- Create: `backend/app/models/test_case.py`
- Create: `backend/app/models/export_template.py`
- Create: `backend/app/models/conversation.py`
- Create: `backend/app/models/user_config.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: 创建 File 模型**

```python
# backend/app/models/file.py
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    size: Mapped[int | None] = mapped_column(BigInteger)
    storage_type: Mapped[str] = mapped_column(String(20), default="local")
    storage_path: Mapped[str | None] = mapped_column(String(500))
    parsed_content: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**Step 2: 创建 Requirement 模型**

```python
# backend/app/models/requirement.py
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, default=dict)
    source_file_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("files.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="requirements")
    test_cases: Mapped[list["TestCase"]] = relationship("TestCase", back_populates="requirement", cascade="all, delete-orphan")
    conversation: Mapped["Conversation | None"] = relationship("Conversation", back_populates="requirement", uselist=False)
```

**Step 3: 创建 TestCase 模型**

```python
# backend/app/models/test_case.py
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class TestCase(Base):
    __tablename__ = "test_cases_new"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="P2")
    preconditions: Mapped[str | None] = mapped_column(Text)
    steps: Mapped[list] = mapped_column(JSONB, default=list)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    requirement: Mapped["Requirement"] = relationship("Requirement", back_populates="test_cases")
```

**Step 4: 创建 ExportTemplate 模型**

```python
# backend/app/models/export_template.py
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ExportTemplate(Base):
    __tablename__ = "export_templates"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    field_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    format_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    filter_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**Step 5: 创建 Conversation 模型**

```python
# backend/app/models/conversation.py
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"))
    messages: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    requirement: Mapped["Requirement | None"] = relationship("Requirement", back_populates="conversation")
```

**Step 6: 创建 UserConfig 模型**

```python
# backend/app/models/user_config.py
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class UserConfig(Base):
    __tablename__ = "user_configs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    llm_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Step 7: 更新 __init__.py**

```python
# backend/app/models/__init__.py
from .file import File
from .requirement import Requirement
from .test_case import TestCase
from .export_template import ExportTemplate
from .conversation import Conversation
from .user_config import UserConfig
from .project import Project  # 保留

__all__ = [
    "File",
    "Requirement",
    "TestCase",
    "ExportTemplate",
    "Conversation",
    "UserConfig",
    "Project",
]
```

**Step 8: 验证模型导入**

```bash
cd backend && python -c "from app.models import *; print('Models imported successfully')"
```

---

### Task 3: 文件存储服务

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/storage.py`
- Create: `backend/app/tests/test_storage.py`

**Step 1: 创建存储服务接口**

```python
# backend/app/services/storage.py
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import UUID

from ..config import settings


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    async def save(self, file_id: UUID, file_data: BinaryIO, filename: str) -> str:
        """保存文件，返回存储路径"""
        pass

    @abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """读取文件内容"""
        pass

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """删除文件"""
        pass

    @abstractmethod
    async def exists(self, storage_path: str) -> bool:
        """检查文件是否存在"""
        pass


class LocalStorage(StorageBackend):
    """本地文件系统存储"""

    def __init__(self, base_path: str = "./uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, file_id: UUID, file_data: BinaryIO, filename: str) -> str:
        # 按年月组织目录
        subdir = self.base_path / file_id.hex[:2]
        subdir.mkdir(parents=True, exist_ok=True)

        storage_path = subdir / f"{file_id.hex}_{filename}"
        with open(storage_path, "wb") as f:
            shutil.copyfileobj(file_data, f)

        return str(storage_path)

    async def read(self, storage_path: str) -> bytes:
        with open(storage_path, "rb") as f:
            return f.read()

    async def delete(self, storage_path: str) -> None:
        Path(storage_path).unlink(missing_ok=True)

    async def exists(self, storage_path: str) -> bool:
        return Path(storage_path).exists()


class MinioStorage(StorageBackend):
    """MinIO 对象存储"""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        from minio import Minio

        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        self.bucket = bucket
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    async def save(self, file_id: UUID, file_data: BinaryIO, filename: str) -> str:
        object_name = f"{file_id.hex}/{filename}"
        file_data.seek(0, 2)
        size = file_data.tell()
        file_data.seek(0)

        self.client.put_object(self.bucket, object_name, file_data, size)
        return object_name

    async def read(self, storage_path: str) -> bytes:
        response = self.client.get_object(self.bucket, storage_path)
        return response.read()

    async def delete(self, storage_path: str) -> None:
        self.client.remove_object(self.bucket, storage_path)

    async def exists(self, storage_path: str) -> bool:
        try:
            self.client.stat_object(self.bucket, storage_path)
            return True
        except Exception:
            return False


def get_storage_backend() -> StorageBackend:
    """根据配置获取存储后端"""
    storage_type = getattr(settings, 'STORAGE_TYPE', 'local')

    if storage_type == 'minio':
        return MinioStorage(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            bucket=settings.MINIO_BUCKET,
        )
    else:
        return LocalStorage(base_path=getattr(settings, 'UPLOAD_PATH', './uploads'))


# 全局存储实例
storage = get_storage_backend()
```

**Step 2: 编写测试**

```python
# backend/app/tests/test_storage.py
import pytest
from io import BytesIO
from uuid import uuid4

from app.services.storage import LocalStorage


@pytest.fixture
def local_storage(tmp_path):
    return LocalStorage(base_path=str(tmp_path / "uploads"))


@pytest.mark.asyncio
async def test_local_storage_save_and_read(local_storage):
    file_id = uuid4()
    content = b"test content"
    file_data = BytesIO(content)

    storage_path = await local_storage.save(file_id, file_data, "test.txt")
    assert await local_storage.exists(storage_path)

    read_content = await local_storage.read(storage_path)
    assert read_content == content


@pytest.mark.asyncio
async def test_local_storage_delete(local_storage):
    file_id = uuid4()
    content = b"test content"
    file_data = BytesIO(content)

    storage_path = await local_storage.save(file_id, file_data, "test.txt")
    assert await local_storage.exists(storage_path)

    await local_storage.delete(storage_path)
    assert not await local_storage.exists(storage_path)
```

**Step 3: 运行测试**

```bash
cd backend && pytest app/tests/test_storage.py -v
```

---

### Task 4: 文件上传 API（流式）

**Files:**
- Create: `backend/app/api/files.py`
- Create: `backend/app/schemas/file.py`
- Create: `backend/app/tests/test_files_api.py`

**Step 1: 创建文件 Schema**

```python
# backend/app/schemas/file.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FileBase(BaseModel):
    original_name: str
    mime_type: str | None = None
    size: int | None = None


class FileCreate(FileBase):
    pass


class FileResponse(FileBase):
    id: UUID
    filename: str
    storage_type: str
    storage_path: str | None
    parsed_content: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    file: FileResponse
    parsed_content: str  # 解析后的内容
```

**Step 2: 创建文件 API**

```python
# backend/app/api/files.py
import os
from io import BytesIO
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import File
from ..plugins.manager import ParserManager
from ..schemas.file import FileResponse, FileUploadResponse
from ..services.storage import storage

router = APIRouter(prefix="/files", tags=["files"])
parser_manager = ParserManager()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    db: AsyncSession = Depends(get_db),
):
    """上传文件并解析内容"""
    # 检查文件类型
    allowed_extensions = {".md", ".txt", ".pdf"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(400, f"不支持的文件类型: {ext}")

    # 检查文件大小 (10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "文件大小不能超过 10MB")

    # 创建文件记录
    db_file = File(
        filename=file.filename,
        original_name=file.filename,
        mime_type=file.content_type,
        size=len(content),
    )
    db.add(db_file)
    await db.flush()

    # 保存文件
    file_data = BytesIO(content)
    storage_path = await storage.save(db_file.id, file_data, file.filename)
    db_file.storage_type = "local" if isinstance(storage, LocalStorage) else "minio"
    db_file.storage_path = storage_path

    # 解析文件内容
    try:
        parser = parser_manager.get_parser(ext)
        parsed_content = await parser.parse(BytesIO(content))
        db_file.parsed_content = parsed_content
    except Exception as e:
        raise HTTPException(400, f"文件解析失败: {str(e)}")

    await db.commit()
    await db.refresh(db_file)

    return FileUploadResponse(
        file=FileResponse.model_validate(db_file),
        parsed_content=parsed_content,
    )


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(file_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取文件信息"""
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(404, "文件不存在")

    return FileResponse.model_validate(file)


@router.get("/{file_id}/content")
async def get_file_content(file_id: UUID, db: AsyncSession = Depends(get_db)):
    """流式获取文件内容"""
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(404, "文件不存在")

    if not file.parsed_content:
        raise HTTPException(404, "文件内容不存在")

    async def generate():
        # 分块流式返回
        chunk_size = 1024
        content = file.parsed_content
        for i in range(0, len(content), chunk_size):
            yield content[i : i + chunk_size]

    return StreamingResponse(generate(), media_type="text/plain")
```

**Step 3: 编写测试**

```python
# backend/app/tests/test_files_api.py
import pytest
from io import BytesIO
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_upload_txt_file(client):
    content = b"# Test Requirement\n\nThis is a test requirement document."
    file = ("test.txt", BytesIO(content), "text/plain")

    response = client.post(
        "/api/files/upload",
        files={"file": file},
    )

    assert response.status_code == 200
    data = response.json()
    assert "file" in data
    assert "parsed_content" in data
    assert data["file"]["original_name"] == "test.txt"


def test_upload_invalid_extension(client):
    content = b"test content"
    file = ("test.exe", BytesIO(content), "application/octet-stream")

    response = client.post(
        "/api/files/upload",
        files={"file": file},
    )

    assert response.status_code == 400
```

**Step 4: 运行测试**

```bash
cd backend && pytest app/tests/test_files_api.py -v
```

---

### Task 5: 前端路由和布局

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/components/Layout/AppLayout.tsx`
- Create: `frontend/src/pages/Home.tsx`
- Create: `frontend/src/stores/useAppStore.ts`

**Step 1: 创建全局状态 Store**

```typescript
// frontend/src/stores/useAppStore.ts
import { create } from 'zustand';

export interface Project {
  id: string;
  name: string;
  requirements: Requirement[];
}

export interface Requirement {
  id: string;
  title: string;
  projectId: string;
}

interface AppState {
  // 侧边栏状态
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // 当前选中
  selectedProjectId: string | null;
  selectedRequirementId: string | null;
  setSelectedProject: (id: string | null) => void;
  setSelectedRequirement: (id: string | null) => void;

  // 项目数据
  projects: Project[];
  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  selectedProjectId: null,
  selectedRequirementId: null,
  setSelectedProject: (id) => set({ selectedProjectId: id }),
  setSelectedRequirement: (id) => set({ selectedRequirementId: id }),

  projects: [],
  setProjects: (projects) => set({ projects }),
  addProject: (project) => set((state) => ({ projects: [...state.projects, project] })),
}));
```

**Step 2: 创建布局组件**

```typescript
// frontend/src/components/Layout/AppLayout.tsx
import { Outlet } from 'react-router-dom';
import { Layout } from 'antd';
import AppSidebar from './AppSidebar';

const { Content, Sider } = Layout;

export default function AppLayout() {
  const { sidebarCollapsed } = useAppStore();

  return (
    <Layout className="h-screen">
      <Sider
        collapsible
        collapsed={sidebarCollapsed}
        onCollapse={(collapsed) => useAppStore.getState().toggleSidebar()}
        width={280}
        className="bg-white border-r border-gray-200"
      >
        <AppSidebar />
      </Sider>
      <Content className="overflow-auto">
        <Outlet />
      </Content>
    </Layout>
  );
}
```

**Step 3: 更新 App.tsx 路由**

```typescript
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import AppLayout from './components/Layout/AppLayout';
import Home from './pages/Home';
import Requirement from './pages/Requirement';
import TestCase from './pages/TestCase';
import Settings from './pages/Settings';

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Home />} />
            <Route path="projects/:projectId" element={<Home />} />
            <Route path="requirements/:id" element={<Requirement />} />
            <Route path="testcases/:id" element={<TestCase />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}
```

**Step 4: 创建 Home 页面骨架**

```typescript
// frontend/src/pages/Home.tsx
export default function Home() {
  return (
    <div className="flex flex-col h-full">
      {/* 聊天区域 */}
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-800 mb-4">
            测试用例生成平台
          </h1>
          <p className="text-gray-500 mb-8">
            上传需求文档，自动生成功能测试用例
          </p>
        </div>
      </div>

      {/* 输入区域 */}
      <div className="p-4 border-t border-gray-200">
        {/* ChatInput 组件将在这里 */}
        <div className="max-w-3xl mx-auto">
          <div className="bg-gray-100 rounded-lg p-4 text-center text-gray-400">
            聊天输入框（待实现）
          </div>
        </div>
      </div>
    </div>
  );
}
```

**Step 5: 验证路由**

```bash
cd frontend && npm run dev
```

访问 http://localhost:5173 应该看到主页布局

---

## Phase 2: 核心功能实现

### Task 6: 侧边栏项目树

**Files:**
- Create: `frontend/src/components/Layout/AppSidebar.tsx`
- Create: `frontend/src/components/Layout/ProjectTree.tsx`
- Create: `frontend/src/hooks/useProjects.ts`

**Step 1: 创建项目 Hook**

```typescript
// frontend/src/hooks/useProjects.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../utils/api';

export interface Project {
  id: string;
  name: string;
  description?: string;
  requirements: Requirement[];
}

export interface Requirement {
  id: string;
  title: string;
  projectId: string;
}

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const response = await api.get<Project[]>('/projects');
      return response.data;
    },
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { name: string; description?: string }) => {
      const response = await api.post<Project>('/projects', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}
```

**Step 2: 创建项目树组件**

```typescript
// frontend/src/components/Layout/ProjectTree.tsx
import { Tree, Button } from 'antd';
import { FolderOutlined, FileTextOutlined, PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { TreeDataNode } from 'antd';

import { useProjects, useCreateProject } from '../../hooks/useProjects';

export default function ProjectTree() {
  const navigate = useNavigate();
  const { data: projects, isLoading } = useProjects();
  const createProject = useCreateProject();

  const treeData: TreeDataNode[] = (projects || []).map((project) => ({
    key: `project-${project.id}`,
    title: project.name,
    icon: <FolderOutlined />,
    children: project.requirements.map((req) => ({
      key: `requirement-${req.id}`,
      title: req.title,
      icon: <FileTextOutlined />,
      isLeaf: true,
    })),
  }));

  const handleSelect = (selectedKeys: React.Key[]) => {
    if (selectedKeys.length === 0) return;

    const key = selectedKeys[0] as string;
    if (key.startsWith('requirement-')) {
      const id = key.replace('requirement-', '');
      navigate(`/requirements/${id}`);
    } else if (key.startsWith('project-')) {
      const id = key.replace('project-', '');
      navigate(`/projects/${id}`);
    }
  };

  const handleCreateProject = () => {
    const name = prompt('请输入项目名称');
    if (name) {
      createProject.mutate({ name });
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <Button
          type="primary"
          icon={<PlusOutlined />}
          block
          onClick={handleCreateProject}
        >
          新建项目
        </Button>
      </div>

      <div className="flex-1 overflow-auto p-2">
        {isLoading ? (
          <div className="text-center text-gray-400 py-4">加载中...</div>
        ) : (
          <Tree
            showIcon
            treeData={treeData}
            onSelect={handleSelect}
            defaultExpandAll
          />
        )}
      </div>
    </div>
  );
}
```

**Step 3: 更新 AppSidebar**

```typescript
// frontend/src/components/Layout/AppSidebar.tsx
import { SettingsOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import ProjectTree from './ProjectTree';

export default function AppSidebar() {
  const navigate = useNavigate();

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Logo */}
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-lg font-bold text-gray-800">Sisyphus</h1>
        <p className="text-xs text-gray-500">测试用例生成平台</p>
      </div>

      {/* 项目树 */}
      <div className="flex-1 overflow-hidden">
        <ProjectTree />
      </div>

      {/* 底部设置按钮 */}
      <div className="p-4 border-t border-gray-200">
        <Button
          icon={<SettingsOutlined />}
          block
          onClick={() => navigate('/settings')}
        >
          设置
        </Button>
      </div>
    </div>
  );
}
```

**Step 4: 验证项目树**

```bash
cd frontend && npm run dev
```

侧边栏应显示项目树，点击需求可跳转

---

### Task 7: 聊天输入组件

**Files:**
- Create: `frontend/src/components/Chat/ChatInput.tsx`
- Create: `frontend/src/components/Chat/FileUploadButton.tsx`

**Step 1: 创建文件上传按钮**

```typescript
// frontend/src/components/Chat/FileUploadButton.tsx
import { Upload, Button, message } from 'antd';
import { PaperClipOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';

interface FileUploadButtonProps {
  onUpload: (file: UploadFile) => void;
  disabled?: boolean;
}

export default function FileUploadButton({ onUpload, disabled }: FileUploadButtonProps) {
  return (
    <Upload
      accept=".md,.txt,.pdf"
      showUploadList={false}
      beforeUpload={(file) => {
        // 检查文件大小 (10MB)
        if (file.size > 10 * 1024 * 1024) {
          message.error('文件大小不能超过 10MB');
          return false;
        }

        onUpload(file as unknown as UploadFile);
        return false; // 阻止自动上传
      }}
      disabled={disabled}
    >
      <Button
        type="text"
        icon={<PaperClipOutlined />}
        className="text-gray-400 hover:text-gray-600"
      />
    </Upload>
  );
}
```

**Step 2: 创建聊天输入组件**

```typescript
// frontend/src/components/Chat/ChatInput.tsx
import { useState, useRef } from 'react';
import { Input, Button } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';

import FileUploadButton from './FileUploadButton';

const { TextArea } = Input;

interface ChatInputProps {
  onSend: (message: string, files: UploadFile[]) => void;
  onFileUpload: (file: UploadFile) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSend,
  onFileUpload,
  disabled,
  placeholder = '描述你想要生成的测试用例...',
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState<UploadFile[]>([]);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!message.trim() && files.length === 0) return;

    onSend(message, files);
    setMessage('');
    setFiles([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = (file: UploadFile) => {
    setFiles((prev) => [...prev, file]);
    onFileUpload(file);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
      {/* 已上传文件列表 */}
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2 p-3 border-b border-gray-100">
          {files.map((file, index) => (
            <div
              key={index}
              className="flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-600 rounded text-sm"
            >
              <span>{file.name}</span>
              <button
                onClick={() => setFiles((prev) => prev.filter((_, i) => i !== index))}
                className="text-blue-400 hover:text-blue-600"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* 输入区域 */}
      <div className="flex items-end p-3">
        <FileUploadButton onUpload={handleFileUpload} disabled={disabled} />

        <TextArea
          ref={inputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          autoSize={{ minRows: 1, maxRows: 4 }}
          className="flex-1 mx-2 border-none shadow-none resize-none focus:ring-0"
        />

        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          disabled={disabled || (!message.trim() && files.length === 0)}
        />
      </div>
    </div>
  );
}
```

**Step 3: 更新 Home 页面使用 ChatInput**

```typescript
// frontend/src/pages/Home.tsx (更新)
import ChatInput from '../components/Chat/ChatInput';
import type { UploadFile } from 'antd/es/upload/interface';

export default function Home() {
  const handleSend = (message: string, files: UploadFile[]) => {
    console.log('Send:', message, files);
    // TODO: 实现 WebSocket 连接
  };

  const handleFileUpload = (file: UploadFile) => {
    console.log('File uploaded:', file);
    // TODO: 实现文件上传 API
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-800 mb-4">
            测试用例生成平台
          </h1>
          <p className="text-gray-500 mb-8">
            上传需求文档，自动生成功能测试用例
          </p>
        </div>
      </div>

      <div className="p-4">
        <div className="max-w-3xl mx-auto">
          <ChatInput
            onSend={handleSend}
            onFileUpload={handleFileUpload}
          />
        </div>
      </div>
    </div>
  );
}
```

**Step 4: 验证聊天输入**

```bash
cd frontend && npm run dev
```

输入框应可输入文字，点击附件按钮可选择文件

---

## Phase 3: 详情页面

### Task 8: 需求详情页

**Files:**
- Create: `frontend/src/pages/Requirement.tsx`
- Create: `frontend/src/components/Requirement/RequirementDetail.tsx`
- Create: `frontend/src/components/Requirement/ModuleCard.tsx`
- Create: `frontend/src/hooks/useRequirement.ts`

**Step 1: 创建需求 Hook**

```typescript
// frontend/src/hooks/useRequirement.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '../utils/api';

export interface StructuredRequirement {
  modules: Module[];
}

export interface Module {
  name: string;
  description: string;
  features: Feature[];
}

export interface Feature {
  name: string;
  description: string;
  input: string;
  output: string;
  exceptions: string;
}

export interface Requirement {
  id: string;
  projectId: string;
  title: string;
  content: StructuredRequirement;
  createdAt: string;
  updatedAt: string;
}

export function useRequirement(id: string) {
  return useQuery({
    queryKey: ['requirement', id],
    queryFn: async () => {
      const response = await api.get<Requirement>(`/requirements/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}
```

**Step 2: 创建模块卡片组件**

```typescript
// frontend/src/components/Requirement/ModuleCard.tsx
import { Card, Descriptions, Tag } from 'antd';
import type { Module } from '../../hooks/useRequirement';

interface ModuleCardProps {
  module: Module;
}

export default function ModuleCard({ module }: ModuleCardProps) {
  return (
    <Card title={module.name} className="mb-4">
      <p className="text-gray-600 mb-4">{module.description}</p>

      <div className="space-y-4">
        {module.features.map((feature, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Tag color="blue">{feature.name}</Tag>
            </div>
            <p className="text-gray-600 mb-3">{feature.description}</p>
            <Descriptions size="small" column={2}>
              <Descriptions.Item label="输入">{feature.input}</Descriptions.Item>
              <Descriptions.Item label="输出">{feature.output}</Descriptions.Item>
              <Descriptions.Item label="异常处理" span={2}>
                {feature.exceptions}
              </Descriptions.Item>
            </Descriptions>
          </div>
        ))}
      </div>
    </Card>
  );
}
```

**Step 3: 创建需求详情组件**

```typescript
// frontend/src/components/Requirement/RequirementDetail.tsx
import { Typography } from 'antd';
import ModuleCard from './ModuleCard';
import type { Requirement } from '../../hooks/useRequirement';

const { Title } = Typography;

interface RequirementDetailProps {
  requirement: Requirement;
}

export default function RequirementDetail({ requirement }: RequirementDetailProps) {
  return (
    <div>
      <Title level={3}>{requirement.title}</Title>

      <div className="mt-6">
        {requirement.content.modules.map((module, index) => (
          <ModuleCard key={index} module={module} />
        ))}
      </div>
    </div>
  );
}
```

**Step 4: 创建需求页面**

```typescript
// frontend/src/pages/Requirement.tsx
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { Button, Spin, Empty, List } from 'antd';
import { useRequirement, useTestCases } from '../hooks';
import RequirementDetail from '../components/Requirement/RequirementDetail';

export default function Requirement() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: requirement, isLoading } = useRequirement(id!);
  const { data: testCases } = useTestCases(id!);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spin size="large" />
      </div>
    );
  }

  if (!requirement) {
    return <Empty description="需求不存在" />;
  }

  return (
    <div className="h-full flex">
      {/* 左侧：需求详情 */}
      <div className="flex-1 overflow-auto p-6">
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(-1)}
          className="mb-4"
        >
          返回
        </Button>

        <RequirementDetail requirement={requirement} />
      </div>

      {/* 右侧：关联用例列表 */}
      <div className="w-80 border-l border-gray-200 overflow-auto p-4">
        <h3 className="font-bold mb-4">关联测试用例</h3>
        <List
          dataSource={testCases}
          renderItem={(tc) => (
            <List.Item>
              <Link to={`/testcases/${tc.id}`} className="text-blue-600 hover:underline">
                {tc.title}
              </Link>
            </List.Item>
          )}
        />
      </div>
    </div>
  );
}
```

---

### Task 9: 用例详情页

**Files:**
- Create: `frontend/src/pages/TestCase.tsx`
- Create: `frontend/src/components/TestCase/TestCaseDetail.tsx`
- Create: `frontend/src/hooks/useTestCases.ts`

**Step 1: 创建用例 Hook**

```typescript
// frontend/src/hooks/useTestCases.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '../utils/api';

export interface TestStep {
  step: number;
  action: string;
  expected: string;
}

export interface TestCase {
  id: string;
  requirementId: string;
  title: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  preconditions: string;
  steps: TestStep[];
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

export function useTestCase(id: string) {
  return useQuery({
    queryKey: ['testcase', id],
    queryFn: async () => {
      const response = await api.get<TestCase>(`/testcases/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useTestCases(requirementId: string) {
  return useQuery({
    queryKey: ['testcases', requirementId],
    queryFn: async () => {
      const response = await api.get<TestCase[]>(`/testcases/requirement/${requirementId}`);
      return response.data;
    },
    enabled: !!requirementId,
  });
}
```

**Step 2: 创建用例详情组件**

```typescript
// frontend/src/components/TestCase/TestCaseDetail.tsx
import { Card, Table, Tag, Descriptions } from 'antd';
import type { TestCase } from '../../hooks/useTestCases';

interface TestCaseDetailProps {
  testCase: TestCase;
}

const priorityColors = {
  P0: 'red',
  P1: 'orange',
  P2: 'blue',
  P3: 'gray',
};

export default function TestCaseDetail({ testCase }: TestCaseDetailProps) {
  const columns = [
    {
      title: '序号',
      dataIndex: 'step',
      key: 'step',
      width: 80,
    },
    {
      title: '步骤',
      dataIndex: 'action',
      key: 'action',
    },
    {
      title: '预期结果',
      dataIndex: 'expected',
      key: 'expected',
    },
  ];

  return (
    <Card>
      <Descriptions column={2} bordered>
        <Descriptions.Item label="用例标题" span={2}>
          {testCase.title}
        </Descriptions.Item>
        <Descriptions.Item label="优先级">
          <Tag color={priorityColors[testCase.priority]}>{testCase.priority}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="标签">
          {testCase.tags.map((tag) => (
            <Tag key={tag}>{tag}</Tag>
          ))}
        </Descriptions.Item>
        <Descriptions.Item label="前置条件" span={2}>
          {testCase.preconditions}
        </Descriptions.Item>
      </Descriptions>

      <h4 className="font-bold mt-6 mb-4">测试步骤</h4>
      <Table
        columns={columns}
        dataSource={testCase.steps}
        rowKey="step"
        pagination={false}
        bordered
      />
    </Card>
  );
}
```

**Step 3: 创建用例页面**

```typescript
// frontend/src/pages/TestCase.tsx
import { useParams, Link } from 'react-router-dom';
import { Button, Spin, Empty } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useTestCase } from '../hooks/useTestCases';
import TestCaseDetail from '../components/TestCase/TestCaseDetail';

export default function TestCase() {
  const { id } = useParams<{ id: string }>();
  const { data: testCase, isLoading } = useTestCase(id!);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spin size="large" />
      </div>
    );
  }

  if (!testCase) {
    return <Empty description="用例不存在" />;
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="flex items-center gap-4 mb-6">
        <Button type="text" icon={<ArrowLeftOutlined />}>
          <Link to={`/requirements/${testCase.requirementId}`}>返回用例列表</Link>
        </Button>
        <span className="text-gray-400">|</span>
        <Link
          to={`/requirements/${testCase.requirementId}`}
          className="text-blue-600 hover:underline"
        >
          查看需求详情
        </Link>
      </div>

      <TestCaseDetail testCase={testCase} />
    </div>
  );
}
```

---

## Phase 4: 导出和配置

### Task 10: 导出模板管理

**Files:**
- Create: `backend/app/api/export.py`
- Create: `backend/app/services/export.py`
- Create: `frontend/src/components/Export/TemplateManager.tsx`

**Step 1: 创建导出服务**

```python
# backend/app/services/export.py
import csv
import io
import json
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ExportTemplate, TestCase


class ExportService:
    """用例导出服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_csv(
        self,
        test_case_ids: List[UUID],
        template: ExportTemplate,
    ) -> str:
        """导出为 CSV 格式"""
        # 获取用例
        result = await self.db.execute(
            select(TestCase).where(TestCase.id.in_(test_case_ids))
        )
        test_cases = result.scalars().all()

        # 应用过滤条件
        if template.filter_config.get("priority"):
            test_cases = [tc for tc in test_cases if tc.priority in template.filter_config["priority"]]

        # 获取字段配置
        fields = template.field_config.get("fields", ["title", "priority", "preconditions", "steps"])
        delimiter = template.format_config.get("delimiter", ",")
        header_names = template.format_config.get("header_names", {})

        # 生成 CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)

        # 写入表头
        headers = [header_names.get(f, f) for f in fields]
        writer.writerow(headers)

        # 写入数据
        for tc in test_cases:
            row = []
            for field in fields:
                if field == "steps":
                    row.append(json.dumps(tc.steps, ensure_ascii=False))
                else:
                    row.append(str(getattr(tc, field, "")))
            writer.writerow(row)

        return output.getvalue()

    async def get_templates(self) -> List[ExportTemplate]:
        """获取所有模板"""
        result = await self.db.execute(select(ExportTemplate).order_by(ExportTemplate.name))
        return list(result.scalars().all())

    async def create_template(self, data: dict) -> ExportTemplate:
        """创建模板"""
        template = ExportTemplate(**data)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update_template(self, template_id: UUID, data: dict) -> ExportTemplate:
        """更新模板"""
        result = await self.db.execute(
            select(ExportTemplate).where(ExportTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise ValueError("模板不存在")

        for key, value in data.items():
            setattr(template, key, value)

        await self.db.commit()
        await self.db.refresh(template)
        return template
```

**Step 2: 创建导出 API**

```python
# backend/app/api/export.py
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import PlainTextResponse

from ..database import get_db
from ..services.export import ExportService

router = APIRouter(prefix="/export", tags=["export"])


class TemplateCreate(BaseModel):
    name: str
    field_config: dict = {}
    format_config: dict = {}
    filter_config: dict = {}
    is_default: bool = False


class ExportRequest(BaseModel):
    test_case_ids: List[UUID]
    template_id: UUID


@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    service = ExportService(db)
    templates = await service.get_templates()
    return templates


@router.post("/templates")
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    service = ExportService(db)
    template = await service.create_template(data.model_dump())
    return template


@router.post("/")
async def export_test_cases(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ExportService(db)

    # 获取模板
    from sqlalchemy import select
    from ..models import ExportTemplate

    result = await db.execute(
        select(ExportTemplate).where(ExportTemplate.id == request.template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(404, "模板不存在")

    csv_content = await service.export_csv(request.test_case_ids, template)

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=test_cases.csv"
        },
    )
```

---

### Task 11: LLM 配置页面

**Files:**
- Create: `frontend/src/pages/Settings.tsx`
- Create: `frontend/src/components/Settings/LLMConfig.tsx`
- Create: `backend/app/api/config.py`

**Step 1: 创建配置 API**

```python
# backend/app/api/config.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import UserConfig

router = APIRouter(prefix="/config", tags=["config"])


class LLMConfig(BaseModel):
    provider: str = "openai"
    api_key: str = ""
    model: str = "gpt-4"


@router.get("/llm")
async def get_llm_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        # 创建默认配置
        config = UserConfig(llm_config=LLMConfig().model_dump())
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return config.llm_config


@router.put("/llm")
async def update_llm_config(
    data: LLMConfig,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        config = UserConfig(llm_config=data.model_dump())
        db.add(config)
    else:
        config.llm_config = data.model_dump()

    await db.commit()
    await db.refresh(config)

    return config.llm_config
```

**Step 2: 创建 LLM 配置组件**

```typescript
// frontend/src/components/Settings/LLMConfig.tsx
import { Form, Select, Input, Button, message, Spin } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../utils/api';

interface LLMConfig {
  provider: string;
  apiKey: string;
  model: string;
}

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI', models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
  { value: 'zhipu', label: '智谱 AI (GLM)', models: ['glm-4', 'glm-4-plus', 'glm-3-turbo'] },
  { value: 'alibaba', label: '阿里百炼', models: ['qwen-turbo', 'qwen-plus', 'qwen-max'] },
  { value: 'minimax', label: 'MiniMax', models: ['abab5.5-chat', 'abab5.5s-chat'] },
];

export default function LLMConfig() {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: config, isLoading } = useQuery({
    queryKey: ['llm-config'],
    queryFn: async () => {
      const response = await api.get<LLMConfig>('/config/llm');
      return response.data;
    },
  });

  const updateConfig = useMutation({
    mutationFn: async (values: LLMConfig) => {
      const response = await api.put<LLMConfig>('/config/llm', values);
      return response.data;
    },
    onSuccess: () => {
      message.success('配置已保存');
      queryClient.invalidateQueries({ queryKey: ['llm-config'] });
    },
    onError: () => {
      message.error('保存失败');
    },
  });

  if (isLoading) {
    return <Spin />;
  }

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={config}
      onFinish={(values) => updateConfig.mutate(values)}
      className="max-w-md"
    >
      <Form.Item name="provider" label="LLM 提供商" rules={[{ required: true }]}>
        <Select>
          {PROVIDERS.map((p) => (
            <Select.Option key={p.value} value={p.value}>
              {p.label}
            </Select.Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item name="model" label="模型" rules={[{ required: true }]}>
        <Select>
          {PROVIDERS.find((p) => p.value === form.getFieldValue('provider'))?.models.map((m) => (
            <Select.Option key={m} value={m}>
              {m}
            </Select.Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item name="apiKey" label="API Key" rules={[{ required: true }]}>
        <Input.Password placeholder="请输入 API Key" />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={updateConfig.isPending}>
          保存配置
        </Button>
      </Form.Item>
    </Form>
  );
}
```

**Step 3: 创建设置页面**

```typescript
// frontend/src/pages/Settings.tsx
import { Typography, Card } from 'antd';
import LLMConfig from '../components/Settings/LLMConfig';

const { Title } = Typography;

export default function Settings() {
  return (
    <div className="h-full overflow-auto p-6">
      <Title level={3}>设置</Title>

      <Card title="LLM 配置" className="mt-4">
        <LLMConfig />
      </Card>
    </div>
  );
}
```

---

## 清理旧文件

完成上述任务后，删除不再需要的旧文件：

```bash
# 前端
rm frontend/src/components/ChatInterface.tsx
rm frontend/src/components/DocumentUpload.tsx
rm frontend/src/components/TestCaseTable.tsx
rm frontend/src/pages/CaseGeneration.tsx

# 后端（重构后删除）
rm backend/app/api/cases.py
rm backend/app/api/documents.py
```

---

## 验收检查

- [ ] 主页显示聊天式界面，有项目树侧边栏
- [ ] 上传文件后显示预览
- [ ] WebSocket 流式生成用例
- [ ] 需求详情页显示结构化需求
- [ ] 用例详情页显示步骤表格
- [ ] 导出模板可配置
- [ ] LLM 配置可保存
