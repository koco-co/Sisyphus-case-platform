'use client';

import { BookOpen, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { apiClient } from '@/lib/api-client';
import type { TestPointItem } from '@/stores/scene-map-store';

interface RagResult {
  title: string;
  score: number;
  content: string;
}

interface RagPreviewPanelProps {
  requirementId: string | null;
  checkedPointIds: Set<string>;
  testPoints: TestPointItem[];
}

function sceneTypeToBadgeVariant(
  source: string,
): 'success' | 'warning' | 'danger' | 'info' | 'purple' | 'gray' {
  const map: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'purple' | 'gray'> = {
    document: 'success',
    supplemented: 'warning',
    missing: 'danger',
    pending: 'gray',
  };
  return map[source] ?? 'gray';
}

export default function RagPreviewPanel({
  requirementId,
  checkedPointIds,
  testPoints,
}: RagPreviewPanelProps) {
  const [ragResults, setRagResults] = useState<RagResult[]>([]);
  const [loading, setLoading] = useState(false);

  const checkedPoints = testPoints.filter((tp) => checkedPointIds.has(tp.id));

  useEffect(() => {
    if (!requirementId || checkedPointIds.size === 0) {
      setRagResults([]);
      return;
    }

    let cancelled = false;
    setLoading(true);

    apiClient<{ results: RagResult[] }>(`/scene-map/${requirementId}/rag-preview`, {
      method: 'POST',
      body: JSON.stringify({ test_point_ids: [...checkedPointIds] }),
    })
      .then((data) => {
        if (!cancelled) {
          setRagResults(data.results ?? []);
        }
      })
      .catch(() => {
        if (!cancelled) setRagResults([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [requirementId, checkedPointIds]);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Selected test points summary */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-sy-border">
        <p className="text-[11px] text-sy-text-3 uppercase tracking-wider mb-2">
          已选测试点 ({checkedPoints.length})
        </p>
        {checkedPoints.length === 0 ? (
          <p className="text-[12px] text-sy-text-3 italic">暂未勾选测试点</p>
        ) : (
          <div className="space-y-1.5 max-h-40 overflow-y-auto">
            {checkedPoints.map((tp) => (
              <div key={tp.id} className="flex items-start gap-2">
                <StatusBadge variant={sceneTypeToBadgeVariant(tp.source)}>{tp.source}</StatusBadge>
                <span className="text-[12px] text-sy-text-2 leading-relaxed">{tp.title}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* RAG history preview */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        <p className="text-[11px] text-sy-text-3 uppercase tracking-wider mb-3">历史用例预览</p>

        {checkedPointIds.size === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <BookOpen className="w-8 h-8 text-sy-text-3 opacity-20 mb-2" />
            <p className="text-[12px] text-sy-text-3">勾选测试点后将显示相关历史用例</p>
          </div>
        ) : loading ? (
          <div className="flex items-center justify-center py-8 gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-sy-text-3" />
            <span className="text-[12px] text-sy-text-3">检索历史用例...</span>
          </div>
        ) : ragResults.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <BookOpen className="w-8 h-8 text-sy-text-3 opacity-20 mb-2" />
            <p className="text-[12px] text-sy-text-3">未找到相关历史用例</p>
          </div>
        ) : (
          <div className="space-y-3">
            {ragResults.slice(0, 5).map((result, idx) => (
              <div
                key={`rag-${idx.toString()}`}
                className="rounded-md border border-sy-border bg-sy-bg-2 px-3 py-2.5 hover:-translate-y-px hover:border-sy-border-2 transition-all"
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <span className="text-[12px] font-medium text-sy-text leading-snug flex-1">
                    {result.title}
                  </span>
                  <span
                    className={`text-[11px] font-mono flex-shrink-0 px-1.5 py-0.5 rounded ${
                      result.score >= 0.8
                        ? 'bg-sy-accent/10 text-sy-accent'
                        : result.score >= 0.6
                          ? 'bg-amber/10 text-amber'
                          : 'bg-sy-bg-3 text-sy-text-3'
                    }`}
                  >
                    {result.score.toFixed(2)}
                  </span>
                </div>
                <p className="text-[11px] text-sy-text-3 leading-relaxed line-clamp-2">
                  {result.content.length > 100
                    ? `${result.content.slice(0, 100)}...`
                    : result.content}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
