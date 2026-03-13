'use client';

import { CheckCircle, Clock, MapPinned } from 'lucide-react';
import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';

interface TestPoint {
  id: string;
  title: string;
  group_name: string;
  source: string;
  priority: string;
  status: string;
  estimated_cases?: number;
}

interface TestCase {
  id: string;
  title: string;
  priority: string;
  status: string;
}

interface CoverageMatrixProps {
  reqId: string;
}

const sourceLabels: Record<string, string> = {
  document: '已覆盖',
  supplemented: 'AI补全',
  missing: '缺失',
  pending: '待确认',
};

const sourceClasses: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  document: {
    bg: 'bg-accent/10',
    text: 'text-accent',
    border: 'border-accent/30',
    dot: 'bg-accent',
  },
  supplemented: {
    bg: 'bg-amber/10',
    text: 'text-amber',
    border: 'border-amber/30',
    dot: 'bg-amber',
  },
  missing: { bg: 'bg-red/10', text: 'text-red', border: 'border-red/40', dot: 'bg-red' },
  pending: { bg: 'bg-bg3', text: 'text-text3', border: 'border-border2', dot: 'bg-text3' },
};

function getSourceKey(source: string): string {
  return source in sourceClasses ? source : 'pending';
}

type GroupedPoints = Record<
  string,
  { document: number; supplemented: number; missing: number; pending: number; total: number }
>;

