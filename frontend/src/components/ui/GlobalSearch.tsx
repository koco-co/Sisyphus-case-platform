'use client';

import {
  ArrowRight,
  BookOpen,
  ClipboardList,
  FileText,
  HeartPulse,
  LayoutTemplate,
  Search,
  X,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import { searchApi } from '@/lib/api';

interface SearchResult {
  id: string;
  title: string;
  type: 'requirement' | 'testcase' | 'diagnosis' | 'template' | 'knowledge';
  description: string;
  url: string;
}

const typeConfig = {
  requirement: { label: '需求', icon: FileText, pill: 'pill-blue' },
  testcase: { label: '用例', icon: ClipboardList, pill: 'pill-green' },
  diagnosis: { label: '分析', icon: HeartPulse, pill: 'pill-amber' },
  template: { label: '模板', icon: LayoutTemplate, pill: 'pill-purple' },
  knowledge: { label: '知识库', icon: BookOpen, pill: 'pill-gray' },
};

const mockResults: SearchResult[] = [
  {
    id: '1',
    title: '用户登录功能需求',
    type: 'requirement',
    description: 'REQ-001 · 用户登录认证流程',
    url: '/requirements',
  },
  {
    id: '2',
    title: '登录-密码错误锁定',
    type: 'testcase',
    description: 'TC-LOGIN-003 · P1 · 功能测试',
    url: '/testcases',
  },
  {
    id: '3',
    title: '数据导入需求分析',
    type: 'diagnosis',
    description: '评分 82 · 2 个高风险项',
    url: '/diagnosis',
  },
  {
    id: '4',
    title: '接口测试模板',
    type: 'template',
    description: 'API 接口标准测试模板',
    url: '/templates',
  },
  {
    id: '5',
    title: '支付流程异常处理',
    type: 'requirement',
    description: 'REQ-015 · 支付异常回滚',
    url: '/requirements',
  },
  {
    id: '6',
    title: '批量导入-文件格式校验',
    type: 'testcase',
    description: 'TC-IMP-007 · P0 · 边界测试',
    url: '/testcases',
  },
  {
    id: '7',
    title: '测试规范文档',
    type: 'knowledge',
    description: '企业级测试规范 v2.1',
    url: '/knowledge',
  },
];

export function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const router = useRouter();

  // Debounced API search
  useEffect(() => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const data = await searchApi.search(query, undefined, 10);
        type ValidType = SearchResult['type'];
        const validTypes: ValidType[] = ['requirement', 'testcase', 'diagnosis', 'template', 'knowledge'];
        setSearchResults(
          (data.items ?? []).map((item) => ({
            id: item.id,
            title: item.title,
            type: (validTypes.includes(item.type as ValidType) ? item.type : 'requirement') as ValidType,
            description: item.content ?? item.summary ?? item.highlight ?? '',
            url: `/${item.type}s`,
          })),
        );
      } catch {
        // Fallback to mock filtering
        setSearchResults(
          mockResults.filter(
            (r) =>
              r.title.toLowerCase().includes(query.toLowerCase()) ||
              r.description.toLowerCase().includes(query.toLowerCase()),
          ),
        );
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => {
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    };
  }, [query]);

  const filteredResults = query.trim() ? searchResults : mockResults.slice(0, 5);

  const grouped = filteredResults.reduce<Record<string, SearchResult[]>>((acc, r) => {
    acc[r.type] = acc[r.type] || [];
    acc[r.type].push(r);
    return acc;
  }, {});

  const flatResults = filteredResults;

  const navigate = useCallback(
    (url: string) => {
      setOpen(false);
      setQuery('');
      router.push(url);
    },
    [router],
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen(true);
      }
      if (e.key === 'Escape') {
        setOpen(false);
        setQuery('');
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setSelectedIndex(0);
    }
  }, [open]);

  const prevQueryRef = useRef(query);
  if (prevQueryRef.current !== query) {
    prevQueryRef.current = query;
    if (selectedIndex !== 0) setSelectedIndex(0);
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, flatResults.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter' && flatResults[selectedIndex]) {
      navigate(flatResults[selectedIndex].url);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-start justify-center pt-[15vh]">
      {/* Backdrop */}
      {/* biome-ignore lint/a11y/noStaticElementInteractions: backdrop dismissal */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => {
          setOpen(false);
          setQuery('');
        }}
        onKeyDown={() => {}}
      />

      {/* Dialog */}
      <div
        className="relative w-full max-w-lg bg-bg1 border border-border rounded-xl shadow-lg overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-label="全局搜索"
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Search className="w-4 h-4 text-text3 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="搜索需求、用例、分析报告..."
            aria-label="搜索需求、用例、分析报告"
            className="flex-1 bg-transparent text-text text-[14px] outline-none placeholder:text-text3"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="text-text3 hover:text-text2 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-bg3 border border-border rounded text-[10px] text-text3 font-mono">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto py-2">
          {flatResults.length === 0 ? (
            <div className="py-8 text-center text-text3">
              <Search className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-[12.5px]">未找到匹配结果</p>
            </div>
          ) : (
            Object.entries(grouped).map(([type, items]) => {
              const config = typeConfig[type as keyof typeof typeConfig];
              return (
                <div key={type}>
                  <div className="px-4 py-1.5">
                    <span className="text-[10px] font-semibold text-text3 uppercase tracking-wider">
                      {config.label}
                    </span>
                  </div>
                  {items.map((item) => {
                    const Icon = config.icon;
                    const idx = flatResults.indexOf(item);
                    return (
                      <button
                        type="button"
                        key={item.id}
                        className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                          idx === selectedIndex ? 'bg-accent/8' : 'hover:bg-bg2'
                        }`}
                        onClick={() => navigate(item.url)}
                        onMouseEnter={() => setSelectedIndex(idx)}
                      >
                        <Icon
                          className={`w-4 h-4 shrink-0 ${idx === selectedIndex ? 'text-accent' : 'text-text3'}`}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="text-[13px] text-text truncate">{item.title}</div>
                          <div className="text-[11px] text-text3 truncate">{item.description}</div>
                        </div>
                        {idx === selectedIndex && (
                          <ArrowRight className="w-3.5 h-3.5 text-accent shrink-0" />
                        )}
                      </button>
                    );
                  })}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center gap-4 px-4 py-2 border-t border-border bg-bg2/50 text-[10px] text-text3">
          <span className="flex items-center gap-1">
            <kbd className="px-1 py-0.5 bg-bg3 border border-border rounded font-mono">↑↓</kbd>
            导航
          </span>
          <span className="flex items-center gap-1">
            <kbd className="px-1 py-0.5 bg-bg3 border border-border rounded font-mono">↵</kbd>
            打开
          </span>
          <span className="flex items-center gap-1">
            <kbd className="px-1 py-0.5 bg-bg3 border border-border rounded font-mono">esc</kbd>
            关闭
          </span>
        </div>
      </div>
    </div>
  );
}

export function SearchTrigger() {
  const [, setOpen] = useState(false);

  const handleClick = () => {
    setOpen(true);
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }));
  };

  return (
    <button
      type="button"
      className="flex items-center gap-2 px-3 py-1.5 bg-bg2 border border-border rounded-md text-text3 text-[12px] hover:border-border2 hover:text-text2 transition-all cursor-pointer"
      onClick={handleClick}
      aria-label="搜索 (⌘K)"
    >
      <Search className="w-3.5 h-3.5" />
      <span className="hidden sm:inline">搜索...</span>
      <kbd className="hidden sm:inline-flex ml-2 px-1 py-0.5 bg-bg3 border border-border rounded text-[10px] font-mono">
        ⌘K
      </kbd>
    </button>
  );
}
