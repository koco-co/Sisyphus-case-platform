'use client';

import { ClipboardList, Loader2 } from 'lucide-react';
import { useMemo } from 'react';
import type { TestPointItem } from '@/stores/scene-map-store';
import type { WorkbenchTestCase } from '@/stores/workspace-store';

interface GeneratedCasesByPointProps {
  testCases: WorkbenchTestCase[];
  testPoints: TestPointItem[];
  isStreaming: boolean;
}

export function GeneratedCasesByPoint({
  testCases,
  testPoints,
  isStreaming,
}: GeneratedCasesByPointProps) {
  const grouped = useMemo(() => {
    const map = new Map<string, WorkbenchTestCase[]>();
    for (const tc of testCases) {
      const key = tc.test_point_id ?? '__unknown__';
      const list = map.get(key) ?? [];
      list.push(tc);
      map.set(key, list);
    }
    return map;
  }, [testCases]);

  const groupEntries = useMemo(() => [...grouped.entries()], [grouped]);

  const getPointTitle = (pointId: string) => {
    if (pointId === '__unknown__') return '未关联测试点';
    return testPoints.find((p) => p.id === pointId)?.title ?? `测试点 ${pointId.slice(0, 8)}`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* 头部 */}
      <div className="shrink-0 flex items-center gap-2 px-3 py-3 border-b border-sy-border">
        <ClipboardList className="w-4 h-4 text-sy-text-2" />
        <h4 className="text-[13px] font-semibold text-sy-text flex-1">已生成用例</h4>
        <span className="text-[11px] font-mono text-sy-accent font-semibold">
          共 {testCases.length} 条
        </span>
        {isStreaming && <Loader2 className="w-3.5 h-3.5 animate-spin text-sy-accent" />}
      </div>

      {/* 列表 */}
      <div className="flex-1 overflow-y-auto p-2 space-y-3">
        {testCases.length === 0 && !isStreaming && (
          <p className="text-center text-[12px] text-sy-text-3 py-8">暂无生成用例</p>
        )}

        {testCases.length === 0 && isStreaming && (
          <div className="flex items-center justify-center gap-2 py-8">
            <Loader2 className="w-4 h-4 animate-spin text-sy-accent" />
            <span className="text-[12px] text-sy-text-3">生成中...</span>
          </div>
        )}

        {groupEntries.map(([pointId, cases]) => (
          <div key={pointId} className="rounded-lg border border-sy-border overflow-hidden">
            {/* 分组头 */}
            <div className="flex items-center gap-2 px-3 py-2 bg-sy-bg-2 border-b border-sy-border">
              <span className="text-[11.5px] font-medium text-sy-text-2 flex-1 truncate">
                {getPointTitle(pointId)}
              </span>
              <span className="shrink-0 text-[11px] font-mono text-sy-accent font-semibold">
                {cases.length} 条
                {isStreaming && (
                  <span className="ml-1 inline-block w-1.5 h-1.5 rounded-full bg-sy-accent animate-pulse" />
                )}
              </span>
            </div>

            {/* 用例列表 */}
            <div className="divide-y divide-sy-border/50">
              {cases.map((tc) => (
                <div key={tc.id} className="px-3 py-2 hover:bg-sy-bg-2 transition-colors">
                  <p className="text-[12px] text-sy-text font-medium leading-snug">{tc.title}</p>
                  <p className="text-[11px] text-sy-text-3 mt-0.5">
                    {tc.steps.length} 个步骤
                    {tc.priority && (
                      <span className="ml-2 font-mono text-sy-warn">{tc.priority}</span>
                    )}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
