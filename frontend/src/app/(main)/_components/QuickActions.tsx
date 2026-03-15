'use client';

import { ClipboardList, Download, FileText, HeartPulse, Wand2 } from 'lucide-react';
import Link from 'next/link';
import { getAnalysisHomeHref, getWorkbenchHref } from '@/lib/analysisRoutes';

const actions = [
  {
    label: '新建需求',
    description: '录入需求文档，开启测试生命周期',
    icon: FileText,
    href: '/requirements',
    color: 'var(--accent)',
    bg: 'var(--accent-d)',
  },
  {
    label: '开始分析',
    description: 'AI 健康检查，发现需求风险点',
    icon: HeartPulse,
    href: getAnalysisHomeHref(),
    color: 'var(--red)',
    bg: 'rgba(244, 63, 94, 0.08)',
  },
  {
    label: '生成用例',
    description: '基于测试点自动生成功能用例',
    icon: Wand2,
    href: getWorkbenchHref(),
    color: 'var(--purple)',
    bg: 'rgba(168, 85, 247, 0.08)',
  },
  {
    label: '导出报告',
    description: '导出用例集与测试覆盖度报告',
    icon: Download,
    href: '/testcases',
    color: 'var(--blue)',
    bg: 'rgba(59, 130, 246, 0.08)',
  },
];

export default function QuickActions() {
  return (
    <div style={{ marginBottom: 24 }}>
      <div className="sec-header" style={{ marginBottom: 12 }}>
        <ClipboardList size={14} style={{ color: 'var(--accent)' }} />
        <span style={{ fontSize: 13, fontWeight: 600 }}>快速操作</span>
      </div>
      <div className="grid-4">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <Link
              href={action.href}
              key={action.label}
              className="card card-hover block"
              style={{ padding: 14 }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 8,
                  background: action.bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: action.color,
                  marginBottom: 10,
                }}
              >
                <Icon size={18} />
              </div>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 2 }}>{action.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text3)', lineHeight: 1.5 }}>
                {action.description}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
