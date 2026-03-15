'use client';

import { Loader2, Sparkles } from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useState } from 'react';
import { ThreeColLayout } from '@/components/layout/ThreeColLayout';
import { AiConfigBanner } from '@/components/ui/AiConfigBanner';
import { EmptyState } from '@/components/ui/EmptyState';
import { useAiConfig } from '@/hooks/useAiConfig';
import { useSceneMap } from '@/hooks/useSceneMap';
import { useWorkbench } from '@/hooks/useWorkbench';
import { type Requirement, requirementsApi } from '@/lib/api';
import { TestPointList } from '../scene-map/_components/TestPointList';
import { ChatArea } from './_components/ChatArea';
import { ChatInput } from './_components/ChatInput';
import { ContextPanel } from './_components/ContextPanel';
import { GeneratedCases } from './_components/GeneratedCases';
import { ModeSelector } from './_components/ModeSelector';
import { QuickCommands } from './_components/QuickCommands';
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
  const hasSelectedRequirement = Boolean(wb.selectedReqId);
  const selectedRequirementTitle = wb.selectedReqTitle || sm.selectedReqTitle;
  const selectedPointCount = sm.checkedPointIds.size;
  const [viewStep, setViewStep] = useState<1 | 2>(wb.activeSessionId ? 2 : 1);
  const currentStep = viewStep === 2 && wb.activeSessionId ? 2 : 1;
  const isGenerationStep = currentStep === 2;
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

  useEffect(() => {
    if (!wb.selectedReqId || !wb.activeSessionId) {
      setViewStep(1);
    }
  }, [wb.activeSessionId, wb.selectedReqId]);

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
      setViewStep(1);
    },
    [sm, wb],
  );

  const handleSendMessage = useCallback(
    (text: string) => {
      wb.sendMessage(text);
    },
    [wb],
  );

  const handleStartGeneration = useCallback(async () => {
    if (!wb.selectedReqId || selectedPointCount === 0) return;

    const pendingConfirmIds = sm.testPoints
      .filter((point) => sm.checkedPointIds.has(point.id) && point.status !== 'confirmed')
      .map((point) => point.id);

    await Promise.all(pendingConfirmIds.map((pointId) => sm.confirmPoint(pointId)));

    if (wb.activeSessionId) {
      setViewStep(2);
      return;
    }

    await wb.createSession();
    setViewStep(2);
  }, [selectedPointCount, sm, wb]);

  const handleCreateSession = useCallback(async () => {
    if (wb.activeSessionId) {
      await wb.createSession();
      setViewStep(2);
      return;
    }

    await handleStartGeneration();
  }, [handleStartGeneration, wb]);

  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      await wb.selectSession(sessionId);
      setViewStep(2);
    },
    [wb],
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
      {isGenerationStep ? (
        <>
          <div className="flex items-center justify-between border-b border-border bg-bg1 px-4 py-2.5">
            <div>
              <p className="text-[12px] font-semibold text-text">Step 2：生成用例</p>
              <p className="mt-0.5 text-[11px] text-text3">
                {selectedRequirementTitle || '已进入当前需求的生成会话'}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setViewStep(1)}
              className="inline-flex items-center gap-1.5 rounded-md border border-border bg-bg2 px-3 py-1.5 text-[12px] font-medium text-text transition-colors hover:border-accent/30 hover:text-accent"
            >
              返回 Step 1
            </button>
          </div>
          <ModeSelector value={wb.selectedMode} onChange={wb.setMode} />
          <QuickCommands
            onCommand={handleSendMessage}
            disabled={wb.sse.isStreaming || !wb.activeSessionId}
          />
          <ChatArea
            messages={wb.messages}
            streamingContent={wb.sse.content}
            streamingThinking={wb.sse.thinking}
            streamingCases={wb.sse.cases}
            isStreaming={wb.sse.isStreaming}
          />
          <ChatInput
            onSend={handleSendMessage}
            onStop={wb.stopStream}
            isStreaming={wb.sse.isStreaming}
            disabled={!wb.activeSessionId}
          />
        </>
      ) : hasSelectedRequirement ? (
        <>
          <div className="border-b border-border bg-bg1 px-4 py-3">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[13px] font-semibold text-text">Step 1：确认测试点</p>
                <p className="mt-1 text-[12px] text-text2">
                  {selectedRequirementTitle || '已选需求'}
                </p>
                <p className="mt-1 text-[11px] text-text3">
                  勾选至少 1 个测试点后，才能进入 Step 2 生成用例。
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={sm.generateTestPoints}
                  disabled={sm.sse.isStreaming}
                  className="inline-flex items-center gap-1.5 rounded-md border border-border bg-bg2 px-3 py-1.5 text-[12px] font-medium text-text transition-colors hover:border-accent/30 hover:text-accent disabled:cursor-not-allowed disabled:opacity-60"
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
                  开始生成
                </button>
              </div>
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-hidden bg-bg">
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
  const rightPanel = (
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
        currentStep={currentStep}
        onStepClick={(step) => {
          if (step === 1 && hasSelectedRequirement) setViewStep(1);
          if (step === 2 && wb.activeSessionId) setViewStep(2);
        }}
        step2Completed={Boolean(wb.activeSessionId)}
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
    <div className="flex h-[calc(100vh-49px)] items-center justify-center bg-bg text-[13px] text-text3">
      正在加载工作台...
    </div>
  );
}
