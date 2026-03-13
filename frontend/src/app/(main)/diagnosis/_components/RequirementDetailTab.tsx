'use client';

import { AlertCircle, Edit3, FileText, Loader2, Play, Save, Tag, X } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useRequirement } from '@/hooks/useRequirement';

interface RequirementDetailTabProps {
  reqId: string;
  onStartAnalysis: () => void;
}

const priorityConfig: Record<string, { label: string; cls: string }> = {
  P0: { label: 'P0', cls: 'bg-red/10 text-red border-red/30' },
  P1: { label: 'P1', cls: 'bg-amber/10 text-amber border-amber/30' },
  P2: { label: 'P2', cls: 'bg-blue/10 text-blue border-blue/30' },
  P3: { label: 'P3', cls: 'bg-bg3 text-text3 border-border2' },
};

export function RequirementDetailTab({ reqId, onStartAnalysis }: RequirementDetailTabProps) {
  const { requirement: req, requirementLoading, updateContent, updating } = useRequirement(reqId);
  const [editMode, setEditMode] = useState(false);
  const [localContent, setLocalContent] = useState('');
  const [dirty, setDirty] = useState(false);
  const [savedOnce, setSavedOnce] = useState(false);

  const rawContent =
    (req?.content_ast?.content as string) ??
    (req?.content_ast?.raw_text as string) ??
    req?.content ??
    '';

  // Sync rawContent when requirement changes or edit mode reset
  useEffect(() => {
    setLocalContent(rawContent);
    setDirty(false);
  }, [rawContent]);

  const handleEditToggle = useCallback(() => {
    if (editMode && dirty) {
      // Discard changes
      setLocalContent(rawContent);
      setDirty(false);
    }
    setEditMode((v) => !v);
  }, [editMode, dirty, rawContent]);

  const handleSave = useCallback(async () => {
    if (!dirty) return;
    await updateContent({ content: localContent });
    setDirty(false);
    setEditMode(false);
    setSavedOnce(true);
  }, [dirty, localContent, updateContent]);

  if (requirementLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-5 h-5 text-accent animate-spin" />
      </div>
    );
  }

  if (!req) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <FileText className="w-12 h-12 text-text3 opacity-20 mb-3" />
        <p className="text-[14px] text-text3">需求数据加载失败</p>
      </div>
    );
  }

  const priority = (req.frontmatter?.priority as string) ?? 'P1';
  const prioConfig = priorityConfig[priority] ?? priorityConfig.P2;
  const iterName = req.iteration_name ?? '';
  const productName = req.product_name ?? '';

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Start Analysis Banner — appears after save */}
      {savedOnce && (
        <div className="flex-shrink-0 flex items-center gap-3 px-4 py-2.5 bg-accent/8 border-b border-accent/20">
          <AlertCircle className="w-4 h-4 text-accent flex-shrink-0" />
          <span className="text-[12.5px] text-text2 flex-1">需求已保存，可以开始 AI 分析</span>
          <button
            type="button"
            onClick={onStartAnalysis}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent text-white dark:text-black text-[12px] font-semibold hover:bg-accent2 transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
            开始分析
          </button>
        </div>
      )}

      {/* Metadata header */}
      <div className="flex-shrink-0 px-5 py-4 border-b border-border">
        <div className="flex items-start gap-3">
          <FileText className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <h2 className="text-[15px] font-semibold text-text leading-snug">{req.title}</h2>
            {(productName || iterName) && (
              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                {productName && <span className="text-[11px] text-text3">{productName}</span>}
                {productName && iterName && <span className="text-text3 text-[11px]">/</span>}
                {iterName && <span className="text-[11px] text-text3">{iterName}</span>}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-mono font-semibold ${prioConfig.cls}`}
            >
              <Tag className="w-2.5 h-2.5" />
              {prioConfig.label}
            </span>
            {req.req_id && <span className="text-[11px] text-text3 font-mono">{req.req_id}</span>}
          </div>
        </div>

        {/* Frontmatter fields */}
        {req.frontmatter && Object.keys(req.frontmatter).length > 0 && (
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
            {Object.entries(req.frontmatter).map(([key, val]) => {
              if (key === 'priority' || !val) return null;
              return (
                <div key={key} className="flex items-center gap-1.5">
                  <span className="text-[10.5px] text-text3">{key}:</span>
                  <span className="text-[10.5px] text-text2 font-mono">{String(val)}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-5 py-2.5 border-b border-border bg-bg1 flex-shrink-0">
          <span className="text-[11px] text-text3 uppercase tracking-wider">需求内容</span>
          <div className="flex items-center gap-1.5">
            {editMode && dirty && (
              <button
                type="button"
                onClick={handleSave}
                disabled={updating}
                className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-accent text-white dark:text-black text-[11.5px] font-semibold hover:bg-accent2 transition-colors disabled:opacity-50"
              >
                {updating ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Save className="w-3 h-3" />
                )}
                保存
              </button>
            )}
            <button
              type="button"
              onClick={handleEditToggle}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11.5px] transition-colors ${
                editMode
                  ? 'bg-bg3 text-text3 hover:text-text2 hover:bg-bg2'
                  : 'bg-bg2 text-text2 hover:bg-bg3 border border-border'
              }`}
            >
              {editMode ? (
                <>
                  <X className="w-3 h-3" />
                  取消
                </>
              ) : (
                <>
                  <Edit3 className="w-3 h-3" />
                  编辑
                </>
              )}
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {editMode ? (
            <textarea
              value={localContent}
              onChange={(e) => {
                setLocalContent(e.target.value);
                setDirty(true);
              }}
              className="w-full h-full min-h-[300px] resize-none bg-bg2 border border-border rounded-lg px-3 py-2.5 text-[13px] text-text font-mono placeholder:text-text3 outline-none focus:border-accent transition-colors leading-relaxed"
              placeholder="输入需求内容（支持 Markdown）..."
            />
          ) : (
            <div className="text-[13px] text-text leading-relaxed whitespace-pre-wrap">
              {rawContent || (
                <span className="text-text3 italic">暂无需求内容，点击「编辑」添加</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
