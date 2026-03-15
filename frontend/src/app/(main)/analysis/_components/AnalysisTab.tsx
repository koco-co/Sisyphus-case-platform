'use client';

import {
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Info,
  Loader2,
  Play,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCallback, useRef, useState } from 'react';
import { useDiagnosis } from '@/hooks/useDiagnosis';
import { API_BASE } from '@/lib/api';
import { ChatInput } from '../../diagnosis/_components/ChatInput';
import { DiagnosisChat } from '../../diagnosis/_components/DiagnosisChat';

interface AnalysisTabProps {
  requirementId: string | null;
  visible: boolean;
}

const levelConfig: Record<
  string,
  {
    label: string;
    icon: typeof ShieldAlert;
    textClass: string;
    bgClass: string;
    borderLeftClass: string;
  }
> = {
  high: {
    label: '高风险',
    icon: ShieldAlert,
    textClass: 'text-sy-danger',
    bgClass: 'bg-sy-danger/8',
    borderLeftClass: 'border-l-4 border-sy-danger',
  },
  medium: {
    label: '中风险',
    icon: AlertTriangle,
    textClass: 'text-sy-warn',
    bgClass: 'bg-sy-warn/8',
    borderLeftClass: 'border-l-4 border-sy-warn',
  },
  low: {
    label: '低风险',
    icon: Info,
    textClass: 'text-sy-info',
    bgClass: 'bg-sy-info/8',
    borderLeftClass: 'border-l-4 border-sy-info',
  },
};

interface RiskCardProps {
  risk: {
    id: string;
    level?: string;
    severity?: string;
    description: string;
    title?: string;
    suggestion?: string;
    category?: string;
    confirmed?: boolean;
  };
  onConfirm: (id: string) => void;
  confirming: boolean;
}

