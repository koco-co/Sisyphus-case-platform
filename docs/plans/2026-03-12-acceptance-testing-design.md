# Sisyphus-Y 全量验收测试设计

## 日期：2026-03-12

## 目标

对 Sisyphus-Y 平台执行全量验收测试，覆盖 8 大分类共 42 个测试任务。发现 Bug 即修复并全量重测，直到所有任务通过。

## 验收条件

1. 所有任务 `status: passed`
2. 平台中存在真实业务数据（`real_data_loaded: true`）
3. WebM 操作视频录制完成（`webm_recorded: true`，此项由用户手动完成）

## 任务分类

| 分类 | 任务范围 | 数量 |
|---|---|---|
| 基础设施验证 | TASK-001 ~ TASK-003 | 3 |
| AI 配置页面 | TASK-010 ~ TASK-020 | 11 |
| 数据清洗与导入 | TASK-030 ~ TASK-038 | 9 |
| 核心主链路 | TASK-050 ~ TASK-065 | 16 |
| 页面交互与视觉 | TASK-070 ~ TASK-079 | 10 |
| AI 生成质量保障 | TASK-080 ~ TASK-084 | 5 |
| 真实数据注入 | TASK-090 ~ TASK-091 | 2 |
| 全链路录屏 | TASK-100 | 1 (manual_required) |

## 循环迭代模型

```
发现 Bug → 立即修复 → git commit → iteration+1 → 所有任务重置 pending → 全量重测
```

## 技术手段

- 前端验证：webapp-testing skill (Playwright) 截图
- API 验证：curl 调用后端 REST API
- 数据库验证：psql / Python 脚本查询 PostgreSQL
- 向量库验证：Qdrant REST API
- 清洗数据审查：functional-test-case-reviewer skill 逐条审查

## 特殊标记

- `manual_required`：物理上不可在 CLI 执行（断网测试、WebM 录制）
- `blocked`：前置依赖未满足，等解锁后执行
