'use client';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { ChatBubble, ProgressSteps, StatusPill, ThinkingStream } from '@/components/ui';
import { useSSEStream } from '@/hooks/useSSEStream';
import { apiClient } from '@/lib/api-client';
import { useStreamStore } from '@/stores/stream-store';

interface Risk {
  id: string;
  level: string;
  title: string;
  description: string | null;
  risk_status: string;
}

interface DiagnosisReport {
  id: string;
  requirement_id: string;
  status: string;
  overall_score: number | null;
  summary: string | null;
  risk_count_high: number;
  risk_count_medium: number;
  risk_count_industry: number;
  risks: Risk[];
}

interface ChatMessage {
  id: string;
  role: 'user' | 'ai';
  content: string;
}

const riskLevelConfig: Record<string, { label: string; variant: 'red' | 'amber' | 'blue' }> = {
  high: { label: '高风险', variant: 'red' },
  medium: { label: '中风险', variant: 'amber' },
  industry: { label: '行业建议', variant: 'blue' },
};

export default function DiagnosisPage() {
  const { id } = useParams<{ id: string }>();
  const { streamSSE } = useSSEStream();
  const { thinkingText, contentText, isStreaming, reset: resetStream } = useStreamStore();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const chatRef = useRef<HTMLDivElement>(null);

  const { data: report } = useQuery({
    queryKey: ['diagnosis', id],
    queryFn: () => apiClient<DiagnosisReport>(`/diagnosis/${id}`),
    retry: false,
  });

  const { data: sceneMap } = useQuery({
    queryKey: ['scene-map', id],
    queryFn: () =>
      apiClient<{
        id: string;
        status: string;
        test_points: { id: string; title: string; group_name: string; priority: string }[];
      }>(`/scene-map/${id}`),
    retry: false,
  });

  const { data: historyMessages } = useQuery({
    queryKey: ['diagnosis-messages', id],
    queryFn: () => apiClient<{ role: string; content: string }[]>(`/diagnosis/${id}/messages`),
    retry: false,
  });

  // Initialize messages from history on first load
  useEffect(() => {
    if (historyMessages?.length && messages.length === 0) {
      setMessages(
        historyMessages
          // Filter out raw scan JSON messages (assistant messages that are pure JSON code blocks)
          .filter((m) => {
            if (m.role !== 'assistant') return true;
            const trimmed = m.content.trim();
            // Skip messages that are purely JSON code blocks (diagnosis scan results)
            return !(
              trimmed.startsWith('```json') ||
              trimmed.startsWith('{') ||
              trimmed.startsWith('[')
            );
          })
          .map((m, i) => ({
            id: `history-${i}`,
            role: m.role === 'user' ? 'user' : 'ai',
            content: m.content,
          })),
      );
    }
  }, [historyMessages, messages.length]);

  useEffect(() => {
    const shouldAutoScroll = messages.length > 0 || Boolean(thinkingText) || Boolean(contentText);
    if (!shouldAutoScroll || !chatRef.current) return;
    chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [contentText, messages.length, thinkingText]);

  async function runDiagnosis() {
    await streamSSE(`/diagnosis/${id}/run`, {});
  }

  async function sendMessage() {
    if (!input.trim() || isStreaming) return;
    const msg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { id: Date.now().toString(), role: 'user', content: msg }]);
    await streamSSE(`/diagnosis/${id}/chat`, { message: msg, round_num: messages.length + 1 });
    const latestContent = useStreamStore.getState().contentText;
    if (latestContent) {
      setMessages((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), role: 'ai', content: latestContent },
      ]);
      resetStream();
    }
  }

  const steps = [
    { label: '需求分析', status: report ? ('done' as const) : ('active' as const) },
    { label: '风险识别', status: report?.risks?.length ? ('done' as const) : ('pending' as const) },
    {
      label: '测试点建议',
      status: sceneMap?.test_points?.length ? ('done' as const) : ('pending' as const),
    },
  ];

  const riskGroups = ['high', 'medium', 'industry'];

  return (
    <div className="p-6 h-[calc(100vh-0px)] flex flex-col">
      <div className="mb-4">
        <h1 className="font-display font-bold text-[20px]">需求分析</h1>
        <div className="text-text3 text-[12px] mt-1">需求 ID: {id}</div>
      </div>
      <ProgressSteps steps={steps} />

      <div className="flex-1 grid grid-cols-[300px_1fr_280px] gap-4 min-h-0">
        {/* Left: Risk list */}
        <div className="bg-bg1 border border-border rounded-[10px] p-4 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <div className="text-[13px] font-semibold">风险清单</div>
            <button
              type="button"
              onClick={runDiagnosis}
              disabled={isStreaming}
              className="text-[11px] px-2.5 py-1 rounded-md bg-accent text-black font-medium disabled:opacity-50"
            >
              {isStreaming ? '分析中...' : '开始分析'}
            </button>
          </div>
          {riskGroups.map((level) => {
            const config = riskLevelConfig[level];
            const risks = report?.risks?.filter((r) => r.level === level) ?? [];
            if (risks.length === 0) return null;
            return (
              <div key={level} className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <StatusPill variant={config.variant}>{config.label}</StatusPill>
                  <span className="text-[10px] text-text3 font-mono">{risks.length}</span>
                </div>
                {risks.map((r) => (
                  <div key={r.id} className="p-2.5 bg-bg2 rounded-md mb-1.5 border border-border">
                    <div className="text-[12px] text-text font-medium">{r.title}</div>
                    {r.description && (
                      <div className="text-[11px] text-text3 mt-1">{r.description}</div>
                    )}
                    <div className="mt-1.5">
                      <StatusPill
                        variant={
                          r.risk_status === 'resolved'
                            ? 'green'
                            : r.risk_status === 'acknowledged'
                              ? 'amber'
                              : 'gray'
                        }
                      >
                        {r.risk_status}
                      </StatusPill>
                    </div>
                  </div>
                ))}
              </div>
            );
          })}
          {!report?.risks?.length && (
            <div className="text-text3 text-[12px] text-center py-8">点击「开始分析」分析需求</div>
          )}
        </div>

        {/* Center: Chat */}
        <div className="bg-bg1 border border-border rounded-[10px] flex flex-col overflow-hidden">
          <div ref={chatRef} className="flex-1 overflow-y-auto p-4">
            {messages.map((m) => (
              <ChatBubble
                key={m.id}
                sender={m.role === 'user' ? 'user' : 'ai'}
                content={m.content}
              />
            ))}
            <ThinkingStream text={thinkingText} isStreaming={isStreaming && !contentText} />
            {contentText && (
              <ChatBubble sender="ai" content={contentText} isStreaming={isStreaming} />
            )}
          </div>
          <div className="border-t border-border p-3 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              className="flex-1 bg-bg2 border border-border rounded-md px-3 py-1.5 text-[13px] text-text outline-none focus:border-accent placeholder:text-text3"
              placeholder="输入补充说明或提问..."
              disabled={isStreaming}
            />
            <button
              type="button"
              onClick={sendMessage}
              disabled={isStreaming || !input.trim()}
              className="px-4 py-1.5 rounded-md text-[12px] font-semibold bg-accent text-black disabled:opacity-50"
            >
              发送
            </button>
          </div>
        </div>

        {/* Right: Scene map preview */}
        <div className="bg-bg1 border border-border rounded-[10px] p-4 overflow-y-auto">
          <div className="text-[13px] font-semibold mb-3">场景地图预览</div>
          {sceneMap?.test_points?.length ? (
            <div className="space-y-1.5">
              {sceneMap.test_points.map((tp) => (
                <div key={tp.id} className="p-2 bg-bg2 rounded-md border border-border">
                  <div className="flex items-center gap-1.5">
                    <StatusPill
                      variant={
                        tp.priority === 'P0' ? 'red' : tp.priority === 'P1' ? 'amber' : 'gray'
                      }
                    >
                      {tp.priority}
                    </StatusPill>
                    <span className="text-[11.5px] text-text">{tp.title}</span>
                  </div>
                  <div className="text-[10px] text-text3 mt-1">{tp.group_name}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-text3 text-[12px] text-center py-8">完成分析后自动生成</div>
          )}
        </div>
      </div>
    </div>
  );
}
