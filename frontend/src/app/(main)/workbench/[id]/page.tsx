'use client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { LucideIcon } from 'lucide-react';
import { FileText, MessageSquare, Target, Zap } from 'lucide-react';
import { useParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { ChatBubble, ThinkingStream } from '@/components/ui';
import { useSSEStream } from '@/hooks/useSSEStream';
import { apiClient } from '@/lib/api-client';
import { useStreamStore } from '@/stores/stream-store';
import { CasePreviewCard, type CaseStep } from './_components/CasePreviewCard';

interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
}

interface GeneratedCase {
  id: string;
  case_id: string;
  title: string;
  priority: string;
  case_type: string;
  status: string;
  steps?: CaseStep[];
}

const modes: { key: string; label: string; icon: LucideIcon; desc: string }[] = [
  { key: 'test_point_driven', label: '测试点驱动', icon: Target, desc: '基于确认的测试点逐个生成' },
  { key: 'document', label: '文档驱动', icon: FileText, desc: '直接从需求文档生成' },
  { key: 'dialogue', label: '对话式', icon: MessageSquare, desc: '通过对话逐步细化生成' },
];

export default function WorkbenchPage() {
  const { id } = useParams<{ id: string }>();
  const { streamSSE } = useSSEStream();
  const { thinkingText, contentText, isStreaming } = useStreamStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [mode, setMode] = useState('test_point_driven');
  const chatRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  // Create session on mount
  useEffect(() => {
    apiClient<{ id: string }>('/generation/sessions', {
      method: 'POST',
      body: JSON.stringify({ requirement_id: id, mode }),
    })
      .then((s) => setSessionId(s.id))
      .catch(() => {});
  }, [id, mode]);

  const { data: cases = [] } = useQuery({
    queryKey: ['generation-cases', sessionId],
    queryFn: () => apiClient<GeneratedCase[]>(`/generation/sessions/${sessionId}/cases`),
    enabled: !!sessionId,
  });

  const acceptMutation = useMutation({
    mutationFn: (caseId: string) =>
      apiClient(`/generation/sessions/${sessionId}/cases/${caseId}/accept`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['generation-cases', sessionId] }),
  });

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [thinkingText, contentText, messages]);

  async function sendMessage() {
    if (!input.trim() || isStreaming || !sessionId) return;
    const msg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { id: Date.now().toString(), role: 'user', content: msg }]);
    await streamSSE(`/generation/sessions/${sessionId}/chat`, { message: msg });
    const latestContent = useStreamStore.getState().contentText;
    if (latestContent) {
      setMessages((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), role: 'ai', content: latestContent },
      ]);
    }
    queryClient.invalidateQueries({ queryKey: ['generation-cases', sessionId] });
  }

  return (
    <div className="flex flex-col h-[calc(100vh-0px)] overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center gap-3 p-3 border-b border-border bg-bg1">
        <div className="font-display font-bold text-[14px] text-accent flex items-center gap-1">
          <Zap size={14} /> 生成工作台
        </div>
        <div className="w-px h-5 bg-border mx-1" />
        {modes.map((m) => {
          const ModeIcon = m.icon;
          return (
            <button
              type="button"
              key={m.key}
              onClick={() => setMode(m.key)}
              className={`px-3 py-1 rounded-md text-[11.5px] border transition-colors flex items-center gap-1 ${
                mode === m.key
                  ? 'bg-accent-d text-accent border-[rgba(0,217,163,0.2)]'
                  : 'text-text3 border-border hover:text-text hover:border-border2'
              }`}
            >
              <ModeIcon size={12} /> {m.label}
            </button>
          );
        })}
        <div className="flex-1" />
        <span className="text-[11px] text-text3 font-mono">
          需求: {id?.toString().slice(0, 8)}...
        </span>
      </div>

      {/* Three-col */}
      <div className="flex-1 grid grid-cols-[240px_1fr_340px] min-h-0">
        {/* Left: Requirement nav */}
        <div className="bg-bg1 border-r border-border p-3 overflow-y-auto">
          <div className="text-[11px] font-semibold text-text3 uppercase tracking-wide mb-2">
            需求上下文
          </div>
          <div className="p-2.5 bg-bg2 rounded-md border border-border mb-2">
            <div className="text-[12px] text-text font-medium">当前需求</div>
            <div className="text-[11px] text-text3 mt-0.5 font-mono">
              {id?.toString().slice(0, 12)}...
            </div>
          </div>
          <div className="text-[11px] font-semibold text-text3 uppercase tracking-wide mb-2 mt-4">
            生成模式
          </div>
          {modes.map((m) => {
            const ModeIcon = m.icon;
            return (
              <div
                key={m.key}
                className={`p-2 rounded-md mb-1 text-[11px] ${mode === m.key ? 'bg-accent-d text-accent border border-[rgba(0,217,163,0.2)]' : 'text-text3'}`}
              >
                <div className="font-medium flex items-center gap-1">
                  <ModeIcon size={11} /> {m.label}
                </div>
                <div className="text-[10px] mt-0.5 opacity-70">{m.desc}</div>
              </div>
            );
          })}
        </div>

        {/* Center: AI chat */}
        <div className="flex flex-col bg-bg overflow-hidden">
          <div ref={chatRef} className="flex-1 overflow-y-auto p-4">
            {messages.length === 0 && !thinkingText && !contentText && (
              <div className="text-center py-16">
                <div className="text-[24px] mb-2">
                  <Zap size={24} />
                </div>
                <div className="text-text2 text-[14px] font-medium">AI 用例生成工作台</div>
                <div className="text-text3 text-[12px] mt-1">输入指令开始生成测试用例</div>
              </div>
            )}
            {messages.map((m) => (
              <ChatBubble key={m.id} role={m.role} content={m.content} />
            ))}
            <ThinkingStream text={thinkingText} isStreaming={isStreaming && !contentText} />
            {contentText && (
              <ChatBubble role="ai" content={contentText} isStreaming={isStreaming} />
            )}
          </div>
          <div className="border-t border-border p-3 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              className="flex-1 bg-bg2 border border-border rounded-md px-3 py-2 text-[13px] text-text outline-none focus:border-accent placeholder:text-text3"
              placeholder="描述你需要的测试用例，或输入 /gen 开始自动生成..."
              disabled={isStreaming}
            />
            <button
              type="button"
              onClick={sendMessage}
              disabled={isStreaming || !input.trim()}
              className="px-5 py-2 rounded-md text-[12px] font-semibold bg-accent text-black disabled:opacity-50 hover:bg-accent2 transition-colors"
            >
              生成
            </button>
          </div>
        </div>

        {/* Right: Case preview list */}
        <div className="bg-bg1 border-l border-border p-3 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <div className="text-[12px] font-semibold">生成用例</div>
            <span className="font-mono text-[10px] text-text3">{cases.length} 条</span>
          </div>
          {cases.length > 0 ? (
            cases.map((c) => (
              <CasePreviewCard
                key={c.id}
                caseId={c.case_id}
                title={c.title}
                priority={c.priority}
                caseType={c.case_type}
                status={c.status}
                steps={c.steps}
                onAccept={c.status === 'draft' ? () => acceptMutation.mutate(c.id) : undefined}
              />
            ))
          ) : (
            <div className="text-text3 text-[12px] text-center py-8">用例将在生成后显示在这里</div>
          )}
        </div>
      </div>
    </div>
  );
}
