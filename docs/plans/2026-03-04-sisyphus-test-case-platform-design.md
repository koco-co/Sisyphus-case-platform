# Sisyphus 测试用例生成平台 - 系统设计文档

**日期：** 2026-03-04
**版本：** v1.0
**设计目标：** 将用户输入的需求文档转化为强规范的 CSV 测试用例，通过向量数据库和双 Agent 机制保证用例质量

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     前端 (React + Vite)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 目录树   │  │ 聊天界面 │  │表格编辑 │  │ 配置面板 │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↕ WebSocket (流式输出)
┌─────────────────────────────────────────────────────────────┐
│                   后端 (FastAPI + uv)                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Agent 编排层                            │    │
│  │  ┌──────────────┐      ┌──────────────┐             │    │
│  │  │ 生成 Agent   │ ───→ │ 评审 Agent   │             │    │
│  │  └──────────────┘      └──────────────┘             │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              文档解析层 (Plugin)                     │    │
│  │  Text/MD │ PDF │ Word插件 │ OCR插件 │ 网页插件     │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              向量检索层 (RAG)                        │    │
│  │  历史用例库 → 向量检索 → Few-shot 示例              │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              LLM 接入层                              │    │
│  │  GLM │ MiniMax │ 阿里百炼 │ 可扩展其他              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│            PostgreSQL + pgvector 扩展                        │
│  • 用例数据  • 需求文档  • 向量索引  • 用户配置              │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、核心模块设计

### 2.1 前端模块

#### 目录结构
```
src/
├── components/
│   ├── Sidebar/          # 左侧目录树
│   ├── ChatArea/         # 中间聊天区域
│   ├── TestCaseTable/    # CSV 表格编辑
│   └── ConfigPanel/      # 模型配置面板
├── pages/
│   ├── CaseManagement/   # 用例管理页
│   └── CaseGeneration/   # 用例生成页
├── hooks/
│   ├── useWebSocket.js   # WebSocket 流式接收
│   └── useTestCase.js    # 用例 CRUD
├── utils/
│   └── csvParser.js      # CSV 解析/导出
└── App.jsx
```

#### 关键组件功能

**Sidebar（目录树）**
- 多层级展开/收起
- 点击需求加载关联用例
- 支持拖拽重组（可选）

**ChatArea（聊天界面）**
- 大输入框 + 文件上传按钮
- 流式显示生成过程
- 需求澄清多轮对话（隐藏在思维链中）

**TestCaseTable（表格编辑器）**
- 实时渲染 CSV 数据
- 单元格编辑
- 行删除、审批标记（通过/拒绝）

**ConfigPanel（配置面板）**
- 模型提供商配置（GLM、MiniMax、阿里百炼）
- API Key 管理
- 生成模型 / 评审模型选择

### 2.2 后端模块

#### 目录结构
```
backend/
├── app/
│   ├── api/
│   │   ├── cases.py       # 用例 CRUD API
│   │   ├── projects.py    # 项目/需求管理 API
│   │   └── generation.py  # 用例生成 API（WebSocket）
│   ├── agents/
│   │   ├── generator.py   # 生成 Agent
│   │   ├── reviewer.py    # 评审 Agent
│   │   └── orchestrator.py # Agent 编排器
│   ├── plugins/
│   │   ├── base.py        # 插件基类
│   │   ├── pdf_parser.py
│   │   ├── md_parser.py
│   │   └── txt_parser.py
│   ├── rag/
│   │   ├── retriever.py   # 向量检索
│   │   └── embeddings.py  # 向量化
│   ├── llm/
│   │   ├── base.py        # LLM 基类
│   │   ├── glm.py
│   │   ├── minimax.py
│   │   └── alibaba.py
│   ├── models/
│   │   ├── project.py
│   │   ├── test_case.py
│   │   └── user_config.py
│   ├── database.py
│   └── main.py
├── skills/                # 预留 Skill 目录
└── pyproject.toml
```

#### 核心模块说明

**Agent 编排层**
- `generator.py`: 生成测试用例
- `reviewer.py`: 评审用例质量、规范、格式
- `orchestrator.py`: 协调两个 Agent 的交互

**文档解析层**
- 支持文本、Markdown、PDF
- 预留插件接口，可扩展 Word、OCR、网页抓取

