'use client';

import { AlertTriangle, CheckCircle, Clock, MapPinned, XCircle } from 'lucide-react';
import type { SceneMapData } from '@/lib/api';

interface ScenePreviewProps {
  sceneMap: SceneMapData | null;
  loading?: boolean;
}

const sourceConfig: Record<string, { label: string; dotClass: string; nodeClass: string }> = {
  document: {
    label: '已覆盖',
    dotClass: 'bg-accent',
    nodeClass: 'bg-accent/10 border-accent/35 text-accent',
  },
  supplemented: {
    label: 'AI 补全',
    dotClass: 'bg-amber',
    nodeClass: 'bg-amber/10 border-amber/35 text-amber',
  },
  missing: {
    label: '缺失',
    dotClass: 'bg-red',
    nodeClass: 'bg-red/10 border-red text-red font-semibold',
  },
  pending: {
    label: '待确认',
    dotClass: 'bg-text3',
    nodeClass: 'bg-bg3 border-dashed border-border2 text-text3',
  },
};

function getSourceKey(source: string): string {
  if (source in sourceConfig) return source;
  return 'pending';
}

export function ScenePreview({ sceneMap, loading }: ScenePreviewProps) {
  if (loading) {
    return (
      <div className="p-4 text-center">
        <div className="text-text3 text-[12px]">加载中...</div>
      </div>
    );
  }

  const testPoints = sceneMap?.test_points ?? [];

  const counts = {
    document: testPoints.filter((tp) => tp.source === 'document').length,
    supplemented: testPoints.filter((tp) => tp.source === 'supplemented').length,
    missing: testPoints.filter((tp) => tp.source === 'missing').length,
    pending: testPoints.filter((tp) => !['document', 'supplemented', 'missing'].includes(tp.source))
      .length,
  };

  const statCards = [
    {
      label: '已覆盖',
      count: counts.document,
      icon: CheckCircle,
      color: 'text-accent',
      bg: 'bg-accent/10',
    },
    {
      label: 'AI 补全',
      count: counts.supplemented,
      icon: AlertTriangle,
      color: 'text-amber',
      bg: 'bg-amber/10',
    },
    {
      label: '缺失',
      count: counts.missing,
      icon: XCircle,
      color: 'text-red',
      bg: 'bg-red/10',
    },
    {
      label: '待确认',
      count: counts.pending,
      icon: Clock,
      color: 'text-text3',
      bg: 'bg-bg3',
    },
  ];

  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-4">
        <MapPinned className="w-3.5 h-3.5 text-accent" />
        <span className="text-[12px] font-semibold text-text2">场景地图预览</span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className={`${stat.bg} rounded-lg px-3 py-2.5 border border-transparent`}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <Icon className={`w-3 h-3 ${stat.color}`} />
                <span className="text-[10px] text-text3">{stat.label}</span>
              </div>
              <div className={`font-mono text-[18px] font-semibold ${stat.color}`}>
                {stat.count}
              </div>
            </div>
          );
        })}
      </div>

      {/* Test Point Nodes */}
      {testPoints.length > 0 ? (
        <div className="space-y-1">
          <div className="text-[11px] text-text3 mb-2">测试点列表</div>
          {testPoints.map((tp) => {
            const config = sourceConfig[getSourceKey(tp.source)];
            return (
              <div
                key={tp.id}
                className={`flex items-center gap-2 px-2.5 py-2 rounded-md border ${config.nodeClass} transition-colors`}
              >
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${config.dotClass}`} />
                <div className="flex-1 min-w-0">
                  <div className="text-[11.5px] truncate">{tp.title}</div>
                  <div className="text-[10px] opacity-70">{tp.group_name}</div>
                </div>
                <span
                  className={`flex-shrink-0 text-[10px] font-mono px-1.5 py-0.5 rounded ${
                    tp.priority === 'P0'
                      ? 'bg-red/10 text-red'
                      : tp.priority === 'P1'
                        ? 'bg-amber/10 text-amber'
                        : 'bg-bg3 text-text3'
                  }`}
                >
                  {tp.priority}
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-6">
          <MapPinned className="w-10 h-10 text-text3 opacity-30 mx-auto mb-2" />
          <div className="text-[12px] text-text3">完成分析后自动生成场景地图</div>
        </div>
      )}
    </div>
  );
}
