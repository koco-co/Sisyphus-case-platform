'use client';

import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  Download,
  FileSpreadsheet,
  Loader2,
  Upload,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'sonner';
import { API_BASE, api } from '@/lib/api';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface ImportDialogProps {
  open: boolean;
  onClose: () => void;
  onImportComplete: () => void;
}

type FileFormat = 'xlsx' | 'csv' | 'xmind' | 'json' | null;
type DuplicateStrategyType = 'skip' | 'overwrite' | 'rename';

interface ColumnMapping {
  source: string;
  target: string | null;
}

interface ParseResult {
  columns: string[];
  preview_rows: string[][];
  all_rows: string[][];
  total_rows: number;
  auto_mapping: Record<string, string | null>;
  is_standard: boolean;
}

interface DuplicateInfo {
  index: number;
  title: string;
  existing_id: string;
  existing_case_id: string;
}

interface FlatFolder {
  id: string;
  name: string;
  level: number;
  is_system: boolean;
}

interface FolderTreeNode {
  id: string;
  name: string;
  level: number;
  is_system: boolean;
  children: FolderTreeNode[];
}

interface ImportResult {
  imported: number;
  skipped: number;
  overwritten: number;
  renamed: number;
}

const TARGET_FIELDS = [
  { value: 'title', label: '用例标题' },
  { value: 'precondition', label: '前置条件' },
  { value: 'steps', label: '测试步骤' },
  { value: 'expected_result', label: '预期结果' },
  { value: 'priority', label: '优先级' },
  { value: 'case_type', label: '用例类型' },
  { value: 'module_path', label: '所属模块' },
] as const;