function RiskCard({ risk, onConfirm, confirming }: RiskCardProps) {
  const [expanded, setExpanded] = useState(false);
  const level = risk.level ?? risk.severity ?? 'low';
  const config = levelConfig[level] ?? levelConfig.low;
  const Icon = config.icon;

  return (
    <div
      className={`rounded-lg border border-sy-border ${config.bgClass} ${config.borderLeftClass} transition-all hover:-translate-y-px hover:border-sy-border-2`}
    >
      <div className="flex items-start gap-2.5 px-3 py-2.5">
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="flex-1 flex items-start gap-2.5 text-left min-w-0"
        >
          <Icon className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${config.textClass}`} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span
                className={`text-[11px] font-semibold px-1.5 py-0.5 rounded-full font-mono ${config.bgClass} ${config.textClass} border border-sy-border`}
              >
                {config.label}
              </span>
              {risk.category && (
                <span className="text-[11px] text-sy-text-3 font-mono">{risk.category}</span>
              )}
            </div>
            <p className="text-[12.5px] text-sy-text mt-1 leading-relaxed line-clamp-2">
              {risk.title ?? risk.description}
            </p>
          </div>
          {(risk.suggestion || risk.description) &&
            (expanded ? (
              <ChevronDown className="w-3.5 h-3.5 text-sy-text-3 flex-shrink-0 mt-0.5" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 text-sy-text-3 flex-shrink-0 mt-0.5" />
            ))}
        </button>

        {/* Confirm button */}
        {risk.confirmed ? (
          <span className="flex-shrink-0 inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-sy-bg-3 border border-sy-border text-sy-text-3 cursor-default">
            <CheckCircle className="w-3 h-3" />
            已确认
          </span>
        ) : (
          <button
            type="button"
            onClick={() => onConfirm(risk.id)}
            disabled={confirming}
            className="flex-shrink-0 inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-sy-accent/10 border border-sy-accent/30 text-sy-accent hover:bg-sy-accent/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {confirming ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <CheckCircle className="w-3 h-3" />
            )}
            确认知晓
          </button>
        )}
      </div>

      {expanded && (
        <div className="px-3 pb-3 border-t border-sy-border/50 pt-2.5 space-y-2">
          {risk.title && risk.description !== risk.title && (
            <p className="text-[12px] text-sy-text-2 leading-relaxed">{risk.description}</p>
          )}
          {risk.suggestion && (
            <div className="flex items-start gap-2">
              <CheckCircle className="w-3 h-3 text-sy-accent flex-shrink-0 mt-0.5" />
              <p className="text-[11.5px] text-sy-text-3 leading-relaxed">
                <span className="font-medium text-sy-text-2">建议：</span>
                {risk.suggestion}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function AnalysisTab({ requirementId, visible }: AnalysisTabProps) {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const [splitRatio, setSplitRatio] = useState(0.5);
  const [confirmingIds, setConfirmingIds] = useState<Set<string>>(new Set());

  const { report, messages, sse, loading, sendMessage, startDiagnosis } = useDiagnosis(
    visible && requirementId ? requirementId : null,
  );

  // Local optimistic confirmed state (augments server state)
  const [localConfirmed, setLocalConfirmed] = useState<Set<string>>(new Set());

  const risks = report?.risks ?? [];

  const hasUnhandledHighRisk = risks.some((r) => {
    const level =
      (r as { level?: string; severity?: string }).level ??
      (r as { level?: string; severity?: string }).severity;
    const confirmed = (r as { confirmed?: boolean }).confirmed || localConfirmed.has(r.id);
    return level === 'high' && !confirmed;
  });

  const unhandledCount = risks.filter((r) => {
    const level =
      (r as { level?: string; severity?: string }).level ??
      (r as { level?: string; severity?: string }).severity;
    const confirmed = (r as { confirmed?: boolean }).confirmed || localConfirmed.has(r.id);
    return level === 'high' && !confirmed;
  }).length;

  const hasScanResults = risks.length > 0;
  const canStartScan = !sse.isStreaming && !hasScanResults;

  // Drag handler for split line
  const handleSplitDrag = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      const container = containerRef.current;
      if (!container) return;
      const startY = e.clientY;
      const startRatio = splitRatio;
      const onMove = (moveEvent: MouseEvent) => {
        const delta = moveEvent.clientY - startY;
        const containerHeight = container.getBoundingClientRect().height;
        setSplitRatio(Math.min(0.7, Math.max(0.3, startRatio + delta / containerHeight)));
      };
      const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      };
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    },
    [splitRatio],
  );

  // Confirm risk handler
  const handleConfirmRisk = useCallback(
    async (riskId: string) => {
      if (confirmingIds.has(riskId)) return;
      setConfirmingIds((prev) => new Set(prev).add(riskId));
      try {
        const res = await fetch(`${API_BASE}/diagnosis/risks/${riskId}/confirm`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
        });
        if (res.ok) {
          setLocalConfirmed((prev) => new Set(prev).add(riskId));
        }
      } catch {
        // silently ignore — user can retry
      } finally {
        setConfirmingIds((prev) => {
          const next = new Set(prev);
          next.delete(riskId);
          return next;
        });
      }
    },
    [confirmingIds],
  );

  if (!visible || !requirementId) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-[12px] text-sy-text-3">从左侧选择需求查看 AI 分析</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="flex flex-col h-full overflow-hidden">
      {/* ─── Upper: Scan Results ─── */}
      <div
        className="flex flex-col overflow-hidden flex-shrink-0"
        style={{ height: `${splitRatio * 100}%` }}
      >
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-sy-border bg-sy-bg-1 flex-shrink-0">
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-sy-accent" />
            <span className="text-[12px] font-semibold text-sy-text-2">广度扫描结果</span>
          </div>
          <div className="flex items-center gap-2">
            {canStartScan && (
              <button
                type="button"
                onClick={startDiagnosis}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-sy-accent text-white text-[11.5px] font-semibold hover:bg-sy-accent-2 transition-colors"
              >
                <Play className="w-3 h-3" />
                开始分析
              </button>
            )}
            {sse.isStreaming && (
              <span className="flex items-center gap-1.5 text-[11px] text-sy-warn">
                <Loader2 className="w-3 h-3 animate-spin" />
                分析进行中...
              </span>
            )}
            {/* Enter workbench button */}
            <div className="relative group">
              <button
                type="button"
                disabled={hasUnhandledHighRisk}
                onClick={() => {
                  if (!hasUnhandledHighRisk) {
                    router.push(`/workbench?reqId=${requirementId}`);
                  }
                }}
                title={
                  hasUnhandledHighRisk
                    ? `存在 ${unhandledCount} 个高风险遗漏项未确认，请先在 AI 分析 Tab 中处理`
                    : '进入工作台生成测试用例'
                }
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11.5px] font-semibold transition-colors border ${
                  hasUnhandledHighRisk
                    ? 'opacity-50 cursor-not-allowed bg-sy-bg-3 border-sy-border text-sy-text-3'
                    : 'bg-sy-accent/10 border-sy-accent/30 text-sy-accent hover:bg-sy-accent/20'
                }`}
              >
                <ArrowRight className="w-3 h-3" />
                进入工作台
              </button>
              {hasUnhandledHighRisk && (
                <div className="absolute right-0 top-full mt-1 w-56 px-2.5 py-1.5 rounded-md bg-sy-bg-1 border border-sy-border text-[11px] text-sy-text-2 leading-relaxed z-10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-lg">
                  存在 {unhandledCount} 个高风险遗漏项未确认，请先在 AI 分析 Tab 中处理
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-3">
          {loading && (
            <div className="flex items-center justify-center py-6">
              <span className="text-[12px] text-sy-text-3">加载中...</span>
            </div>
          )}
          {!loading && risks.length === 0 && (
            <div className="flex flex-col items-center justify-center py-6 text-center">
              <Info className="w-8 h-8 text-sy-text-3 opacity-30 mb-2" />
              <p className="text-[12px] text-sy-text-3">暂无广度扫描结果</p>
              <p className="text-[11px] text-sy-text-3 opacity-60 mt-0.5">
                点击「开始分析」运行 AI 广度扫描
              </p>
            </div>
          )}
          {!loading && risks.length > 0 && (
            <div className="space-y-1.5">
              {/* Summary bar */}
              <div className="flex items-center gap-3 px-0.5 mb-2">
                <span className="text-[11px] text-sy-text-3">扫描结果</span>
                {risks.filter(
                  (r) =>
                    ((r as { level?: string; severity?: string }).level ??
                      (r as { level?: string; severity?: string }).severity) === 'high',
                ).length > 0 && (
                  <span className="flex items-center gap-1 text-[11px] text-sy-danger font-mono">
                    <ShieldAlert className="w-3 h-3" />
                    {
                      risks.filter(
                        (r) =>
                          ((r as { level?: string; severity?: string }).level ??
                            (r as { level?: string; severity?: string }).severity) === 'high',
                      ).length
                    }{' '}
                    高
                  </span>
                )}
                {risks.filter(
                  (r) =>
                    ((r as { level?: string; severity?: string }).level ??
                      (r as { level?: string; severity?: string }).severity) === 'medium',
                ).length > 0 && (
                  <span className="flex items-center gap-1 text-[11px] text-sy-warn font-mono">
                    <AlertTriangle className="w-3 h-3" />
                    {
                      risks.filter(
                        (r) =>
                          ((r as { level?: string; severity?: string }).level ??
                            (r as { level?: string; severity?: string }).severity) === 'medium',
                      ).length
                    }{' '}
                    中
                  </span>
                )}
                {risks.filter(
                  (r) =>
                    ((r as { level?: string; severity?: string }).level ??
                      (r as { level?: string; severity?: string }).severity) === 'low',
                ).length > 0 && (
                  <span className="flex items-center gap-1 text-[11px] text-sy-info font-mono">
                    <Info className="w-3 h-3" />
                    {
                      risks.filter(
                        (r) =>
                          ((r as { level?: string; severity?: string }).level ??
                            (r as { level?: string; severity?: string }).severity) === 'low',
                      ).length
                    }{' '}
                    低
                  </span>
                )}
                {report?.overall_score != null && (
                  <span
                    className={`ml-auto font-mono text-[12px] font-semibold ${
                      report.overall_score >= 70
                        ? 'text-sy-accent'
                        : report.overall_score >= 50
                          ? 'text-sy-warn'
                          : 'text-sy-danger'
                    }`}
                  >
                    分析分 {report.overall_score}
                  </span>
                )}
              </div>
              {risks.map((risk) => (
                <RiskCard
                  key={risk.id}
                  risk={{
                    ...risk,
                    confirmed:
                      (risk as { confirmed?: boolean }).confirmed || localConfirmed.has(risk.id),
                  }}
                  onConfirm={handleConfirmRisk}
                  confirming={confirmingIds.has(risk.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ─── Split Divider ─── */}
      <button
        type="button"
        aria-label="拖拽调整分区高度"
        className="h-1 w-full flex-shrink-0 cursor-row-resize bg-sy-border hover:bg-sy-accent transition-colors relative border-none p-0 outline-none focus-visible:bg-sy-accent"
        onMouseDown={handleSplitDrag}
      />

      {/* ─── Lower: Socratic Dialogue ─── */}
      <div className="flex flex-col overflow-hidden flex-1">
        <div className="flex items-center gap-2 px-4 py-2 border-b border-sy-border bg-sy-bg-1 flex-shrink-0">
          <span className="text-[12px] font-semibold text-sy-text-2">苏格拉底追问</span>
        </div>
        <DiagnosisChat
          messages={messages}
          isStreaming={sse.isStreaming}
          streamContent={sse.content}
          streamThinking={sse.thinking}
          reqTitle=""
          hasRequirement={!!requirementId}
        />
        <ChatInput onSend={sendMessage} isStreaming={sse.isStreaming} disabled={!requirementId} />
      </div>
    </div>
  );
}
