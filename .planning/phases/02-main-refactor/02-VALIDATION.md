---
phase: 2
slug: main-refactor
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio (`asyncio_mode = "auto"`) |
| **Config file** | `backend/pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `uv run pytest tests/unit/test_diagnosis/ -x -q` |
| **Full suite command** | `uv run pytest -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/test_diagnosis/ -x -q`
- **After every plan wave:** Run `uv run pytest -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | ANA-01 | unit (smoke) | `uv run pytest tests/unit/test_diagnosis/test_diagnosis_api.py -x` | ✅ | ⬜ pending |
| 2-01-02 | 01 | 1 | ANA-07 | unit | `uv run pytest tests/unit/test_diagnosis/test_diagnosis_service.py -x` | ✅ | ⬜ pending |
| 2-01-03 | 01 | 1 | ANA-07 | unit | `uv run pytest tests/unit/test_diagnosis/test_diagnosis_api.py::test_confirm_risk -x` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 2 | WRK-04 | unit | `uv run pytest tests/unit/test_scene_map/test_rag_preview.py -x` | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 3 | WRK-07 | unit (frontend) | `bun run test -- workbench` | ❌ W0 (optional) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_diagnosis/test_diagnosis_api.py` — 新增 `test_confirm_risk` 测试 PATCH confirm 端点
- [ ] `tests/unit/test_scene_map/test_rag_preview.py` — 覆盖 RAG 预览端点降级行为（Qdrant 不可达返回空列表而非 500）
- [ ] Alembic migration stub: `uv run alembic revision --autogenerate -m "add_confirmed_to_diagnosis_risks"` + `uv run alembic upgrade head`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 分析台三 Tab 切换不刷新、状态保持 | ANA-02, ANA-04 | DOM 保持策略需浏览器验证 | 切换三 Tab 后刷新页面，验证所选 Tab 和内容完整恢复 |
| 广度扫描在上、追问对话框在下，两区同屏可见 | ANA-05 | 布局视觉验证 | 打开 AI 分析 Tab，在 1080p 分辨率确认两区不重叠 |
| 高风险项未确认时「进入工作台」按钮置灰 + hover 提示 | ANA-06, ANA-07 | 交互逻辑端到端验证 | 制造高风险项未确认场景，验证按钮状态和 tooltip |
| 工作台回到 Step1 追加测试点后继续生成不清空已有用例 | WRK-07 | SSE + store 端到端验证 | 生成用例后回 Step1 追加，验证追加生成结果累积 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