const REQUIRED_FIELDS = ['title', 'steps', 'expected_result'];
const ACCEPT_EXTENSIONS = '.xlsx,.csv,.xmind,.json';

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function detectFormat(fileName: string): FileFormat {
  const ext = fileName.split('.').pop()?.toLowerCase() ?? '';
  if (ext === 'xlsx' || ext === 'xls') return 'xlsx';
  if (ext === 'csv') return 'csv';
  if (ext === 'xmind') return 'xmind';
  if (ext === 'json') return 'json';
  return null;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function flattenFolderTree(nodes: FolderTreeNode[]): FlatFolder[] {
  const result: FlatFolder[] = [];
  function walk(list: FolderTreeNode[]) {
    for (const node of list) {
      result.push({ id: node.id, name: node.name, level: node.level, is_system: node.is_system });
      if (node.children?.length) walk(node.children);
    }
  }
  walk(nodes);
  return result;
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

export function ImportDialog({ open, onClose, onImportComplete }: ImportDialogProps) {
  /* ---------- upload state ---------- */
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState<FileFormat>(null);
  const [uploading, setUploading] = useState(false);
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [folderId, setFolderId] = useState<string | null>(null);
  const [folderList, setFolderList] = useState<FlatFolder[]>([]);
  const [folderOpen, setFolderOpen] = useState(false);

  /* ---------- mapping state ---------- */
  const [mappings, setMappings] = useState<ColumnMapping[]>([]);

  /* ---------- duplicate state ---------- */
  const [duplicates, setDuplicates] = useState<DuplicateInfo[]>([]);
  const [perCaseStrategies, setPerCaseStrategies] = useState<Record<number, DuplicateStrategyType>>(
    {},
  );
  const [checkingDuplicates, setCheckingDuplicates] = useState(false);

  /* ---------- import state ---------- */
  const [importing, setImporting] = useState(false);
  const [_importResult, setImportResult] = useState<ImportResult | null>(null);

  /* ---------- step ---------- */
  const [stepIndex, setStepIndex] = useState(0);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropRef = useRef<HTMLDivElement>(null);

  /* ---------- computed steps ---------- */
  const steps = useMemo(() => {
    if (parseResult?.is_standard) {
      return ['上传文件', '数据预览', '重复检测', '确认导入'];
    }
    return ['上传文件', '字段映射', '数据预览', '重复检测', '确认导入'];
  }, [parseResult]);

  /* current logical step label */
  const currentStepLabel = steps[stepIndex];

  /* ---------- mapped cases ---------- */
  const mappedCases = useMemo(() => {
    if (!parseResult) return [];
    return parseResult.all_rows.map((row) => {
      const obj: Record<string, string> = {};
      mappings.forEach((m, i) => {
        if (m.target && row[i] !== undefined) {
          obj[m.target] = row[i];
        }
      });
      return obj;
    });
  }, [parseResult, mappings]);

  /* ---------- canNext ---------- */
  const canNext = useMemo(() => {
    if (currentStepLabel === '上传文件') return file !== null && format !== null && !uploading;
    if (currentStepLabel === '字段映射') {
      return REQUIRED_FIELDS.every((f) => mappings.some((m) => m.target === f));
    }
    if (currentStepLabel === '数据预览') return true;
    if (currentStepLabel === '重复检测') {
      return duplicates.every((d) => perCaseStrategies[d.index] !== undefined);
    }
    if (currentStepLabel === '确认导入') return true;
    return false;
  }, [currentStepLabel, file, format, uploading, mappings, duplicates, perCaseStrategies]);

  /* ---------- fetch folders on open ---------- */
  useEffect(() => {
    if (!open) return;
    api
      .get<FolderTreeNode[]>('/testcases/folders/tree')
      .then((tree) => {
        const flat = flattenFolderTree(tree);
        setFolderList(flat);
        const sys = flat.find((f) => f.is_system);
        if (sys) setFolderId(sys.id);
      })
      .catch(() => {
        /* silently ignore */
      });
  }, [open]);

  /* ---------- reset on close ---------- */
  const handleClose = useCallback(() => {
    setFile(null);
    setFormat(null);
    setUploading(false);
    setParseResult(null);
    setFolderId(null);
    setFolderList([]);
    setFolderOpen(false);
    setMappings([]);
    setDuplicates([]);
    setPerCaseStrategies({});
    setCheckingDuplicates(false);
    setImporting(false);
    setImportResult(null);
    setStepIndex(0);
    onClose();
  }, [onClose]);

  /* ---------- file selection ---------- */
  const handleFileSelect = useCallback((f: File) => {
    const fmt = detectFormat(f.name);
    setFile(f);
    setFormat(fmt);
  }, []);

  /* ---------- drag & drop ---------- */
  useEffect(() => {
    const el = dropRef.current;
    if (!el) return;
    const prevent = (e: DragEvent) => e.preventDefault();
    const drop = (e: DragEvent) => {
      e.preventDefault();
      const f = e.dataTransfer?.files[0];
      if (f) handleFileSelect(f);
    };
    el.addEventListener('dragover', prevent);
    el.addEventListener('drop', drop);
    return () => {
      el.removeEventListener('dragover', prevent);
      el.removeEventListener('drop', drop);
    };
  }, [handleFileSelect]);

  /* ---------- upload & parse ---------- */
  const handleUploadAndParse = useCallback(async () => {
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`${API_BASE}/testcases/import/parse-file`, {
        method: 'POST',
        body: fd,
      });
      if (!res.ok) throw new Error(await res.text());
      const result: ParseResult = await res.json();
      setParseResult(result);

      /* build mappings from auto_mapping */
      const cols = result.columns;
      const autoMap = result.auto_mapping;
      setMappings(cols.map((col) => ({ source: col, target: autoMap[col] ?? null })));

      /* jump: skip mapping if standard */
      setStepIndex(result.is_standard ? 1 : 1);
    } catch {
      toast.error('文件解析失败，请检查文件格式');
    } finally {
      setUploading(false);
    }
  }, [file]);

  /* ---------- check duplicates (auto on entering step) ---------- */
  const handleCheckDuplicates = useCallback(async () => {
    if (!parseResult) return;
    setCheckingDuplicates(true);
    try {
      const cases = mappedCases.map((c) => ({ title: c.title ?? '' }));
      const dups = await api.post<DuplicateInfo[]>('/testcases/import/check-duplicates', {
        cases,
        folder_id: folderId,
      });
      setDuplicates(dups);
      const init: Record<number, DuplicateStrategyType> = {};
      for (const d of dups) init[d.index] = 'skip';
      setPerCaseStrategies(init);
    } catch {
      toast.error('重复检测失败，请重试');
    } finally {
      setCheckingDuplicates(false);
    }
  }, [parseResult, mappedCases, folderId]);

  /* ---------- import ---------- */
  const handleImport = useCallback(async () => {
    setImporting(true);
    try {
      const result = await api.post<ImportResult>('/testcases/import/batch', {
        cases: mappedCases,
        folder_id: folderId,
        per_case_strategies: Object.fromEntries(
          Object.entries(perCaseStrategies).map(([k, v]) => [k, v]),
        ),
      });
      setImportResult(result);
      toast.success(
        `成功导入 ${result.imported + result.renamed} 条，跳过 ${result.skipped} 条，覆盖 ${result.overwritten} 条`,
      );
      onImportComplete();
      handleClose();
    } catch {
      toast.error('导入失败，请重试');
    } finally {
      setImporting(false);
    }
  }, [mappedCases, folderId, perCaseStrategies, onImportComplete, handleClose]);

  /* ---------- next step handler ---------- */
  const handleNext = useCallback(async () => {
    if (currentStepLabel === '上传文件') {
      await handleUploadAndParse();
      return;
    }
    if (currentStepLabel === '数据预览') {
      /* entering duplicate detection */
      setStepIndex((s) => s + 1);
      await handleCheckDuplicates();
      return;
    }
    if (currentStepLabel === '确认导入') {
      await handleImport();
      return;
    }
    setStepIndex((s) => s + 1);
  }, [currentStepLabel, handleUploadAndParse, handleCheckDuplicates, handleImport]);

  const handleBack = useCallback(() => {
    setStepIndex((s) => Math.max(0, s - 1));
  }, []);

  /* ---------- selected folder label ---------- */
  const selectedFolderName = useMemo(() => {
    if (!folderId) return '未选择';
    return folderList.find((f) => f.id === folderId)?.name ?? '未选择';
  }, [folderId, folderList]);

  if (!open) return null;

  /* ---------------------------------------------------------------- */
  /*  Render steps                                                     */
  /* ---------------------------------------------------------------- */

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* biome-ignore lint/a11y/useKeyWithClickEvents: backdrop overlay */}
      {/* biome-ignore lint/a11y/noStaticElementInteractions: backdrop overlay */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={handleClose} />
      <div className="relative z-10 flex h-[680px] w-[760px] flex-col rounded-xl border border-sy-border bg-sy-bg-1 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-sy-border px-6 py-4">
          <div>
            <h2 className="font-display text-base font-semibold text-sy-text">导入用例</h2>
            <p className="mt-0.5 text-[11px] text-sy-text-3">支持 Excel、CSV、XMind 格式</p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="rounded-lg p-1.5 text-sy-text-3 transition-colors hover:bg-sy-bg-2 hover:text-sy-text"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Step indicator */}
        <div className="flex items-center gap-0 border-b border-sy-border px-6 py-3">
          {steps.map((label, idx) => (
            <div key={label} className="flex items-center">
              <div className="flex items-center gap-2">
                <div
                  className={[
                    'flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-mono font-bold',
                    idx < stepIndex
                      ? 'bg-sy-accent text-sy-bg'
                      : idx === stepIndex
                        ? 'bg-sy-accent/20 text-sy-accent ring-1 ring-sy-accent'
                        : 'bg-sy-bg-3 text-sy-text-3',
                  ].join(' ')}
                >
                  {idx < stepIndex ? <Check className="h-2.5 w-2.5" /> : idx + 1}
                </div>
                <span
                  className={[
                    'text-[12px]',
                    idx === stepIndex ? 'font-medium text-sy-text' : 'text-sy-text-3',
                  ].join(' ')}
                >
                  {label}
                </span>
              </div>
              {idx < steps.length - 1 && <div className="mx-3 h-px w-8 bg-sy-border" />}
            </div>
          ))}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {currentStepLabel === '上传文件' && (
            <StepUpload
              file={file}
              format={format}
              uploading={uploading}
              folderId={folderId}
              folderList={folderList}
              folderOpen={folderOpen}
              selectedFolderName={selectedFolderName}
              onFolderToggle={() => setFolderOpen((v) => !v)}
              onFolderSelect={(id) => {
                setFolderId(id);
                setFolderOpen(false);
              }}
              fileInputRef={fileInputRef}
              dropRef={dropRef}
              onFileSelect={handleFileSelect}
            />
          )}
          {currentStepLabel === '字段映射' && parseResult && (
            <StepMapping
              columns={parseResult.columns}
              mappings={mappings}
              onMappingChange={(idx, target) =>
                setMappings((prev) => prev.map((m, i) => (i === idx ? { ...m, target } : m)))
              }
            />
          )}
          {currentStepLabel === '数据预览' && parseResult && (
            <StepPreview
              columns={parseResult.columns}
              previewRows={parseResult.preview_rows}
              mappings={mappings}
              totalRows={parseResult.total_rows}
            />
          )}
          {currentStepLabel === '重复检测' && (
            <StepDuplicates
              checking={checkingDuplicates}
              duplicates={duplicates}
              perCaseStrategies={perCaseStrategies}
              onStrategyChange={(index, strategy) =>
                setPerCaseStrategies((prev) => ({ ...prev, [index]: strategy }))
              }
            />
          )}
          {currentStepLabel === '确认导入' && parseResult && (
            <StepConfirm
              totalRows={parseResult.total_rows}
              duplicatesCount={duplicates.length}
              perCaseStrategies={perCaseStrategies}
              selectedFolderName={selectedFolderName}
              importing={importing}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-sy-border px-6 py-4">
          <button
            type="button"
            onClick={handleClose}
            className="text-[12.5px] text-sy-text-3 transition-colors hover:text-sy-text"
          >
            取消
          </button>
          <div className="flex items-center gap-2">
            {stepIndex > 0 && (
              <button
                type="button"
                onClick={handleBack}
                disabled={uploading || checkingDuplicates || importing}
                className="flex items-center gap-1.5 rounded-lg border border-sy-border px-3 py-1.5 text-[12.5px] text-sy-text-2 transition-colors hover:border-sy-border-2 hover:text-sy-text disabled:opacity-40"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                上一步
              </button>
            )}
            <button
              type="button"
              onClick={handleNext}
              disabled={!canNext || uploading || checkingDuplicates || importing}
              className="flex items-center gap-1.5 rounded-lg bg-sy-accent px-4 py-1.5 text-[12.5px] font-medium text-sy-bg transition-colors hover:bg-sy-accent-2 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {(uploading || checkingDuplicates || importing) && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              {currentStepLabel === '确认导入' ? '开始导入' : '下一步'}
              {!uploading && !checkingDuplicates && !importing && (
                <ArrowRight className="h-3.5 w-3.5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Step 0 — Upload                                                    */
/* ------------------------------------------------------------------ */

interface StepUploadProps {
  file: File | null;
  format: FileFormat;
  uploading: boolean;
  folderId: string | null;
  folderList: FlatFolder[];
  folderOpen: boolean;
  selectedFolderName: string;
  onFolderToggle: () => void;
  onFolderSelect: (id: string) => void;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  dropRef: React.RefObject<HTMLDivElement | null>;
  onFileSelect: (f: File) => void;
}

function StepUpload({
  file,
  format,
  uploading,
  folderId,
  folderList,
  folderOpen,
  selectedFolderName,
  onFolderToggle,
  onFolderSelect,
  fileInputRef,
  dropRef,
  onFileSelect,
}: StepUploadProps) {
  return (
    <div className="flex flex-col gap-5">
      {/* Template downloads */}
      <div className="rounded-lg border border-sy-border bg-sy-bg-2 px-4 py-3">
        <p className="mb-2.5 text-[11px] font-medium text-sy-text-3 uppercase tracking-wider">
          下载导入模板
        </p>
        <div className="flex items-center gap-3">
          <a
            href="/templates/用例导入模板.xlsx"
            download
            className="flex items-center gap-1.5 rounded-md border border-sy-border px-3 py-1.5 text-[12px] text-sy-text-2 transition-colors hover:border-sy-border-2 hover:text-sy-text"
          >
            <Download className="h-3.5 w-3.5 text-sy-info" />
            Excel 模板
          </a>
          <a
            href="/templates/用例导入模板.csv"
            download
            className="flex items-center gap-1.5 rounded-md border border-sy-border px-3 py-1.5 text-[12px] text-sy-text-2 transition-colors hover:border-sy-border-2 hover:text-sy-text"
          >
            <Download className="h-3.5 w-3.5 text-sy-accent" />
            CSV 模板
          </a>
          <a
            href="/templates/用例导入模板.xmind"
            download
            className="flex items-center gap-1.5 rounded-md border border-sy-border px-3 py-1.5 text-[12px] text-sy-text-2 transition-colors hover:border-sy-border-2 hover:text-sy-text"
          >
            <Download className="h-3.5 w-3.5 text-sy-purple" />
            XMind 模板
          </a>
        </div>
      </div>

      {/* Folder selector */}
      <div className="flex flex-col gap-1.5">
        <span className="text-[12px] font-medium text-sy-text-2">导入目标文件夹</span>
        <div className="relative">
          <button
            type="button"
            onClick={onFolderToggle}
            className="flex w-full items-center justify-between rounded-lg border border-sy-border bg-sy-bg-2 px-3 py-2 text-[12.5px] text-sy-text transition-colors hover:border-sy-border-2"
          >
            <span>{selectedFolderName}</span>
            <ChevronDown
              className={[
                'h-4 w-4 text-sy-text-3 transition-transform',
                folderOpen ? 'rotate-180' : '',
              ].join(' ')}
            />
          </button>
          {folderOpen && (
            <div className="absolute left-0 right-0 top-full z-20 mt-1 max-h-48 overflow-y-auto rounded-lg border border-sy-border bg-sy-bg-1 py-1 shadow-xl">
              {folderList.length === 0 ? (
                <div className="px-3 py-2 text-[12px] text-sy-text-3">暂无文件夹</div>
              ) : (
                folderList.map((folder) => (
                  <button
                    key={folder.id}
                    type="button"
                    onClick={() => onFolderSelect(folder.id)}
                    className={[
                      'flex w-full items-center gap-1.5 px-3 py-1.5 text-left text-[12.5px] transition-colors hover:bg-sy-bg-2',
                      folderId === folder.id ? 'text-sy-accent' : 'text-sy-text-2',
                    ].join(' ')}
                    style={{ paddingLeft: `${12 + folder.level * 16}px` }}
                  >
                    {folderId === folder.id && <Check className="h-3 w-3 shrink-0" />}
                    <span>{folder.name}</span>
                    {folder.is_system && (
                      <span className="ml-1 rounded-full bg-sy-bg-3 px-1.5 py-0.5 font-mono text-[10px] text-sy-text-3">
                        默认
                      </span>
                    )}
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Drop zone */}
      {/* biome-ignore lint/a11y/useKeyWithClickEvents: file drop zone */}
      {/* biome-ignore lint/a11y/noStaticElementInteractions: file drop zone */}
      <div
        ref={dropRef}
        onClick={() => fileInputRef.current?.click()}
        className={[
          'flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed py-10 transition-colors',
          file
            ? 'border-sy-accent/50 bg-sy-accent/5'
            : 'border-sy-border bg-sy-bg-2 hover:border-sy-border-2',
        ].join(' ')}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPT_EXTENSIONS}
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onFileSelect(f);
          }}
        />
        {file ? (
          <>
            <FileSpreadsheet className="h-10 w-10 text-sy-accent" />
            <div className="text-center">
              <p className="text-[13px] font-medium text-sy-text">{file.name}</p>
              <p className="mt-0.5 font-mono text-[11px] text-sy-text-3">
                {formatFileSize(file.size)} · {format?.toUpperCase()}
              </p>
            </div>
            <p className="text-[11px] text-sy-text-3">点击重新选择</p>
          </>
        ) : (
          <>
            <Upload className="h-10 w-10 text-sy-text-3" />
            <div className="text-center">
              <p className="text-[13px] font-medium text-sy-text">拖放文件或点击选择</p>
              <p className="mt-0.5 text-[11px] text-sy-text-3">
                支持 .xlsx .csv .xmind 格式，最大 10 MB
              </p>
            </div>
          </>
        )}
      </div>

      {uploading && (
        <div className="flex items-center gap-2 text-[12.5px] text-sy-text-2">
          <Loader2 className="h-4 w-4 animate-spin text-sy-accent" />
          正在解析文件，请稍候…
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Step 1 — Field Mapping                                             */
/* ------------------------------------------------------------------ */

interface StepMappingProps {
  columns: string[];
  mappings: ColumnMapping[];
  onMappingChange: (idx: number, target: string | null) => void;
}

function StepMapping({ columns, mappings, onMappingChange }: StepMappingProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border border-sy-warn/30 bg-sy-warn/5 px-4 py-3">
        <div className="flex items-start gap-2">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-sy-warn" />
          <p className="text-[12.5px] text-sy-warn">
            未识别为标准格式。请手动映射列名到字段，标题、测试步骤、预期结果为必填项。
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-sy-border overflow-hidden">
        <table className="w-full text-[12.5px]">
          <thead>
            <tr className="border-b border-sy-border bg-sy-bg-2">
              <th className="px-4 py-2.5 text-left font-medium text-sy-text-2">文件列名</th>
              <th className="px-4 py-2.5 text-left font-medium text-sy-text-2">映射到字段</th>
              <th className="px-4 py-2.5 text-left font-medium text-sy-text-2">状态</th>
            </tr>
          </thead>
          <tbody>
            {columns.map((col, idx) => {
              const mapping = mappings[idx];
              const isRequired = mapping?.target && REQUIRED_FIELDS.includes(mapping.target);
              return (
                <tr key={col} className="border-b border-sy-border last:border-0">
                  <td className="px-4 py-2.5 font-mono text-sy-text">{col}</td>
                  <td className="px-4 py-2.5">
                    <select
                      value={mapping?.target ?? ''}
                      onChange={(e) => onMappingChange(idx, e.target.value || null)}
                      className="w-full rounded-md border border-sy-border bg-sy-bg-2 px-2 py-1 text-[12px] text-sy-text focus:border-sy-accent focus:outline-none"
                    >
                      <option value="">— 忽略此列 —</option>
                      {TARGET_FIELDS.map((f) => (
                        <option key={f.value} value={f.value}>
                          {f.label}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-2.5">
                    {mapping?.target ? (
                      <span
                        className={[
                          'inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-mono text-[10px]',
                          isRequired
                            ? 'bg-sy-accent/10 text-sy-accent'
                            : 'bg-sy-bg-3 text-sy-text-3',
                        ].join(' ')}
                      >
                        {isRequired && <Check className="h-2.5 w-2.5" />}
                        {isRequired ? '必填' : '可选'}
                      </span>
                    ) : (
                      <span className="font-mono text-[10px] text-sy-text-3">忽略</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Step 2 — Preview                                                   */
/* ------------------------------------------------------------------ */

interface StepPreviewProps {
  columns: string[];
  previewRows: string[][];
  mappings: ColumnMapping[];
  totalRows: number;
}

function StepPreview({ columns, previewRows, mappings, totalRows }: StepPreviewProps) {
  /* Only show columns that are mapped */
  const visibleCols = columns
    .map((col, i) => ({ col, target: mappings[i]?.target }))
    .filter((c) => c.target);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-[12.5px] text-sy-text-2">
          共 <span className="font-mono font-semibold text-sy-text">{totalRows}</span>{' '}
          条数据，下方显示前{' '}
          <span className="font-mono font-semibold text-sy-text">{previewRows.length}</span> 条预览
        </p>
      </div>

      <div className="overflow-x-auto rounded-lg border border-sy-border">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-sy-border bg-sy-bg-2">
              <th className="px-3 py-2 text-left font-mono font-medium text-sy-text-3">#</th>
              {visibleCols.map(({ col, target }) => (
                <th key={col} className="px-3 py-2 text-left font-medium text-sy-text-2">
                  <div>{col}</div>
                  <div className="font-mono text-[10px] text-sy-accent">
                    → {TARGET_FIELDS.find((f) => f.value === target)?.label}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {previewRows.map((row, ri) => (
              // biome-ignore lint/suspicious/noArrayIndexKey: preview rows are stable
              <tr key={ri} className="border-b border-sy-border last:border-0 hover:bg-sy-bg-2/50">
                <td className="px-3 py-2 font-mono text-sy-text-3">{ri + 1}</td>
                {visibleCols.map(({ col }, _ci) => {
                  const colIdx = columns.indexOf(col);
                  return (
                    <td key={col} className="max-w-[180px] truncate px-3 py-2 text-sy-text">
                      {row[colIdx] ?? ''}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Step 3 — Duplicates                                               */
/* ------------------------------------------------------------------ */

interface StepDuplicatesProps {
  checking: boolean;
  duplicates: DuplicateInfo[];
  perCaseStrategies: Record<number, DuplicateStrategyType>;
  onStrategyChange: (index: number, strategy: DuplicateStrategyType) => void;
}

function StepDuplicates({
  checking,
  duplicates,
  perCaseStrategies,
  onStrategyChange,
}: StepDuplicatesProps) {
  if (checking) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20">
        <Loader2 className="h-8 w-8 animate-spin text-sy-accent" />
        <p className="text-[12.5px] text-sy-text-2">正在检测重复用例…</p>
      </div>
    );
  }

  if (duplicates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-sy-accent/10">
          <Check className="h-6 w-6 text-sy-accent" />
        </div>
        <p className="text-[13px] font-medium text-sy-text">未发现重复用例</p>
        <p className="text-[12px] text-sy-text-3">所有用例均为新增，可直接导入</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border border-sy-warn/30 bg-sy-warn/5 px-4 py-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 text-sy-warn" />
          <p className="text-[12.5px] text-sy-warn">
            发现 <span className="font-semibold">{duplicates.length}</span>{' '}
            条重复用例，请为每条选择处理策略后方可继续
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        {duplicates.map((dup) => {
          const strategy = perCaseStrategies[dup.index];
          return (
            <div
              key={dup.index}
              className="rounded-lg border border-sy-border bg-sy-bg-2 px-4 py-3"
            >
              <div className="mb-2.5 flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-[12.5px] font-medium text-sy-text">{dup.title}</p>
                  <p className="mt-0.5 font-mono text-[10px] text-sy-text-3">
                    已存在 ID: {dup.existing_case_id}
                  </p>
                </div>
                <span className="shrink-0 rounded-full bg-sy-warn/10 px-2 py-0.5 font-mono text-[10px] text-sy-warn">
                  第 {dup.index + 1} 行
                </span>
              </div>
              <div className="flex items-center gap-2">
                {(['overwrite', 'skip', 'rename'] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => onStrategyChange(dup.index, s)}
                    className={[
                      'rounded-md px-3 py-1 text-[11.5px] font-medium transition-colors',
                      strategy === s
                        ? s === 'overwrite'
                          ? 'bg-sy-danger/15 text-sy-danger ring-1 ring-sy-danger/40'
                          : s === 'rename'
                            ? 'bg-sy-accent/15 text-sy-accent ring-1 ring-sy-accent/40'
                            : 'bg-sy-bg-3 text-sy-text ring-1 ring-sy-border-2'
                        : 'bg-sy-bg-3 text-sy-text-3 hover:text-sy-text-2',
                    ].join(' ')}
                  >
                    {s === 'overwrite' ? '覆盖' : s === 'skip' ? '跳过' : '重命名'}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Step 4 — Confirm                                                   */
/* ------------------------------------------------------------------ */

interface StepConfirmProps {
  totalRows: number;
  duplicatesCount: number;
  perCaseStrategies: Record<number, DuplicateStrategyType>;
  selectedFolderName: string;
  importing: boolean;
}

function StepConfirm({
  totalRows,
  duplicatesCount,
  perCaseStrategies,
  selectedFolderName,
  importing,
}: StepConfirmProps) {
  const overwriteCount = Object.values(perCaseStrategies).filter((s) => s === 'overwrite').length;
  const skipCount = Object.values(perCaseStrategies).filter((s) => s === 'skip').length;
  const renameCount = Object.values(perCaseStrategies).filter((s) => s === 'rename').length;
  const newCount = totalRows - duplicatesCount;

  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-lg border border-sy-accent/30 bg-sy-accent/5 px-4 py-3">
        <div className="flex items-center gap-2">
          <Check className="h-4 w-4 shrink-0 text-sy-accent" />
          <p className="text-[12.5px] text-sy-accent font-medium">已就绪，确认后开始导入</p>
        </div>
      </div>

      <div className="rounded-lg border border-sy-border overflow-hidden">
        <table className="w-full text-[12.5px]">
          <tbody>
            {[
              { label: '目标文件夹', value: selectedFolderName },
              { label: '总数据量', value: `${totalRows} 条` },
              { label: '新增导入', value: `${newCount} 条`, accent: true },
              ...(duplicatesCount > 0
                ? [
                    { label: '覆盖', value: `${overwriteCount} 条` },
                    { label: '跳过', value: `${skipCount} 条` },
                    { label: '重命名导入', value: `${renameCount} 条` },
                  ]
                : []),
            ].map(({ label, value, accent }) => (
              <tr key={label} className="border-b border-sy-border last:border-0">
                <td className="w-40 bg-sy-bg-2 px-4 py-2.5 text-sy-text-2">{label}</td>
                <td
                  className={[
                    'px-4 py-2.5 font-mono',
                    accent ? 'text-sy-accent font-semibold' : 'text-sy-text',
                  ].join(' ')}
                >
                  {value}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {importing && (
        <div className="flex items-center gap-2 text-[12.5px] text-sy-text-2">
          <Loader2 className="h-4 w-4 animate-spin text-sy-accent" />
          正在导入，请勿关闭窗口…
        </div>
      )}
    </div>
  );
}
