'use client';

import { AlertTriangle, Loader2, RefreshCw } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { ThinkingStream } from '@/components/ui/ThinkingStream';
import { CaseCard } from '@/components/workspace/CaseCard';
import { StreamCursor } from '@/components/workspace/StreamCursor';
import { type SSEStreamingCase, useSSE } from '@/hooks/useSSE';
import { api } from '@/lib/api';
import type { WorkbenchTestCase } from '@/stores/workspace-store';

interface GenerationPanelProps {
  requirementId: string | null;
  testPointIds: string[];
  onComplete: (cases: WorkbenchTestCase[]) => void;
}

function mapStreamingCasesToWorkbench(
  cases: SSEStreamingCase[],
  sessionId: string,
): WorkbenchTestCase[] {
  return cases.map((c, idx) => ({
    id: `${sessionId}-streaming-${idx}`,
    case_id: `#${c._idx + 1}`,
    title: c.title,
    priority: (c.priority as 'P0' | 'P1' | 'P2' | 'P3') ?? 'P1',
    case_type: c.case_type ?? 'functional',
    status: 'draft',
    precondition: c.precondition,
    source: 'ai',
    steps: (c.steps ?? []).map((s, i) => ({
      no: s.step_num ?? i + 1,
      action: s.action,
      expected_result: s.expected_result,
    })),
  }));
}

export function GenerationPanel({ requirementId, testPointIds, onComplete }: GenerationPanelProps) {
  const sse = useSSE();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [hasStarted, setHasStarted] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const startGeneration = useCallback(async () => {
    if (!requirementId || testPointIds.length === 0) return;

    setHasStarted(true);
    setIsCompleted(false);

    try {
      const sessionData = await api.post<{ id: string }>('/generation/sessions', {
        requirement_id: requirementId,
        mode: 'test_point_driven',
      });

      setSessionId(sessionData.id);

      const pointIdsText = testPointIds.join(', ');
      const message = `请根据以下测试点 ID 生成测试用例：${pointIdsText}`;

      await sse.startStream(`/generation/sessions/${sessionData.id}/chat`, {
        body: { message },
        onDone: () => {
          setIsCompleted(true);
        },
        onError: (err) => {
          toast.error(`生成失败：${err.message}`);
        },
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : '请求失败';
      toast.error(`创建生成会话失败：${msg}`);
      setHasStarted(false);
    }
  }, [requirementId, testPointIds, sse]);

  // 流结束后调用 onComplete 回调
  useEffect(() => {
    if (isCompleted && sse.cases.length > 0 && sessionId) {
      const cases = mapStreamingCasesToWorkbench(sse.cases, sessionId);
      onCompleteRef.current(cases);
    }
  }, [isCompleted, sse.cases, sessionId]);

  const handleRetry = useCallback(() => {
    setHasStarted(false);
    setIsCompleted(false);
    setSessionId(null);
    startGeneration();
  }, [startGeneration]);

  if (!requirementId || testPointIds.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-4 gap-3">
        <AlertTriangle className="w-10 h-10 text-sy-text-3" />
        <p className="text-[13px] text-sy-text-2">请先选择需求并勾选测试点</p>
      </div>
    );
  }

  if (!hasStarted) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-4 gap-4">
        <p className="text-[13px] text-sy-text-2">
          已选 <span className="text-sy-accent font-semibold">{testPointIds.length}</span>{' '}
          个测试点，准备生成
        </p>
        <button
          type="button"
          onClick={startGeneration}
          className="inline-flex items-center gap-2 rounded-md bg-sy-accent px-4 py-2 text-[13px] font-semibold text-black hover:bg-sy-accent-2 transition-colors"
        >
          开始生成
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* 状态栏 */}
      <div className="shrink-0 flex items-center gap-2 px-4 py-2.5 border-b border-sy-border bg-sy-bg-1">
        {sse.isStreaming ? (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin text-sy-accent" />
            <span className="text-[12px] text-sy-text-2">生成中...</span>
            <span className="ml-auto text-[11px] text-sy-text-3 font-mono">
              已生成 {sse.cases.length} 条
            </span>
          </>
        ) : isCompleted ? (
          <>
            <span className="w-2 h-2 rounded-full bg-sy-accent" />
            <span className="text-[12px] text-sy-text-2">
              生成完成，共 <span className="text-sy-accent font-semibold">{sse.cases.length}</span>{' '}
              条
            </span>
            <button
              type="button"
              onClick={handleRetry}
              className="ml-auto inline-flex items-center gap-1 text-[11px] text-sy-text-3 hover:text-sy-text-2 transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              重新生成
            </button>
          </>
        ) : sse.error ? (
          <>
            <AlertTriangle className="w-3.5 h-3.5 text-sy-danger" />
            <span className="text-[12px] text-sy-danger">生成失败</span>
            <button
              type="button"
              onClick={handleRetry}
              className="ml-auto inline-flex items-center gap-1 text-[11px] text-sy-text-3 hover:text-sy-text-2 transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              重试
            </button>
          </>
        ) : (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin text-sy-accent" />
            <span className="text-[12px] text-sy-text-2">正在连接...</span>
          </>
        )}
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {/* 思考过程 */}
        {(sse.thinking || sse.isStreaming) && (
          <ThinkingStream text={sse.thinking} isStreaming={sse.isStreaming && !sse.content} />
        )}

        {/* 已渲染的用例卡片 */}
        {sse.cases.map((c) => (
          <CaseCard
            key={c._idx}
            caseId={`#${c._idx + 1}`}
            title={c.title}
            priority={(c.priority as 'P0' | 'P1' | 'P2' | 'P3') ?? 'P1'}
            type={c.case_type}
            precondition={c.precondition}
            steps={(c.steps ?? []).map((s, i) => ({
              no: s.step_num ?? i + 1,
              action: s.action,
              expected_result: s.expected_result,
            }))}
          />
        ))}

        {/* 流式光标 */}
        {sse.isStreaming && sse.cases.length === 0 && !sse.thinking && (
          <div className="flex items-center gap-2 text-[12.5px] text-sy-text-2 p-3 rounded-lg bg-sy-bg-2 border border-sy-border">
            <StreamCursor />
            <span>AI 正在生成...</span>
          </div>
        )}
        {sse.isStreaming && sse.cases.length > 0 && <StreamCursor />}
      </div>
    </div>
  );
}
