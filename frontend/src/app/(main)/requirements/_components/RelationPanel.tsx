'use client';

import { ChevronRight, ClipboardList, ExternalLink, Loader2, TreePine } from 'lucide-react';
import Link from 'next/link';
import { StatusPill } from '@/components/ui';
import { getAnalysisSceneMapHref, getWorkbenchHref } from '@/lib/analysisRoutes';

interface TestPointItem {
  id: string;
  title: string;
  group_name: string;
  priority: string;
  status: string;
}

interface TestCaseItem {
  id: string;
  case_id: string;
  title: string;
  priority: string;
  status: string;
}

interface RelationPanelProps {
  requirementId: string;
  testPoints: TestPointItem[];
  testCases: TestCaseItem[];
  loading?: boolean;
}

const priorityVariant = (p: string): 'red' | 'amber' | 'blue' | 'gray' => {
  if (p === 'P0') return 'red';
  if (p === 'P1') return 'amber';
  if (p === 'P2') return 'blue';
  return 'gray';
};

const statusVariant = (s: string): 'green' | 'amber' | 'gray' | 'blue' => {
  if (s === 'confirmed' || s === 'passed') return 'green';
  if (s === 'pending' || s === 'draft') return 'gray';
  if (s === 'running' || s === 'generating') return 'amber';
  return 'blue';
};

export function RelationPanel({
  requirementId,
  testPoints,
  testCases,
  loading = false,
}: RelationPanelProps) {
  if (loading) {
    return (
      <div className="bg-bg1 border border-border rounded-[10px] p-4">
        <div className="flex items-center justify-center py-8">
          <Loader2 size={16} className="text-text3 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Test Points */}
      <div className="bg-bg1 border border-border rounded-[10px] p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <TreePine size={14} className="text-accent" />
            <span className="text-[12px] font-semibold text-text2">关联测试点</span>
            <span className="text-[10px] font-mono text-text3 bg-bg3 px-1.5 py-0.5 rounded">
              {testPoints.length}
            </span>
          </div>
          <Link
            href={getAnalysisSceneMapHref(requirementId)}
            className="flex items-center gap-1 text-[11px] text-accent hover:text-accent2 transition-colors"
          >
            查看场景地图 <ExternalLink size={11} />
          </Link>
        </div>

        {testPoints.length === 0 ? (
          <div className="text-center py-4 text-text3 text-[12px]">暂无关联测试点</div>
        ) : (
          <div className="space-y-1 max-h-[200px] overflow-y-auto">
            {testPoints.map((tp) => (
              <Link
                key={tp.id}
                href={getAnalysisSceneMapHref(requirementId)}
                className="flex items-center gap-2 p-2 rounded-md hover:bg-bg2 transition-colors group"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-[12px] text-text truncate">{tp.title}</div>
                  <div className="text-[10.5px] text-text3 truncate">{tp.group_name}</div>
                </div>
                <StatusPill variant={priorityVariant(tp.priority)}>{tp.priority}</StatusPill>
                <ChevronRight
                  size={12}
                  className="text-text3 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                />
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Test Cases */}
      <div className="bg-bg1 border border-border rounded-[10px] p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <ClipboardList size={14} className="text-blue" />
            <span className="text-[12px] font-semibold text-text2">关联用例</span>
            <span className="text-[10px] font-mono text-text3 bg-bg3 px-1.5 py-0.5 rounded">
              {testCases.length}
            </span>
          </div>
          <Link
            href={getWorkbenchHref(requirementId)}
            className="flex items-center gap-1 text-[11px] text-accent hover:text-accent2 transition-colors"
          >
            生成工作台 <ExternalLink size={11} />
          </Link>
        </div>

        {testCases.length === 0 ? (
          <div className="text-center py-4 text-text3 text-[12px]">暂无关联用例</div>
        ) : (
          <div className="space-y-1 max-h-[200px] overflow-y-auto">
            {testCases.map((tc) => (
              <Link
                key={tc.id}
                href={`/testcases?highlight=${tc.id}`}
                className="flex items-center gap-2 p-2 rounded-md hover:bg-bg2 transition-colors group"
              >
                <span className="text-[11px] font-mono text-accent shrink-0">{tc.case_id}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-[12px] text-text truncate">{tc.title}</div>
                </div>
                <StatusPill variant={priorityVariant(tc.priority)}>{tc.priority}</StatusPill>
                <StatusPill variant={statusVariant(tc.status)}>
                  {tc.status === 'passed' ? '通过' : tc.status === 'draft' ? '草稿' : tc.status}
                </StatusPill>
                <ChevronRight
                  size={12}
                  className="text-text3 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
