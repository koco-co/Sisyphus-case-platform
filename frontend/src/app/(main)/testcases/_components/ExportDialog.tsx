'use client';

import {
  Check,
  Download,
  FileJson,
  FileSpreadsheet,
  FileText,
  FolderTree,
  Loader2,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
  selectedCount?: number;
  currentFolder?: string | null;
}

type ExportFormat = 'xlsx' | 'csv' | 'xmind' | 'json';
type ExportScope = 'folder' | 'filtered' | 'selected' | 'all';

const FORMAT_OPTIONS: {
  value: ExportFormat;
  label: string;
  desc: string;
  icon: typeof FileSpreadsheet;
  recommended?: boolean;
}[] = [
  {
    value: 'xlsx',
    label: 'Excel (.xlsx)',
    desc: '兼容主流测试管理工具导入',
    icon: FileSpreadsheet,
    recommended: true,
  },
  {
    value: 'csv',
    label: 'CSV (.csv)',
    desc: '通用文本格式，轻量便捷',
    icon: FileText,
  },
  {
    value: 'xmind',
    label: 'XMind (.xmind)',
    desc: '脑图结构，适合评审展示',
    icon: FolderTree,
  },
  {
    value: 'json',
    label: 'JSON (.json)',
    desc: '结构化数据，便于程序处理',
    icon: FileJson,
  },
];

const ALL_FIELDS = [
  { key: 'caseId', label: '用例ID', default: true },
  { key: 'title', label: '标题', default: true },
  { key: 'precondition', label: '前置条件', default: true },
  { key: 'steps', label: '步骤', default: true },
  { key: 'expected', label: '预期结果', default: true },
  { key: 'priority', label: '优先级', default: true },
  { key: 'type', label: '类型', default: true },
  { key: 'modulePath', label: '模块路径', default: false },
  { key: 'createdAt', label: '创建时间', default: false },
  { key: 'updatedAt', label: '更新时间', default: false },
  { key: 'status', label: '状态', default: false },
  { key: 'source', label: '来源', default: false },
  { key: 'tags', label: '标签', default: false },
] as const;

const DEFAULT_FIELDS = new Set(ALL_FIELDS.filter((f) => f.default).map((f) => f.key));

