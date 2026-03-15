'use client';

import { Braces, Download, FileText, Image, Loader2 } from 'lucide-react';
import { useCallback, useState } from 'react';
import { API_BASE } from '@/lib/api';

interface ExportButtonsProps {
  requirementId: string | null;
  disabled?: boolean;
}

type ExportFormat = 'json' | 'markdown' | 'png';

async function exportAsJson(reqId: string) {
  const res = await fetch(`${API_BASE}/scene-map/${reqId}`);
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  const data = await res.json();
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `scene-map-${reqId}.json`;
  document.body.appendChild(a);
  a.click();
  URL.revokeObjectURL(a.href);
  a.remove();
}

async function exportAsMarkdown(reqId: string) {
  const res = await fetch(`${API_BASE}/scene-map/${reqId}`);
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  const data = await res.json();

  const points = data.test_points || [];
  const grouped: Record<string, typeof points> = {};
  for (const tp of points) {
    const group = tp.group_name || '未分组';
    if (!grouped[group]) grouped[group] = [];
    grouped[group].push(tp);
  }

  let md = `# 场景地图 — ${reqId}\n\n`;
  md += `> 状态: ${data.status || 'N/A'} | 测试点: ${points.length}\n\n`;

  for (const [group, items] of Object.entries(grouped)) {
    md += `## ${group}\n\n`;
    md += '| 测试点 | 优先级 | 来源 | 状态 | 预计用例 |\n';
    md += '|--------|--------|------|------|----------|\n';
    for (const tp of items) {
      md += `| ${tp.title} | ${tp.priority} | ${tp.source} | ${tp.status} | ${tp.estimated_cases} |\n`;
    }
    md += '\n';
  }

  const blob = new Blob([md], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `scene-map-${reqId}.md`;
  document.body.appendChild(a);
  a.click();
  URL.revokeObjectURL(a.href);
  a.remove();
}

async function exportAsPng(reqId: string) {
  const el = document.querySelector('[data-scene-map-view]');
  if (!el) throw new Error('场景地图视图未找到');

  const { default: html2canvas } = await import('html2canvas');
  const canvas = await html2canvas(el as HTMLElement, {
    backgroundColor: null,
    scale: 2,
  });

  canvas.toBlob((blob) => {
    if (!blob) return;
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `scene-map-${reqId}.png`;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(a.href);
    a.remove();
  }, 'image/png');
}

const EXPORT_OPTIONS: {
  format: ExportFormat;
  label: string;
  icon: typeof Download;
}[] = [
  { format: 'json', label: 'JSON', icon: Braces },
  { format: 'markdown', label: 'Markdown', icon: FileText },
  { format: 'png', label: 'PNG', icon: Image },
];

export function ExportButtons({ requirementId, disabled }: ExportButtonsProps) {
  const [loading, setLoading] = useState<ExportFormat | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = useCallback(
    async (format: ExportFormat) => {
      if (!requirementId || loading) return;
      setLoading(format);
      setError(null);

      try {
        switch (format) {
          case 'json':
            await exportAsJson(requirementId);
            break;
          case 'markdown':
            await exportAsMarkdown(requirementId);
            break;
          case 'png':
            await exportAsPng(requirementId);
            break;
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : '导出失败');
      } finally {
        setLoading(null);
      }
    },
    [requirementId, loading],
  );

  return (
    <div className="px-3 py-2 border-b border-sy-border">
      <div className="flex items-center gap-1.5 mb-2">
        <Download size={12} className="text-sy-text-3" />
        <span className="text-[11px] text-sy-text-3 font-medium">导出</span>
      </div>
      <div className="flex gap-1.5">
        {EXPORT_OPTIONS.map(({ format, label, icon: Icon }) => (
          <button
            key={format}
            type="button"
            disabled={!requirementId || disabled || loading !== null}
            onClick={() => handleExport(format)}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] border border-sy-border bg-sy-bg-2 text-sy-text-2 hover:bg-sy-bg-3 hover:text-sy-text disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            aria-label={`导出为 ${label}`}
          >
            {loading === format ? (
              <Loader2 size={11} className="animate-spin" />
            ) : (
              <Icon size={11} />
            )}
            {label}
          </button>
        ))}
      </div>
      {error && <p className="text-[10px] text-sy-danger mt-1.5">{error}</p>}
    </div>
  );
}
