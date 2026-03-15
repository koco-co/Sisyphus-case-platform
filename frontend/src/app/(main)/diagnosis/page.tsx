'use client';

import {
  Activity,
  ChevronDown,
  ChevronRight,
  FileText,
  FolderOpen,
  IterationCw,
  Loader2,
  ShieldAlert,
} from 'lucide-react';
import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { AiConfigBanner } from '@/components/ui/AiConfigBanner';
import { useAiConfig } from '@/hooks/useAiConfig';
import { useDiagnosis } from '@/hooks/useDiagnosis';
import { useRequirementTree } from '@/hooks/useRequirementTree';
import { diagnosisApi } from '@/lib/api';
import { AnalysisTab } from './_components/AnalysisTab';
import { CoverageMatrix } from './_components/CoverageMatrix';
import { RequirementDetailTab } from './_components/RequirementDetailTab';

type ActiveTab = 'detail' | 'analysis' | 'coverage';

const tabLabels: { key: ActiveTab; label: string }[] = [
  { key: 'detail', label: '需求详情' },
  { key: 'analysis', label: 'AI 分析' },
  { key: 'coverage', label: '覆盖追踪' },
];

// Status badge for each requirement
type ReqStatus = 'unanalyzed' | 'analyzing' | 'completed';

function statusBadge(status: ReqStatus) {
  const map: Record<ReqStatus, { label: string; cls: string }> = {
    unanalyzed: { label: '未分析', cls: 'bg-bg3 text-text3 border-border' },
    analyzing: { label: '分析中', cls: 'bg-amber/10 text-amber border-amber/30' },
    completed: { label: '已完成', cls: 'bg-accent/10 text-accent border-accent/30' },
  };
  const cfg = map[status];
  return (
    <span
      className={`flex-shrink-0 inline-flex items-center px-1.5 py-0.5 rounded-full border font-mono text-[10px] ${cfg.cls}`}
    >
      {cfg.label}
    </span>
  );
}

function reportStatusToReqStatus(reportStatus: string | undefined): ReqStatus {
  if (!reportStatus || reportStatus === 'pending') return 'unanalyzed';
  if (reportStatus === 'completed') return 'completed';
  return 'analyzing';
}

