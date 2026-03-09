'use client';

import {
  Activity,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Database,
  FileText,
  FolderOpen,
  Globe,
  IterationCw,
  Loader2,
  Lock,
  Send,
  Shield,
  Zap,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useRequirementTree } from '@/hooks/useRequirementTree';
import { useSSE } from '@/hooks/useSSE';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

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

interface DiagnosisReport {
  id: string;
  requirement_id: string;
  status: string;
  overall_score: number | null;
  summary: string | null;
  risk_count_high: number;
  risk_count_medium: number;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  thinking_content?: string;
  created_at: string;
}

export default function DiagnosisPage() {
  const tree = useRequirementTree();
  const sse = useSSE();

  const [report, setReport] = useState<DiagnosisReport | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Load diagnosis report + persisted messages when selecting a requirement
  useEffect(() => {
    if (!tree.selectedReqId) return;
    const reqId = tree.selectedReqId;
    setMessages([]);
    setReport(null);

    (async () => {
      try {
        const reportRes = await fetch(`${API}/diagnosis/${reqId}/create`, { method: 'POST' });
        if (reportRes.ok) setReport(await reportRes.json());

        const msgRes = await fetch(`${API}/diagnosis/${reqId}/messages`);
        if (msgRes.ok) {
          const msgData = await msgRes.json();
          setMessages(Array.isArray(msgData) ? msgData : []);
        }
      } catch (e) {
        console.error('Failed to load diagnosis:', e);
      }
    })();
  }, [tree.selectedReqId]);

  const sendMessage = useCallback(async () => {
    if (!inputText.trim() || !tree.selectedReqId || sse.isStreaming) return;

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

    await sse.startStream(`/diagnosis/${tree.selectedReqId}/chat`, {
      method: 'POST',
      body: { message: userMsg },
      onDone: (fullText) => {
        setMessages((prev) => [
          ...prev,
          {
            id: `ai-${Date.now()}`,
            role: 'assistant',
            content: fullText || '诊断完成',
            created_at: new Date().toISOString(),
          },
        ]);
      },
      onError: (err) => {
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: 'assistant',
            content: `错误: ${err.message}`,
            created_at: new Date().toISOString(),
          },
        ]);
      },
    });
  }, [inputText, tree.selectedReqId, sse]);

  // Auto-scroll on new messages or streaming updates
  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll must trigger on content changes
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sse.content]);

  const completeDiagnosis = async () => {
    if (!tree.selectedReqId) return;
    try {
      const res = await fetch(`${API}/diagnosis/${tree.selectedReqId}/complete`, {
        method: 'POST',
      });
      if (res.ok) setReport(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const scoreColor = (score: number | null) => {
    if (!score) return 'var(--text-secondary, var(--text3))';
    if (score >= 80) return '#00d9a3';
    if (score >= 60) return '#f59e0b';
    return '#ef4444';
  };

  const diagnosisDimensions = [
    { icon: Shield, label: '功能边界', desc: '功能边界遗漏检测' },
    { icon: AlertTriangle, label: '异常场景', desc: '异常场景缺失扫描' },
    { icon: Database, label: '数据约束', desc: '数据约束模糊识别' },
    { icon: Zap, label: '性能指标', desc: '性能指标缺失检查' },
    { icon: Globe, label: '兼容性', desc: '兼容性未提及发现' },
    { icon: Lock, label: '安全风险', desc: '安全风险忽略扫描' },
  ];

  return (
    <div className="diag-col" style={{ height: 'calc(100vh - 64px)' }}>
      {/* Left Sidebar - Requirement Tree */}
      <aside className="col-left" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="col-header">
          <Activity size={14} />
          需求健康诊断
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '8px' }}>
          {tree.products.map((product) => (
            <div key={product.id}>
              <button
                type="button"
                onClick={() => tree.toggleProduct(product.id)}
                className="card-hover"
                style={{
                  all: 'unset',
                  boxSizing: 'border-box',
                  width: '100%',
                  padding: '8px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  borderRadius: 6,
                  fontSize: 13,
                  color: 'var(--text)',
                }}
              >
                {tree.expandedProducts.has(product.id) ? (
                  <ChevronDown size={14} />
                ) : (
                  <ChevronRight size={14} />
                )}
                <FolderOpen size={14} style={{ color: 'var(--accent)' }} />
                {product.name}
              </button>
              {tree.expandedProducts.has(product.id) &&
                (tree.iterations[product.id] || []).map((iter) => (
                  <div key={iter.id} style={{ paddingLeft: 20 }}>
                    <button
                      type="button"
                      onClick={() => tree.toggleIteration(product.id, iter.id)}
                      className="card-hover"
                      style={{
                        all: 'unset',
                        boxSizing: 'border-box',
                        width: '100%',
                        padding: '6px 12px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        borderRadius: 6,
                        fontSize: 12,
                        color: 'var(--text3, var(--text-secondary))',
                      }}
                    >
                      {tree.expandedIterations.has(iter.id) ? (
                        <ChevronDown size={12} />
                      ) : (
                        <ChevronRight size={12} />
                      )}
                      <IterationCw size={12} />
                      {iter.name}
                    </button>
                    {tree.expandedIterations.has(iter.id) &&
                      (tree.requirements[iter.id] || []).map((req) => (
                        <button
                          type="button"
                          key={req.id}
                          onClick={() => tree.selectRequirement(req)}
                          className="card-hover"
                          style={{
                            all: 'unset',
                            boxSizing: 'border-box',
                            width: '100%',
                            padding: '6px 12px',
                            marginLeft: 20,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                            borderRadius: 6,
                            fontSize: 12,
                            background:
                              tree.selectedReqId === req.id
                                ? 'var(--accent-d, rgba(0,217,163,0.1))'
                                : undefined,
                            color:
                              tree.selectedReqId === req.id
                                ? 'var(--accent)'
                                : 'var(--text3, var(--text-secondary))',
                          }}
                        >
                          <FileText size={12} />
                          {req.title || req.req_id}
                        </button>
                      ))}
                  </div>
                ))}
            </div>
          ))}
          {tree.products.length === 0 && (
            <div
              style={{
                padding: 16,
                textAlign: 'center',
                color: 'var(--text3, var(--text-secondary))',
                fontSize: 13,
              }}
            >
              暂无产品数据
            </div>
          )}
        </div>

        {/* Report Summary */}
        {report && (
          <div style={{ padding: 16, borderTop: '1px solid var(--border)' }}>
            <div style={{ textAlign: 'center', marginBottom: 12 }}>
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  border: `3px solid ${scoreColor(report.overall_score)}`,
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 20,
                  fontWeight: 700,
                  color: scoreColor(report.overall_score),
                }}
              >
                {report.overall_score ?? '—'}
              </div>
              <div
                style={{
                  fontSize: 11,
                  color: 'var(--text3, var(--text-secondary))',
                  marginTop: 4,
                }}
              >
                健康评分
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-around', fontSize: 12 }}>
              <span className="pill pill-red">高风险 {report.risk_count_high}</span>
              <span className="pill pill-amber">中风险 {report.risk_count_medium}</span>
            </div>
          </div>
        )}
      </aside>

      {/* Center - Diagnosis Content */}
      <main className="col-mid" style={{ display: 'flex', flexDirection: 'column' }}>
        {tree.selectedReqId ? (
          <>
            {/* Diagnosis Dimensions */}
            <div style={{ padding: '16px', borderBottom: '1px solid var(--border)' }}>
              <h4 style={{ margin: '0 0 12px', fontSize: 14, color: 'var(--text)' }}>
                诊断维度 — {tree.selectedReqTitle}
              </h4>
              <div className="grid-3" style={{ gap: 8 }}>
                {diagnosisDimensions.map((dim) => (
                  <div
                    key={dim.label}
                    className="card"
                    style={{ padding: '10px 12px', display: 'flex', alignItems: 'center', gap: 8 }}
                  >
                    <dim.icon size={16} style={{ color: 'var(--accent)' }} />
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>
                        {dim.label}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text3, var(--text-secondary))' }}>
                        {dim.desc}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Chat Area */}
            <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
              {messages.length === 0 && !sse.isStreaming && (
                <div
                  style={{
                    textAlign: 'center',
                    padding: 40,
                    color: 'var(--text3, var(--text-secondary))',
                  }}
                >
                  <Activity size={48} style={{ opacity: 0.3, marginBottom: 16 }} />
                  <p style={{ fontSize: 14 }}>选择需求后，开始 AI 健康诊断对话</p>
                  <p style={{ fontSize: 12 }}>
                    试试输入：&quot;请对这个需求进行全面的健康诊断&quot;
                  </p>
                </div>
              )}
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className="chat-msg"
                  style={{
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  {msg.role === 'assistant' && <div className="chat-avatar chat-ai">AI</div>}
                  {msg.role === 'user' ? (
                    <div className="chat-bubble">{msg.content}</div>
                  ) : (
                    <div
                      className="chat-bubble ai-bubble markdown-body"
                      // biome-ignore lint/security/noDangerouslySetInnerHtml: renderMarkdown sanitizes AI content
                      dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                    />
                  )}
                  {msg.role === 'user' && <div className="chat-avatar chat-user">U</div>}
                </div>
              ))}
              {sse.isStreaming && sse.content && (
                <div className="chat-msg">
                  <div className="chat-avatar chat-ai">AI</div>
                  <div
                    className="chat-bubble ai-bubble markdown-body"
                    // biome-ignore lint/security/noDangerouslySetInnerHtml: renderMarkdown sanitizes AI content
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(sse.content) }}
                  />
                </div>
              )}
              {sse.isStreaming && !sse.content && (
                <div className="chat-msg">
                  <div className="chat-avatar chat-ai">AI</div>
                  <div className="chat-bubble ai-bubble">
                    <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                    <span
                      style={{
                        marginLeft: 8,
                        fontSize: 13,
                        color: 'var(--text3, var(--text-secondary))',
                      }}
                    >
                      AI 正在分析...
                    </span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input Area */}
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
                placeholder="输入诊断问题，如：请对这个需求进行健康诊断..."
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
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center', color: 'var(--text3, var(--text-secondary))' }}>
              <Activity size={64} style={{ opacity: 0.2, marginBottom: 16 }} />
              <p style={{ fontSize: 16 }}>请从左侧选择一个需求</p>
              <p style={{ fontSize: 13 }}>开始 AI 驱动的需求健康诊断</p>
            </div>
          </div>
        )}
      </main>

      {/* Right Panel */}
      <aside
        className="col-right"
        style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 16 }}
      >
        <div className="col-header" style={{ padding: 0, border: 'none', position: 'static' }}>
          快速操作
        </div>
        {tree.selectedReqId ? (
          <>
            <button
              type="button"
              className="btn btn-primary"
              style={{ width: '100%' }}
              onClick={completeDiagnosis}
            >
              <CheckCircle size={16} style={{ marginRight: 8 }} />
              完成诊断
            </button>
            <div className="card" style={{ padding: 12 }}>
              <div
                style={{
                  fontSize: 12,
                  color: 'var(--text3, var(--text-secondary))',
                  marginBottom: 8,
                }}
              >
                诊断状态
              </div>
              <span
                className={`pill ${report?.status === 'completed' ? 'pill-green' : 'pill-amber'}`}
              >
                {report?.status === 'completed' ? '已完成' : '进行中'}
              </span>
            </div>
            {report?.summary && (
              <div className="card" style={{ padding: 12 }}>
                <div
                  style={{
                    fontSize: 12,
                    color: 'var(--text3, var(--text-secondary))',
                    marginBottom: 8,
                  }}
                >
                  诊断摘要
                </div>
                <p
                  style={{
                    fontSize: 12,
                    color: 'var(--text)',
                    lineHeight: 1.5,
                    margin: 0,
                  }}
                >
                  {report.summary}
                </p>
              </div>
            )}
          </>
        ) : (
          <div style={{ fontSize: 13, color: 'var(--text3, var(--text-secondary))' }}>
            选择需求后显示操作面板
          </div>
        )}
      </aside>
    </div>
  );
}
