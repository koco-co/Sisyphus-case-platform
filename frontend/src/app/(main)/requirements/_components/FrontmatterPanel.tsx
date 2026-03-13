'use client';

import { CircleDot, Clock, Flag, FolderOpen, Loader2, Pencil, Save, User } from 'lucide-react';
import { useCallback, useState } from 'react';
import { CustomSelect } from '@/components/ui/CustomSelect';

interface FrontmatterData {
  priority?: string;
  status?: string;
  module?: string;
  owner?: string;
  [key: string]: unknown;
}

interface FrontmatterPanelProps {
  frontmatter: FrontmatterData | null;
  status: string;
  createdAt: string;
  onSave?: (data: { frontmatter: FrontmatterData; status: string }) => Promise<void>;
  readOnly?: boolean;
}

const PRIORITY_OPTIONS = ['P0', 'P1', 'P2', 'P3'];
const STATUS_OPTIONS = [
  { value: 'draft', label: '草稿' },
  { value: 'confirmed', label: '已确认' },
  { value: 'diagnosed', label: '已分析' },
  { value: 'generating', label: '生成中' },
  { value: 'completed', label: '已完成' },
];

const priorityColor: Record<string, string> = {
  P0: 'text-red',
  P1: 'text-amber',
  P2: 'text-blue',
  P3: 'text-text3',
};

export function FrontmatterPanel({
  frontmatter,
  status,
  createdAt,
  onSave,
  readOnly = false,
}: FrontmatterPanelProps) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState<FrontmatterData>({
    priority: frontmatter?.priority ?? 'P1',
    module: (frontmatter?.module as string) ?? '',
    owner: (frontmatter?.owner as string) ?? '',
  });
  const [draftStatus, setDraftStatus] = useState(status);

  const handleEdit = useCallback(() => {
    setDraft({
      priority: frontmatter?.priority ?? 'P1',
      module: (frontmatter?.module as string) ?? '',
      owner: (frontmatter?.owner as string) ?? '',
    });
    setDraftStatus(status);
    setEditing(true);
  }, [frontmatter, status]);

  const handleSave = useCallback(async () => {
    if (!onSave) return;
    setSaving(true);
    try {
      await onSave({ frontmatter: draft, status: draftStatus });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }, [draft, draftStatus, onSave]);

  const formattedDate = createdAt
    ? new Date(createdAt).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—';

  const currentPriority = editing ? draft.priority : (frontmatter?.priority ?? 'P1');
  const currentStatus = editing ? draftStatus : status;
  const currentModule = editing ? draft.module : ((frontmatter?.module as string) ?? '');
  const currentOwner = editing ? draft.owner : ((frontmatter?.owner as string) ?? '');

  return (
    <div className="bg-bg1 border border-border rounded-[10px] p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-[12px] font-semibold text-text2 uppercase tracking-wide">元数据</span>
        {!readOnly && !editing && (
          <button
            type="button"
            onClick={handleEdit}
            className="flex items-center gap-1 px-2 py-1 rounded text-[11px] text-text3 hover:text-text hover:bg-bg2 transition-colors"
          >
            <Pencil size={12} /> 编辑
          </button>
        )}
        {editing && (
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-medium bg-accent text-black hover:bg-accent2 transition-colors disabled:opacity-50"
          >
            {saving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
            保存
          </button>
        )}
      </div>

      <div className="space-y-3">
        {/* Priority */}
        <div className="flex items-center gap-2.5">
          <Flag size={13} className="text-text3 shrink-0" />
          <span className="text-[11.5px] text-text3 w-14 shrink-0">优先级</span>
          {editing ? (
            <CustomSelect
              value={draft.priority ?? 'P1'}
              onChange={(value) => setDraft((d) => ({ ...d, priority: value }))}
              options={PRIORITY_OPTIONS.map((p) => ({ value: p, label: p }))}
              size="sm"
              className="flex-1"
            />
          ) : (
            <span
              className={`font-mono text-[12px] font-semibold ${priorityColor[currentPriority ?? 'P1'] ?? 'text-text3'}`}
            >
              {currentPriority}
            </span>
          )}
        </div>

        {/* Status */}
        <div className="flex items-center gap-2.5">
          <CircleDot size={13} className="text-text3 shrink-0" />
          <span className="text-[11.5px] text-text3 w-14 shrink-0">状态</span>
          {editing ? (
            <CustomSelect
              value={draftStatus}
              onChange={(value) => setDraftStatus(value)}
              options={STATUS_OPTIONS}
              size="sm"
              className="flex-1"
            />
          ) : (
            <span className="text-[12px] text-text2">
              {STATUS_OPTIONS.find((s) => s.value === currentStatus)?.label ?? currentStatus}
            </span>
          )}
        </div>

        {/* Module */}
        <div className="flex items-center gap-2.5">
          <FolderOpen size={13} className="text-text3 shrink-0" />
          <span className="text-[11.5px] text-text3 w-14 shrink-0">模块</span>
          {editing ? (
            <input
              value={draft.module ?? ''}
              onChange={(e) => setDraft((d) => ({ ...d, module: e.target.value }))}
              className="input text-[12px] py-1 px-2 flex-1"
              placeholder="所属模块"
            />
          ) : (
            <span className="text-[12px] text-text2">{currentModule || '未指定'}</span>
          )}
        </div>

        {/* Owner */}
        <div className="flex items-center gap-2.5">
          <User size={13} className="text-text3 shrink-0" />
          <span className="text-[11.5px] text-text3 w-14 shrink-0">创建者</span>
          {editing ? (
            <input
              value={draft.owner ?? ''}
              onChange={(e) => setDraft((d) => ({ ...d, owner: e.target.value }))}
              className="input text-[12px] py-1 px-2 flex-1"
              placeholder="负责人"
            />
          ) : (
            <span className="text-[12px] text-text2">{currentOwner || '未指定'}</span>
          )}
        </div>

        {/* Created At */}
        <div className="flex items-center gap-2.5">
          <Clock size={13} className="text-text3 shrink-0" />
          <span className="text-[11.5px] text-text3 w-14 shrink-0">创建时间</span>
          <span className="text-[12px] text-text3 font-mono">{formattedDate}</span>
        </div>
      </div>
    </div>
  );
}
