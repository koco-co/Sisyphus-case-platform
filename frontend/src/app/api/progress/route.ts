import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { NextResponse } from 'next/server';

interface LegacyRawTask {
  id: string;
  group: string;
  module: string;
  title: string;
  status: string;
  description?: string;
}

interface CurrentRawTask {
  id: string;
  category: string;
  title: string;
  status: string;
  steps?: string[];
  expected?: string[];
  evidence?: string;
}

interface LegacyRawProgress {
  version: string;
  lastUpdated: string;
  stats: Record<string, number>;
  tasks: LegacyRawTask[];
}

interface CurrentRawProgress {
  project: string;
  version: string;
  last_updated: string;
  stats: Record<string, number>;
  tasks: CurrentRawTask[];
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
  M00: '产品/迭代/需求',
  M01: '文档解析(UDA)',
  M02: '数据清洗',
  M03: '需求分析',
  M04: '场景地图',
  M05: '用例生成工作台',
  M06: '用例管理',
  M07: 'Diff分析',
  M08: '覆盖度矩阵',
  M09: '测试计划',
  M10: '模板库',
  M11: '知识库(RAG)',
  M12: '导出集成',
  M13: '执行回流',
  M14: '质量看板',
  M16: '通知系统',
  M17: '全局搜索',
  M18: '协作功能',
  M19: '首页仪表盘',
  M20: '审计日志',
  M21: '回收站',
  infra: '基础设施',
  test: '测试',
  ui: 'UI组件',
  integration: '集成测试',
  'engine-case_gen': '用例生成引擎',
  'engine-diagnosis': '分析引擎',
  'engine-scene_map': '场景地图引擎',
  'engine-diff': 'Diff引擎',
  'engine-rag': 'RAG引擎',
  'engine-uda': 'UDA引擎',
};

function derivePhaseStatus(modules: { status: string }[]): string {
  if (modules.every((m) => m.status === 'done')) return 'done';
  if (
    modules.some((m) => m.status === 'in_progress' || m.status === 'done' || m.status === 'partial')
  ) {
    return 'in_progress';
  }
  return 'pending';
}

function transformLegacyProgress(raw: LegacyRawProgress) {
  const phaseMap = new Map<
    string,
    {
      id: string;
      name: string;
      order: number;
      moduleMap: Map<string, { id: string; name: string; tasks: LegacyRawTask[] }>;
    }
  >();

  for (const task of raw.tasks) {
    const groupCfg = GROUP_LABELS[task.group] ?? { phase: 'other', phaseName: '其他', order: 99 };

    let phase = phaseMap.get(groupCfg.phase);
    if (!phase) {
      phase = {
        id: groupCfg.phase,
        name: groupCfg.phaseName,
        order: groupCfg.order,
        moduleMap: new Map(),
      };
      phaseMap.set(groupCfg.phase, phase);
    }

    const modKey = task.module;
    let module = phase.moduleMap.get(modKey);
    if (!module) {
      module = {
        id: modKey,
        name: MODULE_NAMES[modKey] ?? modKey,
        tasks: [],
      };
      phase.moduleMap.set(modKey, module);
    }
    module.tasks.push(task);
  }

  const phases = [...phaseMap.values()]
    .sort((a, b) => a.order - b.order)
    .map((phase) => {
      const modules = [...phase.moduleMap.values()].map((mod) => {
        const tasks = mod.tasks.map((task) => ({
          id: task.id,
          name: task.title,
          status: task.status,
          type: task.group,
        }));
        const allDone = tasks.every((task) => task.status === 'done');
        const anyActive = tasks.some(
          (task) =>
            task.status === 'in_progress' || task.status === 'done' || task.status === 'partial',
        );
        const status = allDone ? 'done' : anyActive ? 'in_progress' : 'pending';
        return { id: mod.id, name: mod.name, status, tasks };
      });
      return { id: phase.id, name: phase.name, status: derivePhaseStatus(modules), modules };
    });

  return { version: raw.version, lastUpdated: raw.lastUpdated, phases };
}

function mapCurrentStatus(status: string): 'done' | 'partial' | 'failed' | 'pending' {
  switch (status) {
    case 'passed':
      return 'done';
    case 'manual_required':
      return 'partial';
    case 'failed':
      return 'failed';
    default:
      return 'pending';
  }
}

function slugifyCategory(value: string): string {
  return value
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^\p{Letter}\p{Number}-]+/gu, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .toLowerCase();
}

function transformCurrentProgress(raw: CurrentRawProgress) {
  const phaseMap = new Map<
    string,
    {
      id: string;
      name: string;
      order: number;
      modules: Array<{ id: string; name: string; status: string }>;
    }
  >();

  raw.tasks.forEach((task, index) => {
    const phaseId = slugifyCategory(task.category) || 'other';
    let phase = phaseMap.get(phaseId);
    if (!phase) {
      phase = {
        id: phaseId,
        name: task.category || '其他',
        order: index,
        modules: [],
      };
      phaseMap.set(phaseId, phase);
    }
    phase.modules.push({
      id: task.id,
      name: task.title,
      status: mapCurrentStatus(task.status),
    });
  });

  const phases = [...phaseMap.values()]
    .sort((a, b) => a.order - b.order)
    .map((phase) => ({
      id: phase.id,
      name: phase.name,
      status: derivePhaseStatus(phase.modules),
      modules: phase.modules,
    }));

  return {
    version: raw.version,
    lastUpdated: raw.last_updated,
    phases,
  };
}

function isLegacyProgress(raw: LegacyRawProgress | CurrentRawProgress): raw is LegacyRawProgress {
  return 'lastUpdated' in raw;
}

function transformProgress(raw: LegacyRawProgress | CurrentRawProgress) {
  return isLegacyProgress(raw) ? transformLegacyProgress(raw) : transformCurrentProgress(raw);
}

export async function GET() {
  try {
    const filePath = join(process.cwd(), '..', 'progress.json');
    const content = await readFile(filePath, 'utf-8');
    const raw = JSON.parse(content) as LegacyRawProgress | CurrentRawProgress;
    return NextResponse.json(transformProgress(raw));
  } catch {
    return NextResponse.json({ error: 'Progress data not available' }, { status: 404 });
  }
}
