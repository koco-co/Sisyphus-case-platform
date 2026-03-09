# Sisyphus-Y 完整开发计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完成 Sisyphus-Y 平台所有核心功能开发，实现需求上传→文档解析→健康诊断→测试点生成→用例流式生成的全链路打通，并通过自测验收。

**Architecture:** 后端 FastAPI + SQLAlchemy 2.0 async + 多 LLM 适配器（智谱/阿里百炼），前端 Next.js 16 + Tailwind CSS + Zustand。AI 引擎层（engine/）管理所有 Prompt，7 层 Prompt 组装体系。UDA 层负责文档解析（docx/pdf/md/图片）。

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Redis, Next.js 16, Tailwind CSS v4, Zustand, React Flow, Recharts, SSE streaming, 智谱 GLM-4-Flash, 阿里百炼 Qwen-Plus

---

## 当前状态分析

### ✅ 已完成
- 后端 21/22 模块框架（products, diagnosis, scene_map, generation, testcases, diff, knowledge, templates, coverage, dashboard, auth 等）
- AI 引擎层：4 个 LLM 适配器 + 故障转移 + SSE 收集器 + 输出解析器
- 前端 11+ 页面基础实现
- 数据库模型 + 3 个迁移文件
- JWT 认证 + 软删除 + 版本管理

### ❌ 待完成
1. **B-TASK-03**: UDA 文档解析引擎（完全空白 stub）
2. **Prompt 体系**: 7 层 Prompt 组装、系统 Rules、ai_configurations 表
3. **Prompt 增强**: 当前 prompts 过于简单，需要替换为完整版本
4. **前端验证**: CaseCard 渲染、样式一致性、文件上传功能
5. **全链路打通**: 上传→解析→诊断→测试点→用例生成
6. **.env 配置**: 确保后端正确加载项目根目录的 .env

---

## Phase 1: 后端基础设施补全

### Task 1.1: UDA 文档解析引擎 — Models & Schemas

**Files:**
- Modify: `backend/app/modules/uda/models.py`
- Modify: `backend/app/modules/uda/schemas.py`

**Step 1:** 实现 UDA models — ParsedDocument 和 DocumentChunk

```python
# models.py
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.shared.base_model import BaseModel
import uuid

class ParsedDocument(BaseModel):
    __tablename__ = "parsed_documents"
    requirement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("requirements.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(20))  # docx, pdf, md, txt, image
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_ast: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
```

**Step 2:** 实现 UDA schemas

---

### Task 1.2: UDA 文档解析引擎 — Service

**Files:**
- Modify: `backend/app/modules/uda/service.py`
- May create: `backend/app/modules/uda/parsers/docx_parser.py`
- May create: `backend/app/modules/uda/parsers/pdf_parser.py`
- May create: `backend/app/modules/uda/parsers/md_parser.py`

**Step 1:** 实现文档解析服务 — 支持 docx/pdf/md/txt 格式
- docx: python-docx 提取段落和表格
- pdf: pypdf 提取文本，PyMuPDF 提取图片
- md: 直接读取文本
- txt: 直接读取文本
- 图片: 可选 OCR（PaddleOCR 如可用）

**Step 2:** 实现文件上传到 MinIO 存储

---

### Task 1.3: UDA 文档解析引擎 — Router

**Files:**
- Modify: `backend/app/modules/uda/router.py`

**Step 1:** 实现 UDA API 端点
- POST `/api/uda/parse` — 上传并解析文档
- GET `/api/uda/{doc_id}` — 获取解析结果
- POST `/api/uda/parse-to-requirement` — 解析并创建/更新需求

---

### Task 1.4: 需求模块文件上传增强

**Files:**
- Modify: `backend/app/modules/products/router.py`
- Modify: `backend/app/modules/products/service.py`

**Step 1:** 增强 `/api/products/upload-requirement` 端点
- 支持 docx/pdf/md/txt/图片格式
- 调用 UDA 服务解析文档内容
- 将解析结果存入 Requirement.content_ast

---

## Phase 2: Prompt 体系实现

### Task 2.1: 增强系统 Prompt

**Files:**
- Modify: `backend/app/ai/prompts.py`

**Step 1:** 替换当前基础 prompts 为完整版本（来自 Sisyphus-Y_Prompt与Rule体系.md）
- DIAGNOSIS_SYSTEM: 10年测试架构师角色，6维度分析
- SCENE_MAP_SYSTEM: 测试点粒度规范，5种场景类型
- GENERATION_SYSTEM: 可执行用例规范，数据中台专项
- DIAGNOSIS_FOLLOWUP_SYSTEM: 苏格拉底追问，最多3轮
- DIFF_SEMANTIC_SYSTEM: 影响评级 needs_rewrite/needs_review/no_impact
- EXPLORATORY_SYSTEM: 自由对话模式