**向量检索层**
- 将历史用例向量化存入 pgvector
- 新需求到来时检索相似用例作为 Few-shot 示例

**LLM 接入层**
- 统一的 LLM 接口
- 支持 GLM、MiniMax、阿里百炼
- 可扩展其他兼容 OpenAI API 的模型

### 2.3 数据库设计

#### 核心表结构

```sql
-- 项目/需求表（支持树形结构）
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES projects(id),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 测试用例表
CREATE TABLE test_cases (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    module VARCHAR(255),           -- 所属模块
    title VARCHAR(500),            -- 用例标题
    prerequisites TEXT,            -- 前置条件
    steps TEXT,                    -- 步骤
    expected_results TEXT,         -- 预期结果
    keywords TEXT,                 -- 关键词
    priority VARCHAR(50),          -- 优先级（1/2/3）
    case_type VARCHAR(50),         -- 用例类型
    stage VARCHAR(50),             -- 适用阶段
    status VARCHAR(50) DEFAULT 'pending',  -- pending/approved/rejected
    embedding VECTOR(1536),        -- pgvector 存储向量
    created_at TIMESTAMP DEFAULT NOW()
);

-- 用户配置表（加密存储 API Key）
CREATE TABLE user_configs (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL, -- glm/minimax/alibaba
    api_key_encrypted TEXT NOT NULL,
    generator_model VARCHAR(100),
    reviewer_model VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_test_cases_project ON test_cases(project_id);
CREATE INDEX idx_test_cases_status ON test_cases(status);
CREATE INDEX idx_projects_parent ON projects(parent_id);
```

---

## 三、工作流设计

### 3.1 用例生成完整流程

```python
async def generate_test_case_workflow(
    requirement_document: str,
    file_type: str
) -> AsyncIterator[TestCase]:
    """
    测试用例生成工作流
    """

    # 1. 文档解析
    parsed_text = await parse_document(requirement_document, file_type)

    # 2. 需求澄清（思维链，不展示给用户）
    clarified_requirement = await clarify_requirements(parsed_text)

    # 3. 向量检索历史用例（RAG）
    similar_cases = await vector_search(
        query=clarified_requirement,
        top_k=5,
        status='approved'  # 只检索已审批通过的用例
    )

    # 4. 测试点分析（思维链，不展示给用户）
    test_points = await analyze_test_points(
        requirement=clarified_requirement,
        similar_cases=similar_cases
    )

    # 5. 生成 Agent 生成用例
    max_retries = 3
    for attempt in range(max_retries):
        # 生成用例
        generated_cases = await generator_agent.generate(
            requirement=clarified_requirement,
            test_points=test_points,
            examples=similar_cases  # Few-shot learning
        )

        # 评审 Agent 评审
        review_result = await reviewer_agent.review(generated_cases)

        if review_result.passed:
            break  # 评审通过
        else:
            # 不通过，重新生成
            if attempt < max_retries - 1:
                await generator_agent.regenerate(
                    cases=generated_cases,
                    feedback=review_result.feedback
                )

    # 6. 流式输出到前端
    async for case in stream_cases(generated_cases):
        yield case
```

### 3.2 前端实时渲染流程

```javascript
// WebSocket 连接
const ws = new WebSocket('ws://localhost:8000/generate');

// 接收流式数据
ws.onmessage = (event) => {
  const testCase = JSON.parse(event.data);

  // 实时渲染到表格
  addTestCaseToTable(testCase);

  // 用户可以实时审批
  renderApprovalButtons(testCase);
};
```

---

## 四、关键技术实现

### 4.1 真实测试数据生成策略

#### Prompt 模板

```python
TEST_CASE_GENERATION_PROMPT = """
你是一个资深的测试用例设计专家。

**任务：**
基于以下需求文档，生成高质量、规范的测试用例。

**重要约束（CRITICAL）：**
1. 测试数据必须真实、可用、符合行业实际
2. 禁止使用"比如""例如""XXX""测试数据"等模糊字眼
3. 手机号必须是真实格式（如：13812345678）
4. 身份证号必须是真实格式（如：110101199001011234）
5. 邮箱必须是真实格式（如：test@example.com）
6. 金额必须是合理数值（如：99.99，而非 999999999.99）
7. 日期必须是真实日期（如：2026-03-04）
8. URL 必须是真实格式（如：https://example.com/api/user）

**CSV 格式要求：**
- 所属模块 | 用例标题 | 前置条件 | 步骤 | 预期 | 关键词 | 优先级 | 用例类型 | 适用阶段

**需求文档：**
{requirement}

**历史参考用例（请模仿这些用例的风格和规范）：**
{examples}

请生成符合上述要求的测试用例，确保每一条用例都是可执行的。
"""
```

