'use client';

import { ProgressSteps } from '@/components/ui/ProgressSteps';

interface WorkbenchStepBarProps {
  currentStep: 1 | 2;
  onStepClick: (step: 1 | 2) => void;
  step2Completed: boolean;
}

export default function WorkbenchStepBar({
  currentStep,
  onStepClick,
  step2Completed,
}: WorkbenchStepBarProps) {
  const steps = [
    {
      label: 'Step 1 确认测试点',
      status: (currentStep === 1 ? 'active' : 'done') as 'active' | 'done' | 'pending',
    },
    {
      label: 'Step 2 生成用例',
      status: (
        currentStep === 2 ? 'active' : step2Completed ? 'done' : 'pending'
      ) as 'active' | 'done' | 'pending',
    },
  ];

  return (
    <div className="sticky top-0 z-10 bg-sy-bg-1 border-b border-sy-border px-4 py-2">
      <ProgressSteps
        steps={steps}
        onStepClick={(idx: number) => {
          if (idx === 0 && (currentStep === 2 || step2Completed)) onStepClick(1);
          if (idx === 1 && step2Completed) onStepClick(2);
        }}
      />
    </div>
  );
}
