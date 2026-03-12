'use client';

import { Bot, Brain, Loader2, User } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { EmptyState } from '@/components/ui/EmptyState';
import { CaseCard } from '@/components/workspace/CaseCard';
import { StreamCursor } from '@/components/workspace/StreamCursor';
import type { SSEStreamingCase } from '@/hooks/useSSE';
import type { WorkbenchMessage } from '@/stores/workspace-store';
import { CaseSkeleton } from './CaseSkeleton';

interface ChatAreaProps {
  messages: WorkbenchMessage[];
  streamingContent: string;
  streamingThinking: string;
  streamingCases: SSEStreamingCase[];
  isStreaming: boolean;
}

function renderMarkdown(text: string): string {
  return text
    .replace(/### (.+)/g, '<h3 class="text-[13px] font-semibold text-sy-text mt-3 mb-1">$1</h3>')
    .replace(/## (.+)/g, '<h2 class="text-[14px] font-semibold text-sy-text mt-3 mb-1">$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-sy-text">$1</strong>')
    .replace(
      /`([^`]+)`/g,
      '<code class="px-1 py-0.5 rounded bg-sy-bg-3 text-sy-accent font-mono text-[11px]">$1</code>',
    )
    .replace(
      /^- (.+)$/gm,
      '<li class="ml-3 text-[12.5px] text-sy-text-2 leading-relaxed">• $1</li>',
    )
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');
}

/** 检测文本是否包含 JSON 用例块（纯 JSON 或 ```json 代码块） */
function hasJsonBlock(text: string): boolean {
  const t = text.trimStart();
  return t.startsWith('{') || t.startsWith('[') || text.includes('```json');
}

/** 提取 JSON 块之前的自然语言部分（用于分段渲染） */
function extractPreJsonText(content: string): string {
  const idx = content.indexOf('```json');
  if (idx !== -1) return content.slice(0, idx).trim();
  const t = content.trimStart();
  if (t.startsWith('[') || t.startsWith('{')) return '';
  return '';
}

const AI_AVATAR = (
  <div className="w-7 h-7 rounded-full shrink-0 flex items-center justify-center bg-gradient-to-br from-sy-accent/15 to-sy-info/15 border border-sy-accent/30">
    <Bot className="w-3.5 h-3.5 text-sy-accent" />
  </div>
);

/** 思考中等待状态（尚无任何内容时显示） */
function ThinkingWaitPanel() {
  return (
    <div className="rounded-xl rounded-bl-sm px-3.5 py-3 bg-sy-accent/4 border border-sy-accent/15">
      <div className="flex items-center gap-2.5">
        <div className="relative flex items-center justify-center w-5 h-5">
          <span className="absolute inline-flex w-full h-full rounded-full bg-sy-accent/20 animate-ping" />
          <Brain className="w-3 h-3 text-sy-accent relative" />
        </div>
        <span className="text-[12.5px] text-sy-text-2">AI 正在思考</span>
        <div className="flex gap-0.5 ml-0.5">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-1 h-1 rounded-full bg-sy-accent/60 animate-bounce"
              style={{ animationDelay: `${i * 150}ms` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

/** 思考内容流式展示（可折叠） */
function ThinkingStreamPanel({ text, isStreaming }: { text: string; isStreaming: boolean }) {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <div className="mb-2 rounded-lg border border-sy-border overflow-hidden">
      <button
        type="button"
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-sy-bg-2 text-[11.5px] text-sy-text-3 hover:text-sy-text-2 transition-colors"
      >
        <Brain className="w-3 h-3 text-sy-purple shrink-0" />
        <span className="text-sy-purple font-medium">思考过程</span>
        {isStreaming && (
          <span className="w-1.5 h-1.5 rounded-full bg-sy-accent animate-pulse ml-0.5" />
        )}
        <span className="ml-auto text-[10px]">{collapsed ? '▼' : '▲'}</span>
      </button>
      {!collapsed && (
        <div className="px-3 py-2 bg-sy-bg text-sy-text-3 text-[12px] font-mono leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto">
          {text}
          {isStreaming && (
            <span className="inline-block w-[2px] h-[13px] bg-sy-text-3 ml-0.5 animate-blink" />
          )}
        </div>
      )}
    </div>
  );
}

/** 流式用例生成面板 — 实时渲染已完成的 case，末尾附 skeleton 表示还在生成 */
function CaseGeneratingPanel({
  cases,
  preText,
  isGenerating,
}: {
  cases: SSEStreamingCase[];
  preText?: string;
  isGenerating: boolean;
}) {
  return (
    <div className="rounded-xl rounded-bl-sm px-3.5 py-3 bg-sy-accent/4 border border-sy-accent/15">
      {/* JSON 前的自然语言 */}
      {preText && (
        <div
          className="prose-sm text-[12.5px] leading-relaxed text-sy-text mb-3 pb-3 border-b border-sy-accent/10"
          // biome-ignore lint/security/noDangerouslySetInnerHtml: pre-JSON natural language render
          dangerouslySetInnerHTML={{ __html: renderMarkdown(preText) }}
        />
      )}

      {/* 进度标题 */}
      <div className="flex items-center gap-2 text-[12.5px] text-sy-text-2 mb-3">
        <Loader2 className="w-3.5 h-3.5 animate-spin text-sy-accent shrink-0" />
        <span>
          AI 正在生成测试用例
          {cases.length > 0 ? (
            <span className="ml-1 text-sy-accent font-semibold">（已完成 {cases.length} 条）</span>
          ) : (
            <StreamCursor />
          )}
        </span>
      </div>

      {/* 已完成的 case 实时渲染 */}
      {cases.length > 0 && (
        <div className="space-y-2 mb-2">
          {cases.map((c) => (
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
        </div>
      )}

      {/* 还在生成中时展示 skeleton */}
      {isGenerating && <CaseSkeleton count={1} />}
    </div>
  );
}

function MessageBubble({ message }: { message: WorkbenchMessage }) {
  const isAI = message.role === 'assistant';
  const [thinkingOpen, setThinkingOpen] = useState(false);

  // 如果 AI 消息含有 JSON 块（纯 JSON 或 ```json 代码块）且已解析出用例，隐藏 JSON 原文
  const hasCases = isAI && (message.cases?.length ?? 0) > 0;
  const contentHasJson = isAI && hasJsonBlock(message.content);
  const showRawContent = !contentHasJson || !hasCases;
  // JSON 块前的自然语言部分
  const preJsonText = contentHasJson ? extractPreJsonText(message.content) : '';

  return (
    <div className={`flex gap-2.5 mb-4 ${isAI ? '' : 'flex-row-reverse'}`}>
      {/* Avatar */}
      <div
        className={`w-7 h-7 rounded-full shrink-0 flex items-center justify-center ${
          isAI
            ? 'bg-gradient-to-br from-sy-accent/15 to-sy-info/15 border border-sy-accent/30'
            : 'bg-sy-bg-3 border border-sy-border'
        }`}
      >
        {isAI ? (
          <Bot className="w-3.5 h-3.5 text-sy-accent" />
        ) : (
          <User className="w-3.5 h-3.5 text-sy-text-2" />
        )}
      </div>

      {/* Content */}
      <div className={`flex-1 min-w-0 ${isAI ? 'max-w-[85%]' : 'max-w-[75%]'}`}>
        {/* Thinking block (collapsible) */}
        {isAI && message.thinking_content && (
          <div className="mb-2">
            <button
              type="button"
              onClick={() => setThinkingOpen(!thinkingOpen)}
              className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] text-sy-text-3 bg-sy-bg-2 border border-sy-border hover:border-sy-border-2 transition-colors"
            >
              <Brain className="w-2.5 h-2.5 text-sy-purple" />
              <span className="text-sy-purple">思考过程</span>
              <span className="text-[10px]">{thinkingOpen ? '▲' : '▼'}</span>
            </button>
            {thinkingOpen && (
              <div className="mt-1.5 px-3 py-2 rounded-md bg-sy-bg-2 border border-sy-border text-[11px] text-sy-text-3 font-mono leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto">
                {message.thinking_content}
              </div>
            )}
          </div>
        )}

        {/* Message body */}
        <div
          className={`rounded-xl px-3.5 py-2.5 text-[12.5px] leading-relaxed ${
            isAI
              ? 'bg-sy-accent/4 border border-sy-accent/15 text-sy-text rounded-bl-sm'
              : 'bg-sy-bg-2 border border-sy-border text-sy-text rounded-br-sm'
          }`}
        >
          {isAI ? (
            showRawContent ? (
              <div
                className="prose-sm"
                // biome-ignore lint/security/noDangerouslySetInnerHtml: markdown render of AI content
                dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
              />
            ) : (
              <>
                {/* 保留 JSON 块前的自然语言 */}
                {preJsonText && (
                  <div
                    className="prose-sm mb-2 pb-2 border-b border-sy-accent/10"
                    // biome-ignore lint/security/noDangerouslySetInnerHtml: pre-JSON text render
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(preJsonText) }}
                  />
                )}
                <span className="text-sy-text-2">
                  AI 已生成{' '}
                  <span className="font-semibold text-sy-accent">{message.cases?.length}</span>{' '}
                  个测试用例
                </span>
              </>
            )
          ) : (
            <span className="whitespace-pre-wrap">{message.content}</span>
          )}
        </div>

        {/* Embedded test cases */}
        {hasCases && (
          <div className="mt-2 space-y-2">
            {message.cases?.map((tc) => (
              <CaseCard
                key={tc.id}
                caseId={tc.case_id}
                title={tc.title}
                priority={tc.priority}
                type={tc.case_type}
                status={tc.status}
                precondition={tc.precondition}
                steps={tc.steps}
                aiScore={tc.ai_score}
              />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <div className={`mt-1 text-[10px] text-sy-text-3 font-mono ${isAI ? '' : 'text-right'}`}>
          {message.created_at?.slice(11, 16)}
        </div>
      </div>
    </div>
  );
}

export function ChatArea({
  messages,
  streamingContent,
  streamingThinking,
  streamingCases,
  isStreaming,
}: ChatAreaProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  // 用户是否主动向上滚动（为 true 时暂停自动跟随）
  const isUserScrolledUp = useRef(false);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    isUserScrolledUp.current = distFromBottom > 80;
  }, []);

  // 流式输出期间用 instant，避免 smooth 持续接管用户滚动
  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll must run on every content tick
  useEffect(() => {
    if (isUserScrolledUp.current) return;
    chatEndRef.current?.scrollIntoView({
      behavior: isStreaming ? 'instant' : 'smooth',
    });
  }, [messages.length, streamingContent, streamingThinking, streamingCases.length, isStreaming]);

  // 新消息到来（非流式）时强制回到底部并重置状态
  // biome-ignore lint/correctness/useExhaustiveDependencies: only reset on message count change
  useEffect(() => {
    isUserScrolledUp.current = false;
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  if (messages.length === 0 && !isStreaming) {
    return (
      <div className="flex-1 overflow-y-auto flex items-center justify-center">
        <EmptyState
          title="开始对话，生成测试用例"
          description="试试输入：请根据测试点生成详细测试用例"
        />
      </div>
    );
  }

  // 是否检测到 JSON 块（用于决定用哪种渲染模式）
  const streamHasJson = hasJsonBlock(streamingContent) || streamingCases.length > 0;
  const streamPreText = streamHasJson ? extractPreJsonText(streamingContent) : '';

  return (
    <div ref={scrollRef} onScroll={handleScroll} className="flex-1 overflow-y-auto px-4 py-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {/* 流式 thinking 内容（可折叠） */}
      {isStreaming && streamingThinking && (
        <div className="flex gap-2.5 mb-2">
          {AI_AVATAR}
          <div className="flex-1 max-w-[85%]">
            <ThinkingStreamPanel text={streamingThinking} isStreaming={!streamingContent} />
          </div>
        </div>
      )}

      {/* 流式输出内容 */}
      {isStreaming && (streamingContent || streamingCases.length > 0) && (
        <div className="flex gap-2.5 mb-4">
          {AI_AVATAR}
          <div className="flex-1 max-w-[85%]">
            {streamHasJson ? (
              // JSON 模式：实时渲染 CaseCard + 末尾 skeleton
              <CaseGeneratingPanel
                cases={streamingCases}
                preText={streamPreText || undefined}
                isGenerating={isStreaming}
              />
            ) : (
              // 普通文本：Markdown 渲染 + 光标
              <div className="rounded-xl rounded-bl-sm px-3.5 py-2.5 bg-sy-accent/4 border border-sy-accent/15 text-[12.5px] leading-relaxed text-sy-text">
                <div
                  className="prose-sm"
                  // biome-ignore lint/security/noDangerouslySetInnerHtml: streaming markdown content
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(streamingContent) }}
                />
                <StreamCursor />
              </div>
            )}
          </div>
        </div>
      )}

      {/* 等待状态 — 尚未收到任何内容时 */}
      {isStreaming && !streamingContent && !streamingThinking && streamingCases.length === 0 && (
        <div className="flex gap-2.5 mb-4">
          {AI_AVATAR}
          <div className="flex-1 max-w-[85%]">
            <ThinkingWaitPanel />
          </div>
        </div>
      )}

      <div ref={chatEndRef} />
    </div>
  );
}
