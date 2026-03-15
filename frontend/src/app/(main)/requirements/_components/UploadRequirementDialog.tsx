'use client';

import { AlertTriangle, ArrowLeft, Download, Loader2, Plus, Trash2, Upload, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { API_BASE } from '@/lib/api';

interface ParsedItem {
  id: string;
  title: string;
  content: string;
}

interface ParseResponse {
  items: Array<{ title: string; content: string }>;
  confidence: number;
  confidence_reason: string;
  raw_text: string;
  file_type: string;
}

export interface UploadRequirementDialogProps {
  open: boolean;
  onClose: () => void;
  productId?: string;
  iterationId?: string;
  onSuccess: () => void;
}

export function UploadRequirementDialog({
  open,
  onClose,
  productId,
  iterationId,
  onSuccess,
}: UploadRequirementDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [step, setStep] = useState<1 | 2>(1);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [parseResult, setParseResult] = useState<ParseResponse | null>(null);
  const [items, setItems] = useState<ParsedItem[]>([]);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    else if (!open && el.open) el.close();
  }, [open]);

  const resetState = () => {
    setStep(1);
    setFile(null);
    setTitle('');
    setParseError(null);
    setParseResult(null);
    setItems([]);
    setSaveError(null);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    if (f && !title) {
      setTitle(f.name.replace(/\.[^.]+$/, ''));
    }
  };

  const handleParse = async () => {
    if (!file) return;
    setParsing(true);
    setParseError(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`${API_BASE}/uda/parse-structure`, {
        method: 'POST',
        body: fd,
      });
      if (!res.ok) {
        const detail = await res.text().catch(() => res.statusText);
        throw new Error(`解析失败: ${detail}`);
      }
      const data: ParseResponse = await res.json();
      setParseResult(data);
      setItems(
        (data.items ?? []).map((item, i) => ({
          id: `item-${i}-${Date.now()}`,
          title: item.title ?? '',
          content: item.content ?? '',
        })),
      );
      setStep(2);
    } catch (err) {
      setParseError(err instanceof Error ? err.message : '解析失败');
    } finally {
      setParsing(false);
    }
  };

  const handleSave = async () => {
    if (!iterationId || !productId || items.length === 0) return;
    setSaving(true);
    setSaveError(null);
    try {
      const ts = Date.now();
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const reqId = `REQ-${ts}-${i + 1}`;
        const res = await fetch(
          `${API_BASE}/products/${productId}/iterations/${iterationId}/requirements`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              req_id: reqId,
              iteration_id: iterationId,
              title: item.title || title || `需求条目 ${i + 1}`,
              content_ast: { raw_text: item.content, sections: [] },
            }),
          },
        );
        if (!res.ok) {
          const detail = await res.text().catch(() => res.statusText);
          throw new Error(`保存第 ${i + 1} 条失败: ${detail}`);
        }
      }
      handleClose();
      onSuccess();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : '保存失败');
    } finally {
      setSaving(false);
    }
  };

  const updateItem = (id: string, field: 'title' | 'content', value: string) => {
    setItems((prev) => prev.map((it) => (it.id === id ? { ...it, [field]: value } : it)));
  };

  const deleteItem = (id: string) => {
    setItems((prev) => prev.filter((it) => it.id !== id));
  };

  const addItem = () => {
    setItems((prev) => [...prev, { id: `item-new-${Date.now()}`, title: '', content: '' }]);
  };

  if (!open) return null;

  return (
    <dialog
      ref={dialogRef}
      className="fixed inset-0 z-50 m-auto rounded-xl border border-sy-border bg-sy-bg-1 p-0 shadow-lg backdrop:bg-black/50"
      style={{
        width: step === 2 ? 640 : 480,
        maxHeight: '85vh',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
      onClose={handleClose}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 pt-4 pb-3 border-b border-sy-border flex-shrink-0">
        <div className="flex items-center gap-2">
          {step === 2 && (
            <button
              type="button"
              onClick={() => setStep(1)}
              className="text-sy-text-2 hover:text-sy-text transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}
          <h3 className="text-[14px] font-semibold text-sy-text">
            {step === 1 ? '上传需求文档' : '确认解析结构'}
          </h3>
          <span className="text-[10px] font-mono text-sy-text-3 bg-sy-bg-3 px-1.5 py-0.5 rounded-full">
            {step}/2
          </span>
        </div>
        <button
          type="button"
          onClick={handleClose}
          className="text-sy-text-3 hover:text-sy-text transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* ── Step 1: 选择文件 ── */}
      {step === 1 && (
        <div className="px-5 py-4 flex flex-col gap-4 overflow-y-auto">
          {/* Guidance banner */}
          <div className="flex items-start gap-2 rounded-lg bg-sy-warn/10 border border-sy-warn/30 px-3 py-2.5">
            <AlertTriangle className="w-3.5 h-3.5 text-sy-warn mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-[12px] text-sy-warn leading-snug">
                建议使用标准模板上传，结构化识别效果更佳
              </p>
              <div className="flex items-center gap-3 mt-1.5">
                <a
                  href="/templates/需求文档模板.docx"
                  download
                  className="inline-flex items-center gap-1 text-[11px] text-sy-text-2 hover:text-sy-accent underline underline-offset-2 transition-colors"
                >
                  <Download className="w-3 h-3" />
                  下载 .docx 模板
                </a>
                <a
                  href="/templates/需求文档模板.md"
                  download
                  className="inline-flex items-center gap-1 text-[11px] text-sy-text-2 hover:text-sy-accent underline underline-offset-2 transition-colors"
                >
                  <Download className="w-3 h-3" />
                  下载 .md 模板
                </a>
              </div>
            </div>
          </div>

          {/* File input */}
          <div>
            <label
              htmlFor="upload-req-file"
              className="text-[12px] text-sy-text-2 block mb-1.5 font-medium"
            >
              需求文档
            </label>
            <input
              id="upload-req-file"
              type="file"
              accept=".docx,.doc,.pdf,.md,.txt"
              onChange={handleFileChange}
              className="w-full text-[12px] text-sy-text rounded-lg border border-sy-border bg-sy-bg-2 px-2 py-1.5 cursor-pointer transition-colors file:mr-3 file:px-3 file:py-1 file:rounded-md file:border-0 file:text-[11.5px] file:font-medium file:bg-sy-bg-3 file:text-sy-text-2 file:cursor-pointer hover:file:bg-sy-border"
            />
            <p className="text-[11px] text-sy-text-3 mt-1">支持 .docx · .doc · .pdf · .md · .txt</p>
          </div>

          {/* Title input */}
          <div>
            <label
              htmlFor="upload-req-title"
              className="text-[12px] text-sy-text-2 block mb-1.5 font-medium"
            >
              需求标题{' '}
              <span className="text-sy-text-3 font-normal">（可选，自动从文件名填充）</span>
            </label>
            <input
              id="upload-req-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="输入需求标题..."
              className="w-full text-[12.5px] text-sy-text rounded-lg border border-sy-border bg-sy-bg-2 px-3 py-2 placeholder:text-sy-text-3 focus:outline-none focus:border-sy-accent transition-colors"
            />
          </div>

          {parseError && (
            <div className="flex items-center gap-2 rounded-lg bg-sy-danger/10 border border-sy-danger/30 px-3 py-2 text-[12px] text-sy-danger">
              <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
              {parseError}
            </div>
          )}

          {/* Footer */}
          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={handleClose}
              className="px-3 py-1.5 rounded-md text-[12.5px] font-medium border border-sy-border bg-sy-bg-2 text-sy-text-2 hover:bg-sy-bg-3 transition-colors"
            >
              取消
            </button>
            <button
              type="button"
              onClick={handleParse}
              disabled={!file || parsing}
              className="px-3 py-1.5 rounded-md text-[12.5px] font-medium bg-sy-accent text-white hover:bg-sy-accent-2 transition-colors disabled:opacity-50 inline-flex items-center gap-1.5"
            >
              {parsing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  解析中...
                </>
              ) : (
                <>
                  <Upload className="w-3.5 h-3.5" />
                  解析文档
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* ── Step 2: 确认结构 ── */}
      {step === 2 && (
        <>
          <div className="px-5 py-3 flex flex-col gap-3 overflow-y-auto flex-1 min-h-0">
            {/* Low confidence warning */}
            {parseResult && parseResult.confidence < 0.6 && (
              <div className="flex items-start gap-2 rounded-lg bg-sy-warn/10 border border-sy-warn/30 px-3 py-2.5 flex-shrink-0">
                <AlertTriangle className="w-3.5 h-3.5 text-sy-warn mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-[12px] text-sy-warn font-medium">识别置信度较低</p>
                  <p className="text-[11.5px] text-sy-warn/80 mt-0.5 leading-snug">
                    {parseResult.confidence_reason}
                  </p>
                  <p className="text-[11px] text-sy-text-3 mt-1.5">
                    您可以继续使用，或返回重新上传更规范的文档
                  </p>
                </div>
              </div>
            )}

            {/* Items list */}
            <div className="flex flex-col gap-2">
              {items.map((item, idx) => (
                <div key={item.id} className="rounded-lg border border-sy-border bg-sy-bg-2 p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[10px] font-mono text-sy-text-3 bg-sy-bg-3 px-1.5 py-0.5 rounded flex-shrink-0">
                      #{idx + 1}
                    </span>
                    <input
                      type="text"
                      value={item.title}
                      onChange={(e) => updateItem(item.id, 'title', e.target.value)}
                      placeholder="条目标题..."
                      className="flex-1 text-[12.5px] font-medium text-sy-text bg-transparent border-b border-transparent hover:border-sy-border focus:border-sy-accent focus:outline-none pb-0.5 transition-colors placeholder:text-sy-text-3"
                    />
                    <button
                      type="button"
                      onClick={() => deleteItem(item.id)}
                      className="text-sy-text-3 hover:text-sy-danger transition-colors p-1 rounded flex-shrink-0"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <textarea
                    value={item.content}
                    onChange={(e) => updateItem(item.id, 'content', e.target.value)}
                    placeholder="条目内容..."
                    rows={3}
                    className="w-full text-[12px] text-sy-text-2 bg-sy-bg-3 rounded-md border border-sy-border px-2.5 py-2 resize-none focus:outline-none focus:border-sy-accent placeholder:text-sy-text-3 transition-colors"
                  />
                </div>
              ))}
            </div>

            {/* Add item button */}
            <button
              type="button"
              onClick={addItem}
              className="w-full py-2 rounded-lg border border-dashed border-sy-border text-sy-text-3 hover:border-sy-accent hover:text-sy-accent text-[12px] inline-flex items-center justify-center gap-1.5 transition-colors flex-shrink-0"
            >
              <Plus className="w-3.5 h-3.5" />
              添加条目
            </button>

            {saveError && (
              <div className="flex items-center gap-2 rounded-lg bg-sy-danger/10 border border-sy-danger/30 px-3 py-2 text-[12px] text-sy-danger flex-shrink-0">
                <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                {saveError}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-between items-center px-5 py-3 border-t border-sy-border flex-shrink-0">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="px-3 py-1.5 rounded-md text-[12.5px] font-medium border border-sy-border bg-sy-bg-2 text-sy-text-2 hover:bg-sy-bg-3 transition-colors inline-flex items-center gap-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              返回
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving || items.length === 0 || !iterationId || !productId}
              className="px-3 py-1.5 rounded-md text-[12.5px] font-medium bg-sy-accent text-white hover:bg-sy-accent-2 transition-colors disabled:opacity-50 inline-flex items-center gap-1.5"
            >
              {saving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  保存中...
                </>
              ) : (
                `确认保存（${items.length} 条）`
              )}
            </button>
          </div>
        </>
      )}
    </dialog>
  );
}
