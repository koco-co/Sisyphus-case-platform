'use client';

import { ArrowLeft, Loader2, Stethoscope, TreePine, Zap } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useCallback, useRef, useState } from 'react';
import { StatusPill } from '@/components/ui';
import { useRequirement } from '@/hooks/useRequirement';
import { EditorToolbar } from '../_components/EditorToolbar';
import { FileUpload } from '../_components/FileUpload';
import { FrontmatterPanel } from '../_components/FrontmatterPanel';
import { RelationPanel } from '../_components/RelationPanel';
import { VersionHistory } from '../_components/VersionHistory';

const statusConfig: Record<
  string,
  { variant: 'green' | 'amber' | 'gray' | 'blue'; label: string }
> = {
  draft: { variant: 'gray', label: '草稿' },
  confirmed: { variant: 'green', label: '已确认' },
  diagnosed: { variant: 'blue', label: '已分析' },
  generating: { variant: 'amber', label: '生成中' },
  completed: { variant: 'green', label: '已完成' },
};

export default function RequirementDetailPage() {
  const { id } = useParams<{ id: string }>();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [contentDirty, setContentDirty] = useState(false);
  const [localContent, setLocalContent] = useState<string | null>(null);

  const {
    requirement: req,
    requirementLoading,
    versions,
    versionsLoading,
    testPoints,
    testCases,
    relationsLoading,
    updateFrontmatter,
    updateContent,
    rollbackToVersion,
    uploadFile,
    updating,
  } = useRequirement(id);

  const status = statusConfig[req?.status ?? 'draft'] ?? statusConfig.draft;
  const priority = (req?.frontmatter?.priority as string) ?? 'P1';
  const rawContent =
    (req?.content_ast?.content as string) ?? (req?.content_ast?.raw_text as string) ?? '';
  const displayContent = localContent ?? rawContent;

  const handleContentChange = useCallback((value: string) => {
    setLocalContent(value);
    setContentDirty(true);
  }, []);

  const handleSaveContent = useCallback(async () => {
    if (!contentDirty || localContent === null) return;
    await updateContent({ content: localContent });
    setContentDirty(false);
  }, [contentDirty, localContent, updateContent]);

  const handleCompare = useCallback(
    (versionId: string) => {
      window.open(`/diff/${id}?versionId=${versionId}`, '_blank');
    },
    [id],
  );

  if (requirementLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 size={24} className="text-text3 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <Link
            href="/requirements"
            className="flex items-center gap-1 text-[11.5px] text-text3 hover:text-text mb-2 transition-colors"
          >
            <ArrowLeft size={12} /> 返回需求列表
          </Link>
          <div className="text-text3 text-[11px] font-mono mb-1">{req?.req_id ?? '...'}</div>
          <h1 className="font-display font-bold text-[20px]">{req?.title ?? '加载中...'}</h1>
          <div className="flex items-center gap-2 mt-2">
            <StatusPill variant={status.variant}>{status.label}</StatusPill>
            <StatusPill variant={priority === 'P0' ? 'red' : priority === 'P1' ? 'amber' : 'gray'}>
              {priority}
            </StatusPill>
            <span className="text-text3 text-[11px] font-mono">v{req?.version ?? 1}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {contentDirty && (
            <button
              type="button"
              onClick={handleSaveContent}
              disabled={updating}
              className="flex items-center gap-1.5 px-3 py-2 rounded-md text-[12.5px] font-medium border border-accent text-accent hover:bg-accent/10 transition-colors disabled:opacity-50"
            >
              {updating ? <Loader2 size={14} className="animate-spin" /> : null}
              保存内容
            </button>
          )}
          <Link href={`/diagnosis/${id}`}>
            <button
              type="button"
              className="flex items-center gap-1.5 px-4 py-2 rounded-md text-[12.5px] font-semibold bg-accent text-black hover:bg-accent2 transition-colors"
            >
              <Stethoscope size={14} /> 开始需求分析
            </button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-6">
        {/* Main content */}
        <div className="space-y-5">
          {/* Editor with toolbar */}
          <div>
            <div className="text-[12px] font-semibold text-text3 uppercase tracking-wide mb-2">
              需求内容
            </div>
            <EditorToolbar textareaRef={textareaRef} onContentChange={handleContentChange} />
            <textarea
              ref={textareaRef}
              value={displayContent}
              onChange={(e) => handleContentChange(e.target.value)}
              placeholder="输入需求描述（支持 Markdown）..."
              className="w-full min-h-[360px] bg-bg1 border border-border rounded-b-lg p-4 text-[13px] text-text leading-relaxed resize-y outline-none font-mono focus:border-accent transition-colors"
            />
          </div>

          {/* File Upload */}
          <div>
            <div className="text-[12px] font-semibold text-text3 uppercase tracking-wide mb-2">
              附件上传
            </div>
            <FileUpload onUpload={uploadFile} />
          </div>
        </div>

        {/* Right panel */}
        <div className="space-y-4">
          {/* Frontmatter */}
          <FrontmatterPanel
            frontmatter={req?.frontmatter ?? null}
            status={req?.status ?? 'draft'}
            createdAt={req?.created_at ?? ''}
            onSave={updateFrontmatter}
          />

          {/* Quick actions */}
          <div className="bg-bg1 border border-border rounded-[10px] p-4">
            <div className="text-[12px] font-semibold text-text2 mb-3">快速操作</div>
            <div className="space-y-2">
              <Link href={`/diagnosis/${id}`} className="block">
                <button
                  type="button"
                  className="w-full flex items-center gap-2 text-left px-3 py-2 rounded-md text-[12px] bg-bg2 border border-border text-text2 hover:text-text hover:border-border2 transition-colors"
                >
                  <Stethoscope size={13} /> 需求分析
                </button>
              </Link>
              <Link href={`/scene-map/${id}`} className="block">
                <button
                  type="button"
                  className="w-full flex items-center gap-2 text-left px-3 py-2 rounded-md text-[12px] bg-bg2 border border-border text-text2 hover:text-text hover:border-border2 transition-colors"
                >
                  <TreePine size={13} /> 测试点确认
                </button>
              </Link>
              <Link href={`/workbench/${id}`} className="block">
                <button
                  type="button"
                  className="w-full flex items-center gap-2 text-left px-3 py-2 rounded-md text-[12px] bg-bg2 border border-border text-text2 hover:text-text hover:border-border2 transition-colors"
                >
                  <Zap size={13} /> 生成工作台
                </button>
              </Link>
            </div>
          </div>

          {/* Version History */}
          <VersionHistory
            versions={versions}
            currentVersion={req?.version ?? 1}
            loading={versionsLoading}
            onRollback={rollbackToVersion}
            onCompare={handleCompare}
          />

          {/* Relation Panel */}
          <RelationPanel
            requirementId={id}
            testPoints={testPoints}
            testCases={testCases}
            loading={relationsLoading}
          />
        </div>
      </div>
    </div>
  );
}
