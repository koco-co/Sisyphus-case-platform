import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { NextResponse } from 'next/server';

interface RawTask {
  id: string;
  group: string;
  module: string;
  title: string;
  status: string;
  description?: string;
}

interface RawProgress {
  version: string;
  lastUpdated: string;
  stats: Record<string, number>;
  tasks: RawTask[];
}

const GROUP_LABELS: Record<string, { phase: string; phaseName: string; order: number }> = {
  'P0-workbench': { phase: 'P0', phaseName: 'P0 — 核心工作台', order: 0 },
  'P0-data-clean': { phase: 'P0', phaseName: 'P0 — 核心工作台', order: 0 },
  'P1-core-modules': { phase: 'P1', phaseName: 'P1 — 核心业务模块', order: 1 },
  'P1-ai-config': { phase: 'P1', phaseName: 'P1 — 核心业务模块', order: 1 },
  'P1-ui-components': { phase: 'P1', phaseName: 'P1 — 核心业务模块', order: 1 },
  'P2-infrastructure': { phase: 'P2', phaseName: 'P2 — 基础设施与测试', order: 2 },
  'P2-testing': { phase: 'P2', phaseName: 'P2 — 基础设施与测试', order: 2 },
};

const MODULE_NAMES: Record<string, string> = {
  M00: '产品/迭代/需求', M01: '文档解析(UDA)', M02: '数据清洗',
  M03: '需求诊断', M04: '场景地图', M05: '用例生成工作台',
  M06: '用例管理', M07: 'Diff分析', M08: '覆盖度矩阵',
  M09: '测试计划', M10: '模板库', M11: '知识库(RAG)',
  M12: '导出集成', M13: '执行回流', M14: '质量看板',
  M16: '通知系统', M17: '全局搜索', M18: '协作功能',
  M19: '首页仪表盘', M20: '审计日志', M21: '回收站',
  infra: '基础设施', test: '测试', ui: 'UI组件', integration: '集成测试',
  'engine-case_gen': '用例生成引擎', 'engine-diagnosis': '诊断引擎',
  'engine-scene_map': '场景地图引擎', 'engine-diff': 'Diff引擎',
  'engine-rag': 'RAG引擎', 'engine-uda': 'UDA引擎',
};

function derivePhaseStatus(modules: { status: string }[]): string {
  if (modules.every((m) => m.status === 'done')) return 'done';
  if (modules.some((m) => m.status === 'in_progress' || m.status === 'done')) return 'in_progress';
  return 'pending';
}

function transformProgress(raw: RawProgress) {
  const phaseMap = new Map<string, { id: string; name: string; order: number; moduleMap: Map<string, { id: string; name: string; tasks: RawTask[] }> }>();

  for (const task of raw.tasks) {
    const groupCfg = GROUP_LABELS[task.group] ?? { phase: 'other', phaseName: '其他', order: 99 };

    if (!phaseMap.has(groupCfg.phase)) {
      phaseMap.set(groupCfg.phase, { id: groupCfg.phase, name: groupCfg.phaseName, order: groupCfg.order, moduleMap: new Map() });
    }
    const phase = phaseMap.get(groupCfg.phase)!;

    const modKey = task.module;
    if (!phase.moduleMap.has(modKey)) {
      phase.moduleMap.set(modKey, { id: modKey, name: MODULE_NAMES[modKey] ?? modKey, tasks: [] });
    }
    phase.moduleMap.get(modKey)!.tasks.push(task);
  }

  const phases = [...phaseMap.values()]
    .sort((a, b) => a.order - b.order)
    .map((p) => {
      const modules = [...p.moduleMap.values()].map((m) => {
        const tasks = m.tasks.map((t) => ({ id: t.id, name: t.title, status: t.status, type: t.group }));
        const allDone = tasks.every((t) => t.status === 'done');
        const anyActive = tasks.some((t) => t.status === 'in_progress' || t.status === 'done');
        const status = allDone ? 'done' : anyActive ? 'in_progress' : 'pending';
        return { id: m.id, name: m.name, status, tasks };
      });
      return { id: p.id, name: p.name, status: derivePhaseStatus(modules), modules };
    });

  return { version: raw.version, lastUpdated: raw.lastUpdated, phases };
}

export async function GET() {
  try {
    const filePath = join(process.cwd(), '..', 'progress.json');
    const content = await readFile(filePath, 'utf-8');
    const raw = JSON.parse(content) as RawProgress;
    return NextResponse.json(transformProgress(raw));
  } catch {
    return NextResponse.json({ error: 'Progress data not available' }, { status: 404 });
  }
}
