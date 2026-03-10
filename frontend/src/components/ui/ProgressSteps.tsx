import { Check } from 'lucide-react';

interface Step {
  label: string;
  status: 'done' | 'active' | 'pending';
}

export function ProgressSteps({ steps }: { steps: Step[] }) {
  return (
    <div className="flex items-center mb-5">
      {steps.map((step, i) => (
        <div key={step.label} className="flex items-center">
          <div
            className={`flex items-center gap-1.5 px-3.5 py-1.5 text-[12px] font-medium rounded-md ${
              step.status === 'done'
                ? 'text-accent'
                : step.status === 'active'
                  ? 'text-text bg-bg2'
                  : 'text-text3'
            }`}
          >
            {step.status === 'done' && <Check className="w-3.5 h-3.5" />}
            {step.label}
          </div>
          {i < steps.length - 1 && <span className="text-border2 text-[12px] mx-1">›</span>}
        </div>
      ))}
    </div>
  );
}
