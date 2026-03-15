'use client';

import { Loader2, Sparkles } from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { ThreeColLayout } from '@/components/layout/ThreeColLayout';
import { AiConfigBanner } from '@/components/ui/AiConfigBanner';
import { EmptyState } from '@/components/ui/EmptyState';
import { useAiConfig } from '@/hooks/useAiConfig';
import { useSceneMap } from '@/hooks/useSceneMap';
import { useWorkbench } from '@/hooks/useWorkbench';
import { type Requirement, requirementsApi } from '@/lib/api';
import type { WorkbenchTestCase } from '@/stores/workspace-store';
import { useWorkspaceStore } from '@/stores/workspace-store';
import { TestPointList } from '../scene-map/_components/TestPointList';
import { ContextPanel } from './_components/ContextPanel';
import { GeneratedCases } from './_components/GeneratedCases';
import { GeneratedCasesByPoint } from './_components/GeneratedCasesByPoint';
import { GenerationPanel } from './_components/GenerationPanel';
import { RequirementNav } from './_components/RequirementNav';
import WorkbenchStepBar from './_components/WorkbenchStepBar';
import { getWorkbenchRequirementId } from './query';

const SUB_NAV_HEIGHT = 41;

export default function WorkbenchPage() {
  return (
    <Suspense fallback={<WorkbenchPageFallback />}>
      <WorkbenchPageContent />
    </Suspense>
  );
}

