# Phase 1: 清场 - Research

**Researched:** 2026-03-15
**Domain:** 模块裁剪 / 路由清理 / UI 简化
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MOD-01 | M09 迭代测试计划：删除前端入口和后端路由（保留 DB 表） | 后端 `_MODULE_NAMES` 列表动态注册，移除条目即可；前端导航已无 test-plan 入口，但路由目录需确认 |
| MOD-02 | M18 协作功能：删除前端入口，后端保留但不注册路由 | `collaboration` 在 `_MODULE_NAMES` 中，从列表移除即停止注册；前端 `/review/[token]` 页面存在需处理 |
| MOD-03 | M16 通知：简化为 Toast + 长任务进度条，不做通知中心/消息列表 | `sonner` 已安装且全局挂载，`NotificationBell` 组件 + `/notifications` 页面需替换/删除，`notification` 后端路由需从 `_MODULE_NAMES` 移除 |
| MOD-04 | M17 全局搜索：Cmd+K 唤起，只搜用例和需求两类，结果按类型分组 | `GlobalSearch.tsx` 已实现 Cmd+K，当前支持 5 种类型，需裁剪为 2 种；后端搜索 service 已支持 entity_types 过滤 |
| MOD-05 | M20 操作日志：设置页只读列表（最近 100 条，时间范围筛选） | 前端 `AuditLogs.tsx` 已有列表但缺少时间范围筛选；后端 `/api/audit` 端点缺少 `date_from`/`date_to` 参数；后端路径不匹配（前端调用 `/audit/logs`，实际端点为 `/audit`） |
</phase_requirements>

---

## Summary

Phase 1 是纯粹的「删减」阶段，目标是让代码库在主链路重构前先变干净。所有 5 个需求均属于已有代码的裁剪或局部补完，不涉及新的业务逻辑设计。

后端路由注册方式为动态 `importlib` 加载（`_MODULE_NAMES` 列表），因此移除模块只需从列表中删除模块名，无需修改路由文件本身。这一设计让 MOD-01（M09）和 MOD-02（M18）的后端工作极为简单——一行代码变更即可。

前端导航（`layout.tsx`）当前已无 test-plan / collaboration 的显式菜单项，但有 3 个关联组件需要处理：`NotificationBell`（通知铃铛 + 消息列表下拉）、`/notifications` 独立页面、`/review/[token]` 协作审阅页面。MOD-04 和 MOD-05 均需要少量功能补完而非纯删除。

**Primary recommendation:** 5 个需求拆为 5 个独立 Plan，按依赖顺序执行（MOD-01/02 后端 → MOD-03 前端 → MOD-04 前端 → MOD-05 前后端联动）。

---

## Standard Stack

### Core（此阶段用到的技术）

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI `_MODULE_NAMES` 动态注册 | — | 控制哪些路由被注册，移除名称即禁用路由 |
| Next.js App Router | 16 | 前端路由，删除目录即删除路由 |
| sonner | ^2.0.3 | Toast 通知，已全局挂载于根 `layout.tsx` |
| lucide-react | latest | 图标，替换 Bell 为合适图标 |
| SQLAlchemy 2.0 async | 2.0 | 后端 ORM，时间过滤用 `where(col >= from_dt)` |

### 不需要引入的库

此阶段全部是删减和小补丁，**不引入任何新依赖**。

---

## Architecture Patterns

### 后端路由开关机制

```python
# backend/app/main.py - 移除模块只需从此列表删除
_MODULE_NAMES = [
    "auth",
    "products",
    # ...
    "test_plan",      # MOD-01: 删除这一行 → /api/test-plans/* 返回 404
    # ...
    "collaboration",  # MOD-02: 删除这一行 → /api/collaboration/* 不注册
    "notification",   # MOD-03: 删除这一行 → /api/notifications/* 不注册
]
```

**重要约束：** 删除路由注册不等于删除模块文件，DB 表不受影响（Alembic 迁移独立管理）。

### 前端路由删除模式

Next.js App Router 中删除路由只需删除对应目录：

```
删除 frontend/src/app/(main)/notifications/   # MOD-03
删除 frontend/src/app/(main)/review/          # MOD-02（协作审阅页）
```

删除前检查是否有其他页面 `import` 或 `Link` 指向这些路径。

### Toast 替换通知中心模式

当前通知铃铛（`NotificationBell`）展开为下拉列表，点击「查看全部通知→」跳转到 `/notifications` 页面。

MOD-03 目标状态：
- 删除 `NotificationBell` 组件及其引用
- 删除 `/notifications` 页面目录
- `layout.tsx` 中 `<NotificationBell />` 替换为删除（无替代 UI，通知仅通过 sonner `toast()` 呈现）
- `ProgressDashboard` 组件已存在（负责长任务进度条），保留不动

