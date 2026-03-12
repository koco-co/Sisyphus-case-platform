'use client';

import { Plus, Sparkles } from 'lucide-react';
import { useCallback, useEffect } from 'react';
import { ThreeColLayout } from '@/components/layout/ThreeColLayout';
import { EmptyState } from '@/components/ui/EmptyState';
import { useWorkbench } from '@/hooks/useWorkbench';
import type { Requirement } from '@/lib/api';
import { ChatArea } from './_components/ChatArea';
import { ChatInput } from './_components/ChatInput';
import { ContextPanel } from './_components/ContextPanel';
import { GeneratedCases } from './_components/GeneratedCases';
import { ModeSelector } from './_components/ModeSelector';
import { QuickCommands } from './_components/QuickCommands';
import { RequirementNav } from './_components/RequirementNav';

const SUB_NAV_HEIGHT = 41;

export default function WorkbenchPage() {
  const wb = useWorkbench();

  // 离开页面时停止正在进行的 SSE 流
  const { stopStream } = wb;
  // biome-ignore lint/correctness/useExhaustiveDependencies: stopStream is stable
  useEffect(() => {
    return () => stopStream();
  }, []);

  const handleSelectRequirement = useCallback(
    (req: Requirement) => {
      wb.selectRequirement(req.id, req.title || req.req_id || '');
    },
    [wb],
  );

  const handleSendMessage = useCallback(
    (text: string) => {
      wb.sendMessage(text);
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
        onSelectSession={wb.selectSession}
        onCreateSession={wb.createSession}
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
      {wb.activeSessionId ? (
        <>
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
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <EmptyState
            icon={<Sparkles className="w-12 h-12" />}
            title={wb.selectedReqId ? '选择或新建会话' : '请从左侧选择需求'}
            description="对话式 AI 测试用例生成"
            action={
              wb.selectedReqId ? (
                <button
                  type="button"
                  onClick={wb.createSession}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-md text-[12.5px] font-semibold bg-sy-accent text-black hover:bg-sy-accent-2 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  新建会话
                </button>
              ) : undefined
            }
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
    <ThreeColLayout
      left={leftPanel}
      center={centerPanel}
      right={rightPanel}
      leftWidth="260px"
      rightWidth="340px"
      subNavHeight={SUB_NAV_HEIGHT}
    />
  );
}