### 4.2 文档解析插件架构

```python
from abc import ABC, abstractmethod
from pathlib import Path

class DocumentParser(ABC):
    """文档解析器基类"""

    @abstractmethod
    def parse(self, file_path: str) -> str:
        """解析文档，返回纯文本"""
        pass

    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        """是否支持该文件类型"""
        pass


class PDFParser(DocumentParser):
    """PDF 解析器"""

    def supports(self, file_extension: str) -> bool:
        return file_extension.lower() == '.pdf'

    def parse(self, file_path: str) -> str:
        # 使用 PyPDF2 或 pdfplumber
        import pypdf
        text = ""
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()
        return text


class MarkdownParser(DocumentParser):
    """Markdown 解析器"""

    def supports(self, file_extension: str) -> bool:
        return file_extension.lower() in ['.md', '.markdown']

    def parse(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


# 插件管理器
class ParserManager:
    def __init__(self):
        self.parsers: List[DocumentParser] = [
            MarkdownParser(),
            PDFParser(),
            # 后续可动态加载 Word、OCR 插件
        ]

    def get_parser(self, file_path: str) -> DocumentParser:
        ext = Path(file_path).suffix
        for parser in self.parsers:
            if parser.supports(ext):
                return parser
        raise ValueError(f"不支持的文件类型: {ext}")
```

### 4.3 向量检索实现

```python
from sentence_transformers import SentenceTransformer
from app.database import get_db

class VectorRetriever:
    """向量检索器"""

    def __init__(self):
        # 使用中文友好的嵌入模型
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    def embed_text(self, text: str) -> List[float]:
        """将文本向量化"""
        return self.model.encode(text).tolist()

    async def search_similar_cases(
        self,
        query: str,
        top_k: int = 5,
        status: str = 'approved'
    ) -> List[TestCase]:
        """检索相似的历史用例"""
        query_vector = self.embed_text(query)

        db = get_db()
        result = await db.execute("""
            SELECT id, module, title, prerequisites, steps, expected_results,
                   1 - (embedding <=> $1) as similarity
            FROM test_cases
            WHERE status = $2
            ORDER BY embedding <=> $1
            LIMIT $3
        """, query_vector, status, top_k)

        return result.fetchall()
```

### 4.4 双 Agent 质量保证机制

#### 生成 Agent（generator.py）

```python
class GeneratorAgent:
    async def generate(
        self,
        requirement: str,
        test_points: List[str],
        examples: List[TestCase]
    ) -> List[TestCase]:
        prompt = self._build_prompt(requirement, test_points, examples)
        response = await self.llm.generate(prompt)
        return self._parse_csv_to_test_cases(response)

    def _build_prompt(
        self,
        requirement: str,
        test_points: List[str],
        examples: List[TestCase]
    ) -> str:
        # 构建 Few-shot Prompt
        examples_text = "\n".join([
            f"示例 {i+1}:\n{case.to_csv()}"
            for i, case in enumerate(examples)
        ])

        return TEST_CASE_GENERATION_PROMPT.format(
            requirement=requirement,
            test_points="\n".join(test_points),
            examples=examples_text
        )
```

#### 评审 Agent（reviewer.py）

```python
class ReviewerAgent:
    async def review(self, test_cases: List[TestCase]) -> ReviewResult:
        """评审测试用例质量"""
        prompt = self._build_review_prompt(test_cases)
        response = await self.llm.generate(prompt)

        # 解析评审结果
        return self._parse_review_result(response)

    def _build_review_prompt(self, test_cases: List[TestCase]) -> str:
        return f"""
请评审以下测试用例的质量：

**评审维度：**
1. 规范性：是否符合 CSV 格式要求
2. 完整性：是否包含所有必填字段
3. 可执行性：步骤是否清晰、预期是否明确
4. 数据真实性：是否使用真实测试数据

**待评审用例：**
{self._format_cases(test_cases)}

**评审格式：**
- 通过/不通过
- 不通过原因（如果不通过）
- 改进建议
"""
```