### GlobalSearch 裁剪模式

当前 `GlobalSearch.tsx` 支持 5 种类型：`requirement | testcase | diagnosis | template | knowledge`

MOD-04 目标：仅保留 `requirement` 和 `testcase` 两种。

需要修改的点：
1. `typeConfig` 对象：只保留 `requirement` 和 `testcase`
2. `ValidType` 联合类型：缩减为两种
3. `mockResults`：清除非这两类的 mock 数据
4. 后端 `GET /api/search` 的 `types` 参数：前端调用时固定传 `types=requirement,testcase`
5. `SearchResultItem` 接口中 `type` 字段类型缩减

**注意：** 后端 `SearchService` 已支持 `entity_types` 过滤，不需要改后端逻辑。

### 审计日志时间范围筛选模式

当前状态：
- 后端 `/api/audit` GET 端点支持 `entity_type`、`action`、`user_id` 过滤，**无时间范围参数**
- 后端 service `get_audit_logs()` **无** `date_from`/`date_to` 参数
- 前端 `AuditLogs.tsx` 调用路径为 `/audit/logs?limit=100`，但实际端点是 `/audit`（路径不匹配 bug）
- 前端只有关键词搜索，**无时间范围 UI**

MOD-05 需要补完：
1. 后端 router：添加 `date_from: datetime | None` 和 `date_to: datetime | None` Query 参数
2. 后端 service：`where(AuditLog.created_at >= date_from)` / `where(AuditLog.created_at <= date_to)`
3. 后端 router：添加 `limit` 参数，支持最多 100 条（或固定 `page_size=100` 的第一页）
4. 前端 `AuditLogs.tsx`：
   - 修复 API 路径（`/audit/logs` → `/audit`）
   - 添加时间范围选择器（两个 `date` input）
   - 时间变化时重新请求

---

## Don't Hand-Roll

| 问题 | 不要自己实现 | 直接使用 |
|------|-------------|----------|
| Toast 通知 | 自定义 toast 组件 | `sonner` 的 `toast()` API（已安装） |
| 时间范围 date picker | 自定义日历组件 | HTML `<input type="date">` 或 shadcn/ui `<Input type="date">` |
| 路由 404 | 自定义 404 中间件 | 从 `_MODULE_NAMES` 删除，FastAPI 自动返回 404 |

---

## Common Pitfalls

### Pitfall 1: 删除路由但忘记清理前端引用

**What goes wrong:** 删除 `/notifications` 目录后，`NotificationBell` 中有 `Link href="/notifications"` 指向它，点击会出现 Next.js 404 但不报编译错误。
**Why it happens:** Next.js 不做 build-time Link href 合法性检查。
**How to avoid:** 删除路由目录时，同时搜索所有含该路径字符串的文件并处理。
**Warning signs:** TypeScript 编译通过但运行时点击报 404。

### Pitfall 2: 删除 `_MODULE_NAMES` 条目但模块依然被其他模块 import

**What goes wrong:** `notification` 路由虽不再注册，但若 `audit_middleware` 或其他模块直接 `import` notification service，应用启动仍会加载其代码。
**Why it happens:** 动态路由注册与 Python import 解耦，后者不受 `_MODULE_NAMES` 控制。
**How to avoid:** 用 grep 确认 `from app.modules.notification` / `from app.modules.test_plan` / `from app.modules.collaboration` 在非本模块文件中是否存在引用。

### Pitfall 3: 前端 AuditLogs API 路径错误

**What goes wrong:** 前端当前调用 `/audit/logs?limit=100`，但后端实际端点是 `GET /api/audit`，导致请求 404，触发 fallback demo 数据展示，看不出问题。
**Why it happens:** 前端用的是 demo fallback，错误被 try/catch 吞掉。
**How to avoid:** MOD-05 实施时第一步先修正 API 路径。

### Pitfall 4: 时间范围筛选只做前端不做后端

**What goes wrong:** 仅在前端用 JS 过滤 `created_at` 字段，但后端每次仍返回最近 100 条，时间范围筛选无法找到超过 100 条之前的记录。
**Why it happens:** 误以为前端过滤就够了。
**How to avoid:** 时间范围参数必须传给后端，后端 service 用 `where` 子句过滤后再分页。

### Pitfall 5: 删除 collaboration 路由但遗漏 review 页面

