'use client';

import { Clock, FileText, GitCompareArrows, History, Loader2, Target } from 'lucide-react';
import { useState } from 'react';
import { ThreeColLayout } from '@/components/layout/ThreeColLayout';
import { EmptyState } from '@/components/ui/EmptyState';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useDiff } from '@/hooks/useDiff';
import type { DiffHistoryItem } from '@/stores/diff-store';
import { AffectedCases } from './_components/AffectedCases';
import { DiffView } from './_components/DiffView';
import { RegenerateButton } from './_components/RegenerateButton';
import { SemanticAnalysis } from './_components/SemanticAnalysis';
import { SuggestedPoints } from './_components/SuggestedPoints';
import { VersionSelector } from './_components/VersionSelector';

// ── Impact level helpers ──

const impactVariant = (level: string) =>
  level === 'high' ? 'danger' : level === 'medium' ? 'warning' : 'success';

const impactLabel = (level: string) => (level === 'high' ? '高' : level === 'medium' ? '中' : '低');

// ── Left Column ──

function LeftColumn() {
  const {
    requirementId,
    setRequirementId,
    computing,
    computeDiff,
    loadHistory,
    loadSuggestions,
    history,
    diffResult,
  } = useDiff();

  const handleCompute = async () => {
    await computeDiff();
    await loadSuggestions();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="col-header">
        <GitCompareArrows className="w-3.5 h-3.5 text-accent" />
        <span>需求版本</span>
      </div>

      <div className="p-3 space-y-3 flex-1 overflow-y-auto">
        {/* Requirement ID input */}
        <div>
          <label
            htmlFor="diff-requirement-id"
            className="block text-[10px] font-semibold text-text3 uppercase tracking-wider mb-1"
          >
            需求 ID
          </label>
          <input
            id="diff-requirement-id"
            type="text"
            value={requirementId ?? ''}
            onChange={(e) => setRequirementId(e.target.value || null)}
            placeholder="输入需求 UUID"
            className="w-full px-3 py-1.5 text-[12.5px] bg-bg2 border border-border rounded-md text-text placeholder:text-text3 outline-none focus:border-accent transition-colors"
          />
        </div>

        {/* Version selector */}
        <VersionSelector />

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleCompute}
            disabled={computing || !requirementId}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-[12px] font-semibold bg-accent text-white dark:text-black hover:bg-accent2 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {computing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                分析中...
              </>
            ) : (
              '计算 Diff'
            )}
          </button>
          <button
            type="button"
            onClick={loadHistory}
            disabled={!requirementId}
            className="flex items-center gap-1.5 px-3 py-2 rounded-md text-[12px] font-medium border border-border bg-bg2 text-text2 hover:bg-bg3 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <History className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Impact summary */}
        {diffResult && (
          <div className="space-y-2 pt-2 border-t border-border">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-text3">影响等级</span>
              <StatusBadge variant={impactVariant(diffResult.impact_level)}>
                {impactLabel(diffResult.impact_level)}
              </StatusBadge>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-bg2 rounded-md p-2 text-center">
                <div className="font-mono text-[16px] font-semibold text-accent leading-none">
                  +{diffResult.text_diff?.additions ?? 0}
                </div>
                <div className="text-[10px] text-text3 mt-0.5">新增</div>
              </div>
              <div className="bg-bg2 rounded-md p-2 text-center">
                <div className="font-mono text-[16px] font-semibold text-red leading-none">
                  −{diffResult.text_diff?.deletions ?? 0}
                </div>
                <div className="text-[10px] text-text3 mt-0.5">删除</div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-bg2 rounded-md p-2 text-center">
                <div className="font-mono text-[14px] font-semibold text-amber leading-none">
                  {diffResult.affected_test_points?.count ?? 0}
                </div>
                <div className="text-[10px] text-text3 mt-0.5">测试点</div>
              </div>
              <div className="bg-bg2 rounded-md p-2 text-center">
                <div className="font-mono text-[14px] font-semibold text-blue leading-none">
                  {diffResult.affected_test_cases?.count ?? 0}
                </div>
                <div className="text-[10px] text-text3 mt-0.5">用例</div>
              </div>
            </div>
          </div>
        )}

        {/* History list */}
        {history.length > 0 && (
          <div className="pt-2 border-t border-border">
            <div className="text-[10px] font-semibold text-text3 uppercase tracking-wider mb-2">
              变更历史
            </div>
            <div className="space-y-1.5">
              {history.map((h: DiffHistoryItem) => (
                <HistoryRow key={h.id} item={h} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function HistoryRow({ item }: { item: DiffHistoryItem }) {
  return (
    <div className="flex items-center gap-2 p-2 bg-bg2 border border-border rounded-md hover:border-border2 cursor-pointer transition-colors">
      <StatusBadge variant={impactVariant(item.impact_level)}>
        {impactLabel(item.impact_level)}
      </StatusBadge>
      <div className="flex-1 min-w-0">
        <div className="font-mono text-[11px] text-text2">
          v{item.version_from} → v{item.version_to}
        </div>
        <div className="text-[10px] text-text3 truncate">{item.summary}</div>
      </div>
      <div className="flex items-center gap-1 text-[10px] text-text3 font-mono shrink-0">
        <Clock className="w-2.5 h-2.5" />
        {item.created_at?.slice(5, 16)}
      </div>
    </div>
  );
}

// ── Center Column ──

function CenterColumn() {
  const {
    diffResult,
    suggestions,
    adoptedIds,
    dismissedIds,
    adoptSuggestion,
    dismissSuggestion,
    computing,
  } = useDiff();
  const [activeTab, setActiveTab] = useState<'text' | 'summary'>('text');

  if (computing) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-text3 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
        <span className="text-[13px] font-medium">正在执行两阶段 Diff 分析...</span>
        <span className="text-[11px] text-text3/70">文本级 + 语义级</span>
      </div>
    );
  }

  if (!diffResult) {
    return (
      <EmptyState
        icon={<GitCompareArrows className="w-12 h-12" />}
        title="输入需求 ID 并选择版本范围"
        description="系统将进行文本级 + 语义级两阶段 Diff 分析"
        className="h-full"
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Dual tab */}
      <div className="flex items-center gap-1 px-4 pt-3 pb-2">
        <div className="flex bg-bg2 rounded-lg p-0.5">
          <button
            type="button"
            onClick={() => setActiveTab('text')}
            className={`px-3 py-1 rounded-md text-[12px] font-medium transition-all ${
              activeTab === 'text'
                ? 'bg-bg1 text-text shadow-sm'
                : 'text-text3 hover:text-text2'
            }`}
          >
            文本对比
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('summary')}
            className={`px-3 py-1 rounded-md text-[12px] font-medium transition-all ${
              activeTab === 'summary'
                ? 'bg-bg1 text-text shadow-sm'
                : 'text-text3 hover:text-text2'
            }`}
          >
            变更摘要
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 pt-0 space-y-4">
        {activeTab === 'text' ? (
          <>
            {/* Diff view */}
            {diffResult.text_diff?.diff_text && (
              <DiffView
                diffText={diffResult.text_diff.diff_text}
                additions={diffResult.text_diff.additions}
                deletions={diffResult.text_diff.deletions}
              />
            )}
          </>
        ) : (
          <>
            {/* AI Summary */}
            {diffResult.summary && (
              <div className="p-3 bg-bg1 border border-border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-accent text-white dark:text-black">
                    AI 摘要
                  </span>
                </div>
                <p className="text-[12.5px] text-text2 leading-relaxed">{diffResult.summary}</p>
              </div>
            )}

            {/* Semantic analysis */}
            {diffResult.semantic_impact && <SemanticAnalysis impact={diffResult.semantic_impact} />}
          </>
        )}

        {/* Suggested test points (always visible) */}
        {suggestions.length > 0 && (
          <SuggestedPoints
            suggestions={suggestions}
            adoptedIds={adoptedIds}
            dismissedIds={dismissedIds}
            onAdopt={adoptSuggestion}
            onDismiss={dismissSuggestion}
          />
        )}
      </div>
    </div>
  );
}

// ── Right Column ──

function RightColumn() {
  const { diffResult, regenerating, regenerateProgress, regenerateCases } = useDiff();

  const cases = diffResult?.affected_test_cases?.items ?? [];
  const testPointCount = diffResult?.affected_test_points?.count ?? 0;
  const rewriteCount = cases.filter((c) => c.impact_type === 'rewrite').length;

  return (
    <div className="flex flex-col h-full">
      <div className="col-header">
        <Target className="w-3.5 h-3.5 text-amber" />
        <span>受影响用例</span>
        {cases.length > 0 && (
          <span className="ml-auto font-mono text-[10px] text-text3">{cases.length}</span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {diffResult ? (
          <AffectedCases cases={cases} totalTestPoints={testPointCount} />
        ) : (
          <EmptyState
            icon={<FileText className="w-8 h-8" />}
            title="等待 Diff 分析"
            description="完成分析后显示受影响的用例"
          />
        )}
      </div>

      {/* Regenerate button */}
      {diffResult && rewriteCount > 0 && (
        <div className="p-3 border-t border-border">
          <RegenerateButton
            onRegenerate={() => regenerateCases()}
            regenerating={regenerating}
            progress={regenerateProgress}
            affectedCount={rewriteCount}
          />
        </div>
      )}
    </div>
  );
}

// ── Page ──

export default function DiffPage() {
  return (
    <div className="no-sidebar">
      {/* Header */}
      <div className="topbar">
        <GitCompareArrows className="w-5 h-5 text-accent" />
        <h1>需求变更 Diff</h1>
        <span className="sub">Requirement Change Diff</span>
        <div className="spacer" />
        <span className="page-watermark">M07 · DIFF</span>
      </div>

      {/* Three-column layout */}
      <ThreeColLayout
        left={<LeftColumn />}
        center={<CenterColumn />}
        right={<RightColumn />}
        leftWidth="280px"
        rightWidth="320px"
      />
    </div>
  );
}
