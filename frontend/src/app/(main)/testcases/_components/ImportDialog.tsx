'use client';

import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Check,
  FileJson,
  FileSpreadsheet,
  Loader2,
  Table2,
  Upload,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface ImportDialogProps {
  open: boolean;
  onClose: () => void;
  onImportComplete: () => void;
}

type FileFormat = 'xlsx' | 'csv' | 'xmind' | 'json' | null;
type DuplicateStrategy = 'skip' | 'overwrite' | 'new';

interface ColumnMapping {
  source: string;
  target: string | null;
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

const STEPS = ['上传文件', '字段映射', '数据预览', '重复检测', '确认导入'] as const;

const ACCEPT_EXTENSIONS = '.xlsx,.csv,.xmind,.json';

/* Auto-mapping rules: source column name → target field */
const AUTO_MAP: Record<string, string> = {
  用例标题: 'title',
  标题: 'title',
  title: 'title',
  name: 'title',
  前置条件: 'precondition',
  precondition: 'precondition',
  测试步骤: 'steps',
  操作步骤: 'steps',
  steps: 'steps',
  预期结果: 'expected_result',
  expected_result: 'expected_result',
  expected: 'expected_result',
  优先级: 'priority',
  priority: 'priority',
  用例类型: 'case_type',
  type: 'case_type',
  case_type: 'case_type',
  模块: 'module_path',
  所属模块: 'module_path',
  module: 'module_path',
  module_path: 'module_path',
};

/* ------------------------------------------------------------------ */
/*  Mock helpers                                                       */
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

const MOCK_COLUMNS = [
  '用例标题',
  '前置条件',
  '测试步骤',
  '预期结果',
  '优先级',
  '用例类型',
  '所属模块',
];

const MOCK_ROWS = [
  [
    '登录 - 正常账号密码',
    '用户已注册',
    '输入账号和密码，点击登录',
    '登录成功，跳转首页',
    'P0',
    '功能测试',
    '用户管理/登录',
  ],
  [
    '登录 - 密码错误',
    '用户已注册',
    '输入账号，输入错误密码，点击登录',
    '提示密码错误',
    'P0',
    '功能测试',
    '用户管理/登录',
  ],
  [
    '登录 - 账号不存在',
    '无',
    '输入未注册账号，点击登录',
    '提示账号不存在',
    'P1',
    '功能测试',
    '用户管理/登录',
  ],
  [
    '登录 - 验证码过期',
    '已发送验证码',
    '等待 60s 后输入验证码',
    '提示验证码已过期',
    'P1',
    '异常测试',
    '用户管理/登录',
  ],
  [
    '登录 - 连续失败锁定',
    '无',
    '连续输入 5 次错误密码',
    '账号锁定 15 分钟',
    'P2',
    '安全测试',
    '用户管理/登录',
  ],
];

const MOCK_TOTAL = 42;
const MOCK_DUPLICATES = 3;

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */

function FormatIcon({ format, className }: { format: FileFormat; className?: string }) {
  const cls = className ?? 'w-5 h-5';
  switch (format) {
    case 'xlsx':
      return <FileSpreadsheet className={`${cls} text-sy-accent`} />;
    case 'csv':
      return <Table2 className={`${cls} text-sy-info`} />;
    case 'json':
      return <FileJson className={`${cls} text-sy-warn`} />;
    case 'xmind':
      return <FileSpreadsheet className={`${cls} text-sy-purple`} />;
    default:
      return <Upload className={`${cls} text-sy-text-3`} />;
  }
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

export function ImportDialog({ open, onClose, onImportComplete }: ImportDialogProps) {
  const [step, setStep] = useState(0);
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState<FileFormat>(null);
  const [mappings, setMappings] = useState<ColumnMapping[]>([]);
  const [duplicateStrategy, setDuplicateStrategy] = useState<DuplicateStrategy>('skip');
  const [importing, setImporting] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  /* Reset state when dialog closes */
  useEffect(() => {
    if (!open) {
      setStep(0);
      setFile(null);
      setFormat(null);
      setMappings([]);
      setDuplicateStrategy('skip');
      setImporting(false);
      setDragOver(false);
    }
  }, [open]);

  /* ---- File handling ---- */

  const handleFile = useCallback((f: File) => {
    const detected = detectFormat(f.name);
    setFile(f);
    setFormat(detected);

    // Build initial mappings with auto-map
    const cols = MOCK_COLUMNS; // In reality, parsed from file
    const initialMappings: ColumnMapping[] = cols.map((col) => ({
      source: col,
      target: AUTO_MAP[col] ?? AUTO_MAP[col.toLowerCase()] ?? null,
    }));
    setMappings(initialMappings);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) handleFile(droppedFile);
    },
    [handleFile],
  );

  const onFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = e.target.files?.[0];
      if (selected) handleFile(selected);
    },
    [handleFile],
  );

  /* ---- Mapping helpers ---- */

  const updateMapping = useCallback((index: number, target: string | null) => {
    setMappings((prev) => prev.map((m, i) => (i === index ? { ...m, target } : m)));
  }, []);

  const mappedCount = useMemo(() => mappings.filter((m) => m.target).length, [mappings]);

  /* ---- Preview data ---- */

  const previewRows = useMemo(() => {
    return MOCK_ROWS.map((row) => {
      const mapped: Record<string, string> = {};
      mappings.forEach((m, idx) => {
        if (m.target && row[idx] !== undefined) {
          mapped[m.target] = row[idx];
        }
      });
      return mapped;
    });
  }, [mappings]);

  /* ---- Import action ---- */

  const handleImport = useCallback(() => {
    setImporting(true);
    setTimeout(() => {
      setImporting(false);
      onImportComplete();
      onClose();
    }, 1500);
  }, [onImportComplete, onClose]);

  /* ---- Navigation ---- */

  const canNext = useMemo(() => {
    switch (step) {
      case 0:
        return file !== null && format !== null;
      case 1:
        return mappedCount >= 1;
      case 2:
      case 3:
        return true;
      default:
        return false;
    }
  }, [step, file, format, mappedCount]);

  if (!open) return null;

  /* ---------------------------------------------------------------- */
  /*  Step renderers                                                    */
  /* ---------------------------------------------------------------- */

  const renderStepUpload = () => (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        className={`flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-10 cursor-pointer transition-colors ${
          dragOver
            ? 'border-sy-accent bg-sy-accent/5'
            : 'border-sy-border-2 hover:border-sy-accent/50 hover:bg-sy-bg-2'
        }`}
      >
        <Upload className="w-8 h-8 text-sy-text-3" />
        <p className="text-[12.5px] text-sy-text-2">
          拖拽文件到此处，或 <span className="text-sy-accent font-medium">点击选择文件</span>
        </p>
        <p className="text-[11px] text-sy-text-3">支持 Excel (.xlsx)、CSV、XMind、JSON 格式</p>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPT_EXTENSIONS}
          className="hidden"
          onChange={onFileChange}
        />
      </div>

      {/* Format badges */}
      <div className="flex items-center justify-center gap-4">
        {(
          [
            { fmt: 'xlsx' as const, label: 'Excel' },
            { fmt: 'csv' as const, label: 'CSV' },
            { fmt: 'xmind' as const, label: 'XMind' },
            { fmt: 'json' as const, label: 'JSON' },
          ] as const
        ).map(({ fmt, label }) => (
          <div
            key={fmt}
            className="flex items-center gap-1.5 rounded-full bg-sy-bg-3 px-3 py-1 text-[11px] text-sy-text-3"
          >
            <FormatIcon format={fmt} className="w-3.5 h-3.5" />
            {label}
          </div>
        ))}
      </div>

      {/* Selected file info */}
      {file && (
        <div className="flex items-center gap-3 rounded-lg border border-sy-border bg-sy-bg-2 px-4 py-3">
          <FormatIcon format={format} />
          <div className="flex-1 min-w-0">
            <p className="text-[12.5px] text-sy-text font-medium truncate">{file.name}</p>
            <p className="text-[11px] text-sy-text-3">
              {formatFileSize(file.size)} · 格式：{format?.toUpperCase() ?? '未知'}
            </p>
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setFile(null);
              setFormat(null);
              setMappings([]);
            }}
            className="p-1 rounded hover:bg-sy-bg-3 text-sy-text-3 hover:text-sy-text transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );

  const renderStepMapping = () => (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-[11.5px] text-sy-text-3 uppercase tracking-wider font-semibold">
          字段映射
        </p>
        <p className="text-[11px] text-sy-text-3">
          已映射 <span className="text-sy-accent font-medium">{mappedCount}</span> /{' '}
          {mappings.length}
        </p>
      </div>

      <div className="rounded-lg border border-sy-border overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-[1fr_32px_1fr] items-center gap-2 bg-sy-bg-3 px-4 py-2 text-[11px] text-sy-text-3 uppercase tracking-wider font-semibold">
          <span>检测到的列</span>
          <span />
          <span>目标字段</span>
        </div>

        {/* Rows */}
        {mappings.map((m, idx) => (
          <div
            key={m.source}
            className="grid grid-cols-[1fr_32px_1fr] items-center gap-2 px-4 py-2.5 border-t border-sy-border"
          >
            <span className="text-[12.5px] text-sy-text truncate">{m.source}</span>
            <ArrowRight className="w-3.5 h-3.5 text-sy-text-3 mx-auto" />
            <select
              value={m.target ?? ''}
              onChange={(e) => updateMapping(idx, e.target.value || null)}
              className="w-full px-2.5 py-1.5 text-[12.5px] bg-sy-bg-2 border border-sy-border rounded-md text-sy-text outline-none focus:border-sy-accent transition-colors appearance-none cursor-pointer"
            >
              <option value="">— 不映射 —</option>
              {TARGET_FIELDS.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
    </div>
  );

  const renderStepPreview = () => {
    const targetCols = mappings.filter((m) => m.target);

    return (
      <div className="space-y-3">
        <p className="text-[11.5px] text-sy-text-3 uppercase tracking-wider font-semibold">
          前 5 条数据预览
        </p>

        <div className="rounded-lg border border-sy-border overflow-x-auto">
          <table className="w-full text-[12px]">
            <thead>
              <tr className="bg-sy-bg-3">
                {targetCols.map((m) => (
                  <th
                    key={m.target}
                    className="px-3 py-2 text-left text-[11px] text-sy-text-3 uppercase tracking-wider font-semibold whitespace-nowrap"
                  >
                    {TARGET_FIELDS.find((f) => f.value === m.target)?.label ?? m.target}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {previewRows.map((row) => {
                const rowKey = Object.values(row).join('|');
                return (
                <tr key={rowKey} className="border-t border-sy-border">
                  {targetCols.map((m) => {
                    const val = m.target ? row[m.target] : '';
                    const missing = !val;
                    return (
                      <td
                        key={m.target}
                        className={`px-3 py-2 text-sy-text whitespace-nowrap max-w-[180px] truncate ${
                          missing ? 'bg-sy-warn/8 text-sy-warn' : ''
                        }`}
                      >
                        {val || '—'}
                      </td>
                    );
                  })}
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <p className="text-[11px] text-sy-text-3">
          共检测到 <span className="text-sy-text font-medium">{MOCK_TOTAL}</span> 条用例数据
          {previewRows.some((r) => Object.values(r).some((v) => !v)) && (
            <span className="ml-2 text-sy-warn">
              <AlertTriangle className="w-3 h-3 inline -mt-px mr-0.5" />
              部分字段为空，请检查映射
            </span>
          )}
        </p>
      </div>
    );
  };

  const renderStepDuplicates = () => (
    <div className="space-y-4">
      <div className="flex items-start gap-3 rounded-lg border border-sy-warn/30 bg-sy-warn/5 px-4 py-3">
        <AlertTriangle className="w-4 h-4 text-sy-warn mt-0.5 shrink-0" />
        <div>
          <p className="text-[12.5px] text-sy-text font-medium">
            检测到 {MOCK_DUPLICATES} 条潜在重复用例
          </p>
          <p className="text-[11px] text-sy-text-3 mt-1">
            基于用例标题匹配，发现已有用例与导入数据存在重复
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-[11.5px] text-sy-text-3 uppercase tracking-wider font-semibold">
          重复处理策略
        </p>

        {(
          [
            { value: 'skip' as const, label: '跳过重复', desc: '保留已有用例，不导入重复项' },
            {
              value: 'overwrite' as const,
              label: '覆盖已有',
              desc: '用导入数据替换已有的重复用例',
            },
            {
              value: 'new' as const,
              label: '全部导入',
              desc: '将重复项作为新用例导入，不做去重',
            },
          ] as const
        ).map((opt) => (
          <label
            key={opt.value}
            className={`flex items-start gap-3 rounded-lg border px-4 py-3 cursor-pointer transition-colors ${
              duplicateStrategy === opt.value
                ? 'border-sy-accent bg-sy-accent/5'
                : 'border-sy-border hover:border-sy-border-2'
            }`}
          >
            <input
              type="radio"
              name="duplicateStrategy"
              value={opt.value}
              checked={duplicateStrategy === opt.value}
              onChange={() => setDuplicateStrategy(opt.value)}
              className="mt-0.5 accent-[var(--accent)]"
            />
            <div>
              <p className="text-[12.5px] text-sy-text font-medium">{opt.label}</p>
              <p className="text-[11px] text-sy-text-3 mt-0.5">{opt.desc}</p>
            </div>
          </label>
        ))}
      </div>
    </div>
  );

  const renderStepConfirm = () => {
    const importCount = duplicateStrategy === 'skip' ? MOCK_TOTAL - MOCK_DUPLICATES : MOCK_TOTAL;

    return (
      <div className="space-y-4">
        <div className="rounded-lg border border-sy-border bg-sy-bg-2 divide-y divide-sy-border">
          {[
            { label: '文件', value: file?.name ?? '—' },
            { label: '格式', value: format?.toUpperCase() ?? '—' },
            { label: '已映射字段', value: `${mappedCount} / ${mappings.length}` },
            { label: '总用例数', value: String(MOCK_TOTAL) },
            {
              label: '重复用例',
              value: `${MOCK_DUPLICATES} 条（${
                duplicateStrategy === 'skip'
                  ? '跳过'
                  : duplicateStrategy === 'overwrite'
                    ? '覆盖'
                    : '全部导入'
              }）`,
            },
            { label: '实际导入', value: `${importCount} 条`, highlight: true },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between px-4 py-2.5">
              <span className="text-[11.5px] text-sy-text-3">{item.label}</span>
              <span
                className={`text-[12.5px] font-medium ${
                  'highlight' in item && item.highlight ? 'text-sy-accent' : 'text-sy-text'
                }`}
              >
                {item.value}
              </span>
            </div>
          ))}
        </div>

        <div className="flex items-start gap-3 rounded-lg border border-sy-info/30 bg-sy-info/5 px-4 py-3">
          <Check className="w-4 h-4 text-sy-info mt-0.5 shrink-0" />
          <p className="text-[12px] text-sy-text-2">
            导入后用例将进入「待评审」状态，可在用例管理中心查看和编辑
          </p>
        </div>
      </div>
    );
  };

  const stepRenderers = [
    renderStepUpload,
    renderStepMapping,
    renderStepPreview,
    renderStepDuplicates,
    renderStepConfirm,
  ];

  /* ---------------------------------------------------------------- */
  /*  Render                                                            */
  /* ---------------------------------------------------------------- */

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div
        role="presentation"
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
        onKeyDown={(e) => {
          if (e.key === 'Escape') onClose();
        }}
      />

      {/* Panel */}
      <div className="relative bg-sy-bg-1 border border-sy-border rounded-xl shadow-lg w-full max-w-2xl mx-4 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-sy-border shrink-0">
          <h2 className="text-[14px] font-semibold text-sy-text">导入测试用例</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded hover:bg-sy-bg-3 text-sy-text-3 hover:text-sy-text transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-1 px-5 py-3 border-b border-sy-border shrink-0">
          {STEPS.map((label, idx) => (
            <div key={label} className="flex items-center gap-1">
              <button
                type="button"
                disabled={idx > step}
                onClick={() => idx < step && setStep(idx)}
                className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors ${
                  idx === step
                    ? 'bg-sy-accent/10 text-sy-accent'
                    : idx < step
                      ? 'bg-sy-bg-3 text-sy-text-2 hover:text-sy-text cursor-pointer'
                      : 'text-sy-text-3'
                }`}
              >
                <span
                  className={`flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-semibold ${
                    idx === step
                      ? 'bg-sy-accent text-white'
                      : idx < step
                        ? 'bg-sy-text-3 text-sy-bg-1'
                        : 'bg-sy-bg-3 text-sy-text-3'
                  }`}
                >
                  {idx < step ? <Check className="w-2.5 h-2.5" /> : idx + 1}
                </span>
                <span className="hidden sm:inline">{label}</span>
              </button>
              {idx < STEPS.length - 1 && (
                <div className={`w-4 h-px ${idx < step ? 'bg-sy-accent/40' : 'bg-sy-border-2'}`} />
              )}
            </div>
          ))}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4">{stepRenderers[step]()}</div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-sy-border shrink-0">
          <div>
            {step > 0 && (
              <button
                type="button"
                onClick={() => setStep((s) => s - 1)}
                className="flex items-center gap-1.5 bg-sy-bg-2 text-sy-text-2 hover:text-sy-text hover:bg-sy-bg-3 rounded-md px-4 py-2 text-[12.5px] transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                上一步
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="bg-sy-bg-2 text-sy-text-2 hover:text-sy-text hover:bg-sy-bg-3 rounded-md px-4 py-2 text-[12.5px] transition-colors"
            >
              取消
            </button>

            {step < STEPS.length - 1 ? (
              <button
                type="button"
                disabled={!canNext}
                onClick={() => setStep((s) => s + 1)}
                className="flex items-center gap-1.5 bg-sy-accent text-white dark:text-black hover:bg-sy-accent-2 rounded-md px-4 py-2 text-[12.5px] font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                下一步
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="button"
                disabled={importing}
                onClick={handleImport}
                className="flex items-center gap-1.5 bg-sy-accent text-white dark:text-black hover:bg-sy-accent-2 rounded-md px-4 py-2 text-[12.5px] font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {importing ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    导入中...
                  </>
                ) : (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    确认导入
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
