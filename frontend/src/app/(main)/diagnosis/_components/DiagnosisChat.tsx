'use client';

import { Activity, Loader2 } from 'lucide-react';
import { useEffect, useRef } from 'react';
import { StreamCursor } from '@/components/workspace/StreamCursor';
import type { ChatMessage } from '@/lib/api';

interface DiagnosisChatProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  streamContent: string;
  streamThinking: string;
  reqTitle: string;
  hasRequirement: boolean;
}

interface DiagnosisDimension {
  title: string;
  description: string;
  risk_level: 'high' | 'medium' | 'low';
  suggestion: string;
}

interface DiagnosisJsonResult {
  overall_health_score?: number;
  dimensions?: DiagnosisDimension[];
  [key: string]: unknown;
}

function renderDiagnosisJson(json: DiagnosisJsonResult): string {
  const riskLabels: Record<string, string> = {
    high: '<span style="color:var(--red);font-weight:600">高风险</span>',
    medium: '<span style="color:var(--amber);font-weight:600">中风险</span>',
    low: '<span style="color:var(--blue);font-weight:600">低风险</span>',
  };

  let html = '';
  if (json.overall_health_score !== undefined) {
    const score = json.overall_health_score;
    const scoreColor = score >= 70 ? 'var(--accent)' : score >= 50 ? 'var(--amber)' : 'var(--red)';
    html += `<div style="margin-bottom:12px;padding:8px 12px;background:var(--bg2);border-radius:8px;display:flex;align-items:center;gap:8px">
      <span style="font-size:11px;color:var(--text3)">总体健康评分</span>
      <span style="font-size:20px;font-weight:700;color:${scoreColor}">${score}</span>
      <span style="font-size:11px;color:var(--text3)">/100</span>
    </div>`;
  }

  if (Array.isArray(json.dimensions)) {
    html += '<div style="display:flex;flex-direction:column;gap:8px">';
    for (const dim of json.dimensions) {
      const label = riskLabels[dim.risk_level] || dim.risk_level;
      html += `<div style="padding:10px 12px;border-radius:6px;background:var(--bg2)">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
          <span style="font-size:12.5px;font-weight:600;color:var(--text)">${dim.title}</span>
          ${label}
        </div>
        <p style="font-size:12px;color:var(--text2);margin:0 0 4px 0">${dim.description}</p>
        <p style="font-size:11.5px;color:var(--text3);margin:0"><strong>建议：</strong>${dim.suggestion}</p>
      </div>`;
    }
    html += '</div>';
  }
  return (
    html ||
    `<pre style="font-size:11px;color:var(--text2);white-space:pre-wrap">${JSON.stringify(json, null, 2)}</pre>`
  );
}

