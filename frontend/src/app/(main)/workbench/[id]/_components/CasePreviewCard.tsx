import { Check } from 'lucide-react';
import { StatusPill } from '@/components/ui';

export interface CaseStep {
  step_num: number;
  action: string;
  expected_result: string;
}

interface CasePreviewCardProps {
  caseId: string;
  title: string;
  priority: string;
  caseType: string;
  status: string;
  steps?: CaseStep[];
  onAccept?: () => void;
}

export function CasePreviewCard({
  caseId,
  title,
  priority,
  caseType,
  status,
  steps = [],
  onAccept,
}: CasePreviewCardProps) {
  const caseTypeLabel =
    caseType === 'normal' ? '功能' : caseType === 'exception' ? '异常' : caseType;
  const isAccepted = status === 'review' || status === 'reviewed' || status === 'approved';

  return (
    <div className="bg-bg2 border border-border rounded-lg p-3 mb-2">
      <div className="flex items-center gap-1.5 mb-1.5">
        <StatusPill variant={priority === 'P0' ? 'red' : priority === 'P1' ? 'amber' : 'gray'}>
          {priority}
        </StatusPill>
        <StatusPill
          variant={caseType === 'normal' ? 'green' : caseType === 'exception' ? 'red' : 'blue'}
        >
          {caseTypeLabel}
        </StatusPill>
      </div>
      <div className="text-[12.5px] font-medium text-text mb-1">{title}</div>
      <div className="flex items-center gap-2 text-[10.5px] text-text3 font-mono">
        <span>{caseId}</span>
        <span>·</span>
        <span>{steps.length} 步骤</span>
      </div>
      {steps.length > 0 && (
        <div className="mt-2 space-y-1.5">
          {steps.map((step) => (
            <div
              key={step.step_num}
              className="rounded-md bg-bg p-2 border border-border text-[11px]"
            >
              <div className="flex items-start gap-1.5">
                <span className="font-mono text-accent shrink-0" style={{ minWidth: 18 }}>
                  {step.step_num}.
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-text">{step.action}</div>
                  {step.expected_result && (
                    <div className="text-text3 mt-0.5">
                      <span className="text-accent2 font-medium">预期：</span>
                      {step.expected_result}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {status === 'draft' && onAccept && (
        <button
          type="button"
          onClick={onAccept}
          className="mt-2 w-full text-center py-1 rounded-md text-[11px] font-medium bg-accent text-black hover:bg-accent2 transition-colors"
        >
          <Check className="w-3.5 h-3.5 inline-block -mt-px" /> 接受用例
        </button>
      )}
      {isAccepted && (
        <div className="mt-2 text-center py-1 text-[11px] text-accent font-mono flex items-center justify-center gap-1">
          <Check className="w-3.5 h-3.5" /> 已接受
        </div>
      )}
    </div>
  );
}
