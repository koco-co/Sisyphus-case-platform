'use client';

import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  GitBranch,
  HeartPulse,
  Shield,
  TestTube,
} from 'lucide-react';
import Link from 'next/link';
import type { PendingItem } from '@/stores/dashboard-store';

const TYPE_CONFIG: Record<
  string,
  {
    icon: React.ComponentType<{ size?: number }>;
    pillClass: string;
    label: string;
  }
> = {
  unconfirmed_testpoint: {
    icon: GitBranch,
    pillClass: 'pill pill-amber',
    label: '未确认测试点',
  },
  pending_review: {
    icon: TestTube,
    pillClass: 'pill pill-blue',
    label: '待审用例',
  },
  failed_diagnosis: {
    icon: HeartPulse,
    pillClass: 'pill pill-red',
    label: '分析异常',
  },
  low_coverage: {
    icon: Shield,
    pillClass: 'pill pill-purple',
    label: '低覆盖率',
  },
};

const PRIORITY_COLOR: Record<string, string> = {
  high: 'var(--red)',
  medium: 'var(--amber)',
  low: 'var(--text3)',
};

interface PendingItemsProps {
  items: PendingItem[];
}

export default function PendingItems({ items }: PendingItemsProps) {
  if (items.length === 0) {
    return (
      <div>
        <div className="sec-header" style={{ marginBottom: 12 }}>
          <AlertTriangle size={14} style={{ color: 'var(--amber)' }} />
          <span style={{ fontSize: 13, fontWeight: 600 }}>待处理事项</span>
        </div>
        <div className="card">
          <div className="empty-state" style={{ padding: 24 }}>
            <CheckCircle2 size={36} style={{ color: 'var(--accent)' }} />
            <p style={{ fontWeight: 500, color: 'var(--accent)' }}>所有事项已处理完毕</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="sec-header" style={{ marginBottom: 12 }}>
        <AlertTriangle size={14} style={{ color: 'var(--amber)' }} />
        <span style={{ fontSize: 13, fontWeight: 600 }}>待处理事项</span>
        <span className="pill pill-amber" style={{ marginLeft: 4 }}>
          {items.length}
        </span>
      </div>

      <div style={{ display: 'grid', gap: 8 }}>
        {items.map((item) => {
          const cfg = TYPE_CONFIG[item.type] || TYPE_CONFIG.pending_review;
          const Icon = cfg.icon;

          return (
            <Link
              href={item.link}
              key={item.id}
              className="card card-hover"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 16px',
                borderLeft: `3px solid ${PRIORITY_COLOR[item.priority] || 'var(--border)'}`,
              }}
            >
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 8,
                  background: 'var(--bg2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  color: PRIORITY_COLOR[item.priority] || 'var(--text3)',
                }}
              >
                <Icon size={16} />
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 2,
                  }}
                >
                  <span
                    style={{
                      fontSize: 12.5,
                      fontWeight: 500,
                      color: 'var(--text)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {item.title}
                  </span>
                  <span className={cfg.pillClass}>{cfg.label}</span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text3)' }}>
                  {item.product_name} · {item.description}
                </div>
              </div>

              <ArrowRight size={14} style={{ color: 'var(--text3)', flexShrink: 0 }} />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
