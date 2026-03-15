'use client';

import { BarChart3, FileText, Loader2, RefreshCw, Sparkles } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useDashboard } from '@/hooks/useDashboard';
import { api } from '@/lib/api';
import ActivityTimeline from './_components/ActivityTimeline';
import PendingItems from './_components/PendingItems';
import QuickActions from './_components/QuickActions';

interface QualityStats {
  by_priority: Record<string, number>;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  by_source: Record<string, number>;
  avg_ai_score: number | null;
  coverage_rate: number;
  total_cases: number;
}

const fallbackQuality: QualityStats = {
  by_priority: { P0: 42, P1: 186, P2: 412, P3: 207 },
  by_type: { functional: 520, boundary: 156, exception: 98, performance: 43, security: 30 },
  by_status: { approved: 487, review: 198, draft: 112, rejected: 50 },
  by_source: { ai_generated: 640, manual: 142, imported: 65 },
  avg_ai_score: 82.5,
  coverage_rate: 94,
  total_cases: 847,
};

const priorityColors: Record<string, string> = {
  P0: 'var(--red)',
  P1: 'var(--amber)',
  P2: 'var(--blue)',
  P3: 'var(--text3)',
};

const statusLabels: Record<string, string> = {
  approved: '已通过',
  review: '待审核',
  draft: '草稿',
  rejected: '已拒绝',
};

const sourceLabels: Record<string, string> = {
  ai_generated: 'AI 生成',
  manual: '手动创建',
  imported: '导入',
};

const typeLabels: Record<string, string> = {
  functional: '功能',
  boundary: '边界',
  exception: '异常',
  performance: '性能',
  security: '安全',
};

const iterationStatusLabels: Record<string, string> = {
  active: '进行中',
  completed: '已完成',
  planned: '未开始',
  draft: '草稿',
};

function formatCount(value: number) {
  return value.toLocaleString('zh-CN');
}

function formatPercentage(value: number) {
  return `${value.toFixed(1)}%`;
}

function getDeltaText(value: number, suffix = '', precision = 0) {
  if (value === 0) {
    return '较上一迭代 持平';
  }

  const absolute = Math.abs(value).toFixed(precision);
  const normalized = precision === 0 ? absolute.replace(/\.0+$/, '') : absolute;
  const sign = value > 0 ? '+' : '-';
  return `较上一迭代 ${sign}${normalized}${suffix}`;
}

function getDeltaColor(value: number) {
  if (value > 0) return 'var(--accent)';
  if (value < 0) return 'var(--red)';
  return 'var(--text3)';
}

function BarChart({
  data,
  labels,
  colors,
}: {
  data: Record<string, number>;
  labels?: Record<string, string>;
  colors?: Record<string, string>;
}) {
  const entries = Object.entries(data);
  const max = Math.max(...entries.map(([, v]) => v), 1);
  return (
    <div className="flex flex-col gap-2.5">
      {entries.map(([key, value]) => (
        <div key={key} className="flex items-center gap-3">
          <span className="text-[11px] text-text2 w-16 text-right font-mono shrink-0">
            {labels?.[key] ?? key}
          </span>
          <div className="flex-1 h-5 bg-bg2 rounded overflow-hidden">
            <div
              className="h-full rounded transition-all"
              style={{
                width: `${(value / max) * 100}%`,
                backgroundColor: colors?.[key] ?? 'var(--accent)',
              }}
            />
          </div>
          <span className="text-[11px] font-mono text-text3 w-10 text-right">{value}</span>
        </div>
      ))}
    </div>
  );
}

/* ── Page ── */

