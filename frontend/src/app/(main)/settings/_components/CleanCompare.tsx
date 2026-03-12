'use client';

import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Database,
  Filter,
  RefreshCw,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

interface CleanStat {
  status: string;
  count: number;
  avg_score: number;
}

interface StepItem {
  no: string | number;
  action: string;
  expected_result: string;
}

interface ImportedCase {
  id: string;
  case_id: string;
  title: string;
  module_path: string | null;
  clean_status: string | null;
  quality_score: number | null;
  original_raw: Record<string, unknown> | null;
  steps: StepItem[];
  priority: string;
}

interface CleanStatsResponse {
  total: number;
  by_status: CleanStat[];
}

interface CaseListResponse {
  items: ImportedCase[];
  total: number;
  page: number;
  pages: number;
}

const STATUS_META: Record<string, { label: string; color: string }> = {
  raw: { label: '原始', color: 'text-sy-text-3 border-sy-border bg-sy-bg-3' },
  scored: { label: '已评分', color: 'text-sy-warn border-sy-warn/35 bg-sy-warn/10' },
  llm_cleaned: { label: 'AI 清洗', color: 'text-sy-accent border-sy-accent/35 bg-sy-accent/10' },
  cleaned: { label: '已清洗', color: 'text-sy-info border-sy-info/35 bg-sy-info/10' },
};

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-sy-text-3 text-[11px]">—</span>;
  const color = score >= 80 ? 'text-sy-accent' : score >= 60 ? 'text-sy-warn' : 'text-sy-danger';
  return <span className={`font-mono text-[11px] font-semibold ${color}`}>{score.toFixed(0)}</span>;
}

