'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Target,
  FileText,
  MessageSquare,
  ClipboardList,
  Upload,
  ChevronLeft,
  Clock,
  Settings,
  SendHorizontal,
  Loader2,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { apiClient } from '@/lib/api-client';
import { useSSEStream } from '@/hooks/useSSEStream';
import { useStreamStore } from '@/stores/stream-store';
import type { GenerationSession, TestCase, SceneMap, TestPoint } from '@/types/api';

/* ── Static demo data ── */

const staticTreeData = [
  { id: 's1', label: '1. 需求概述', children: [] },
  {
    id: 's2',
    label: '2. 自动保存功能',
    children: [
      { id: 'TP-001', label: 'TP-001 正常自动保存触发', dot: 'green', count: 3, checked: true, active: false },
      { id: 'TP-002', label: 'TP-002 手动保存优先级', dot: 'green', count: 2, checked: true, active: false },
      { id: 'TP-003', label: 'TP-003 草稿恢复交互', dot: 'yellow', count: 3, checked: false, active: false },
      { id: 'TP-004', label: 'TP-004 localStorage暂存', dot: 'yellow', count: 4, checked: false, active: true },
    ],
  },
  {
    id: 's3',
    label: '3. 并发编辑',
    children: [
      { id: 'TP-005', label: 'TP-005 并发编辑冲突', dot: 'red', count: 5, checked: false, active: false },
    ],
  },
  {
    id: 's4',
    label: '4. 权限控制',
    children: [
      { id: 'TP-006', label: 'TP-006 角色权限校验', dot: 'gray', count: 0, checked: false, active: false },
      { id: 'TP-007', label: 'TP-007 越权操作拦截', dot: 'gray', count: 0, checked: false, active: false },
    ],
  },
];

const staticChatMessages = [
  { id: 'm1', role: 'system' as const, content: '正在为 TP-004 生成测试用例…', time: '14:32' },
  {
    id: 'm2',
    role: 'ai' as const,
    time: '14:32',
    content: '已为您生成 TC-004-01「localStorage 暂存写入验证」，包含 4 个步骤。',
  },
  {
    id: 'm3',
    role: 'ai' as const,
    time: '14:33',
    content: '已为您生成 TC-004-02「暂存数据过期清理」，验证超过 72 小时的草稿是否自动清除',
  },
];

const staticGeneratedCases = [
  { id: 'TC-001', title: '正常编辑触发自动保存', status: 'confirmed' as const, brief: '验证用户在编辑器中输入内容后，系统在 5 秒内自动触发保存操作', tp: 'TP-001', steps: 4, priority: 'P1', type: '正常' },
  { id: 'TC-002', title: '手动保存覆盖自动保存', status: 'confirmed' as const, brief: '验证用户手动点击保存时，取消当前自动保存定时器', tp: 'TP-002', steps: 3, priority: 'P1', type: '正常' },
  { id: 'TC-003', title: '草稿恢复弹窗交互', status: 'pending' as const, brief: '验证用户重新打开含未保存草稿的文档时弹窗提示', tp: 'TP-003', steps: 5, priority: 'P2', type: '正常' },
  { id: 'TC-004', title: 'localStorage 暂存写入验证', status: 'pending' as const, brief: '验证自动暂存功能将草稿内容正确写入 localStorage', tp: 'TP-004', steps: 4, priority: 'P1', type: '正常' },
  { id: 'TC-005', title: '暂存容量超限降级', status: 'pending' as const, brief: '验证当 localStorage 容量接近上限时降级处理', tp: 'TP-004', steps: 3, priority: 'P2', type: '边界' },
];

interface ChatMessage {
  id: string;
  role: 'user' | 'ai' | 'system';
  content: string;
  thinking?: string;
  time: string;
}

const quickCommands = ['/生成全部', '/优化', '/换一种思路', '/调整粒度'];
const modeButtons = [
  { key: 'tp', label: '测试点驱动', icon: Target, active: false },
  { key: 'doc', label: '文档驱动', icon: FileText, active: true },
  { key: 'chat', label: '对话引导', icon: MessageSquare, active: false },
  { key: 'tpl', label: '模板填充', icon: ClipboardList, active: false },
];
const caseFilters = ['全部', '正常', '异常', '边界'];

