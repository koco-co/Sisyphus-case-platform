'use client';

import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Circle,
  Loader2,
  X,
  XCircle,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

interface Task {
  id: string;
  name: string;
  status: 'done' | 'in_progress' | 'partial' | 'pending' | 'failed';
  type?: string;
}

interface Module {
  id: string;
  name: string;
  status: 'done' | 'in_progress' | 'partial' | 'pending' | 'failed';
  tasks?: Task[];
}

interface Phase {
  id: string;
  name: string;
  status: string;
  modules: Module[];
}

interface ProgressData {
  version: string;
  lastUpdated: string;
  phases: Phase[];
}

const STATUS_CFG = {
  done: { icon: CheckCircle2, color: 'var(--accent)', pill: 'pill pill-green', label: '已完成' },
  in_progress: { icon: Loader2, color: 'var(--blue)', pill: 'pill pill-blue', label: '进行中' },
  partial: { icon: AlertCircle, color: 'var(--amber)', pill: 'pill pill-amber', label: '部分完成' },
  pending: { icon: Circle, color: 'var(--text3)', pill: 'pill pill-gray', label: '待开始' },
  failed: { icon: XCircle, color: 'var(--red)', pill: 'pill pill-red', label: '失败' },
} as const;

type StatusKey = keyof typeof STATUS_CFG;

function StatusIcon({ status, size = 13 }: { status: string; size?: number }) {
  const cfg = STATUS_CFG[status as StatusKey] ?? STATUS_CFG.pending;
  const Icon = cfg.icon;
  return (
    <Icon
      size={size}
      style={{ color: cfg.color, flexShrink: 0 }}
      className={status === 'in_progress' ? 'animate-spin' : undefined}
    />
  );
}

function deriveModuleStatus(mod: Module): StatusKey {
  const tasks = mod.tasks ?? [];
  if (!tasks.length) return mod.status as StatusKey;
  const allDone = tasks.every((t) => t.status === 'done');
  if (allDone) return 'done';
  const anyActive = tasks.some((t) => t.status === 'in_progress' || t.status === 'done');
  if (anyActive) return 'in_progress';
  return 'pending';
}

function getProgress(items: { status: string }[]): number {
  if (!items.length) return 0;
  const done = items.filter((m) => m.status === 'done').length;
  const partial = items.filter((m) => m.status === 'partial' || m.status === 'in_progress').length;
  return Math.round(((done + partial * 0.5) / items.length) * 100);
}

function getPhaseProgress(phase: Phase): number {
  if (!phase.modules.length) return 0;
  const statuses = phase.modules.map((m) => deriveModuleStatus(m));
  const done = statuses.filter((s) => s === 'done').length;
  const partial = statuses.filter((s) => s === 'in_progress' || s === 'partial').length;
  return Math.round(((done + partial * 0.5) / statuses.length) * 100);
}