export default function ExportDialog({
  open,
  onClose,
  selectedCount = 0,
  currentFolder,
}: ExportDialogProps) {
  const [format, setFormat] = useState<ExportFormat>('xlsx');
  const [scope, setScope] = useState<ExportScope>(selectedCount > 0 ? 'selected' : 'all');
  const [fields, setFields] = useState<Set<string>>(() => new Set(DEFAULT_FIELDS));
  const [exporting, setExporting] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  // Reset state when dialog opens
  useEffect(() => {
    if (open) {
      setFormat('xlsx');
      setScope(selectedCount > 0 ? 'selected' : 'all');
      setFields(new Set(DEFAULT_FIELDS));
      setExporting(false);
    }
  }, [open, selectedCount]);

  const allSelected = fields.size === ALL_FIELDS.length;

  const toggleAllFields = useCallback(() => {
    setFields(allSelected ? new Set() : new Set(ALL_FIELDS.map((f) => f.key)));
  }, [allSelected]);

  const toggleField = useCallback((key: string) => {
    setFields((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  const handleExport = useCallback(async () => {
    if (fields.size === 0) return;
    setExporting(true);

    // Mock export: simulate network delay then trigger download
    await new Promise((r) => setTimeout(r, 1500));

    const mockData = {
      format,
      scope,
      fields: Array.from(fields),
      exportedAt: new Date().toISOString(),
      totalCases: scope === 'selected' ? selectedCount : 42,
    };

    const blob = new Blob([JSON.stringify(mockData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `testcases-export.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setExporting(false);
    onClose();
  }, [format, scope, fields, selectedCount, onClose]);

  if (!open) return null;

  const scopeOptions: {
    value: ExportScope;
    label: string;
    disabled?: boolean;
    badge?: string;
  }[] = [
    ...(currentFolder
      ? [
          {
            value: 'folder' as ExportScope,
            label: `当前目录（${currentFolder}）`,
          },
        ]
      : []),
    { value: 'filtered', label: '当前筛选结果' },
    ...(selectedCount > 0
      ? [
          {
            value: 'selected' as ExportScope,
            label: '已选用例',
            badge: `${selectedCount}`,
          },
        ]
      : []),
    { value: 'all', label: '全部用例' },
  ];

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <button
        type="button"
        className="absolute inset-0 bg-black/50 backdrop-blur-sm cursor-default"
        onClick={exporting ? undefined : onClose}
        aria-label="关闭对话框"
        tabIndex={-1}
      />

      {/* Panel */}
      <div
        ref={panelRef}
        className="relative bg-sy-bg-1 border border-sy-border rounded-xl shadow-lg w-full max-w-md max-h-[85vh] flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-sy-border">
          <div className="flex items-center gap-2">
            <Download className="w-4 h-4 text-sy-accent" />
            <h2 className="text-[14px] font-semibold text-sy-text">导出用例</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={exporting}
            className="p-1 rounded-md text-sy-text-3 hover:text-sy-text hover:bg-sy-bg-2 transition-colors disabled:opacity-50"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
          {/* Format Selection */}
          <section>
            <h3 className="text-[12px] font-medium text-sy-text-2 uppercase tracking-wider mb-2.5">
              导出格式
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {FORMAT_OPTIONS.map((opt) => {
                const Icon = opt.icon;
                const active = format === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setFormat(opt.value)}
                    className={`relative flex items-start gap-2.5 p-3 rounded-lg border text-left transition-all ${
                      active
                        ? 'border-sy-accent bg-sy-accent/5'
                        : 'border-sy-border hover:border-sy-border-2 bg-sy-bg-2/50'
                    }`}
                  >
                    <Icon
                      className={`w-4 h-4 mt-0.5 shrink-0 ${active ? 'text-sy-accent' : 'text-sy-text-3'}`}
                    />
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`text-[12.5px] font-medium ${active ? 'text-sy-accent' : 'text-sy-text'}`}
                        >
                          {opt.label}
                        </span>
                        {opt.recommended && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-sy-accent/10 text-sy-accent font-medium">
                            推荐
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-sy-text-3 mt-0.5 leading-relaxed">
                        {opt.desc}
                      </p>
                    </div>
                    {active && (
                      <Check className="absolute top-2 right-2 w-3.5 h-3.5 text-sy-accent" />
                    )}
                  </button>
                );
              })}
            </div>
          </section>

          {/* Export Scope */}
          <section>
            <h3 className="text-[12px] font-medium text-sy-text-2 uppercase tracking-wider mb-2.5">
              导出范围
            </h3>
            <div className="space-y-1.5">
              {scopeOptions.map((opt) => {
                const active = scope === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setScope(opt.value)}
                    disabled={opt.disabled}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg border text-left transition-all ${
                      active
                        ? 'border-sy-accent bg-sy-accent/5'
                        : 'border-transparent hover:bg-sy-bg-2'
                    } ${opt.disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
                  >
                    <div
                      className={`w-3.5 h-3.5 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors ${
                        active ? 'border-sy-accent' : 'border-sy-border-2'
                      }`}
                    >
                      {active && <div className="w-1.5 h-1.5 rounded-full bg-sy-accent" />}
                    </div>
                    <span className={`text-[12.5px] ${active ? 'text-sy-text' : 'text-sy-text-2'}`}>
                      {opt.label}
                    </span>
                    {opt.badge && (
                      <span className="ml-auto text-[11px] font-mono px-1.5 py-0.5 rounded bg-sy-accent/10 text-sy-accent">
                        {opt.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </section>

          {/* Field Selection */}
          <section>
            <div className="flex items-center justify-between mb-2.5">
              <h3 className="text-[12px] font-medium text-sy-text-2 uppercase tracking-wider">
                导出字段
              </h3>
              <button
                type="button"
                onClick={toggleAllFields}
                className="text-[11px] text-sy-accent hover:text-sy-accent-2 transition-colors"
              >
                {allSelected ? '取消全选' : '全选'}
              </button>
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              {ALL_FIELDS.map((f) => {
                const checked = fields.has(f.key);
                return (
                  <button
                    key={f.key}
                    type="button"
                    onClick={() => toggleField(f.key)}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border text-left transition-all ${
                      checked
                        ? 'border-sy-accent/30 bg-sy-accent/5'
                        : 'border-sy-border hover:border-sy-border-2 bg-sy-bg-2/40'
                    }`}
                  >
                    <div
                      className={`w-3 h-3 rounded-[3px] border flex items-center justify-center shrink-0 transition-colors ${
                        checked ? 'bg-sy-accent border-sy-accent' : 'border-sy-border-2'
                      }`}
                    >
                      {checked && <Check className="w-2 h-2 text-white dark:text-black" />}
                    </div>
                    <span
                      className={`text-[11.5px] truncate ${checked ? 'text-sy-text' : 'text-sy-text-3'}`}
                    >
                      {f.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-3.5 border-t border-sy-border">
          <span className="text-[11px] text-sy-text-3">
            已选 {fields.size}/{ALL_FIELDS.length} 个字段
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={exporting}
              className="bg-sy-bg-2 text-sy-text-2 hover:text-sy-text hover:bg-sy-bg-3 rounded-md px-4 py-2 text-[12.5px] transition-colors disabled:opacity-50"
            >
              取消
            </button>
            <button
              type="button"
              onClick={handleExport}
              disabled={exporting || fields.size === 0}
              className="bg-sy-accent text-white dark:text-black hover:bg-sy-accent-2 rounded-md px-4 py-2 text-[12.5px] font-semibold transition-colors disabled:opacity-50 flex items-center gap-1.5"
            >
              {exporting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  导出中...
                </>
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  导出
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
