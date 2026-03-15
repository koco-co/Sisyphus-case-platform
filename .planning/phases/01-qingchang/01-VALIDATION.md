---
phase: 1
slug: qingchang
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend) + Playwright/手动 (frontend) |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `cd backend && uv run pytest tests/ -x -q` |
| **Full suite command** | `cd backend && uv run pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest tests/ -x -q`
- **After every plan wave:** Run `cd backend && uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | MOD-01 | integration | `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/test-plan/` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | MOD-02 | integration | `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/collaboration/` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | MOD-03 | manual | 手动检查通知 Toast 显示 | manual | ⬜ pending |
| 1-03-01 | 03 | 2 | MOD-04 | manual | 手动按 Cmd+K 验证搜索仅返回 testcase/requirement | manual | ⬜ pending |
| 1-04-01 | 04 | 2 | MOD-05 | integration | `cd backend && uv run pytest tests/unit/test_audit/ -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_audit/test_audit_filter.py` — MOD-05 时间范围过滤测试桩
- [ ] `tests/unit/test_search/test_search_types.py` — MOD-04 entity_types 过滤测试桩
- [ ] `tests/conftest.py` — 确认共享 fixtures 存在

*若现有基础设施已覆盖所有需求，Wave 0 只需创建缺失的测试文件。*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 通知以 Toast + 进度条呈现，无通知中心页面 | MOD-03 | 纯 UI 删除，无对应后端 API | 启动前端，触发任意通知事件，确认只出现 Toast 而非通知列表 |
| Cmd+K 全局搜索结果分类展示 | MOD-04 | 搜索结果分组 UI 需目视确认 | 按 Cmd+K，输入关键词，确认只有「需求」「用例」两个分组 |
| M09/M18 导航入口不可见 | MOD-01/02 | 前端路由删除后 UI 确认 | 刷新页面，确认导航栏无「迭代测试计划」「协作」入口 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
