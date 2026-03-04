# LLM 接入层实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 LLM 统一接入层，支持 GLM、MiniMax、阿里百炼等多种模型提供商

**Architecture:**
- 抽象基类定义统一接口
- 各提供商实现具体适配器
- 配置驱动的模型选择
- 支持流式输出

**Tech Stack:** OpenAI API 兼容接口, HTTPX, Pydantic

---

## Task 1: 创建 LLM 基类和统一接口

**Files:**
- Create: `backend/app/llm/base.py`
- Create: `backend/app/llm/__init__.py`

**Step 1: Write failing test for LLM base class**

创建 `backend/app/tests/test_llm_base.py`:

```python
import pytest
from app.llm.base import LLMProvider, Message

@pytest.mark.asyncio
async def test_llm_provider_interface():
    """测试 LLM 提供商接口"""
    # 这会失败，因为还没实现
    provider = LLMProvider(api_key="test")
    response = await provider.generate("Hello")
    assert response.text is not None
```

**Step 2: Run test to verify it fails**

```bash
cd backend
uv run pytest app/tests/test_llm_base.py::test_llm_provider_interface -v
```

Expected: FAIL with "Cannot instantiate abstract class"

**Step 3: Implement LLM base class**

创建 `backend/app/llm/base.py`:

```python
from abc import ABC, abstractmethod
from typing import List, Optional, AsyncIterator
from pydantic import BaseModel

class Message(BaseModel):
    """消息模型"""
    role: str  # system, user, assistant
    content: str

class LLMResponse(BaseModel):
    """LLM 响应模型"""
    text: str
    model: str
    usage: Optional[dict] = None

class LLMProvider(ABC):
    """LLM 提供商抽象基类"""

    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """生成文本"""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        """流式生成文本"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """对话模式生成"""
        pass
```

创建 `backend/app/llm/__init__.py`:

```python
from app.llm.base import LLMProvider, Message, LLMResponse
```

**Step 4: Update test to be more realistic**

修改 `backend/app/tests/test_llm_base.py`:

```python
import pytest
from app.llm.base import LLMProvider, Message

def test_message_model():
    """测试消息模型"""
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"

def test_llm_response_model():
    """测试响应模型"""
    response = LLMResponse(
        text="Generated text",
        model="test-model",
        usage={"prompt_tokens": 10, "completion_tokens": 20}
    )
    assert response.text == "Generated text"
    assert response.model == "test-model"
```

**Step 5: Run tests**

```bash
uv run pytest app/tests/test_llm_base.py -v
```

Expected: All PASS

**Step 6: Commit**

```bash
git add backend/app/llm/
git commit -m "feat: 创建 LLM 抽象基类和统一接口"
```

---

## Task 2: 实现 GLM（智谱 AI）适配器

**Files:**
- Create: `backend/app/llm/glm.py`

**Step 1: Write failing test for GLM provider**

创建 `backend/app/tests/test_glm.py`:

```python
import pytest
import os
from app.llm.glm import GLMProvider

@pytest.mark.asyncio
async def test_glm_generate():
    """测试 GLM 生成（需要真实的 API Key）"""
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        pytest.skip("需要 GLM_API_KEY 环境变量")

    provider = GLMProvider(api_key=api_key)
    response = await provider.generate("你好，请做一个简单的自我介绍")

    assert response.text is not None
    assert len(response.text) > 0
    assert response.model is not None
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_glm.py::test_glm_generate -v
```

Expected: FAIL with "module 'app.llm.glm' not found"

**Step 3: Implement GLM provider**

创建 `backend/app/llm/glm.py`:

```python
import httpx
from typing import List, Optional, AsyncIterator
from app.llm.base import LLMProvider, Message, LLMResponse

class GLMProvider(LLMProvider):
    """智谱 GLM 提供商"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.default_model = "glm-4"

    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        model = model or self.default_model

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data.get("usage")
            )

    async def generate_stream(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        model = model or self.default_model

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True
                },
                timeout=60.0
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        # 解析 SSE 数据
                        # 这里需要实现 JSON 解析逻辑
                        yield data_str

    async def chat(
        self,
        messages: List[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        model = model or self.default_model

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [msg.dict() for msg in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data.get("usage")
            )
```

**Step 4: Run tests (if API key available)**

```bash
# 设置 API key（测试用）
export GLM_API_KEY=your-api-key-here

uv run pytest app/tests/test_glm.py::test_glm_generate -v
```

Expected: PASS (如果有有效的 API key)

**Step 5: Commit**

```bash
git add backend/app/llm/glm.py backend/app/tests/test_glm.py
git commit -m "feat: 实现 GLM（智谱 AI）适配器"
```

---

## Task 3: 实现 MiniMax 适配器

**Files:**
- Create: `backend/app/llm/minimax.py`