export function CoverageMatrix({ reqId }: CoverageMatrixProps) {
  const [testPoints, setTestPoints] = useState<TestPoint[]>([]);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!reqId) return;
    setLoading(true);

    Promise.allSettled([
      apiClient<{ test_points: TestPoint[] }>(`/scene-map/${reqId}`),
      apiClient<TestCase[]>(`/testcases?requirement_id=${reqId}`),
    ]).then(([smResult, tcResult]) => {
      if (smResult.status === 'fulfilled') {
        setTestPoints(smResult.value.test_points ?? []);
      }
      if (tcResult.status === 'fulfilled') {
        setTestCases(Array.isArray(tcResult.value) ? tcResult.value : []);
      }
      setLoading(false);
    });
  }, [reqId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="text-[12px] text-text3">加载覆盖数据...</span>
      </div>
    );
  }

  if (testPoints.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <MapPinned className="w-12 h-12 text-text3 opacity-20 mb-3" />
        <p className="text-[14px] text-text3">暂无场景地图数据</p>
        <p className="text-[12px] text-text3 opacity-60 mt-1">完成 AI 分析后自动生成测试点</p>
      </div>
    );
  }

  // Group test points by group_name
  const groups: GroupedPoints = {};
  const groupNames: string[] = [];

  for (const tp of testPoints) {
    const group = tp.group_name || '其他';
    if (!groups[group]) {
      groups[group] = { document: 0, supplemented: 0, missing: 0, pending: 0, total: 0 };
      groupNames.push(group);
    }
    const key = getSourceKey(tp.source);
    if (key === 'document') groups[group].document++;
    else if (key === 'supplemented') groups[group].supplemented++;
    else if (key === 'missing') groups[group].missing++;
    else groups[group].pending++;
    groups[group].total++;
  }

  // Summary stats
  const totalCovered = testPoints.filter((tp) => tp.source === 'document').length;
  const totalMissing = testPoints.filter((tp) => tp.source === 'missing').length;
  const coverageRate =
    testPoints.length > 0 ? Math.round((totalCovered / testPoints.length) * 100) : 0;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Summary bar */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-border bg-bg1">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-accent" />
            <span className="text-[11px] text-text3">
              已覆盖 <span className="text-accent font-mono font-semibold">{totalCovered}</span>
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-red" />
            <span className="text-[11px] text-text3">
              缺失 <span className="text-red font-mono font-semibold">{totalMissing}</span>
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] text-text3">覆盖率</span>
            <span
              className={`font-mono text-[13px] font-semibold ${coverageRate >= 70 ? 'text-accent' : coverageRate >= 40 ? 'text-amber' : 'text-red'}`}
            >
              {coverageRate}%
            </span>
          </div>
          {testCases.length > 0 && (
            <div className="ml-auto flex items-center gap-1.5">
              <CheckCircle className="w-3 h-3 text-accent" />
              <span className="text-[11px] text-text3">
                已生成用例 <span className="text-accent font-mono">{testCases.length}</span> 条
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Matrix table */}
      <div className="flex-1 overflow-auto px-4 py-3">
        <table className="w-full text-[12px] border-collapse">
          <thead>
            <tr>
              <th className="text-left py-2 px-3 text-[11px] text-text3 font-medium bg-bg2 rounded-tl-lg border-b border-border w-[40%]">
                需求域 / 场景
              </th>
              <th className="py-2 px-2 text-center text-[11px] font-medium bg-accent/8 text-accent border-b border-border">
                已覆盖
              </th>
              <th className="py-2 px-2 text-center text-[11px] font-medium bg-amber/8 text-amber border-b border-border">
                AI补全
              </th>
              <th className="py-2 px-2 text-center text-[11px] font-medium bg-red/8 text-red border-b border-border">
                缺失
              </th>
              <th className="py-2 px-2 text-center text-[11px] font-medium bg-bg3 text-text3 border-b border-border rounded-tr-lg">
                待确认
              </th>
            </tr>
          </thead>
          <tbody>
            {groupNames.map((groupName, i) => {
              const counts = groups[groupName];
              const groupCoveredRate =
                counts.total > 0 ? Math.round((counts.document / counts.total) * 100) : 0;
              return (
                <tr
                  key={groupName}
                  className={`border-b border-border/50 hover:bg-bg2/40 transition-colors ${i % 2 === 0 ? '' : 'bg-bg1/30'}`}
                >
                  <td className="py-2.5 px-3">
                    <div className="font-medium text-text truncate">{groupName}</div>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <div className="h-1 flex-1 bg-bg3 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${groupCoveredRate >= 70 ? 'bg-accent' : groupCoveredRate >= 40 ? 'bg-amber' : 'bg-red'}`}
                          style={{ width: `${groupCoveredRate}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-text3 font-mono w-8 text-right">
                        {groupCoveredRate}%
                      </span>
                    </div>
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    {counts.document > 0 ? (
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-accent/15 text-accent font-mono text-[12px] font-semibold">
                        {counts.document}
                      </span>
                    ) : (
                      <span className="text-text3 text-[11px]">—</span>
                    )}
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    {counts.supplemented > 0 ? (
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber/15 text-amber font-mono text-[12px] font-semibold">
                        {counts.supplemented}
                      </span>
                    ) : (
                      <span className="text-text3 text-[11px]">—</span>
                    )}
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    {counts.missing > 0 ? (
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-red/15 text-red font-mono text-[12px] font-semibold">
                        {counts.missing}
                      </span>
                    ) : (
                      <span className="text-text3 text-[11px]">—</span>
                    )}
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    {counts.pending > 0 ? (
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-bg3 text-text3 font-mono text-[12px] font-semibold">
                        {counts.pending}
                      </span>
                    ) : (
                      <span className="text-text3 text-[11px]">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {/* Test point detail list */}
        {testPoints.length > 0 && (
          <div className="mt-4">
            <div className="text-[11px] text-text3 uppercase tracking-wider mb-2 px-0.5">
              测试点明细
            </div>
            <div className="space-y-1">
              {testPoints.map((tp) => {
                const key = getSourceKey(tp.source);
                const cfg = sourceClasses[key];
                return (
                  <div
                    key={tp.id}
                    className={`flex items-center gap-2.5 px-2.5 py-2 rounded-md border ${cfg.bg} ${cfg.border}`}
                  >
                    <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
                    <div className="flex-1 min-w-0">
                      <span className={`text-[12px] ${cfg.text} truncate block`}>{tp.title}</span>
                      <span className="text-[10px] text-text3">{tp.group_name}</span>
                    </div>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <span
                        className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                          tp.priority === 'P0'
                            ? 'bg-red/10 text-red'
                            : tp.priority === 'P1'
                              ? 'bg-amber/10 text-amber'
                              : 'bg-bg3 text-text3'
                        }`}
                      >
                        {tp.priority}
                      </span>
                      <span
                        className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full ${cfg.bg} ${cfg.text} border ${cfg.border}`}
                      >
                        {sourceLabels[key] ?? key}
                      </span>
                    </div>
                    {tp.estimated_cases != null && tp.estimated_cases > 0 && (
                      <div className="flex items-center gap-1 flex-shrink-0">
                        <Clock className="w-3 h-3 text-text3" />
                        <span className="text-[10px] text-text3 font-mono">
                          {tp.estimated_cases}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