**What goes wrong:** `/api/collaboration/*` 路由停止注册，但前端 `/review/[token]` 页面还在，调用 `collaborationApi` 会报 404 网络错误并呈现异常 UI。
**Why it happens:** 协作功能的前端页面与后端路由是分开的，需要联动处理。
**How to avoid:** MOD-02 同时处理：移除 `_MODULE_NAMES` 中的 `collaboration`，并删除 `frontend/src/app/(main)/review/` 目录。

---

## Code Examples

### 后端：时间范围过滤 (AuditService)

```python
# backend/app/modules/audit/service.py
from datetime import datetime

async def get_audit_logs(
    self,
    entity_type: str | None = None,
    action: str | None = None,
    user_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[AuditLog], int]:
    q = select(AuditLog).where(AuditLog.deleted_at.is_(None))
    count_q = select(func.count()).select_from(AuditLog).where(AuditLog.deleted_at.is_(None))

    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
        count_q = count_q.where(AuditLog.entity_type == entity_type)
    if action:
        q = q.where(AuditLog.action == action)
        count_q = count_q.where(AuditLog.action == action)
    if user_id:
        q = q.where(AuditLog.user_id == user_id)
        count_q = count_q.where(AuditLog.user_id == user_id)
    if date_from:
        q = q.where(AuditLog.created_at >= date_from)
        count_q = count_q.where(AuditLog.created_at >= date_from)
    if date_to:
        q = q.where(AuditLog.created_at <= date_to)
        count_q = count_q.where(AuditLog.created_at <= date_to)

    total = (await self.session.execute(count_q)).scalar() or 0
    q = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await self.session.execute(q)
    return list(result.scalars().all()), total
```

### 后端：audit router 添加时间参数

```python
# backend/app/modules/audit/router.py
from datetime import datetime

@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    session: AsyncSessionDep,
    entity_type: str | None = None,
    action: str | None = None,
    user_id: uuid.UUID | None = None,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),  # 默认和上限均为100
) -> dict:
    svc = AuditService(session)
    logs, total = await svc.get_audit_logs(
        entity_type, action, user_id, date_from, date_to, page, page_size
    )
    return {
        "items": [AuditLogResponse.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }
```

### 前端：GlobalSearch 裁剪为 2 种类型

```typescript
// frontend/src/components/ui/GlobalSearch.tsx

// 修改 type 定义
interface SearchResult {
  id: string;
  title: string;
  type: 'requirement' | 'testcase';  // 从 5 种缩减为 2 种
  description: string;
  url: string;
}

// 修改 typeConfig
const typeConfig = {
  requirement: { label: '需求', icon: FileText, pill: 'pill-blue' },
  testcase: { label: '用例', icon: ClipboardList, pill: 'pill-green' },
};

// 后端调用时固定 types 参数
const response = await searchApi.search(query, { types: 'requirement,testcase' });
```

### 前端：AuditLogs 时间范围筛选

```typescript
// frontend/src/app/(main)/settings/_components/AuditLogs.tsx
const [dateFrom, setDateFrom] = useState('');
const [dateTo, setDateTo] = useState('');

const loadLogs = useCallback(async () => {
  setLoading(true);
  try {
    const params = new URLSearchParams({ page_size: '100' });
    if (dateFrom) params.set('date_from', new Date(dateFrom).toISOString());
    if (dateTo) params.set('date_to', new Date(dateTo + 'T23:59:59').toISOString());
    const data = await api.get<{ items: AuditEntry[] }>(`/audit?${params}`);
    setLogs(data.items);
  } catch { /* fallback */ }
}, [dateFrom, dateTo]);

// JSX 中添加两个 date input
<input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="input" />
<input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="input" />
```

---

## Current State Analysis（现状速览）

