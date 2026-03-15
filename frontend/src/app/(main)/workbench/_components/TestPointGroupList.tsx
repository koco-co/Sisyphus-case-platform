'use client';

import { ChevronDown, ChevronRight, Plus, Sparkles } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useSceneMap } from '@/hooks/useSceneMap';
import type { TestPointItem } from '@/stores/scene-map-store';

const FOLD_THRESHOLD = 5;

interface TestPointGroupListProps {
  requirementId: string | null;
  checkedPointIds: Set<string>;
  onToggle: (id: string) => void;
  onAdd: (groupName: string, title: string) => void;
  onStartGenerate: () => void;
}

function sceneTypeToBadgeVariant(
  sceneType: string,
): 'success' | 'warning' | 'danger' | 'info' | 'purple' | 'gray' {
  const map: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'purple' | 'gray'> = {
    document: 'success',
    supplemented: 'warning',
    missing: 'danger',
    pending: 'gray',
  };
  return map[sceneType] ?? 'gray';
}

interface GroupSectionProps {
  groupName: string;
  points: TestPointItem[];
  checkedPointIds: Set<string>;
  onToggle: (id: string) => void;
  onAdd: (groupName: string, title: string) => void;
}

function GroupSection({ groupName, points, checkedPointIds, onToggle, onAdd }: GroupSectionProps) {
  const [expanded, setExpanded] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [addingPoint, setAddingPoint] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (addingPoint) {
      inputRef.current?.focus();
    }
  }, [addingPoint]);

  const checkedCount = points.filter((p) => checkedPointIds.has(p.id)).length;
  const visiblePoints = showAll ? points : points.slice(0, FOLD_THRESHOLD);
  const hiddenCount = points.length - FOLD_THRESHOLD;

  const handleAddSubmit = useCallback(() => {
    const trimmed = newTitle.trim();
    if (trimmed) {
      onAdd(groupName, trimmed);
    }
    setNewTitle('');
    setAddingPoint(false);
  }, [groupName, newTitle, onAdd]);

  return (
    <div className="mb-3">
      {/* Group header */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center gap-1.5 w-full px-3 py-1.5 text-left hover:bg-sy-bg-2 transition-colors rounded-md"
      >
        {expanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-sy-text-3 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-sy-text-3 flex-shrink-0" />
        )}
        <span className="text-[12px] font-semibold text-sy-text flex-1">{groupName}</span>
        <span className="text-[11px] text-sy-text-3 font-mono">
          {checkedCount}/{points.length}
        </span>
      </button>

      {expanded && (
        <div className="ml-2 space-y-1 mt-1">
          {visiblePoints.map((point) => (
            <button
              key={point.id}
              type="button"
              className="flex items-start gap-2.5 px-3 py-2 rounded-md hover:bg-sy-bg-2 transition-colors w-full text-left group"
              onClick={() => onToggle(point.id)}
            >
              {/* Checkbox */}
              <div
                className={`mt-0.5 w-3.5 h-3.5 flex-shrink-0 rounded border transition-colors ${
                  checkedPointIds.has(point.id)
                    ? 'bg-sy-accent border-sy-accent'
                    : 'border-sy-border-2 bg-transparent group-hover:border-sy-accent/50'
                }`}
                aria-hidden="true"
              >
                {checkedPointIds.has(point.id) && (
                  <svg viewBox="0 0 14 14" fill="none" className="w-full h-full" aria-hidden="true">
                    <path
                      d="M2.5 7L5.5 10L11.5 4"
                      stroke="black"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </div>

              {/* Title + badges */}
              <div className="flex-1 min-w-0">
                <span
                  className={`text-[12px] leading-relaxed block ${
                    checkedPointIds.has(point.id) ? 'text-sy-text' : 'text-sy-text-2'
                  }`}
                >
                  {point.title}
                </span>
                <div className="flex items-center gap-1.5 mt-1">
                  <StatusBadge variant={sceneTypeToBadgeVariant(point.source)}>
                    {point.source}
                  </StatusBadge>
                  {point.estimated_cases > 0 && (
                    <span className="text-[10px] text-sy-text-3 font-mono">
                      ~{point.estimated_cases} 用例
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))}

          {/* Show more / less */}
          {points.length > FOLD_THRESHOLD && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setShowAll((v) => !v);
              }}
              className="w-full px-3 py-1.5 text-[11px] text-sy-text-3 hover:text-sy-text transition-colors text-left"
            >
              {showAll ? '收起' : `展示更多 (${hiddenCount})`}
            </button>
          )}

          {/* Add test point row */}
          {addingPoint ? (
            <div className="px-3 py-2">
              <input
                ref={inputRef}
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAddSubmit();
                  if (e.key === 'Escape') {
                    setNewTitle('');
                    setAddingPoint(false);
                  }
                }}
                onBlur={handleAddSubmit}
                placeholder="输入测试点标题后按 Enter"
                className="w-full bg-sy-bg-2 border border-sy-border-2 rounded-md px-2.5 py-1.5 text-[12px] text-sy-text placeholder:text-sy-text-3 outline-none focus:border-sy-accent/50"
              />
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setAddingPoint(true)}
              className="flex items-center gap-1.5 w-full px-3 py-2 rounded-md border border-dashed border-sy-border-2 text-sy-text-3 hover:bg-sy-bg-2 hover:text-sy-text-2 transition-colors text-[12px]"
            >
              <Plus className="w-3 h-3" />
              添加测试点
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default function TestPointGroupList({
  requirementId,
  checkedPointIds,
  onToggle,
  onAdd,
  onStartGenerate,
}: TestPointGroupListProps) {
  const sm = useSceneMap();

  // Only load points for the given requirementId — sm.testPoints is already filtered by store
  const testPoints = requirementId ? sm.testPoints : [];

  // Group by group_name
  const grouped = testPoints.reduce<Record<string, TestPointItem[]>>((acc, tp) => {
    const key = tp.group_name || '其他';
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(tp);
    return acc;
  }, {});
  const groupNames = Object.keys(grouped);

  if (testPoints.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center py-12">
        <Sparkles className="w-10 h-10 text-sy-text-3 opacity-20 mb-3" />
        <p className="text-[13px] text-sy-text-3">暂无测试点</p>
        <p className="text-[11px] text-sy-text-3 opacity-60 mt-1">请先生成测试点</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Scrollable group list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {groupNames.map((name) => (
          <GroupSection
            key={name}
            groupName={name}
            points={grouped[name]}
            checkedPointIds={checkedPointIds}
            onToggle={onToggle}
            onAdd={onAdd}
          />
        ))}
      </div>

      {/* Bottom action */}
      <div className="flex-shrink-0 px-4 py-3 border-t border-sy-border">
        <button
          type="button"
          onClick={onStartGenerate}
          disabled={checkedPointIds.size === 0}
          className="flex items-center justify-center gap-2 w-full rounded-md bg-sy-accent px-4 py-2 text-[13px] font-semibold text-black transition-colors hover:bg-sy-accent-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Sparkles className="w-3.5 h-3.5" />
          开始生成（{checkedPointIds.size} 个测试点）
        </button>
      </div>
    </div>
  );
}