function CaseRow({
  c,
  expanded,
  onToggle,
}: {
  c: ImportedCase;
  expanded: boolean;
  onToggle: () => void;
}) {
  const meta = STATUS_META[c.clean_status ?? 'raw'] ?? STATUS_META.raw;
  const originalTitle = (c.original_raw?.title as string) ?? null;
  const titleChanged = originalTitle && originalTitle !== c.title;

  return (
    <div className="border border-sy-border rounded-lg overflow-hidden">
      <button
        type="button"
        className="w-full flex items-center gap-3 px-4 py-2.5 bg-sy-bg-1 hover:bg-sy-bg-2 transition-colors text-left"
        onClick={onToggle}
      >
        {expanded ? (
          <ChevronDown size={13} className="text-sy-text-3 shrink-0" />
        ) : (
          <ChevronRight size={13} className="text-sy-text-3 shrink-0" />
        )}
        <span className="font-mono text-[11px] text-sy-text-3 shrink-0 w-24 truncate">
          {c.case_id}
        </span>
        <span className="flex-1 text-[12.5px] text-sy-text truncate">{c.title}</span>
        {c.module_path && (
          <span className="text-[11px] text-sy-text-3 truncate max-w-[160px] hidden md:block">
            {c.module_path}
          </span>
        )}
        <ScoreBadge score={c.quality_score} />
        <span
          className={`font-mono text-[10px] rounded-full border px-2 py-0.5 shrink-0 ${meta.color}`}
        >
          {meta.label}
        </span>
      </button>

      {expanded && (
        <div className="px-4 pb-3 pt-2 bg-sy-bg space-y-3 border-t border-sy-border">
          {titleChanged && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-[10px] text-sy-text-3 mb-1 uppercase tracking-wide">原始标题</p>
                <p className="text-[12px] text-sy-warn bg-sy-warn/5 rounded px-2 py-1 border border-sy-warn/20">
                  {originalTitle}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-sy-text-3 mb-1 uppercase tracking-wide">
                  清洗后标题
                </p>
                <p className="text-[12px] text-sy-accent bg-sy-accent/5 rounded px-2 py-1 border border-sy-accent/20">
                  {c.title}
                </p>
              </div>
            </div>
          )}
          {c.steps.length > 0 && (
            <div>
              <p className="text-[10px] text-sy-text-3 mb-1.5 uppercase tracking-wide">
                步骤（{c.steps.length}）
              </p>
              <div className="space-y-1">
                {c.steps.slice(0, 4).map((s) => (
                  <div
                    key={`${s.no}-${s.action.slice(0, 10)}`}
                    className="flex gap-2 text-[11.5px]"
                  >
                    <span className="text-sy-text-3 shrink-0 font-mono w-4">{s.no}.</span>
                    <span className="text-sy-text-2 flex-1">{s.action}</span>
                    {s.expected_result && (
                      <span className="text-sy-text-3 max-w-[160px] truncate">
                        → {s.expected_result}
                      </span>
                    )}
                  </div>
                ))}
                {c.steps.length > 4 && (
                  <p className="text-[11px] text-sy-text-3">…还有 {c.steps.length - 4} 步</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function CleanCompare() {
  const [stats, setStats] = useState<CleanStatsResponse | null>(null);
  const [cases, setCases] = useState<ImportedCase[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [keyword, setKeyword] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);

  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const res = await fetch('/api/testcases/clean/stats');
      if (res.ok) setStats(await res.json());
    } finally {
      setStatsLoading(false);
    }
  }, []);

  const fetchCases = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        source: 'imported',
        page: String(page),
        page_size: '20',
      });
      if (filterStatus) params.set('clean_status', filterStatus);
      if (keyword) params.set('keyword', keyword);
      const res = await fetch(`/api/testcases?${params}`);
      if (res.ok) {
        const data: CaseListResponse = await res.json();
        setCases(data.items);
        setTotal(data.total);
      }
    } finally {
      setLoading(false);
    }
  }, [page, filterStatus, keyword]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  const totalImported = stats?.total ?? 0;
  const scored = stats?.by_status.find((s) => s.status === 'scored');
  const llmCleaned = stats?.by_status.find((s) => s.status === 'llm_cleaned');
  const cleaned = stats?.by_status.find((s) => s.status === 'cleaned');
  const avgScore = scored?.avg_score ?? llmCleaned?.avg_score ?? cleaned?.avg_score ?? 0;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[13px] font-medium text-sy-text flex items-center gap-2">
            <Database size={14} className="text-sy-accent" />
            历史数据清洗视图
          </h2>
          <p className="text-[11.5px] text-sy-text-3 mt-0.5">
            查看并对比导入用例的原始数据与清洗结果
          </p>
        </div>
        <button
          type="button"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] border border-sy-border bg-sy-bg-2 text-sy-text-2 hover:text-sy-text transition-colors"
          onClick={() => {
            fetchStats();
            fetchCases();
          }}
        >
          <RefreshCw size={12} className={statsLoading || loading ? 'animate-spin' : ''} />
          刷新
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="card">
          <div className="flex items-center gap-2 mb-1">
            <Database size={13} className="text-sy-info" />
            <span className="text-[11.5px] text-sy-text-3">总导入用例</span>
          </div>
          <p className="text-2xl font-semibold font-mono text-sy-text">{totalImported}</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp size={13} className="text-sy-warn" />
            <span className="text-[11.5px] text-sy-text-3">平均质量分</span>
          </div>
          <p
            className={`text-2xl font-semibold font-mono ${avgScore >= 70 ? 'text-sy-accent' : avgScore >= 50 ? 'text-sy-warn' : 'text-sy-danger'}`}
          >
            {avgScore.toFixed(0)}
          </p>
        </div>
        <div className="card">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles size={13} className="text-sy-accent" />
            <span className="text-[11.5px] text-sy-text-3">AI 已清洗</span>
          </div>
          <p className="text-2xl font-semibold font-mono text-sy-accent">
            {(llmCleaned?.count ?? 0) + (cleaned?.count ?? 0)}
          </p>
        </div>
      </div>

      {/* Status breakdown */}
      {stats && stats.by_status.length > 0 && (
        <div className="card">
          <p className="text-[11.5px] text-sy-text-3 mb-2">清洗状态分布</p>
          <div className="flex gap-3 flex-wrap">
            {stats.by_status.map((s) => {
              const m = STATUS_META[s.status] ?? STATUS_META.raw;
              return (
                <div
                  key={s.status}
                  className={`flex items-center gap-2 px-3 py-1 rounded-full border text-[11px] ${m.color}`}
                >
                  <span>{m.label}</span>
                  <span className="font-mono font-semibold">{s.count}</span>
                  {s.avg_score > 0 && (
                    <span className="opacity-70">均分 {s.avg_score.toFixed(0)}</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 items-center">
        <Filter size={13} className="text-sy-text-3" />
        <input
          type="text"
          value={keyword}
          onChange={(e) => {
            setKeyword(e.target.value);
            setPage(1);
          }}
          placeholder="搜索用例编号或标题…"
          className="flex-1 px-3 py-1.5 rounded-md bg-sy-bg-2 border border-sy-border text-[12px] text-sy-text placeholder:text-sy-text-3 outline-none focus:border-sy-accent/50"
        />
        <select
          value={filterStatus}
          onChange={(e) => {
            setFilterStatus(e.target.value);
            setPage(1);
          }}
          className="px-3 py-1.5 rounded-md bg-sy-bg-2 border border-sy-border text-[12px] text-sy-text-2 outline-none focus:border-sy-accent/50"
        >
          <option value="">全部状态</option>
          <option value="raw">原始</option>
          <option value="scored">已评分</option>
          <option value="llm_cleaned">AI 清洗</option>
        </select>
      </div>

      {/* Case List */}
      {loading ? (
        <div className="flex justify-center py-8">
          <RefreshCw size={16} className="animate-spin text-sy-text-3" />
        </div>
      ) : cases.length === 0 ? (
        <div className="card flex flex-col items-center py-10 gap-3">
          <AlertTriangle size={24} className="text-sy-text-3" />
          <p className="text-[13px] text-sy-text-3">暂无导入用例</p>
          <p className="text-[11.5px] text-sy-text-3 text-center max-w-xs">
            通过 POST /api/import-clean/clean/trigger 触发批量清洗任务后，数据将在此显示。
          </p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {cases.map((c) => (
            <CaseRow
              key={c.id}
              c={c}
              expanded={expandedId === c.id}
              onToggle={() => setExpandedId(expandedId === c.id ? null : c.id)}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > 20 && (
        <div className="flex items-center justify-between">
          <p className="text-[11.5px] text-sy-text-3">共 {total} 条</p>
          <div className="flex gap-1.5">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="px-3 py-1 rounded-md text-[11.5px] border border-sy-border bg-sy-bg-2 text-sy-text-2 disabled:opacity-40 hover:border-sy-border-2 transition-colors"
            >
              上一页
            </button>
            <button
              type="button"
              disabled={page * 20 >= total}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1 rounded-md text-[11.5px] border border-sy-border bg-sy-bg-2 text-sy-text-2 disabled:opacity-40 hover:border-sy-border-2 transition-colors"
            >
              下一页
            </button>
          </div>
        </div>
      )}

      {/* Score Legend */}
      <div className="card border-dashed">
        <p className="text-[11px] text-sy-text-3 mb-1.5">质量分说明</p>
        <div className="flex gap-4 text-[11px]">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 size={11} className="text-sy-accent" />
            <span className="text-sy-text-2">80+ 优质</span>
          </span>
          <span className="flex items-center gap-1.5">
            <AlertTriangle size={11} className="text-sy-warn" />
            <span className="text-sy-text-2">60–79 待改善</span>
          </span>
          <span className="flex items-center gap-1.5">
            <AlertTriangle size={11} className="text-sy-danger" />
            <span className="text-sy-text-2">{'<60 需清洗'}</span>
          </span>
        </div>
      </div>
    </div>
  );
}