export default function DashboardPage() {
  const { stats, pendingItems, activities, loading, selectedIterationId, setIterationId, refresh } =
    useDashboard();
  const [activeTab, setActiveTab] = useState<'overview' | 'quality'>('overview');
  const [quality, setQuality] = useState<QualityStats>(fallbackQuality);
  const [qualityLoading, setQualityLoading] = useState(false);

  const loadQuality = useCallback(async () => {
    setQualityLoading(true);
    try {
      const query = selectedIterationId ? `?iteration_id=${selectedIterationId}` : '';
      const data = await api.get<QualityStats>(`/dashboard/quality${query}`);
      setQuality(data);
    } catch {
      setQuality(fallbackQuality);
    } finally {
      setQualityLoading(false);
    }
  }, [selectedIterationId]);

  useEffect(() => {
    if (activeTab === 'quality') {
      loadQuality();
    }
  }, [activeTab, loadQuality]);

  const selectedIterationLabel =
    stats.selected_iteration_product_name && stats.selected_iteration_name
      ? `${stats.selected_iteration_product_name} · ${stats.selected_iteration_name}`
      : '暂无可用迭代';
  const selectedIterationStatus = stats.selected_iteration_status
    ? (iterationStatusLabels[stats.selected_iteration_status] ?? stats.selected_iteration_status)
    : '暂无状态';
  const qualityScore = quality.avg_ai_score ?? 0;

  return (
    <div className="no-sidebar">
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        {/* ── Welcome bar ── */}
        <div className="topbar">
          <div>
            <div className="page-watermark">SISYPHUS · DASHBOARD</div>
            <h1>仪表盘</h1>
            <div className="sub">
              AI 驱动的测试用例生成平台 · 当前聚焦 {selectedIterationLabel} · {stats.product_count}{' '}
              个产品 · {stats.iteration_count} 个活跃迭代
            </div>
          </div>
          <div className="spacer" />
          <div className="flex items-center gap-2">
            <label
              htmlFor="dashboard-iteration-selector"
              className="flex items-center gap-2 rounded-lg bg-bg2 px-3 py-1.5 text-[12px] text-text2"
            >
              <span>迭代</span>
              <select
                id="dashboard-iteration-selector"
                aria-label="选择迭代"
                className="bg-transparent text-text outline-none"
                value={selectedIterationId ?? ''}
                onChange={(event) => setIterationId(event.target.value || null)}
                disabled={stats.available_iterations.length === 0}
              >
                {stats.available_iterations.length === 0 ? (
                  <option value="">暂无迭代数据</option>
                ) : (
                  stats.available_iterations.map((iteration) => (
                    <option key={iteration.id} value={iteration.id}>
                      {iteration.product_name} · {iteration.name}
                    </option>
                  ))
                )}
              </select>
            </label>
            <div className="flex items-center bg-bg2 rounded-lg p-0.5">
              <button
                type="button"
                className={`px-3 py-1 rounded-md text-[12px] transition-colors ${
                  activeTab === 'overview'
                    ? 'bg-bg1 text-text font-medium shadow-sm'
                    : 'text-text3 hover:text-text2'
                }`}
                onClick={() => setActiveTab('overview')}
              >
                项目概览
              </button>
              <button
                type="button"
                className={`px-3 py-1 rounded-md text-[12px] transition-colors flex items-center gap-1 ${
                  activeTab === 'quality'
                    ? 'bg-bg1 text-text font-medium shadow-sm'
                    : 'text-text3 hover:text-text2'
                }`}
                onClick={() => setActiveTab('quality')}
              >
                <BarChart3 className="w-3 h-3" />
                质量分析
              </button>
            </div>
            <button type="button" className="btn" onClick={refresh}>
              <RefreshCw size={14} />
              刷新
            </button>
          </div>
        </div>

        {activeTab === 'overview' ? (
          <>
            {/* ── Welcome banner ── */}
            <div
              className="card fade-in"
              style={{
                marginBottom: 24,
                background: 'linear-gradient(135deg, var(--accent-d), rgba(59, 130, 246, 0.06))',
                borderColor: 'rgba(0, 217, 163, 0.2)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    background: 'var(--accent-d)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--accent)',
                  }}
                >
                  <Sparkles size={20} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 2 }}>
                    欢迎回到 Sisyphus-Y
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text2)' }}>
                    需求录入 → 需求分析 → 测试点确认 → 用例生成 → 执行回流，构建完整测试生命周期
                  </div>
                </div>
              </div>
            </div>

            {/* ── Stat cards ── */}
            <div className="grid-4" style={{ marginBottom: 24 }}>
              <div className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
                <div className="stat-val">
                  {loading ? '—' : formatCount(stats.requirement_count)}
                </div>
                <div className="stat-label">需求总数</div>
                <div
                  className="stat-delta"
                  style={{ color: getDeltaColor(stats.requirement_delta) }}
                >
                  {stats.previous_iteration_name
                    ? getDeltaText(stats.requirement_delta)
                    : '首个迭代，无上一迭代'}
                </div>
              </div>
              <div className="card" style={{ borderLeft: '3px solid var(--blue)' }}>
                <div className="stat-val">{loading ? '—' : formatCount(stats.testcase_count)}</div>
                <div className="stat-label">用例总数</div>
                <div className="stat-delta" style={{ color: getDeltaColor(stats.testcase_delta) }}>
                  {stats.previous_iteration_name
                    ? getDeltaText(stats.testcase_delta)
                    : '首个迭代，无上一迭代'}
                </div>
              </div>
              <div className="card" style={{ borderLeft: '3px solid var(--purple)' }}>
                <div className="stat-val">
                  {loading ? '—' : formatPercentage(stats.coverage_rate)}
                </div>
                <div className="stat-label">平均覆盖率</div>
                <div className="stat-delta" style={{ color: getDeltaColor(stats.coverage_delta) }}>
                  {stats.previous_iteration_name
                    ? getDeltaText(stats.coverage_delta, '%', 1)
                    : '首个迭代，无上一迭代'}
                </div>
              </div>
              <div
                className="card"
                style={{
                  borderLeft: `3px solid ${stats.selected_iteration_status === 'active' ? 'var(--accent)' : 'var(--blue)'}`,
                }}
              >
                <div className="stat-val">
                  {loading ? '—' : (stats.selected_iteration_name ?? '—')}
                </div>
                <div className="stat-label">本迭代进度</div>
                <div
                  className="stat-delta"
                  style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <span
                    style={{
                      color:
                        stats.selected_iteration_status === 'active'
                          ? 'var(--accent)'
                          : 'var(--blue)',
                    }}
                  >
                    <FileText size={12} style={{ display: 'inline-block', marginRight: 4 }} />
                    {selectedIterationStatus}
                  </span>
                  <span style={{ color: 'var(--text3)' }}>
                    {stats.previous_iteration_name
                      ? `对比 ${stats.previous_iteration_name}`
                      : '首个迭代，无上一迭代'}
                  </span>
                </div>
              </div>
            </div>

            {/* ── Quick actions ── */}
            <QuickActions />

            {/* ── Two-column: Pending + Activity ── */}
            <div className="grid-2" style={{ marginBottom: 32, alignItems: 'start' }}>
              <PendingItems items={pendingItems} />
              <ActivityTimeline activities={activities} loading={loading} />
            </div>
          </>
        ) : (
          /* ── Quality Analysis Tab ── */
          <div className="fade-in">
            {qualityLoading ? (
              <div className="py-16 text-center">
                <Loader2 className="w-8 h-8 text-text3 mx-auto mb-3 animate-spin" />
                <p className="text-[13px] text-text3">正在加载质量分析数据...</p>
              </div>
            ) : (
              <>
                {/* ── Quality stat cards ── */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
                    <div className="stat-val">{quality.total_cases}</div>
                    <div className="stat-label">用例总数</div>
                  </div>
                  <div className="card" style={{ borderLeft: '3px solid var(--blue)' }}>
                    <div
                      className="stat-val"
                      style={{
                        color: qualityScore >= 80 ? 'var(--accent)' : 'var(--amber)',
                      }}
                    >
                      {qualityScore.toFixed(1)}
                    </div>
                    <div className="stat-label">AI 平均质量评分</div>
                  </div>
                  <div className="card" style={{ borderLeft: '3px solid var(--purple)' }}>
                    <div
                      className="stat-val"
                      style={{
                        color: quality.coverage_rate >= 80 ? 'var(--accent)' : 'var(--amber)',
                      }}
                    >
                      {quality.coverage_rate}%
                    </div>
                    <div className="stat-label">需求覆盖率</div>
                  </div>
                </div>

                {/* ── Charts grid ── */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="card">
                    <div className="text-[13px] font-medium text-text mb-4">按优先级分布</div>
                    <BarChart data={quality.by_priority} colors={priorityColors} />
                  </div>
                  <div className="card">
                    <div className="text-[13px] font-medium text-text mb-4">按用例类型分布</div>
                    <BarChart data={quality.by_type} labels={typeLabels} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="card">
                    <div className="text-[13px] font-medium text-text mb-4">按审核状态分布</div>
                    <BarChart data={quality.by_status} labels={statusLabels} />
                  </div>
                  <div className="card">
                    <div className="text-[13px] font-medium text-text mb-4">按来源分布</div>
                    <BarChart data={quality.by_source} labels={sourceLabels} />
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