function WorkbenchPageContent() {
  const wb = useWorkbench();
  const sm = useSceneMap();
  const aiConfig = useAiConfig();
  const searchParams = useSearchParams();
  const store = useWorkspaceStore();

  const hasSelectedRequirement = Boolean(wb.selectedReqId);
  const selectedRequirementTitle = wb.selectedReqTitle || sm.selectedReqTitle;
  const selectedPointCount = sm.checkedPointIds.size;

  // viewStep 决定显示 Step1 还是 Step2
  const [viewStep, setViewStep] = useState<1 | 2>(1);
  // step2Completed 追踪是否完成过至少一次生成（用于步骤条和「回到 Step1」）
  const [step2Completed, setStep2Completed] = useState(false);
  // 当前传给 GenerationPanel 的测试点 ID 列表（首次全量 / 追加时差集）
  const [pointIdsToGenerate, setPointIdsToGenerate] = useState<string[]>([]);
  // isAppendMode 区分 onComplete 时应调用 appendTestCases 还是 setTestCases
  const isAppendModeRef = useRef(false);

  const queryRequirementId = getWorkbenchRequirementId(searchParams);
  const hasConfiguredAiModel = Boolean(
    aiConfig.effectiveConfig?.llm_model?.trim() ||
      aiConfig.modelConfigs.some((model) => model.is_enabled && model.model_id),
  );
  const showAiConfigBanner = !aiConfig.loading && !hasConfiguredAiModel;

  // 离开页面时停止正在进行的 SSE 流
  const { stopStream } = wb;
  // biome-ignore lint/correctness/useExhaustiveDependencies: stopStream is stable
  useEffect(() => {
    return () => stopStream();
  }, []);

  // URL 中的 reqId 参数自动选中需求
  useEffect(() => {
    let cancelled = false;

    if (!queryRequirementId || queryRequirementId === wb.selectedReqId) {
      return;
    }

    (async () => {
      try {
        const req = await requirementsApi.get(queryRequirementId);
        if (cancelled) {
          return;
        }
        const reqTitle = req.title || req.req_id || '';
        await Promise.all([
          wb.selectRequirement(queryRequirementId, reqTitle),
          sm.selectRequirement(queryRequirementId, reqTitle),
        ]);
        setViewStep(1);
      } catch (error) {
        console.error('Failed to hydrate workbench requirement from URL:', error);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [queryRequirementId, sm, wb]);

  const handleSelectRequirement = useCallback(
    async (req: Requirement) => {
      const reqTitle = req.title || req.req_id || '';
      await Promise.all([
        wb.selectRequirement(req.id, reqTitle),
        sm.selectRequirement(req.id, reqTitle),
      ]);
      // 切换需求时重置追加状态
      store.setLastGeneratedPointIds(new Set());
      setStep2Completed(false);
      setViewStep(1);
    },
    [sm, wb, store],
  );

  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      await wb.selectSession(sessionId);
      setViewStep(2);
    },
    [wb],
  );

  const handleCreateSession = useCallback(async () => {
    await wb.createSession();
    setViewStep(2);
  }, [wb]);

  /**
   * 「开始生成」点击逻辑
   * - 首次生成：快照全量 checkedPointIds，传给 GenerationPanel
   * - 追加生成：计算差集，只传新增 ID
   */
  const handleStartGeneration = useCallback(async () => {
    if (!wb.selectedReqId || selectedPointCount === 0) return;

    // 自动确认未确认的测试点
    const pendingConfirmIds = sm.testPoints
      .filter((point) => sm.checkedPointIds.has(point.id) && point.status !== 'confirmed')
      .map((point) => point.id);
    await Promise.all(pendingConfirmIds.map((pointId) => sm.confirmPoint(pointId)));

    const { lastGeneratedPointIds } = store;
    const isFirstGenerate = lastGeneratedPointIds.size === 0;

    if (isFirstGenerate) {
      // 首次生成：快照全量
      store.setLastGeneratedPointIds(new Set(sm.checkedPointIds));
      setPointIdsToGenerate([...sm.checkedPointIds]);
      isAppendModeRef.current = false;
    } else {
      // 追加生成：差集
      const newIds = new Set(
        [...sm.checkedPointIds].filter((id) => !lastGeneratedPointIds.has(id)),
      );
      if (newIds.size === 0) {
        // 没有新测试点，直接跳到 Step2 展示现有结果
        setViewStep(2);
        return;
      }
      store.setLastGeneratedPointIds(new Set(sm.checkedPointIds));
      setPointIdsToGenerate([...newIds]);
      isAppendModeRef.current = true;
    }

    setViewStep(2);
  }, [wb.selectedReqId, selectedPointCount, sm, store]);

  /**
   * GenerationPanel 生成完成回调
   * - 首次：setTestCases
   * - 追加：appendTestCases
   */
  const handleGenerationComplete = useCallback(
    (cases: WorkbenchTestCase[]) => {
      if (isAppendModeRef.current) {
        store.appendTestCases(cases);
      } else {
        store.setTestCases(cases);
      }
      setStep2Completed(true);
    },
    [store],
  );

  // ── Left column ──
  const leftPanel = (
    <div className="flex flex-col h-full">
      <RequirementNav
        sessions={wb.sessions}
        activeSessionId={wb.activeSessionId}
        selectedReqId={wb.selectedReqId}
        onSelectRequirement={handleSelectRequirement}
        onSelectSession={handleSelectSession}
        onCreateSession={handleCreateSession}
      />
      {wb.selectedReqId && (
        <ContextPanel
          items={wb.contextItems}
          onAdd={wb.addContextItem}
          onRemove={wb.removeContextItem}
        />
      )}
    </div>
  );

  // ── Center column ──
  const centerPanel = (
    <div className="flex flex-col h-full">
      {viewStep === 2 ? (
        <>
          <div className="shrink-0 flex items-center justify-between border-b border-sy-border bg-sy-bg-1 px-4 py-2.5">
            <div>
              <p className="text-[12px] font-semibold text-sy-text">Step 2：生成用例</p>
              <p className="mt-0.5 text-[11px] text-sy-text-3">
                {selectedRequirementTitle || '已进入当前需求的生成会话'}
                {pointIdsToGenerate.length > 0 && (
                  <span className="ml-2 text-sy-accent">
                    {isAppendModeRef.current ? '追加' : '首次'}生成 {pointIdsToGenerate.length}{' '}
                    个测试点
                  </span>
                )}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setViewStep(1)}
              className="inline-flex items-center gap-1.5 rounded-md border border-sy-border bg-sy-bg-2 px-3 py-1.5 text-[12px] font-medium text-sy-text transition-colors hover:border-sy-accent/30 hover:text-sy-accent"
            >
              返回 Step 1
            </button>
          </div>
          <div className="min-h-0 flex-1 overflow-hidden">
            <GenerationPanel
              requirementId={wb.selectedReqId}
              testPointIds={pointIdsToGenerate}
              onComplete={handleGenerationComplete}
            />
          </div>
        </>
      ) : hasSelectedRequirement ? (
        <>
          <div className="border-b border-sy-border bg-sy-bg-1 px-4 py-3">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[13px] font-semibold text-sy-text">Step 1：确认测试点</p>
                <p className="mt-1 text-[12px] text-sy-text-2">
                  {selectedRequirementTitle || '已选需求'}
                </p>
                <p className="mt-1 text-[11px] text-sy-text-3">
                  {store.lastGeneratedPointIds.size > 0
                    ? '可继续勾选新测试点，点「追加生成」只生成新增部分。'
                    : '勾选至少 1 个测试点后，才能进入 Step 2 生成用例。'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={sm.generateTestPoints}
                  disabled={sm.sse.isStreaming}
                  className="inline-flex items-center gap-1.5 rounded-md border border-sy-border bg-sy-bg-2 px-3 py-1.5 text-[12px] font-medium text-sy-text transition-colors hover:border-sy-accent/30 hover:text-sy-accent disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {sm.sse.isStreaming ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="h-3.5 w-3.5" />
                  )}
                  {sm.sse.isStreaming ? '生成中...' : 'AI 生成测试点'}
                </button>
                <button
                  type="button"
                  onClick={handleStartGeneration}
                  disabled={selectedPointCount === 0 || sm.sse.isStreaming}
                  className="inline-flex items-center gap-1.5 rounded-md bg-sy-accent px-3 py-1.5 text-[12px] font-semibold text-black transition-colors hover:bg-sy-accent-2 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  {store.lastGeneratedPointIds.size > 0 ? '追加生成' : '开始生成'}
                </button>
              </div>
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-hidden bg-sy-bg">
            <TestPointList
              testPoints={sm.testPoints}
              selectedPointId={sm.selectedPointId}
              checkedPointIds={sm.checkedPointIds}
              searchQuery={sm.searchQuery}
              isLocked={false}
              stats={sm.stats}
              onSelectPoint={sm.selectPoint}
              onToggleCheck={sm.toggleCheckPoint}
              onSearchChange={sm.setSearchQuery}
              onAddPoint={sm.addPoint}
            />
          </div>
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <EmptyState
            icon={<Sparkles className="w-12 h-12" />}
            title="请从左侧选择需求"
            description="对话式 AI 测试用例生成"
          />
        </div>
      )}
    </div>
  );

  // ── Right column ──
  // Step2 时用按测试点分组的视图，Step1 时用原有过滤视图
  const rightPanel =
    viewStep === 2 ? (
      <GeneratedCasesByPoint
        testCases={wb.testCases}
        testPoints={sm.testPoints}
        isStreaming={false}
      />
    ) : (
      <GeneratedCases
        testCases={wb.testCases}
        isStreaming={wb.sse.isStreaming}
        selectedReqId={wb.selectedReqId}
        priorityFilter={wb.priorityFilter}
        typeFilter={wb.typeFilter}
        onPriorityChange={wb.setPriorityFilter}
        onTypeChange={wb.setTypeFilter}
        onExport={wb.exportCases}
      />
    );

  return (
    <div className="flex h-full flex-col">
      {showAiConfigBanner && <AiConfigBanner />}
      <WorkbenchStepBar
        currentStep={viewStep}
        onStepClick={(step) => {
          if (step === 1 && hasSelectedRequirement) setViewStep(1);
          if (step === 2 && step2Completed) setViewStep(2);
        }}
        step2Completed={step2Completed}
      />
      <div className="min-h-0 flex-1">
        <ThreeColLayout
          left={leftPanel}
          center={centerPanel}
          right={rightPanel}
          leftWidth="260px"
          rightWidth="340px"
          subNavHeight={SUB_NAV_HEIGHT}
        />
      </div>
    </div>
  );
}

function WorkbenchPageFallback() {
  return (
    <div className="flex h-[calc(100vh-49px)] items-center justify-center bg-sy-bg text-[13px] text-sy-text-3">
      正在加载工作台...
    </div>
  );
}