function WorkbenchContent() {
  const searchParams = useSearchParams();
  const reqId = searchParams.get('reqId');
  const queryClient = useQueryClient();
  const { streamSSE } = useSSEStream();
  const { thinkingText, contentText, isStreaming, reset: resetStream } = useStreamStore();
  const chatEndRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionLoading, setSessionLoading] = useState(false);

  const useStatic = !reqId;

  // Create or fetch generation session
  useEffect(() => {
    if (!reqId) return;
    let cancelled = false;
    (async () => {
      setSessionLoading(true);
      try {
        const session = await apiClient<GenerationSession>('/generation/sessions', {
          method: 'POST',
          body: JSON.stringify({ requirement_id: reqId }),
        });
        if (!cancelled) {
          setSessionId(session.id);
          setMessages([{
            id: 'sys-init',
            role: 'system',
            content: `会话已创建 (${session.mode})，模型: ${session.model_used}`,
            time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          }]);
        }
      } catch (err) {
        if (!cancelled) {
          setMessages([{
            id: 'sys-err',
            role: 'system',
            content: `创建会话失败: ${err instanceof Error ? err.message : '未知错误'}`,
            time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          }]);
        }
      } finally {
        if (!cancelled) setSessionLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [reqId]);

  // Fetch test points for left column
  const { data: sceneMap } = useQuery({
    queryKey: ['sceneMap', reqId],
    queryFn: () => apiClient<SceneMap>(`/scene-map/${reqId}`),
    enabled: !!reqId,
  });

  // Fetch generated test cases
  const { data: cases } = useQuery({
    queryKey: ['generatedCases', sessionId],
    queryFn: () => apiClient<TestCase[]>(`/generation/sessions/${sessionId}/cases`),
    enabled: !!sessionId,
    refetchInterval: isStreaming ? 5000 : false,
  });

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, contentText, thinkingText]);

  // After streaming is done, append AI response to messages
  useEffect(() => {
    if (!isStreaming && (contentText || thinkingText) && sessionId) {
      const now = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
      setMessages((prev) => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          role: 'ai',
          content: contentText || '(无内容)',
          thinking: thinkingText || undefined,
          time: now,
        },
      ]);
      resetStream();
      queryClient.invalidateQueries({ queryKey: ['generatedCases', sessionId] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isStreaming]);

  const handleSend = useCallback(async () => {
    if (!inputText.trim() || !sessionId || isStreaming) return;
    const userMsg = inputText.trim();
    setInputText('');
    const now = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    setMessages((prev) => [...prev, { id: `user-${Date.now()}`, role: 'user', content: userMsg, time: now }]);

    try {
      await streamSSE(`/generation/sessions/${sessionId}/chat`, { message: userMsg });
    } catch {
      /* handled by store */
    }
  }, [inputText, sessionId, isStreaming, streamSSE]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Build tree data from real test points
  const treeData = (() => {
    if (useStatic || !sceneMap?.test_points?.length) return staticTreeData;
    const groups = [...new Set(sceneMap.test_points.map((tp: TestPoint) => tp.group_name))];
    return groups.map((g, i) => ({
      id: `g-${i}`,
      label: `${i + 1}. ${g}`,
      children: sceneMap.test_points
        .filter((tp: TestPoint) => tp.group_name === g)
        .map((tp: TestPoint) => ({
          id: tp.id,
          label: tp.title,
          dot: tp.priority === 'P0' ? 'red' : tp.priority === 'P1' ? 'yellow' : 'green',
          count: tp.estimated_cases,
          checked: tp.status === 'confirmed',
          active: false,
        })),
    }));
  })();

  const displayCases = useStatic ? staticGeneratedCases : (cases ?? []).map((c) => ({
    id: c.case_id,
    title: c.title,
    status: c.status === 'accepted' ? 'confirmed' as const : 'pending' as const,
    brief: c.precondition ?? '',
    tp: '',
    steps: 0,
    priority: c.priority,
    type: c.case_type,
  }));

  const displayMessages = useStatic ? staticChatMessages : messages;

  return (
    <div className="no-sidebar">
      {/* ── Top bar ── */}
      <div className="topbar" style={{ flexWrap: 'wrap' }}>
        <div style={{ width: '100%' }}>
          <span className="page-watermark">{reqId ? `${reqId.slice(0, 8)}… · 生成工作台` : 'REQ-089 · 生成工作台'}</span>
        </div>
        <h1>用例生成工作台</h1>
        <span className="sub" style={{ whiteSpace: 'nowrap' }}>
          {sessionLoading ? '创建会话中...' : '文档驱动模式'}
        </span>
        <div className="spacer" />
        <div style={{ display: 'flex', gap: 4 }}>
          {modeButtons.map((m) => {
            const ModeIcon = m.icon;
            return (
              <button type="button" key={m.key} className={m.active ? 'btn btn-primary btn-sm' : 'btn btn-sm'}>
                <ModeIcon size={12} />{m.label}
              </button>
            );
          })}
        </div>
        <button type="button" className="btn" style={{ marginLeft: 8 }}><Upload size={12} /> 导出</button>
        <button type="button" className="btn btn-primary">提交到用例库</button>
      </div>

      {/* ── Three-column layout ── */}
      <div className="three-col">
        {/* ── Left: Requirement navigation ── */}
        <div className="col-left">
          <div className="col-header">
            <span><FileText size={14} /> 需求文档</span>
            <div className="spacer" />
            <button type="button" className="btn btn-ghost btn-sm"><ChevronLeft size={14} /></button>
          </div>
          <div style={{ padding: '8px 10px' }}>
            {treeData.map((section) => (
              <div key={section.id} style={{ marginBottom: 8 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text2)', padding: '6px 4px', cursor: 'pointer' }}>
                  {section.label}
                </div>
                {section.children.map((tp) => (
                  <div key={tp.id} className={`tp-item${tp.active ? ' active' : ''}`} style={{ marginLeft: 8, fontSize: 11.5 }}>
                    <span className={`scene-dot dot-${tp.dot}`} />
                    <span style={{ flex: 1, color: tp.active ? 'var(--accent)' : 'var(--text2)' }}>{tp.label}</span>
                    <span className="mono" style={{ fontSize: 10, color: 'var(--text3)' }}>~{tp.count}条</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* ── Middle: AI chat ── */}
        <div className="col-mid" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="col-header" style={{ background: 'var(--bg)' }}>
            <span><MessageSquare size={14} /> AI 生成对话</span>
            <div className="spacer" />
            {isStreaming && (
              <span className="pill pill-amber" style={{ fontSize: 10 }}><Clock size={10} /> 生成中...</span>
            )}
          </div>

          {/* Chat area */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
            {displayMessages.map((msg) => {
              if (msg.role === 'system') {
                return (
                  <div key={msg.id} style={{ textAlign: 'center', fontSize: 11, color: 'var(--text3)', margin: '12px 0', fontFamily: 'var(--font-mono)' }}>
                    <Settings size={12} /> {msg.content}
                  </div>
                );
              }
              if (msg.role === 'user') {
                return (
                  <div key={msg.id} className="chat-msg" style={{ justifyContent: 'flex-end' }}>
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                      <div className="chat-bubble" style={{ background: 'var(--accent-d)', maxWidth: 520 }}>{msg.content}</div>
                      <div className="chat-time">{msg.time}</div>
                    </div>
                    <div className="chat-avatar" style={{ background: 'var(--blue)' }}>U</div>
                  </div>
                );
              }
              return (
                <div key={msg.id} className="chat-msg">
                  <div className="chat-avatar chat-ai">AI</div>
                  <div style={{ flex: 1 }}>
                    {'thinking' in msg && msg.thinking && (
                      <details style={{ marginBottom: 4 }}>
                        <summary style={{ fontSize: 11, color: 'var(--text3)', cursor: 'pointer' }}>💭 思考过程</summary>
                        <pre style={{ fontSize: 11, color: 'var(--text3)', whiteSpace: 'pre-wrap', margin: '4px 0' }}>{msg.thinking}</pre>
                      </details>
                    )}
                    <div className="chat-bubble ai-bubble markdown-body"><ReactMarkdown>{msg.content}</ReactMarkdown></div>
                    <div className="chat-time">{msg.time}</div>
                  </div>
                </div>
              );
            })}

            {/* Live streaming message */}
            {isStreaming && (thinkingText || contentText) && (
              <div className="chat-msg">
                <div className="chat-avatar chat-ai">AI</div>
                <div style={{ flex: 1 }}>
                  {thinkingText && (
                    <details open={!contentText} style={{ marginBottom: 4 }}>
                      <summary style={{ fontSize: 11, color: 'var(--text3)', cursor: 'pointer' }}>💭 思考中...</summary>
                      <pre style={{ fontSize: 11, color: 'var(--text3)', whiteSpace: 'pre-wrap', margin: '4px 0' }}>{thinkingText}</pre>
                    </details>
                  )}
                  {contentText && (
                    <div className="chat-bubble ai-bubble markdown-body">
                      <ReactMarkdown>{contentText}</ReactMarkdown>
                      <span className="streaming-cursor" />
                    </div>
                  )}
                  {!contentText && thinkingText && (
                    <div className="chat-bubble ai-bubble" style={{ color: 'var(--text3)' }}>
                      <Loader2 size={12} className="spin" /> 思考中...
                    </div>
                  )}
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Quick commands */}
          <div style={{ display: 'flex', gap: 6, padding: '6px 16px', borderTop: '1px solid var(--border)', background: 'var(--bg)' }}>
            {quickCommands.map((cmd) => (
              <button type="button" key={cmd} className="btn btn-ghost btn-sm mono" onClick={() => { setInputText(cmd); }}>
                {cmd}
              </button>
            ))}
          </div>

          {/* Input area */}
          <div style={{ display: 'flex', gap: 8, padding: '10px 16px', borderTop: '1px solid var(--border)', background: 'var(--bg)' }}>
            <textarea
              className="input"
              placeholder="输入指令或描述需要生成的用例场景…"
              rows={2}
              style={{ flex: 1, resize: 'none' }}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isStreaming || (!useStatic && !sessionId)}
            />
            <button
              type="button"
              className="btn btn-primary"
              style={{ alignSelf: 'flex-end' }}
              onClick={handleSend}
              disabled={isStreaming || !inputText.trim() || (!useStatic && !sessionId)}
            >
              {isStreaming ? <Loader2 size={12} className="spin" /> : <SendHorizontal size={12} />} 发送
            </button>
          </div>
        </div>

        {/* ── Right: Generated cases ── */}
        <div className="col-right" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="col-header">
            <span><ClipboardList size={14} /> 已生成用例</span>
            <div className="spacer" />
            <span className="mono" style={{ fontSize: 11, color: 'var(--text3)' }}>{displayCases.length} 条</span>
          </div>

          {/* Filter pills */}
          <div style={{ display: 'flex', gap: 4, padding: '8px 12px' }}>
            {caseFilters.map((f, i) => (
              <button type="button" key={f} className={i === 0 ? 'btn btn-primary btn-sm' : 'btn btn-sm'}>{f}</button>
            ))}
          </div>

          {/* Case cards list */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '4px 12px 12px' }}>
            {displayCases.map((c) => (
              <div key={c.id} className="case-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <span className="case-id">{c.id}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', flex: 1 }}>{c.title}</span>
                  <span className={`pill ${c.status === 'confirmed' ? 'pill-green' : 'pill-amber'}`} style={{ fontSize: 10 }}>
                    {c.status === 'confirmed' ? '已确认' : '待确认'}
                  </span>
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--text3)', lineHeight: 1.5, marginBottom: 8 }}>{c.brief}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 10.5 }}>
                  {c.tp && <span className="tag">{c.tp}</span>}
                  {c.steps > 0 && <span style={{ color: 'var(--text3)' }}>{c.steps} 步骤</span>}
                  <div className="spacer" />
                  <span className="pill pill-gray" style={{ fontSize: 10 }}>{c.priority}</span>
                  <span className="tag">{c.type}</span>
                </div>
              </div>
            ))}
            {!useStatic && displayCases.length === 0 && !isStreaming && (
              <div style={{ textAlign: 'center', color: 'var(--text3)', padding: 32, fontSize: 12 }}>
                发送消息开始生成用例
              </div>
            )}
          </div>

          {/* Batch actions */}
          <div style={{ display: 'flex', gap: 8, padding: '10px 12px', borderTop: '1px solid var(--border)' }}>
            <button type="button" className="btn btn-sm" style={{ flex: 1 }}>批量确认</button>
            <button type="button" className="btn btn-sm" style={{ flex: 1 }}>导出选中</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}><Loader2 size={24} /></div>}>
      <WorkbenchContent />
    </Suspense>
  );
}