**Step 1: Write failing test for MiniMax provider**

创建 `backend/app/tests/test_minimax.py`:

```python
import pytest
import os
from app.llm.minimax import MiniMaxProvider

@pytest.mark.asyncio
async def test_minimax_generate():
    """测试 MiniMax 生成"""
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        pytest.skip("需要 MINIMAX_API_KEY 环境变量")

    provider = MiniMaxProvider(api_key=api_key)
    response = await provider.generate("你好")

    assert response.text is not None
    assert len(response.text) > 0
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_minimax.py::test_minimax_generate -v
```

Expected: FAIL with "module 'app.llm.minimax' not found"

**Step 3: Implement MiniMax provider**

创建 `backend/app/llm/minimax.py`:

```python
import httpx
from typing import List, Optional, AsyncIterator
from app.llm.base import LLMProvider, Message, LLMResponse

class MiniMaxProvider(LLMProvider):
    """MiniMax 提供商"""

    def __init__(self, api_key: str, group_id: str = None):
        super().__init__(api_key)
        self.group_id = group_id
        self.base_url = "https://api.minimax.chat/v1"
        self.default_model = "abab6.5s-chat"

    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        model = model or self.default_model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if self.group_id:
            headers["GroupId"] = self.group_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data.get("usage")
            )

    async def generate_stream(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        # 流式生成实现（类似 GLM）
        raise NotImplementedError("流式生成待实现")

    async def chat(
        self,
        messages: List[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        model = model or self.default_model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if self.group_id:
            headers["GroupId"] = self.group_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [msg.dict() for msg in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data.get("usage")
            )
```

**Step 4: Commit**

```bash
git add backend/app/llm/minimax.py backend/app/tests/test_minimax.py
git commit -m "feat: 实现 MiniMax 适配器"
```

---

## Task 4: 实现阿里百炼适配器

**Files:**
- Create: `backend/app/llm/alibaba.py`

**Step 1: Write failing test**

创建 `backend/app/tests/test_alibaba.py`:

```python
import pytest
import os
from app.llm.alibaba import AlibabaProvider

@pytest.mark.asyncio
async def test_alibaba_generate():
    """测试阿里百炼生成"""
    api_key = os.getenv("ALIBABA_API_KEY")
    if not api_key:
        pytest.skip("需要 ALIBABA_API_KEY 环境变量")

    provider = AlibabaProvider(api_key=api_key)
    response = await provider.generate("你好")

    assert response.text is not None
```

**Step 2: Implement Alibaba provider**

创建 `backend/app/llm/alibaba.py`:

```python
import httpx
from typing import List, Optional, AsyncIterator
from app.llm.base import LLMProvider, Message, LLMResponse

class AlibabaProvider(LLMProvider):
    """阿里百炼提供商"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.default_model = "qwen-max"

    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        model = model or self.default_model

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "input": {
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    "parameters": {
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                text=data["output"]["text"],
                model=model,
                usage=data.get("usage")
            )

    async def generate_stream(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        raise NotImplementedError("流式生成待实现")

    async def chat(
        self,
        messages: List[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        model = model or self.default_model

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "input": {
                        "messages": [msg.dict() for msg in messages]
                    },
                    "parameters": {
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                text=data["output"]["text"],
                model=model,
                usage=data.get("usage")
            )
```

**Step 3: Commit**

```bash
git add backend/app/llm/alibaba.py backend/app/tests/test_alibaba.py
git commit -m "feat: 实现阿里百炼适配器"
```

---

## Task 5: 创建 LLM 工厂类

**Files:**
- Create: `backend/app/llm/factory.py`
- Modify: `backend/app/llm/__init__.py`

**Step 1: Write failing test for factory**

创建 `backend/app/tests/test_llm_factory.py`:

```python
import pytest
from app.llm.factory import create_llm_provider

def test_create_glm_provider():
    """测试创建 GLM 提供商"""
    provider = create_llm_provider("glm", api_key="test-key")
    assert provider.__class__.__name__ == "GLMProvider"

def test_create_minimax_provider():
    """测试创建 MiniMax 提供商"""
    provider = create_llm_provider("minimax", api_key="test-key")
    assert provider.__class__.__name__ == "MiniMaxProvider"

def test_create_alibaba_provider():
    """测试创建阿里百炼提供商"""
    provider = create_llm_provider("alibaba", api_key="test-key")
    assert provider.__class__.__name__ == "AlibabaProvider"

def test_invalid_provider():
    """测试无效提供商"""
    with pytest.raises(ValueError):
        create_llm_provider("invalid", api_key="test-key")
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_llm_factory.py -v
```

Expected: FAIL with "module 'app.llm.factory' not found"

**Step 3: Implement factory class**

创建 `backend/app/llm/factory.py`:

```python
from app.llm.base import LLMProvider
from app.llm.glm import GLMProvider
from app.llm.minimax import MiniMaxProvider
from app.llm.alibaba import AlibabaProvider

PROVIDER_MAP = {
    "glm": GLMProvider,
    "minimax": MiniMaxProvider,
    "alibaba": AlibabaProvider,
}

def create_llm_provider(
    provider_name: str,
    api_key: str,
    **kwargs
) -> LLMProvider:
    """
    创建 LLM 提供商实例

    Args:
        provider_name: 提供商名称 (glm, minimax, alibaba)
        api_key: API 密钥
        **kwargs: 其他参数（如 group_id for MiniMax）

    Returns:
        LLMProvider 实例

    Raises:
        ValueError: 如果提供商名称无效
    """
    provider_class = PROVIDER_MAP.get(provider_name.lower())
    if not provider_class:
        raise ValueError(
            f"不支持的 LLM 提供商: {provider_name}. "
            f"支持的提供商: {', '.join(PROVIDER_MAP.keys())}"
        )

    return provider_class(api_key=api_key, **kwargs)
```

修改 `backend/app/llm/__init__.py`:

```python
from app.llm.base import LLMProvider, Message, LLMResponse
from app.llm.factory import create_llm_provider

__all__ = [
    "LLMProvider",
    "Message",
    "LLMResponse",
    "create_llm_provider",
]
```

**Step 4: Run tests**

```bash
uv run pytest app/tests/test_llm_factory.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add backend/app/llm/factory.py backend/app/llm/__init__.py
git commit -m "feat: 添加 LLM 工厂类"
```

---

## Task 6: 创建用户配置管理 API

**Files:**
- Create: `backend/app/api/config.py`
- Modify: `backend/app/main.py`

**Step 1: Write failing test for config API**

创建 `backend/app/tests/test_config_api.py`:

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_config():
    """测试创建配置"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/configs/",
            json={
                "provider": "glm",
                "api_key": "test-api-key-encrypted",
                "generator_model": "glm-4",
                "reviewer_model": "glm-4"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "glm"
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_config_api.py::test_create_config -v
```

Expected: FAIL with "404 Not Found"

**Step 3: Implement config API**

创建 `backend/app/api/config.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.user_config import UserConfig

router = APIRouter(prefix="/api/configs", tags=["configs"])

class ConfigCreate(BaseModel):
    provider: str  # glm, minimax, alibaba
    api_key_encrypted: str
    generator_model: Optional[str] = None
    reviewer_model: Optional[str] = None

class ConfigResponse(BaseModel):
    id: int
    provider: str
    api_key_encrypted: str
    generator_model: Optional[str]
    reviewer_model: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=ConfigResponse)
async def create_config(
    config: ConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建 LLM 配置"""
    if config.provider not in ["glm", "minimax", "alibaba"]:
        raise HTTPException(status_code=400, detail="不支持的提供商")

    db_config = UserConfig(**config.dict())
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)
    return db_config

@router.get("/", response_model=list[ConfigResponse])
async def list_configs(
    db: AsyncSession = Depends(get_db)
):
    """获取所有配置"""
    result = await db.execute(select(UserConfig))
    configs = result.scalars().all()
    return configs

@router.get("/active", response_model=ConfigResponse)
async def get_active_config(
    db: AsyncSession = Depends(get_db)
):
    """获取当前激活的配置"""
    result = await db.execute(
        select(UserConfig).where(UserConfig.is_active == True)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="没有激活的配置")
    return config

@router.patch("/{config_id}/activate")
async def activate_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """激活指定配置（停用其他配置）"""
    # 停用所有配置
    await db.execute(
        UserConfig.__table__.update().values(is_active=False)
    )

    # 激活指定配置
    result = await db.execute(
        select(UserConfig).where(UserConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    config.is_active = True
    await db.commit()
    return {"message": "配置已激活"}
```

修改 `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import projects, cases, config

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
app.include_router(cases.router)
app.include_router(config.router)

@app.get("/")
async def root():
    return {
        "message": "Sisyphus 测试用例生成平台 API",
        "version": "0.1.0",
        "status": "running"
    }
```

**Step 4: Run tests**

```bash
uv run pytest app/tests/test_config_api.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add backend/app/api/config.py backend/app/main.py
git commit -m "feat: 实现用户配置管理 API"
```

---

## 完成检查清单

- [ ] LLM 基类和接口定义完成
- [ ] GLM、MiniMax、阿里百炼适配器实现
- [ ] 工厂类可以正确创建提供商实例
- [ ] 配置管理 API 可以保存和检索用户配置
- [ ] 所有测试通过

## 下一步

继续实施：
- `2026-03-04-03-vector-rag.md` - 向量检索和 RAG
- `2026-03-04-04-agent-system.md` - Agent 系统