export default function DiagnosisPage() {
  const tree = useRequirementTree();
  const aiConfig = useAiConfig();
  const [activeTab, setActiveTab] = useState<ActiveTab>('detail');
  const [reqStatusMap, setReqStatusMap] = useState<Record<string, ReqStatus>>({});

  const { report, messages, loading, sse, sendMessage, startDiagnosis } = useDiagnosis(
    tree.selectedReqId,
  );

  // Keep status map updated whenever report changes
  useEffect(() => {
    if (!tree.selectedReqId || !report) return;
    setReqStatusMap((prev) => ({
      ...prev,
      [tree.selectedReqId as string]: reportStatusToReqStatus(report.status),
    }));
  }, [report, tree.selectedReqId]);

  // Background-fetch diagnosis status for newly loaded requirements
  const fetchStatusForRequirements = useCallback((reqIds: string[]) => {
    for (const id of reqIds) {
      diagnosisApi
        .getReport(id)
        .then((r) => {
          setReqStatusMap((prev) => ({
            ...prev,
            [id]: reportStatusToReqStatus(r.status),
          }));
        })
        .catch(() => {
          // 404 = unanalyzed, leave as default
        });
    }
  }, []);

  // When new requirements are loaded into the tree, fetch their status
  // biome-ignore lint/correctness/useExhaustiveDependencies: fetchStatusForRequirements is stable (useCallback)
  useEffect(() => {
    const allIds = Object.values(tree.requirements)
      .flat()
      .map((r) => r.id);
    if (allIds.length > 0) {
      fetchStatusForRequirements(allIds);
    }
  }, [tree.requirements]);

  const handleStartAnalysis = useCallback(() => {
    setActiveTab('analysis');
    startDiagnosis();
  }, [startDiagnosis]);

  const hasUnhandledHighRisk = (report?.risks ?? []).some(
    (r) => r.severity === 'high' && (!r.status || r.status === 'open'),
  );
  const hasConfiguredAiModel = Boolean(
    aiConfig.effectiveConfig?.llm_model?.trim() ||
      aiConfig.modelConfigs.some((model) => model.is_enabled && model.model_id),
  );
  const showAiConfigBanner = !aiConfig.loading && !hasConfiguredAiModel;

  // ── Left panel ─────────────────────────────────────────────────────────────
  const leftPanel = (
    <div
      className="flex-shrink-0 flex flex-col border-r border-border overflow-hidden bg-bg1"
      style={{ width: 280 }}
    >
      {/* Header */}
      <div className="px-3.5 py-2.5 border-b border-border flex items-center gap-2 flex-shrink-0">
        <Activity className="w-3.5 h-3.5 text-accent" />
        <span className="text-[12px] font-semibold text-text2">AI 分析</span>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        <div className="text-[10px] font-semibold text-text3 uppercase tracking-wider px-2 mb-1.5">
          需求列表
        </div>

        {tree.products.map((product) => (
          <div key={product.id}>
            <button
              type="button"
              onClick={() => tree.toggleProduct(product.id)}
              className="w-full flex items-center gap-1.5 px-2 py-1.5 rounded-md hover:bg-bg2 transition-colors text-text text-[12.5px]"
            >
              {tree.expandedProducts.has(product.id) ? (
                <ChevronDown className="w-3.5 h-3.5 text-text3 flex-shrink-0" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-text3 flex-shrink-0" />
              )}
              <FolderOpen className="w-3.5 h-3.5 text-accent flex-shrink-0" />
              <span className="truncate flex-1 text-left">{product.name}</span>
            </button>

            {tree.expandedProducts.has(product.id) &&
              (tree.iterationsLoading[product.id] ? (
                <div className="pl-8 py-1 text-[11px] text-text3">迭代加载中...</div>
              ) : (tree.iterations[product.id] ?? []).length === 0 ? (
                <div className="pl-8 py-1 text-[11px] text-text3">当前产品暂无迭代</div>
              ) : (
                (tree.iterations[product.id] ?? []).map((iter) => (
                  <div key={iter.id} className="pl-4">
                    <button
                      type="button"
                      onClick={() => tree.toggleIteration(product.id, iter.id)}
                      className="w-full flex items-center gap-1.5 px-2 py-1 rounded-md hover:bg-bg2 transition-colors text-text3 text-[12px]"
                    >
                      {tree.expandedIterations.has(iter.id) ? (
                        <ChevronDown className="w-3 h-3 flex-shrink-0" />
                      ) : (
                        <ChevronRight className="w-3 h-3 flex-shrink-0" />
                      )}
                      <IterationCw className="w-3 h-3 flex-shrink-0" />
                      <span className="truncate flex-1 text-left">{iter.name}</span>
                    </button>

                    {tree.expandedIterations.has(iter.id) &&
                      (tree.requirementsLoading[iter.id] ? (
                        <div className="pl-8 py-1 text-[11px] text-text3">需求加载中...</div>
                      ) : (tree.requirements[iter.id] ?? []).length === 0 ? (
                        <div className="pl-8 py-1 text-[11px] text-text3">当前迭代暂无需求</div>
                      ) : (
                        (tree.requirements[iter.id] ?? []).map((req) => {
                          const status = reqStatusMap[req.id] ?? 'unanalyzed';
                          const isSelected = tree.selectedReqId === req.id;
                          return (
                            <button
                              type="button"
                              key={req.id}
                              onClick={() => tree.selectRequirement(req)}
                              className={`w-full flex items-center gap-1.5 px-2 py-1.5 ml-4 rounded-md text-[12px] transition-colors ${
                                isSelected
                                  ? 'bg-accent/10 text-accent'
                                  : 'text-text3 hover:bg-bg2 hover:text-text2'
                              }`}
                            >
                              <FileText className="w-3 h-3 flex-shrink-0" />
                              <span className="truncate flex-1 text-left">
                                {req.title || req.req_id}
                              </span>
                              {statusBadge(status)}
                            </button>
                          );
                        })
                      ))}
                  </div>
                ))
              ))}
          </div>
        ))}

        {tree.products.length === 0 && (
          <div className="text-center py-6 text-text3 text-[13px]">暂无产品数据</div>
        )}
      </div>
    </div>
  );

  // ── Right panel ────────────────────────────────────────────────────────────
  const rightPanel = !tree.selectedReqId ? (
    <div className="flex-1 flex items-center justify-center bg-bg">
      <div className="text-center">
        <Activity className="w-16 h-16 text-text3 opacity-15 mx-auto mb-4" />
        <p className="text-[15px] text-text3">从左侧选择需求开始分析</p>
      </div>
    </div>
  ) : (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Top bar */}
      <div
        className="flex-shrink-0 flex items-center gap-3 px-5 border-b border-border bg-bg1"
        style={{ height: 48 }}
      >
        <FileText className="w-4 h-4 text-accent flex-shrink-0" />
        <span className="text-[13px] font-semibold text-text truncate flex-1">
          {tree.selectedReqTitle}
        </span>

        {/* 进入工作台 button */}
        <div className="relative group flex-shrink-0">
          <Link
            href={`/workbench?reqId=${tree.selectedReqId}`}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-colors ${
              hasUnhandledHighRisk
                ? 'opacity-40 pointer-events-none bg-bg3 text-text3 border border-border cursor-not-allowed'
                : 'bg-accent text-white dark:text-black hover:bg-accent2'
            }`}
            aria-disabled={hasUnhandledHighRisk}
            onClick={(e) => hasUnhandledHighRisk && e.preventDefault()}
          >
            {loading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <ShieldAlert className="w-3.5 h-3.5" />
            )}
            进入工作台
          </Link>
          {hasUnhandledHighRisk && (
            <div className="absolute right-0 top-full mt-1 w-44 px-2.5 py-1.5 rounded-md bg-bg2 border border-border text-[11px] text-text2 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 whitespace-nowrap">
              请先处理高风险遗漏项
            </div>
          )}
        </div>
      </div>

      {/* Tab nav */}
      <div className="flex-shrink-0 flex border-b border-border bg-bg1 px-1">
        {tabLabels.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setActiveTab(key)}
            className={`px-4 py-2.5 text-[12.5px] font-medium transition-colors relative ${
              activeTab === key ? 'text-accent' : 'text-text3 hover:text-text2'
            }`}
          >
            {label}
            {activeTab === key && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-t-sm" />
            )}
          </button>
        ))}
      </div>

      {/* Tab content — all mounted to preserve state, toggled via visibility */}
      <div className="flex-1 overflow-hidden relative">
        <div className={`absolute inset-0 ${activeTab === 'detail' ? '' : 'hidden'}`}>
          <div className="h-full overflow-hidden">
            <RequirementDetailTab
              reqId={tree.selectedReqId}
              onStartAnalysis={handleStartAnalysis}
            />
          </div>
        </div>

        <div className={`absolute inset-0 ${activeTab === 'analysis' ? '' : 'hidden'}`}>
          <AnalysisTab
            reqId={tree.selectedReqId}
            reqTitle={tree.selectedReqTitle}
            report={report}
            messages={messages}
            sse={sse}
            loading={loading}
            onSendMessage={sendMessage}
            onStartDiagnosis={handleStartAnalysis}
          />
        </div>

        <div className={`absolute inset-0 ${activeTab === 'coverage' ? '' : 'hidden'}`}>
          <CoverageMatrix reqId={tree.selectedReqId} />
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {showAiConfigBanner && <AiConfigBanner />}
      <div className="flex overflow-hidden" style={{ height: 'calc(100vh - 49px)' }}>
        {leftPanel}
        {rightPanel}
      </div>
    </div>
  );
}