function renderMarkdown(text: string): string {
  // Handle ```json ... ``` code blocks — parse and render diagnosis reports
  const jsonBlockMatch = text.match(/```json\s*([\s\S]*?)```/);
  if (jsonBlockMatch) {
    try {
      const parsed: DiagnosisJsonResult = JSON.parse(jsonBlockMatch[1]);
      if (parsed.dimensions || parsed.overall_health_score !== undefined) {
        const before = text.substring(0, text.indexOf('```json')).trim();
        const after = text.substring(text.indexOf('```', text.indexOf('```json') + 7) + 3).trim();
        const beforeHtml = before ? `<p>${before.replace(/\n/g, '<br/>')}</p>` : '';
        const afterHtml = after ? `<p>${after.replace(/\n/g, '<br/>')}</p>` : '';
        return `${beforeHtml}${renderDiagnosisJson(parsed)}${afterHtml}`;
      }
    } catch {
      // fall through to normal markdown
    }
  }

  return text
    .replace(/### (.+)/g, '<h3>$1</h3>')
    .replace(/## (.+)/g, '<h2>$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>[\s\S]*<\/li>)/g, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br/>');
}

export function DiagnosisChat({
  messages,
  isStreaming,
  streamContent,
  streamThinking,
  reqTitle: _reqTitle,
  hasRequirement,
}: DiagnosisChatProps) {
  const chatEndRef = useRef<HTMLDivElement>(null);

  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll must trigger on content changes
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamContent]);

  if (!hasRequirement) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-16 h-16 text-text3 opacity-20 mx-auto mb-4" />
          <p className="text-[15px] text-text3">从左侧选择需求后开始 AI 分析</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center py-8">
            <Activity className="w-10 h-10 text-text3 opacity-30 mx-auto mb-2.5" />
            <p className="text-[13px] text-text3">苏格拉底追问区</p>
            <p className="text-[11.5px] text-text3 opacity-60 mt-1">
              运行广度扫描后，可在此与 AI 深度追问
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id ?? `${msg.role}-${msg.created_at}`}
            className={`flex gap-2.5 mb-3.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-[12px] font-bold ${
                msg.role === 'user'
                  ? 'bg-bg3 border border-border text-text2'
                  : 'bg-[linear-gradient(135deg,var(--accent-d),rgba(59,130,246,0.15))] border border-accent/30 text-accent'
              }`}
            >
              {msg.role === 'user' ? 'U' : 'AI'}
            </div>
            <div>
              {msg.role === 'user' ? (
                <div className="rounded-lg px-3 py-2.5 max-w-[480px] text-[12.5px] leading-relaxed bg-bg2 border border-border text-text">
                  {msg.content}
                </div>
              ) : (
                <div
                  className="rounded-lg px-3 py-2.5 max-w-[480px] text-[12.5px] leading-relaxed bg-accent/4 border border-accent/20 text-text chat-bubble ai-bubble markdown-body"
                  // biome-ignore lint/security/noDangerouslySetInnerHtml: renderMarkdown sanitizes AI content
                  dangerouslySetInnerHTML={{
                    __html: renderMarkdown(msg.content),
                  }}
                />
              )}
              {msg.created_at && (
                <div className="text-[10px] text-text3 mt-1 font-mono">
                  {new Date(msg.created_at).toLocaleTimeString('zh-CN', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Thinking stream */}
        {isStreaming && streamThinking && !streamContent && (
          <div className="mb-3 rounded-lg border border-border overflow-hidden">
            <div className="flex items-center gap-2 px-3 py-2 bg-bg2 text-[11.5px] text-text3">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
              <span>思考中...</span>
            </div>
            <div className="px-3 py-2 bg-bg text-text3 text-[12px] font-mono leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto">
              {streamThinking}
              <StreamCursor />
            </div>
          </div>
        )}

        {/* Streaming content */}
        {isStreaming && streamContent && (
          <div className="flex gap-2.5 mb-3.5">
            <div className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-[12px] font-bold bg-[linear-gradient(135deg,var(--accent-d),rgba(59,130,246,0.15))] border border-accent/30 text-accent">
              AI
            </div>
            <div>
              <div
                className="rounded-lg px-3 py-2.5 max-w-[480px] text-[12.5px] leading-relaxed bg-accent/4 border border-accent/20 text-text chat-bubble ai-bubble markdown-body"
                // biome-ignore lint/security/noDangerouslySetInnerHtml: renderMarkdown sanitizes AI content
                dangerouslySetInnerHTML={{
                  __html: renderMarkdown(streamContent),
                }}
              />
              <StreamCursor />
            </div>
          </div>
        )}

        {/* Loading indicator */}
        {isStreaming && !streamContent && !streamThinking && (
          <div className="flex gap-2.5 mb-3.5">
            <div className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-[12px] font-bold bg-[linear-gradient(135deg,var(--accent-d),rgba(59,130,246,0.15))] border border-accent/30 text-accent">
              AI
            </div>
            <div className="rounded-lg px-3 py-2.5 bg-accent/4 border border-accent/20 flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-accent animate-spin" />
              <span className="text-[13px] text-text3">AI 正在分析...</span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>
    </div>
  );
}