function ModuleRow({ mod }: { mod: Module }) {
  const [expanded, setExpanded] = useState(false);
  const hasTasks = (mod.tasks?.length ?? 0) > 0;
  const taskProgress = hasTasks && mod.tasks ? getProgress(mod.tasks) : 0;
  const derivedStatus = deriveModuleStatus(mod);
  const cfg = STATUS_CFG[derivedStatus] ?? STATUS_CFG.pending;

  return (
    <div>
      <button
        type="button"
        onClick={() => hasTasks && setExpanded((v) => !v)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 7,
          width: '100%',
          padding: '5px 0',
          background: 'none',
          border: 'none',
          cursor: hasTasks ? 'pointer' : 'default',
          textAlign: 'left',
        }}
      >
        {hasTasks ? (
          expanded ? (
            <ChevronDown size={12} style={{ color: 'var(--text3)', flexShrink: 0 }} />
          ) : (
            <ChevronRight size={12} style={{ color: 'var(--text3)', flexShrink: 0 }} />
          )
        ) : (
          <span style={{ width: 12 }} />
        )}
        <StatusIcon status={derivedStatus} />
        <span style={{ flex: 1, fontSize: 12.5 }}>
          <span className="mono" style={{ color: 'var(--text3)', marginRight: 5, fontSize: 11 }}>
            {mod.id}
          </span>
          {mod.name}
        </span>
        {hasTasks && (
          <span className="mono" style={{ fontSize: 10, color: 'var(--text3)' }}>
            {taskProgress}%
          </span>
        )}
        <span className={cfg.pill} style={{ fontSize: 10, padding: '1px 5px' }}>
          {cfg.label}
        </span>
      </button>

      {expanded && hasTasks && (
        <div
          style={{
            paddingLeft: 26,
            borderLeft: '1px solid var(--border)',
            marginLeft: 6,
            marginBottom: 4,
          }}
        >
          {mod.tasks?.map((task) => {
            const tc = STATUS_CFG[task.status as StatusKey] ?? STATUS_CFG.pending;
            return (
              <div
                key={task.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '3px 0',
                  fontSize: 11.5,
                }}
              >
                <StatusIcon status={task.status} size={11} />
                <span style={{ flex: 1, color: 'var(--text2)' }}>{task.name}</span>
                {task.type && (
                  <span
                    className="mono"
                    style={{
                      fontSize: 9.5,
                      color: 'var(--text3)',
                      background: 'var(--bg3)',
                      padding: '1px 4px',
                      borderRadius: 4,
                    }}
                  >
                    {task.type}
                  </span>
                )}
                <span className={tc.pill} style={{ fontSize: 9.5, padding: '0px 4px' }}>
                  {tc.label}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function PhaseSection({ phase }: { phase: Phase }) {
  const [expanded, setExpanded] = useState(phase.status === 'in_progress');
  const progress = getPhaseProgress(phase);

  return (
    <div className="card" style={{ marginBottom: 10, padding: '10px 12px' }}>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          width: '100%',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
          padding: 0,
        }}
      >
        {expanded ? (
          <ChevronDown size={14} style={{ color: 'var(--text3)', flexShrink: 0 }} />
        ) : (
          <ChevronRight size={14} style={{ color: 'var(--text3)', flexShrink: 0 }} />
        )}
        <StatusIcon status={phase.status} size={14} />
        <span style={{ flex: 1, fontWeight: 600, fontSize: 12.5 }}>{phase.name}</span>
        <span className="mono" style={{ fontSize: 11, color: 'var(--accent)', fontWeight: 600 }}>
          {progress}%
        </span>
      </button>

      {expanded && (
        <div style={{ marginTop: 8 }}>
          <div className="progress-bar" style={{ marginBottom: 10 }}>
            <div
              className={`progress-fill ${progress < 40 ? 'red' : progress < 80 ? 'amber' : ''}`}
              style={{ width: `${progress}%` }}
            />
          </div>
          {phase.modules.map((mod) => (
            <ModuleRow key={mod.id} mod={mod} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProgressDashboard() {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const fetchProgress = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/progress');
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (e) {
      console.warn('Failed to fetch progress:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      fetchProgress();
      const interval = setInterval(fetchProgress, 30000);
      return () => clearInterval(interval);
    }
  }, [open, fetchProgress]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const allModules = data?.phases.flatMap((p) => p.modules) ?? [];
  const derivedStatuses = allModules.map((m) => deriveModuleStatus(m));
  const doneCount = derivedStatuses.filter((s) => s === 'done').length;
  const failedCount = derivedStatuses.filter((s) => s === 'failed').length;
  const partialCount = derivedStatuses.filter((s) => s === 'in_progress' || s === 'partial').length;
  const overall = allModules.length
    ? Math.round(((doneCount + partialCount * 0.5) / allModules.length) * 100)
    : 0;

  return (
    <>
      {/* Floating Action Button */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="progress-fab"
        title="测试进度大盘"
        aria-label="打开测试进度大盘"
      >
        <Activity size={22} />
      </button>

      {/* Backdrop */}
      {open && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.4)',
            zIndex: 1001,
          }}
        />
      )}

      {/* Slide-in Panel */}
      <div
        ref={panelRef}
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: 440,
          background: 'var(--bg1)',
          borderLeft: '1px solid var(--border)',
          zIndex: 1002,
          display: 'flex',
          flexDirection: 'column',
          transform: open ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.25s cubic-bezier(0.4,0,0.2,1)',
          boxShadow: open ? '-8px 0 32px rgba(0,0,0,0.4)' : 'none',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '14px 16px',
            borderBottom: '1px solid var(--border)',
            flexShrink: 0,
          }}
        >
          <Activity size={18} style={{ color: 'var(--accent)' }} />
          <span style={{ flex: 1, fontWeight: 700, fontSize: 14 }}>测试进度大盘</span>
          {loading && (
            <Loader2 size={14} className="animate-spin" style={{ color: 'var(--text3)' }} />
          )}
          <button
            type="button"
            onClick={() => setOpen(false)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text3)',
              display: 'flex',
              padding: 4,
              borderRadius: 4,
            }}
            aria-label="关闭"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '14px 14px' }}>
          {!data && loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
              <Loader2 size={28} className="animate-spin" style={{ color: 'var(--text3)' }} />
            </div>
          ) : data ? (
            <>
              {/* Overall summary */}
              <div className="card" style={{ marginBottom: 14 }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: 8,
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 13 }}>总体测试进度</div>
                    <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 2 }}>
                      {doneCount}/{allModules.length} 模块
                      {failedCount > 0 && (
                        <span style={{ color: 'var(--red)', marginLeft: 6 }}>
                          · {failedCount} 失败
                        </span>
                      )}
                    </div>
                  </div>
                  <span
                    className="mono"
                    style={{ fontSize: 24, fontWeight: 800, color: 'var(--accent)', lineHeight: 1 }}
                  >
                    {overall}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${overall}%` }} />
                </div>
                <div style={{ fontSize: 10.5, color: 'var(--text3)', marginTop: 6 }}>
                  上次更新: {new Date(data.lastUpdated).toLocaleString('zh-CN')}
                  <span className="mono" style={{ marginLeft: 8 }}>
                    v{data.version}
                  </span>
                </div>
              </div>

              {/* Phase list */}
              {data.phases.map((phase) => (
                <PhaseSection key={phase.id} phase={phase} />
              ))}
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--text3)' }}>
              暂无进度数据
            </div>
          )}
        </div>
      </div>
    </>
  );
}