| 模块 | 后端状态 | 前端状态 | 清场工作量 |
|------|---------|---------|-----------|
| M09 test_plan | `_MODULE_NAMES` 中已注册，router 完整 | **无前端入口/路由目录** | 后端：删 1 行；前端：无需处理 |
| M18 collaboration | `_MODULE_NAMES` 中已注册，router 完整 | `/review/[token]` 页面存在 | 后端：删 1 行；前端：删目录 + 检查引用 |
| M16 notification | `_MODULE_NAMES` 中已注册，router 完整 | `NotificationBell` 组件 + `/notifications` 页面 + `layout.tsx` 引用 | 后端：删 1 行；前端：删 2 处 + 清 layout |
| M17 search | 已注册，支持多类型，路径正常 | `GlobalSearch.tsx` 已有 Cmd+K，5 种类型 | 后端：无需改；前端：裁剪类型 |
| M20 audit | 已注册，缺 date 参数，路径 `/audit` | `AuditLogs.tsx` 有列表，缺时间筛选，路径 bug | 后端：加参数；前端：修路径 + 加 UI |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (`asyncio_mode = "auto"`) |
| Config file | `backend/pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `cd backend && uv run pytest tests/unit/test_audit/ -x -q` |
| Full suite command | `cd backend && uv run pytest -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MOD-01 | `/api/test-plans/` 返回 404 | integration smoke | `uv run pytest tests/unit/test_test_plan/ -x -q` | ✅ (tests/unit/test_test_plan/ 存在) |
| MOD-02 | `/api/collaboration/` 路由不注册（返回 404） | integration smoke | `uv run pytest tests/unit/test_collaboration/ -x -q` | ✅ |
| MOD-03 | 后端 `/api/notifications/` 路由不注册 | integration smoke | `uv run pytest tests/unit/test_notification/ -x -q` | ✅ |
| MOD-04 | 搜索只返回 requirement/testcase 类型 | unit | `uv run pytest tests/unit/test_search/ -x -q` | ✅ |
| MOD-05 | 审计日志支持 date_from/date_to 过滤 | unit | `uv run pytest tests/unit/test_audit/ -x -q` | ✅ |

**注意：** MOD-03 前端「不存在通知中心/消息列表页面」和 MOD-04 前端「Cmd+K 只显示两类结果」为 manual-only（需人工验证），无法自动化测试。

### Sampling Rate

- **Per task commit:** `cd backend && uv run pytest tests/unit/test_audit/ tests/unit/test_search/ -x -q`
- **Per wave merge:** `cd backend && uv run pytest -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

现有测试目录存在，但需检查是否有覆盖「路由不注册返回 404」的测试用例，以及 `date_from`/`date_to` 过滤的单元测试。规划阶段建议补充：

- [ ] `tests/unit/test_audit/test_time_range_filter.py` — 覆盖 MOD-05 date_from/date_to 参数
- [ ] `tests/unit/test_search/test_entity_type_filter.py` — 覆盖 MOD-04 类型限制

---

## Open Questions

1. **review 页面的用户入口**
   - What we know: `/review/[token]` 是通过 URL 直接访问的，无 nav 入口
   - What's unclear: 是否有邮件/链接分享给外部用户的场景正在使用中
   - Recommendation: 删除前端目录；若有活跃使用场景则降级为 503 页面

2. **notification 后端是否有其他模块依赖**
   - What we know: 移除 `_MODULE_NAMES` 中的 `notification` 后路由不注册
   - What's unclear: `audit_middleware` 或其他中间件是否直接调用 `NotificationService`
   - Recommendation: Plan 执行前先 grep `from app.modules.notification` 确认无外部引用

3. **AuditLog 模型是否有 user_name 字段**
   - What we know: `AuditLog` 模型只有 `user_id`（UUID），无 `user_name` 字符串字段
   - What's unclear: 前端 `AuditEntry` 接口需要 `user_name`，但 `AuditLogResponse` 中无此字段
   - Recommendation: MOD-05 实施时需决策：① 关联查询 users 表，② `AuditLogResponse` 加 `user_name` 可选字段并由 service 填充；推荐方案②（避免引入跨模块 join）

---

## Sources

### Primary (HIGH confidence)

- 项目源码直接读取 — `backend/app/main.py`，`_MODULE_NAMES` 动态注册机制
- 项目源码直接读取 — `frontend/src/app/(main)/layout.tsx`，现有导航结构
- 项目源码直接读取 — `frontend/src/components/ui/GlobalSearch.tsx`，Cmd+K 实现
- 项目源码直接读取 — `backend/app/modules/audit/`（router/service/models/schemas）
- 项目源码直接读取 — `frontend/src/app/(main)/settings/_components/AuditLogs.tsx`

### Secondary (MEDIUM confidence)

- `frontend/package.json` — sonner ^2.0.3 已安装，确认 Toast 方案可用
- `backend/pyproject.toml` — pytest asyncio_mode=auto 确认测试框架配置

---

## Metadata

**Confidence breakdown:**

- MOD-01 (test_plan 删除): HIGH — 后端一行，前端已无入口，确认无误
- MOD-02 (collaboration 删除): HIGH — 后端一行 + 前端 review 目录，范围清晰
- MOD-03 (notification 简化): HIGH — 删除路由/组件/页面，保留 sonner + ProgressDashboard
- MOD-04 (search 裁剪): HIGH — GlobalSearch.tsx 读完，改动范围清晰
- MOD-05 (audit 补完): HIGH — 现状 gap 明确，补完方案标准

**Research date:** 2026-03-15
**Valid until:** 2026-04-15（代码库稳定，一月内有效）
