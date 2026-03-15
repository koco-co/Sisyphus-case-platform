---
phase: 03-ai
plan: "03-02"
subsystem: ai
tags: [prompt-engineering, few-shot, glm-5, testing]
dependency_graph:
  requires: []
  provides: [PRM-01, PRM-02, PRM-03, PRM-04, RAG-06]
  affects: [backend/app/ai/prompts.py, frontend/src/app/(main)/workbench/_components/ChatArea.tsx]
tech_stack:
  added: []
  patterns: [few-shot-prompting, four-section-structure]
key_files:
  created: []
  modified:
    - backend/app/ai/prompts.py
    - backend/tests/unit/test_ai/test_prompts.py
    - frontend/src/app/(main)/workbench/_components/ChatArea.tsx
  deleted: []
decisions:
  - 保持 ChatArea.tsx 第 255 行不变，因该路径仅处理用户消息（isAI=false），whitespace-pre-wrap 已足够
  - 使用 ### ✅/❌ 标记区分正例/负例，与 GENERATION_SYSTEM 格式保持一致
  - 正例步骤数控制在 ≤4 步，避免 Prompt 膨胀
metrics:
  duration_minutes: 35
  tasks_completed: 2
  test_count: 4
  files_modified: 2
  commits: 2
---

# Phase 03 Plan 02: AI Prompt 质量提升 Summary

**One-liner:** 为 5 个 AI 模块补充 Few-shot 正负例示例，新增 Prompt 结构验证测试，确认 GLM-5 配置。

---

## 完成内容

### 1. 测试覆盖（PRM-02, PRM-03, PRM-04）

新增 4 个测试用例到 `backend/tests/unit/test_ai/test_prompts.py`：

| 测试 | 目的 | 验证点 |
|------|------|--------|
| `test_identity_unique` | 身份声明差异化 | 6 个模块身份声明首句互不相同，长度 >30 字 |
| `test_fewshot_present` | Few-shot 完整性 | 5 个模块均含正例（✅/正例）和负例（❌/负例）标记 |
| `test_four_section_structure` | 四段式结构 | 所有模块包含 ①身份声明 ②任务边界 ③输出规范 ④质量红线 |
| `test_glm5_config` | 模型配置 | `Settings().zhipu_model == "glm-5"` |

同时修复了既有测试 `test_assembly_layer_order` 的 substring 匹配问题（原测试查找 "测试健康诊断"，实际应为 "需求质量分析"）。

### 2. Few-shot 示例补充（PRM-01）

为 5 个模块各添加 2~3 正例 + 1 负例：

| 模块 | 正例场景 | 负例问题 |
|------|----------|----------|
| **DIAGNOSIS_SYSTEM** | 高风险（权限隔离缺失）、中风险（边界值模糊） | description 未引用原文，仅泛泛评价 |
| **SCENE_MAP_SYSTEM** | normal（登录主流程）、exception（批量导入异常） | estimated_cases=8 超出范围 + title 过长 |
| **DIAGNOSIS_FOLLOWUP_SYSTEM** | 单问句追问、追问总结格式 | 一次提出 3 个问题（违反"每次只问一个"） |
| **DIFF_SEMANTIC_SYSTEM** | needs_rewrite（接口参数类型变更）、needs_review（超时调整） | 实质业务变更但判为 no_impact |
| **EXPLORATORY_SYSTEM** | 登录超时场景、追加边界场景 | 用户要求修改单条但重新生成全套 |

格式统一使用 `### ✅ 正例 N — 场景描述` 和 `### ❌ 负例 N — 问题描述`，与 GENERATION_SYSTEM 保持一致。

### 3. SSE 换行渲染确认（RAG-06）

经代码审查确认：
- `renderMarkdown()` 函数已包含 `.replace(/\n/g, '<br/>')` 处理（第 33-34 行）
- AI 消息路径（第 235、244 行）均使用 `renderMarkdown` 处理
- 第 255 行 `<span className="whitespace-pre-wrap">` 仅在 `isAI=false`（用户消息）分支，whitespace-pre-wrap 已足够处理换行

**结论**：SSE 换行渲染无需修改，现有实现正确。

### 4. GLM-5 配置验证（PRM-04）

`backend/app/core/config.py` 中 `zhipu_model: str = "glm-5"` 已是目标值，测试验证通过。

---

## 测试状态

```bash
cd /Users/aa/WorkSpace/Projects/Sisyphus-case-platform/backend
uv run pytest tests/unit/test_ai/test_prompts.py -x -q
# 20 passed

bunx tsc --noEmit
# 无错误
```

---

## 提交记录

| Commit | 说明 |
|--------|------|
| `ee044fa` | test(03-02): add identity/fewshot/four_section/glm5_config tests |
| `9f21cc2` | feat(03-02): add Few-shot examples to 5 AI modules + fix test |

---

## 偏差记录

无偏差。计划执行与预期完全一致。

---

## 自检结果

- [x] `backend/app/ai/prompts.py` 已更新，5 个模块均含 Few-shot
- [x] `backend/tests/unit/test_ai/test_prompts.py` 新增测试通过
- [x] `bunx tsc --noEmit` 无 TypeScript 错误
- [x] `zhipu_model` 默认值为 "glm-5"

**自检状态：PASSED**
