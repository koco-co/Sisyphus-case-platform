'use client';

import { AlertTriangle, Clock, FileText, ShieldAlert, ShieldCheck } from 'lucide-react';
import type { DiagnosisReport } from '@/lib/api';

interface ReportListProps {
  report: DiagnosisReport | null;
  loading?: boolean;
}

function scoreColor(score: number | null): string {
  if (!score) return 'text-text3';
  if (score >= 80) return 'text-accent';
  if (score >= 60) return 'text-amber';
  return 'text-red';
}

function scoreBorderColor(score: number | null): string {
  if (!score) return 'border-border2';
  if (score >= 80) return 'border-accent';
  if (score >= 60) return 'border-amber';
  return 'border-red';
}

export function ReportList({ report, loading }: ReportListProps) {
  if (loading) {
    return (
      <div className="px-3 py-6 text-center">
        <div className="text-text3 text-[12px]">加载中...</div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="px-3 py-6 text-center">
        <FileText className="w-8 h-8 text-text3 opacity-40 mx-auto mb-2" />
        <div className="text-text3 text-[12px]">选择需求后开始分析</div>
      </div>
    );
  }

  const riskItems = [
    {
      level: '高风险',
      count: report.risk_count_high,
      color: 'text-red',
      bgColor: 'bg-red/10',
      borderColor: 'border-red/25',
      icon: ShieldAlert,
    },
    {
      level: '中风险',
      count: report.risk_count_medium,
      color: 'text-amber',
      bgColor: 'bg-amber/10',
      borderColor: 'border-amber/25',
      icon: AlertTriangle,
    },
    {
      level: '低风险',
      count: 0,
      color: 'text-blue',
      bgColor: 'bg-blue/10',
      borderColor: 'border-blue/25',
      icon: ShieldCheck,
    },
  ];

  return (
    <div className="px-3 py-3">
      {/* Score Circle */}
      <div className="text-center mb-4">
        <div
          className={`w-16 h-16 rounded-full border-[3px] ${scoreBorderColor(report.overall_score ?? null)} inline-flex items-center justify-center`}
        >
          <span
            className={`font-mono text-[20px] font-bold ${scoreColor(report.overall_score ?? null)}`}
          >
            {report.overall_score ?? '—'}
          </span>
        </div>
        <div className="text-[11px] text-text3 mt-1.5">健康评分</div>
      </div>

      {/* Risk Counts */}
      <div className="space-y-1.5">
        {riskItems.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.level}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-lg ${item.bgColor} border ${item.borderColor}`}
            >
              <Icon className={`w-3.5 h-3.5 ${item.color} flex-shrink-0`} />
              <span className={`text-[12px] font-medium ${item.color}`}>{item.level}</span>
              <span className={`ml-auto font-mono text-[13px] font-semibold ${item.color}`}>
                {item.count}
              </span>
            </div>
          );
        })}
      </div>

      {/* Status */}
      <div className="mt-4 flex items-center gap-2 px-1">
        <Clock className="w-3 h-3 text-text3" />
        <span className="text-[11px] text-text3">状态</span>
        <span
          className={`ml-auto inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium font-mono ${
            report.status === 'completed'
              ? 'bg-accent/12 text-accent border border-accent/25'
              : 'bg-amber/10 text-amber border border-amber/25'
          }`}
        >
          {report.status === 'completed' ? '已完成' : '进行中'}
        </span>
      </div>

      {/* Summary — strip markdown symbols before display */}
      {report.summary && (
        <div className="mt-3 px-1">
          <div className="text-[11px] text-text3 mb-1">分析摘要</div>
          <p className="text-[12px] text-text2 leading-relaxed line-clamp-4">
            {report.summary.replace(/#{1,6}\s*/g, '').replace(/\|/g, ' ').replace(/[-]{2,}/g, '').replace(/\n+/g, ' ').trim()}
          </p>
        </div>
      )}
    </div>
  );
}
