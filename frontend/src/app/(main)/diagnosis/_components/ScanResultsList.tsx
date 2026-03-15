'use client';

import {
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Info,
  ShieldAlert,
} from 'lucide-react';
import { useState } from 'react';
import type { DiagnosisReport, DiagnosisRisk } from '@/lib/api';

interface ScanResultsListProps {
  report: DiagnosisReport | null;
  loading?: boolean;
}

const severityConfig: Record<
  string,
  {
    label: string;
    icon: typeof ShieldAlert;
    textClass: string;
    bgClass: string;
    borderClass: string;
  }
> = {
  high: {
    label: '高风险',
    icon: ShieldAlert,
    textClass: 'text-red',
    bgClass: 'bg-red/8',
    borderClass: 'border-red/30',
  },
  medium: {
    label: '中风险',
    icon: AlertTriangle,
    textClass: 'text-amber',
    bgClass: 'bg-amber/8',
    borderClass: 'border-amber/30',
  },
  low: {
    label: '低风险',
    icon: Info,
    textClass: 'text-blue',
    bgClass: 'bg-blue/8',
    borderClass: 'border-blue/30',
  },
};

function RiskItem({ risk }: { risk: DiagnosisRisk }) {
  const [expanded, setExpanded] = useState(false);
  // backend returns 'level'; frontend legacy used 'severity' — support both
  const effectiveLevel = risk.level ?? risk.severity;
  const config = severityConfig[effectiveLevel] ?? severityConfig.low;
  const Icon = config.icon;

  return (
    <div className={`rounded-lg border ${config.bgClass} ${config.borderClass}`}>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-start gap-2.5 px-3 py-2.5 text-left"
      >
        <Icon className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${config.textClass}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span
              className={`text-[11px] font-semibold px-1.5 py-0.5 rounded-full font-mono ${config.bgClass} ${config.textClass} border ${config.borderClass}`}
            >
              {config.label}
            </span>
            {risk.category && (
              <span className="text-[11px] text-text3 font-mono">{risk.category}</span>
            )}
          </div>
          <p className="text-[12.5px] text-text mt-1 leading-relaxed line-clamp-2">
            {risk.title ?? risk.description}
          </p>
        </div>
        {(risk.suggestion || risk.description) &&
          (expanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-text3 flex-shrink-0 mt-0.5" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-text3 flex-shrink-0 mt-0.5" />
          ))}
      </button>
      {expanded && (
        <div className="px-3 pb-3 border-t border-border/50 pt-2.5 space-y-2">
          {risk.title && risk.description !== risk.title && (
            <p className="text-[12px] text-text2 leading-relaxed">{risk.description}</p>
          )}
          {risk.suggestion && (
            <div className="flex items-start gap-2">
              <CheckCircle className="w-3 h-3 text-accent flex-shrink-0 mt-0.5" />
              <p className="text-[11.5px] text-text3 leading-relaxed">
                <span className="font-medium text-text2">建议：</span>
                {risk.suggestion}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ScanResultsList({ report, loading }: ScanResultsListProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-6">
        <span className="text-[12px] text-text3">加载中...</span>
      </div>
    );
  }

  const risks = report?.risks ?? [];
  const getLevel = (r: DiagnosisRisk) => r.level ?? r.severity;
  const highRisks = risks.filter((r) => getLevel(r) === 'high');
  const mediumRisks = risks.filter((r) => getLevel(r) === 'medium');
  const lowRisks = risks.filter((r) => getLevel(r) === 'low');

  if (risks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-6 text-center">
        <Info className="w-8 h-8 text-text3 opacity-30 mb-2" />
        <p className="text-[12px] text-text3">暂无广度扫描结果</p>
        <p className="text-[11px] text-text3 opacity-60 mt-0.5">点击「开始分析」运行 AI 广度扫描</p>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {/* Summary bar */}
      <div className="flex items-center gap-3 px-0.5 mb-2">
        <span className="text-[11px] text-text3">扫描结果</span>
        {highRisks.length > 0 && (
          <span className="flex items-center gap-1 text-[11px] text-red font-mono">
            <ShieldAlert className="w-3 h-3" />
            {highRisks.length} 高
          </span>
        )}
        {mediumRisks.length > 0 && (
          <span className="flex items-center gap-1 text-[11px] text-amber font-mono">
            <AlertTriangle className="w-3 h-3" />
            {mediumRisks.length} 中
          </span>
        )}
        {lowRisks.length > 0 && (
          <span className="flex items-center gap-1 text-[11px] text-blue font-mono">
            <Info className="w-3 h-3" />
            {lowRisks.length} 低
          </span>
        )}
        {report?.overall_score != null && (
          <span
            className={`ml-auto font-mono text-[12px] font-semibold ${
              report.overall_score >= 70
                ? 'text-accent'
                : report.overall_score >= 50
                  ? 'text-amber'
                  : 'text-red'
            }`}
          >
            健康分 {report.overall_score}
          </span>
        )}
      </div>
      {[...highRisks, ...mediumRisks, ...lowRisks].map((risk) => (
        <RiskItem key={risk.id} risk={risk} />
      ))}
    </div>
  );
}
