'use client';

import {
  AlertTriangle,
  ArrowLeft,
  BookOpen,
  ClipboardList,
  FileText,
  Filter,
  GitBranch,
  HeartPulse,
  LayoutTemplate,
  Loader2,
  Search,
} from 'lucide-react';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import { ApiError, type SearchResultItem, searchApi } from '@/lib/api';

type ResultType =
  | 'requirement'
  | 'testcase'
  | 'test_point'
  | 'diagnosis'
  | 'template'
  | 'knowledge';
type FilterType = 'all' | ResultType;

interface SearchResult {
  id: string;
  title: string;
  type: ResultType;
  description: string;
  url: string;
  updatedAt: string | null;
}

const typeConfig: Record<
  ResultType,
  {
    label: string;
    icon: typeof FileText;
    pill: string;
  }
> = {
  requirement: { label: '需求', icon: FileText, pill: 'pill-blue' },
  testcase: { label: '用例', icon: ClipboardList, pill: 'pill-green' },
  test_point: { label: '测试点', icon: GitBranch, pill: 'pill-amber' },
  diagnosis: { label: '分析', icon: HeartPulse, pill: 'pill-amber' },
  template: { label: '模板', icon: LayoutTemplate, pill: 'pill-purple' },
  knowledge: { label: '知识库', icon: BookOpen, pill: 'pill-gray' },
};

const filterOptions: Array<{ value: FilterType; label: string }> = [
  { value: 'all', label: '全部' },
  { value: 'requirement', label: '需求' },
  { value: 'testcase', label: '用例' },
  { value: 'test_point', label: '测试点' },
  { value: 'diagnosis', label: '分析' },
  { value: 'template', label: '模板' },
  { value: 'knowledge', label: '知识库' },
];

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message || `请求失败（${error.status}）`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return '搜索失败，请稍后重试。';
}

function getResultUrl(type: ResultType, id: string): string {
  switch (type) {
    case 'requirement':
      return `/requirements/${id}`;
    case 'testcase':
      return '/testcases';
    case 'test_point':
      return '/scene-map';
    case 'diagnosis':
      return '/diagnosis';
    case 'template':
      return '/templates';
    case 'knowledge':
      return '/knowledge';
  }
}

function formatUpdatedAt(value: string | null): string {
  if (!value) {
    return '--';
  }
  return new Date(value).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function normalizeResult(item: SearchResultItem): SearchResult | null {
  const entityType = item.entity_type ?? item.type;
  if (!(entityType in typeConfig)) {
    return null;
  }

  const type = entityType as ResultType;
  return {
    id: item.id,
    title: item.title || '未命名结果',
    type,
    description: item.summary || '暂无摘要信息',
    url: getResultUrl(type, item.id),
    updatedAt: item.updated_at ?? null,
  };
}

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<FilterType>('all');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      setResults([]);
      setTotal(0);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    const timer = window.setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await searchApi.search(
          trimmedQuery,
          filter === 'all' ? undefined : [filter],
          1,
          50,
        );
        if (cancelled) {
          return;
        }
        const nextResults = data.items
          .map(normalizeResult)
          .filter((item): item is SearchResult => Boolean(item));
        setResults(nextResults);
        setTotal(data.total);
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err));
          setResults([]);
          setTotal(0);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }, 250);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [filter, query]);

  const grouped = useMemo(
    () =>
      results.reduce<Record<string, SearchResult[]>>((acc, item) => {
        acc[item.type] = acc[item.type] || [];
        acc[item.type].push(item);
        return acc;
      }, {}),
    [results],
  );

  const hasQuery = query.trim().length > 0;

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/" className="text-text3 hover:text-text2 transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <Search className="w-5 h-5 text-accent" />
        <h1 className="font-display text-lg font-bold text-text">搜索结果</h1>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text3" />
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="搜索需求、测试点、用例、模板、知识文档..."
          className="input w-full pl-10 py-2.5 text-sm"
          // biome-ignore lint/a11y/noAutofocus: search page needs autofocus
          autoFocus
        />
      </div>

      <div className="flex items-center gap-2 mb-6 flex-wrap">
        <Filter className="w-3.5 h-3.5 text-text3" />
        {filterOptions.map((item) => (
          <button
            type="button"
            key={item.value}
            className={`px-3 py-1 rounded-full text-[11.5px] font-medium transition-colors ${
              filter === item.value
                ? 'bg-accent/10 text-accent border border-accent/25'
                : 'text-text3 hover:text-text2 hover:bg-bg2 border border-transparent'
            }`}
            onClick={() => setFilter(item.value)}
          >
            {item.label}
          </button>
        ))}
        <span className="ml-auto text-[11px] text-text3 font-mono">{total} 个结果</span>
      </div>

      {error && (
        <div className="alert-banner mb-6">
          <AlertTriangle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {!hasQuery ? (
        <div className="py-16 text-center">
          <Search className="w-12 h-12 text-text3 mx-auto mb-3 opacity-20" />
          <p className="text-[13px] text-text3">输入关键词开始搜索</p>
          <p className="text-[12px] text-text3/60 mt-1">
            支持需求、测试点、用例、模板、知识文档与分析结果
          </p>
        </div>
      ) : loading ? (
        <div className="py-16 text-center">
          <Loader2 className="w-8 h-8 text-text3 mx-auto mb-3 animate-spin" />
          <p className="text-[13px] text-text3">正在检索匹配结果...</p>
        </div>
      ) : Object.keys(grouped).length === 0 ? (
        <div className="py-16 text-center">
          <Search className="w-12 h-12 text-text3 mx-auto mb-3 opacity-20" />
          <p className="text-[13px] text-text3">未找到匹配结果</p>
          <p className="text-[12px] text-text3/60 mt-1">请尝试其他关键词</p>
        </div>
      ) : (
        Object.entries(grouped).map(([type, items]) => {
          const config = typeConfig[type as ResultType];
          const Icon = config.icon;
          return (
            <div key={type} className="mb-6">
              <div className="flex items-center gap-2 mb-3">
                <span className={`pill ${config.pill} text-[10px]`}>{config.label}</span>
                <span className="text-[10px] text-text3 font-mono">{items.length}</span>
              </div>
              <div className="flex flex-col gap-2">
                {items.map((item) => (
                  <Link
                    key={item.id}
                    href={item.url}
                    className="card card-hover flex items-center gap-3"
                  >
                    <Icon className="w-4 h-4 text-text3 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-[13px] font-medium text-text">{item.title}</div>
                      <div className="text-[11.5px] text-text3 mt-0.5">{item.description}</div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-[10px] text-text3 font-mono">
                        {formatUpdatedAt(item.updatedAt)}
                      </div>
                      <span className="text-[11px] text-text3">→</span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
