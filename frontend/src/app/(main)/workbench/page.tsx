'use client';

import {
  ChevronDown,
  ChevronRight,
  ClipboardList,
  FileText,
  FolderOpen,
  IterationCw,
  Layers,
  ListChecks,
  Loader2,
  MessageSquare,
  Plus,
  Send,
  Sparkles,
  Target,
  TestTube,
  Zap,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

import { useRequirementTree } from '@/hooks/useRequirementTree';
import { useSSE } from '@/hooks/useSSE';
import type { Requirement } from '@/lib/api';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface GenSession {
  id: string;
  mode: string;
  status: string;
  created_at: string;
}
interface ChatMessage {
  id: string;
  role: string;
  content: string;
  thinking_content?: string;
  created_at: string;
}
interface TestCaseItem {
  id: string;
  case_id: string;
  title: string;
  priority: string;
  status: string;
  source: string;
}

function renderMarkdown(text: string): string {
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

const MODES = [
  { value: 'test_point_driven', label: '测试点驱动', icon: Target },
  { value: 'exploratory', label: '探索式', icon: Zap },
  { value: 'template_based', label: '模板驱动', icon: Layers },
  { value: 'batch', label: '批量生成', icon: ListChecks },
];

export default function WorkbenchPage() {
  const tree = useRequirementTree();
  const sse = useSSE();

  const [sessions, setSessions] = useState<GenSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [testCases, setTestCases] = useState<TestCaseItem[]>([]);

  const [inputText, setInputText] = useState('');
  const [selectedMode, setSelectedMode] = useState('test_point_driven');

  const chatEndRef = useRef<HTMLDivElement>(null);

  const selectRequirement = async (req: Requirement) => {
    tree.selectRequirement(req);
    setActiveSessionId(null);
    setMessages([]);

    try {
      const [sessRes, tcRes] = await Promise.all([
        fetch(`${API}/generation/sessions/by-requirement/${req.id}`),
        fetch(`${API}/testcases/?requirement_id=${req.id}`),
      ]);
      if (sessRes.ok) {
        const sessData = await sessRes.json();
        setSessions(Array.isArray(sessData) ? sessData : []);
      }
      if (tcRes.ok) {
        const tcData = await tcRes.json();
        setTestCases(tcData.items || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const createSession = async () => {
    if (!tree.selectedReqId) return;
    try {
      const res = await fetch(`${API}/generation/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirement_id: tree.selectedReqId,
          mode: selectedMode,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        const newSession = {
          id: data.id,
          mode: data.mode,
          status: data.status,
          created_at: new Date().toISOString(),
        };
        setSessions((prev) => [newSession, ...prev]);
        setActiveSessionId(data.id);
        setMessages([]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const selectSession = async (sessionId: string) => {
    setActiveSessionId(sessionId);
    try {
      const res = await fetch(`${API}/generation/sessions/${sessionId}/messages`);
      if (res.ok) {
        const data = await res.json();
        setMessages(Array.isArray(data) ? data : []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const sendMessage = useCallback(async () => {
    if (!inputText.trim() || !activeSessionId || sse.isStreaming) return;
    const userMsg = inputText.trim();
    setInputText('');
    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: 'user',
        content: userMsg,
        created_at: new Date().toISOString(),
      },
    ]);

    const fullText = await sse.startStream(`/generation/sessions/${activeSessionId}/chat`, {
      body: { message: userMsg },
    });

    // After streaming, reload messages from server to get persisted versions
    if (fullText) {
      try {
        const res = await fetch(`${API}/generation/sessions/${activeSessionId}/messages`);
        if (res.ok) {
          const data = await res.json();
          setMessages(data);
        }
      } catch (e) {
        console.error(e);
      }
    } else {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: sse.error ? `错误: ${sse.error}` : '生成完成',
          created_at: new Date().toISOString(),
        },
      ]);
    }

    // Refresh test cases
    if (tree.selectedReqId) {
      try {
        const tcRes = await fetch(`${API}/testcases/?requirement_id=${tree.selectedReqId}`);
        if (tcRes.ok) {
          const d = await tcRes.json();
          setTestCases(d.items || []);
        }
      } catch (e) {
        console.error(e);
      }
    }
  }, [inputText, activeSessionId, sse, tree.selectedReqId]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll must trigger on messages/streaming changes
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sse.content]);

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 64px)' }}>
      {/* Left: Tree + Sessions */}
      <aside
        style={{
          width: 260,
          minWidth: 260,
          borderRight: '1px solid var(--border)',
          background: 'var(--bg1)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div
          style={{
            padding: 16,
            borderBottom: '1px solid var(--border)',
          }}
        >
          <h3
            style={{
              margin: 0,
              fontSize: 14,
              fontWeight: 600,
              color: 'var(--text)',
            }}
          >
            <Sparkles size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />
            生成工作台
          </h3>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: 8 }}>
          {tree.products.map((p) => (
            <div key={p.id}>
              <button
                type="button"
                onClick={() => tree.toggleProduct(p.id)}
                className="card-hover"
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  borderRadius: 6,
                  fontSize: 13,
                  color: 'var(--text)',
                  background: 'none',
                  border: 'none',
                  width: '100%',
                  textAlign: 'left',
                }}
              >
                {tree.expandedProducts.has(p.id) ? (
                  <ChevronDown size={14} />
                ) : (
                  <ChevronRight size={14} />
                )}
                <FolderOpen size={14} style={{ color: 'var(--accent)' }} />
                {p.name}
              </button>
              {tree.expandedProducts.has(p.id) &&
                (tree.iterations[p.id] || []).map((it) => (
                  <div key={it.id} style={{ paddingLeft: 20 }}>
                    <button
                      type="button"
                      onClick={() => tree.toggleIteration(p.id, it.id)}
                      className="card-hover"
                      style={{
                        padding: '6px 12px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        borderRadius: 6,
                        fontSize: 12,
                        color: 'var(--text2)',
                        background: 'none',
                        border: 'none',
                        width: '100%',
                        textAlign: 'left',
                      }}
                    >
                      {tree.expandedIterations.has(it.id) ? (
                        <ChevronDown size={12} />
                      ) : (
                        <ChevronRight size={12} />
                      )}
                      <IterationCw size={12} />
                      {it.name}
                    </button>
                    {tree.expandedIterations.has(it.id) &&
                      (tree.requirements[it.id] || []).map((r) => (
                        <button
                          type="button"
                          key={r.id}
                          onClick={() => selectRequirement(r)}
                          className="card-hover"
                          style={{
                            padding: '6px 12px',
                            marginLeft: 20,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                            borderRadius: 6,
                            fontSize: 12,
                            background: tree.selectedReqId === r.id ? 'var(--accent-d)' : undefined,
                            color: tree.selectedReqId === r.id ? 'var(--accent)' : 'var(--text2)',
                            border: 'none',
                            width: '100%',
                            textAlign: 'left',
                          }}
                        >
                          <FileText size={12} />
                          {r.title || r.req_id}
                        </button>
                      ))}
                  </div>
                ))}
            </div>
          ))}
        </div>
        {/* Sessions */}
        {tree.selectedReqId && (
          <div
            style={{
              borderTop: '1px solid var(--border)',
              maxHeight: '35%',
              overflow: 'auto',
              padding: 8,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '4px 8px',
              }}
            >
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: 'var(--text2)',
                }}
              >
                会话列表
              </span>
              <button
                type="button"
                className="btn"
                style={{ padding: '2px 8px', fontSize: 11 }}
                onClick={createSession}
              >
                <Plus size={12} /> 新建
              </button>
            </div>
            {sessions.map((s) => (
              <button
                type="button"
                key={s.id}
                onClick={() => selectSession(s.id)}
                className="card-hover"
                style={{
                  padding: '8px 10px',
                  marginBottom: 2,
                  borderRadius: 6,
                  cursor: 'pointer',
                  fontSize: 12,
                  background: activeSessionId === s.id ? 'var(--accent-d)' : undefined,
                  color: activeSessionId === s.id ? 'var(--accent)' : 'var(--text2)',
                  border: 'none',
                  width: '100%',
                  textAlign: 'left',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <MessageSquare size={12} style={{ marginRight: 4 }} />
                {MODES.find((m) => m.value === s.mode)?.label || s.mode}
                <span
                  style={{
                    fontSize: 10,
                    marginLeft: 6,
                    opacity: 0.6,
                  }}
                >
                  {s.created_at?.slice(5, 16)}
                </span>
              </button>
            ))}
            {sessions.length === 0 && (
              <div
                style={{
                  padding: 8,
                  fontSize: 11,
                  color: 'var(--text3)',
                  textAlign: 'center',
                }}
              >
                无会话，点击新建
              </div>
            )}
          </div>
        )}
      </aside>

      {/* Center: Chat */}
      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {activeSessionId ? (
          <>
            <div
              style={{
                padding: '12px 16px',
                borderBottom: '1px solid var(--border)',
                display: 'flex',
                gap: 6,
              }}
            >
              {MODES.map((m) => (
                <button
                  type="button"
                  key={m.value}
                  className={`pill ${selectedMode === m.value ? 'pill-green' : ''}`}
                  onClick={() => setSelectedMode(m.value)}
                  style={{
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                    fontSize: 12,
                  }}
                >
                  <m.icon size={12} />
                  {m.label}
                </button>
              ))}
            </div>
            <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
              {messages.length === 0 && !sse.isStreaming && (
                <div
                  style={{
                    textAlign: 'center',
                    padding: 40,
                    color: 'var(--text3)',
                  }}
                >
                  <TestTube size={48} style={{ opacity: 0.3, marginBottom: 16 }} />
                  <p style={{ fontSize: 14 }}>开始对话，生成测试用例</p>
                  <p style={{ fontSize: 12 }}>试试：&quot;请根据测试点生成详细测试用例&quot;</p>
                </div>
              )}
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className="chat-msg"
                  style={{
                    display: 'flex',
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    marginBottom: 12,
                  }}
                >
                  <div
                    className={`chat-bubble ${msg.role === 'assistant' ? 'ai-bubble' : ''}`}
                    style={{
                      maxWidth: '75%',
                      padding: '10px 14px',
                      background: msg.role === 'user' ? 'var(--accent)' : 'var(--bg2)',
                      color: msg.role === 'user' ? '#fff' : 'var(--text)',
                      borderRadius:
                        msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                      fontSize: 13,
                      lineHeight: 1.6,
                    }}
                  >
                    {msg.role === 'assistant' ? (
                      // biome-ignore lint/security/noDangerouslySetInnerHtml: renderMarkdown sanitizes AI content
                      <div dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />
                    ) : (
                      <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
                    )}
                  </div>
                </div>
              ))}
              {sse.isStreaming && sse.content && (
                <div
                  className="chat-msg"
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-start',
                    marginBottom: 12,
                  }}
                >
                  <div
                    className="chat-bubble ai-bubble"
                    style={{
                      maxWidth: '75%',
                      padding: '10px 14px',
                      background: 'var(--bg2)',
                      borderRadius: '12px 12px 12px 2px',
                      fontSize: 13,
                      lineHeight: 1.6,
                    }}
                  >
                    {/* biome-ignore lint/security/noDangerouslySetInnerHtml: renderMarkdown sanitizes AI content */}
                    <div dangerouslySetInnerHTML={{ __html: renderMarkdown(sse.content) }} />
                    <span className="streaming-cursor">▊</span>
                  </div>
                </div>
              )}
              {sse.isStreaming && !sse.content && (
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-start',
                    marginBottom: 12,
                  }}
                >
                  <div
                    className="card"
                    style={{
                      padding: '10px 14px',
                      background: 'var(--bg2)',
                      borderRadius: '12px 12px 12px 2px',
                    }}
                  >
                    <Loader2
                      size={16}
                      style={{
                        animation: 'spin 1s linear infinite',
                      }}
                    />
                    <span
                      style={{
                        marginLeft: 8,
                        fontSize: 13,
                        color: 'var(--text3)',
                      }}
                    >
                      AI 生成中...
                    </span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            <div
              style={{
                padding: '12px 16px',
                borderTop: '1px solid var(--border)',
                display: 'flex',
                gap: 8,
              }}
            >
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="输入指令生成测试用例..."
                style={{
                  flex: 1,
                  resize: 'none',
                  height: 40,
                  padding: '8px 12px',
                  borderRadius: 8,
                  border: '1px solid var(--border)',
                  background: 'var(--bg2)',
                  color: 'var(--text)',
                  fontSize: 13,
                  outline: 'none',
                }}
              />
              <button
                type="button"
                className="btn btn-primary"
                onClick={sendMessage}
                disabled={sse.isStreaming || !inputText.trim()}
                style={{ padding: '8px 16px' }}
              >
                <Send size={16} />
              </button>
            </div>
          </>
        ) : (
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                textAlign: 'center',
                color: 'var(--text3)',
              }}
            >
              <Sparkles size={64} style={{ opacity: 0.2, marginBottom: 16 }} />
              <p style={{ fontSize: 16 }}>
                {tree.selectedReqId ? '选择或新建会话' : '请从左侧选择需求'}
              </p>
              <p style={{ fontSize: 13 }}>对话式 AI 测试用例生成</p>
            </div>
          </div>
        )}
      </main>

      {/* Right: Test Cases */}
      <aside
        style={{
          width: 300,
          minWidth: 300,
          borderLeft: '1px solid var(--border)',
          background: 'var(--bg1)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div
          style={{
            padding: 16,
            borderBottom: '1px solid var(--border)',
          }}
        >
          <h4
            style={{
              margin: 0,
              fontSize: 14,
              color: 'var(--text)',
            }}
          >
            <ClipboardList size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />
            已生成用例 ({testCases.length})
          </h4>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: 8 }}>
          {testCases.length > 0 ? (
            testCases.map((tc) => (
              <div
                key={tc.id}
                className="card card-hover"
                style={{ padding: '10px 12px', marginBottom: 4 }}
              >
                <div
                  style={{
                    fontSize: 11,
                    color: 'var(--accent)',
                    fontFamily: 'var(--font-mono)',
                    marginBottom: 2,
                  }}
                >
                  {tc.case_id}
                </div>
                <div
                  style={{
                    fontSize: 13,
                    color: 'var(--text)',
                    marginBottom: 4,
                  }}
                >
                  {tc.title}
                </div>
                <div style={{ display: 'flex', gap: 4 }}>
                  <span
                    className={`pill ${tc.priority === 'P0' ? 'pill-red' : tc.priority === 'P1' ? 'pill-amber' : 'pill-green'}`}
                    style={{ fontSize: 10 }}
                  >
                    {tc.priority}
                  </span>
                  <span className="pill" style={{ fontSize: 10 }}>
                    {tc.source === 'ai' ? 'AI' : '手动'}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div
              style={{
                textAlign: 'center',
                padding: 24,
                color: 'var(--text3)',
                fontSize: 12,
              }}
            >
              {tree.selectedReqId ? '暂无测试用例' : '选择需求查看用例'}
            </div>
          )}
        </div>
        {testCases.length > 0 && (
          <div
            style={{
              padding: 12,
              borderTop: '1px solid var(--border)',
              display: 'flex',
              justifyContent: 'space-around',
              textAlign: 'center',
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 16,
                  fontWeight: 700,
                  color: 'var(--accent)',
                }}
              >
                {testCases.length}
              </div>
              <div
                style={{
                  fontSize: 10,
                  color: 'var(--text3)',
                }}
              >
                总计
              </div>
            </div>
            <div>
              <div
                style={{
                  fontSize: 16,
                  fontWeight: 700,
                  color: '#00d9a3',
                }}
              >
                {testCases.filter((t) => t.source === 'ai').length}
              </div>
              <div
                style={{
                  fontSize: 10,
                  color: 'var(--text3)',
                }}
              >
                AI生成
              </div>
            </div>
            <div>
              <div
                style={{
                  fontSize: 16,
                  fontWeight: 700,
                  color: '#f59e0b',
                }}
              >
                {testCases.filter((t) => t.source !== 'ai').length}
              </div>
              <div
                style={{
                  fontSize: 10,
                  color: 'var(--text3)',
                }}
              >
                手动
              </div>
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
