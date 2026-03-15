import { Check } from 'lucide-react';

interface Step {
  label: string;
  status: 'done' | 'active' | 'pending';
}

export function ProgressSteps({
  steps,
  onStepClick,
}: {
  steps: Step[];
  onStepClick?: (idx: number) => void;
}) {
  return (
    <div className="flex items-center mb-5">
      {steps.map((step, i) => (
        <div key={step.label} className="flex items-center">
          <button
            type="button"
            onClick={() => onStepClick?.(i)}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 text-[12px] font-medium rounded-md transition-colors ${
              step.status === 'done'
                ? 'text-accent hover:bg-sy-bg-2 cursor-pointer'
                : step.status === 'active'
                  ? 'text-text bg-bg2 cursor-default'
                  : 'text-text3 cursor-default'
            } ${!onStepClick ? 'cursor-default' : ''}`}
          >
            {step.status === 'done' && <Check className="w-3.5 h-3.5" />}
            {step.label}
          </button>
          {i < steps.length - 1 && <span className="text-border2 text-[12px] mx-1">›</span>}
        </div>
      ))}
    </div>
  );
}