**Step 2:** 实现系统 Rules 常量
- RULE_FORMAT: JSON 纯净输出，步骤编号连续，ID 格式规范
- RULE_QUALITY: 禁止模糊断言，步骤原子性，P0≤8步
- RULE_DATAPLAT: 幂等性、大数据量、时区、状态机、权限隔离
- RULE_SAFETY: 禁止真实凭据，禁止越权

**Step 3:** 实现 7 层 Prompt 组装函数 `assemble_prompt()`

---

### Task 2.2: AI 配置数据模型

**Files:**
- Create: `backend/app/modules/ai_config/models.py`
- Create: `backend/app/modules/ai_config/schemas.py`
- Create: `backend/app/modules/ai_config/service.py`
- Create: `backend/app/modules/ai_config/router.py`
- Create: `backend/app/modules/ai_config/__init__.py`

**Step 1:** 创建 ai_configurations 表模型
- scope (global/product/iteration), scope_id
- system_rules_version, team_standard_prompt
- module_rules, output_preference (JSONB)
- scope_preference, rag_config, custom_checklist (JSONB)
- llm_model, llm_temperature

**Step 2:** 实现配置 CRUD service
**Step 3:** 实现配置继承逻辑 (iteration > product > global > default)
**Step 4:** 实现 API 路由

---

## Phase 3: 前端核心功能验证与修复

### Task 3.1: 验证并修复 CaseCard 渲染

**Files:**
- Check/Modify: `frontend/src/app/(main)/workbench/[id]/page.tsx`
- Check/Modify: `frontend/src/app/(main)/workbench/[id]/_components/CasePreviewCard.tsx`

**Step 1:** 检查 CaseCard 是否使用 JSON.stringify 直接渲染
**Step 2:** 确保 steps 数组逐条渲染，每步显示 step_num + action + expected_result

---

### Task 3.2: 需求文件上传前端

**Files:**
- Check/Modify: `frontend/src/app/(main)/requirements/page.tsx`

**Step 1:** 确保文件上传支持 docx/pdf/md/txt/图片格式
**Step 2:** 上传后调用后端解析 API
**Step 3:** 解析完成后自动填充需求内容

---

### Task 3.3: 全局样式验证

**Files:**
- Check/Modify: `frontend/src/app/globals.css`
- Check/Modify: 所有页面组件

**Step 1:** 确认所有页面使用 sy-* 颜色 token，无硬编码色值
**Step 2:** 确认所有图标来自 lucide-react
**Step 3:** 确认三栏布局各列独立滚动

---

## Phase 4: 数据库迁移

### Task 4.1: 创建新表迁移

**Files:**
- Create: `backend/alembic/versions/xxx_add_uda_and_ai_config.py`

**Step 1:** 生成包含 parsed_documents 和 ai_configurations 表的迁移
**Step 2:** 执行迁移

---

## Phase 5: 全链路打通与验证

### Task 5.1: 端到端流程验证

**Step 1:** 启动 Docker 基础设施 (PostgreSQL, Redis, MinIO)
**Step 2:** 启动后端服务
**Step 3:** 启动前端服务
**Step 4:** 验证完整流程：
1. 创建产品 → 创建迭代 → 上传需求文档
2. 文档解析成功
3. 发起诊断 → AI 流式返回诊断结果
4. 生成测试点 → 确认测试点
5. 进入工作台 → 流式生成测试用例
6. 用例正确渲染（非 JSON 字符串）

---

## Phase 6: 自测验收

### Task 6.1: agent-browser 自动化测试

使用 agent-browser skill 进行端到端自测：
1. 访问前端页面，验证所有模块可访问
2. 上传 docs/信永中和/v0.2.2/ 下的需求文档
3. 验证 LLM 调用成功（GLM 或阿里百炼）
4. 验证诊断、测试点、用例生成全流程
5. 验证全局样式一致性

---

## 任务优先级与依赖关系

```
Phase 1 (UDA) ──→ Phase 2 (Prompt) ──→ Phase 4 (Migration)
                                            │
Phase 3 (Frontend) ─────────────────────────┤
                                            ↓
                                      Phase 5 (E2E)
                                            ↓
                                      Phase 6 (Self-test)
```

## 预计任务总数

| Phase | 任务数 | 说明 |
|-------|--------|------|
| Phase 1 | 4 | UDA 引擎 + 上传增强 |
| Phase 2 | 2 | Prompt 体系 + AI 配置 |
| Phase 3 | 3 | 前端验证修复 |
| Phase 4 | 1 | 数据库迁移 |
| Phase 5 | 1 | 全链路验证 |
| Phase 6 | 1 | 自测验收 |
| **合计** | **12** | |
