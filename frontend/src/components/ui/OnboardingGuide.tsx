'use client';

import { CircleHelp, X } from 'lucide-react';
import { usePathname } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import {
  getAnalysisDiagnosisHref,
  getAnalysisSceneMapHref,
  getWorkbenchHref,
} from '@/lib/analysisRoutes';

const STEPS = [
  {
    id: 'requirement',
    label: '录入需求',
    desc: '通过文字输入或上传 .docx/.pdf 文档，将需求录入系统。支持 OCR 解析图片中的文字内容。',
    href: '/requirements',
  },
  {
    id: 'diagnosis',
    label: '需求分析',
    desc: '对需求进行 6 维度扫描（异常路径、边界值、权限、并发、状态机、跨模块），识别遗漏风险。',
    href: getAnalysisDiagnosisHref(),
  },
  {
    id: 'followup',
    label: '追问补充',
    desc: 'AI 对每个遗漏项进行苏格拉底式追问，每轮只问 1 个问题，最多 3 轮，自动补全需求盲区。',
    href: getAnalysisDiagnosisHref(),
  },
  {
    id: 'scenemap',
    label: '场景地图确认',
    desc: '基于分析结果生成测试点场景地图，按 5 种类型分组（正常/异常/边界/并发/权限），逐一确认。',
    href: getAnalysisSceneMapHref(),
  },
  {
    id: 'generation',
    label: '用例生成',
    desc: '进入生成工作台，AI 基于确认的测试点自动生成结构化用例，支持 SSE 实时流式输出。',
    href: getWorkbenchHref(),
  },
  {
    id: 'management',
    label: '用例管理',
    desc: '集中管理所有用例，支持按优先级/类型/状态筛选，查看详情，编辑步骤，导出报告。',
    href: '/testcases',
  },
  {
    id: 'diff',
    label: 'Diff 分析',
    desc: '需求变更时自动检测差异，结合文本级 Myers Diff 和语义级 LLM 分析，标记受影响用例。',
    href: '/diff',
  },
  {
    id: 'knowledge',
    label: '知识库维护',
    desc: '管理历史用例数据，经 LLM 清洗后入库，通过 RAG 向量检索在生成时自动引用相关规范。',
    href: '/knowledge',
  },
];

export const ONBOARDING_GUIDE_SEEN_KEY = 'sisyphus-y-onboarding-seen';

export function shouldAutoOpenOnboarding(storage: Pick<Storage, 'getItem'>, pathname = '/') {
  if (pathname !== '/') {
    return false;
  }
  return storage.getItem(ONBOARDING_GUIDE_SEEN_KEY) !== '1';
}

export function OnboardingGuideButton() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    if (shouldAutoOpenOnboarding(window.localStorage, pathname ?? '/')) {
      setOpen(true);
      window.localStorage.setItem(ONBOARDING_GUIDE_SEEN_KEY, '1');
    }
  }, [pathname]);

  return (
    <>
      <button
        type="button"
        className="fixed bottom-6 right-6 z-50 inline-flex h-11 w-11 items-center justify-center rounded-full border border-sy-border bg-sy-bg-1 text-sy-text shadow-lg shadow-black/20 transition-all hover:-translate-y-px hover:border-sy-border-2 hover:text-sy-accent"
        onClick={() => setOpen(true)}
        aria-label="帮助与引导"
        title="帮助与引导"
      >
        <CircleHelp />
      </button>
      {open && <OnboardingGuideModal onClose={() => setOpen(false)} />}
    </>
  );
}

function OnboardingGuideModal({ onClose }: { onClose: () => void }) {
  const [selected, setSelected] = useState<string | null>(null);
  const selectedStep = STEPS.find((s) => s.id === selected);

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) onClose();
    },
    [onClose],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose],
  );

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={handleOverlayClick}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-label="新手引导"
      tabIndex={-1}
    >
      <div className="relative w-[900px] max-h-[80vh] rounded-xl border border-sy-border bg-sy-bg-1 p-8 shadow-2xl overflow-y-auto">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1.5 text-sy-text-3 hover:bg-sy-bg-2 hover:text-sy-text transition-colors"
          aria-label="关闭"
        >
          <X className="h-5 w-5" />
        </button>

        <h2 className="mb-1 font-display text-xl font-semibold text-sy-text">
          Sisyphus-Y 使用流程
        </h2>
        <p className="mb-6 text-sm text-sy-text-3">
          AI 驱动的测试用例生成平台完整工作流程，点击节点查看详细说明
        </p>

        {/* Flow chart */}
        <div className="flex flex-col items-center gap-0">
          {STEPS.map((step, i) => (
            <div key={step.id} className="flex flex-col items-center w-full">
              <button
                type="button"
                onClick={() => setSelected(selected === step.id ? null : step.id)}
                className={`
                  group flex items-center gap-4 w-full max-w-[640px] rounded-lg border px-5 py-3.5 text-left transition-all
                  ${
                    selected === step.id
                      ? 'border-sy-accent bg-sy-accent/5 shadow-lg shadow-sy-accent/5'
                      : 'border-sy-border hover:border-sy-border-2 hover:-translate-y-px bg-sy-bg-2'
                  }
                `}
              >
                <span
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full font-mono text-xs font-semibold ${
                    selected === step.id
                      ? 'bg-sy-accent text-sy-bg'
                      : 'bg-sy-bg-3 text-sy-text-2 group-hover:bg-sy-accent/20 group-hover:text-sy-accent'
                  }`}
                >
                  {i + 1}
                </span>
                <span
                  className={`font-medium ${selected === step.id ? 'text-sy-accent' : 'text-sy-text'}`}
                >
                  {step.label}
                </span>
                <span className="ml-auto font-mono text-[10px] text-sy-text-3">{step.href}</span>
              </button>

              {/* Description panel */}
              {selected === step.id && selectedStep && (
                <div className="w-full max-w-[640px] mt-1 mb-1 rounded-lg border border-sy-accent/20 bg-sy-accent/5 px-5 py-3">
                  <p className="text-sm text-sy-text leading-relaxed">{selectedStep.desc}</p>
                </div>
              )}

              {/* Arrow connector */}
              {i < STEPS.length - 1 && (
                <div className="flex flex-col items-center py-1">
                  <div className="h-4 w-px bg-sy-border-2" />
                  <div className="h-0 w-0 border-l-[5px] border-r-[5px] border-t-[5px] border-l-transparent border-r-transparent border-t-sy-border-2" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
