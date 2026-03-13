'use client';

import { Loader2, Play, Sparkles } from 'lucide-react';
import type { SSEState } from '@/hooks/useSSE';
import type { ChatMessage, DiagnosisReport } from '@/lib/api';
import { ChatInput } from './ChatInput';
import { DiagnosisChat } from './DiagnosisChat';
import { ScanResultsList } from './ScanResultsList';

interface AnalysisTabProps {
  reqId: string;
  reqTitle: string;
  report: DiagnosisReport | null;
  messages: ChatMessage[];
  sse: SSEState;
  loading: boolean;
  onSendMessage: (text: string) => void;
  onStartDiagnosis: () => void;
}

export function AnalysisTab({
  reqId,
  reqTitle,
  report,
  messages,
  sse,
  loading,
  onSendMessage,
  onStartDiagnosis,
}: AnalysisTabProps) {
  const hasScanResults = (report?.risks?.length ?? 0) > 0;
  const canStartScan = !sse.isStreaming && !hasScanResults;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* ─── Upper: Scan Results ─── */}
      <div className="flex-shrink-0 border-b border-border" style={{ maxHeight: '44%' }}>
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-border/60 bg-bg1">
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-accent" />
            <span className="text-[12px] font-semibold text-text2">广度扫描结果</span>
          </div>
          {canStartScan && (
            <button
              type="button"
              onClick={onStartDiagnosis}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-accent text-white dark:text-black text-[11.5px] font-semibold hover:bg-accent2 transition-colors"
            >
              <Play className="w-3 h-3" />
              开始分析
            </button>
          )}
          {sse.isStreaming && (
            <span className="flex items-center gap-1.5 text-[11px] text-amber">
              <Loader2 className="w-3 h-3 animate-spin" />
              分析进行中...
            </span>
          )}
        </div>
        <div className="overflow-y-auto px-4 py-3" style={{ maxHeight: 'calc(44% - 2rem)' }}>
          <ScanResultsList report={report} loading={loading} />
        </div>
      </div>

      {/* ─── Lower: Chat (Socratic dialogue) ─── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-2 border-b border-border/60 bg-bg1 flex-shrink-0">
          <span className="text-[12px] font-semibold text-text2">苏格拉底追问</span>
          <span className="text-[11px] text-text3">· {reqTitle}</span>
        </div>
        <DiagnosisChat
          messages={messages}
          isStreaming={sse.isStreaming}
          streamContent={sse.content}
          streamThinking={sse.thinking}
          reqTitle={reqTitle}
          hasRequirement={!!reqId}
        />
        <ChatInput onSend={onSendMessage} isStreaming={sse.isStreaming} disabled={!reqId} />
      </div>
    </div>
  );
}