---

## 五、前端界面设计

### 5.1 主页面布局

```
┌─────────────────────────────────────────────────────────┐
│  📁 Sisyphus                        🔔 📊 ⚙️            │
├─────────────┬───────────────────────────────────────────┤
│             │                                           │
│ 📂 项目     │         [输入需求或上传文件...]            │
│   ├ 登录    │         ┌─────────┐  ┌─────────┐         │
│   ├ 支付    │         │ 上传PDF │  │ 粘贴文本 │         │
│   └ 订单    │         └─────────┘  └─────────┘         │
│             │                                           │
│ 📂 用户     │    ─────────────────────────────          │
│   ├ 注册    │    ✨ 登录功能 - 需求澄清中...            │
│   └ 个人中心 │    🔍 正在分析测试点 (3/10)              │
│             │    📝 已生成 15 条测试用例                │
│ 📁 最近使用   │    ─────────────────────────────          │
│             │                                           │
│             │         [查看详情] [导出CSV]              │
└─────────────┴───────────────────────────────────────────┘
```

### 5.2 核心页面说明

**用例管理页面（CaseManagement）**
- 左侧目录树显示所有项目/需求
- 点击需求加载关联的测试用例
- 支持搜索、筛选、导出

**用例生成页面（CaseGeneration）**
- 类似 DeepSeek/Gemini 的简洁设计
- 大输入框 + 文件上传
- 流式显示生成过程
- 实时表格渲染 + 审批按钮

---

## 六、部署方案

### 6.1 Docker Compose 配置

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: sisyphus-db
    environment:
      POSTGRES_DB: sisyphus
      POSTGRES_USER: sisyphus
      POSTGRES_PASSWORD: your_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: sisyphus-backend
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://sisyphus:your_password_here@postgres:5432/sisyphus
      JWT_SECRET: your_jwt_secret_here
    ports:
      - "8000:8000"
    volumes:
      - ./backend/skills:/app/skills

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: sisyphus-frontend
    depends_on:
      - backend
    ports:
      - "3000:3000"

volumes:
  postgres_data:
```

### 6.2 一键启动

```bash
# 克隆项目
git clone https://github.com/your-repo/sisyphus-case-platform.git
cd sisyphus-case-platform

# 启动所有服务
docker-compose up -d

# 访问
open http://localhost:3000
```

---

## 七、MVP 功能范围（YAGNI 原则）

### 7.1 第一版（MVP）包含

✅ **核心功能**
- 文档解析（文本、Markdown、PDF）
- 双 Agent 质量保证（生成 + 评审）
- 向量检索提升用例质量
- 流式输出 + 实时审批
- 历史用例管理
- CSV 导出

✅ **LLM 支持**
- GLM（智谱 AI）
- MiniMax
- 阿里百炼

✅ **数据存储**
- PostgreSQL + pgvector

### 7.2 第一版不包含（未来迭代）

❌ 多用户权限管理
❌ 用例版本控制
❌ 高级统计分析
❌ CI/CD 集成
❌ Word/OCR/网页抓取（通过插件后续添加）

---

## 八、技术栈总结

| 层级 | 技术选择 |
|------|---------|
| 前端 | React + Vite + WebSocket |
| 后端 | FastAPI + uv |
| 数据库 | PostgreSQL + pgvector |
| 向量化 | Sentence-Transformers |
| 文档解析 | PyPDF2 + python-docx（插件） |
| 部署 | Docker + Docker Compose |
| LLM 接入 | OpenAI API 兼容接口 |

---

## 九、未来扩展方向

1. **更多文件格式支持**
   - Word 文档解析
   - 图片 OCR 识别
   - 网页内容抓取

2. **协作功能**
   - 多用户权限管理
   - 用例评论和讨论
   - 团队共享用例库

3. **智能推荐**
   - 基于历史数据的测试点推荐
   - 自动识别重复用例
   - 用例覆盖率分析

4. **CI/CD 集成**
   - 自动导出到测试平台
   - 与自动化测试工具集成
   - 测试报告生成

---

**文档状态：** ✅ 已批准
**下一步：** 调用 writing-plans skill 创建实施计划
