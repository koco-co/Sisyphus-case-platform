'use client';

import { Activity } from 'lucide-react';
import { useCallback } from 'react';
import { useDiagnosis } from '@/hooks/useDiagnosis';
import { RequirementDetailTab } from '../../diagnosis/_components/RequirementDetailTab';
import { AnalysisTab } from './AnalysisTab';
import CoverageTab from './CoverageTab';

interface AnalysisRightPanelProps {
  selectedReqId: string | null;
  activeTab: 'detail' | 'analysis' | 'coverage';
  onTabChange: (tab: 'detail' | 'analysis' | 'coverage') => void;
}

const tabLabels: { key: 'detail' | 'analysis' | 'coverage'; label: string }[] = [
  { key: 'detail', label: '需求详情' },
  { key: 'analysis', label: 'AI 分析' },
  { key: 'coverage', label: '覆盖追踪' },
];

function RightPanelContent({
  selectedReqId,
  activeTab,
  onTabChange,
}: AnalysisRightPanelProps & { selectedReqId: string }) {
  const { startDiagnosis } = useDiagnosis(selectedReqId);

  const handleStartAnalysis = useCallback(() => {
    onTabChange('analysis');
    startDiagnosis();
  }, [onTabChange, startDiagnosis]);

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Tab nav */}
      <div className="flex-shrink-0 flex items-center border-b border-sy-border bg-sy-bg-1 px-1">
        {tabLabels.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => onTabChange(key)}
            className={`px-4 py-2.5 text-[12.5px] font-medium transition-colors relative ${
              activeTab === key ? 'text-sy-accent' : 'text-sy-text-2 hover:text-sy-text'
            }`}
          >
            {label}
            {activeTab === key && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-sy-accent rounded-t-sm" />
            )}
          </button>
        ))}
      </div>

      {/* Tab content — all mounted to preserve state, toggled via visibility */}
      <div className="flex-1 overflow-hidden relative">
        <div className={`absolute inset-0 ${activeTab === 'detail' ? '' : 'hidden'}`}>
          <RequirementDetailTab reqId={selectedReqId} onStartAnalysis={handleStartAnalysis} />
        </div>

        <div className={`absolute inset-0 ${activeTab === 'analysis' ? '' : 'hidden'}`}>
          <AnalysisTab requirementId={selectedReqId} visible={activeTab === 'analysis'} />
        </div>

        <div className={`absolute inset-0 ${activeTab === 'coverage' ? '' : 'hidden'}`}>
          <CoverageTab requirementId={selectedReqId} visible={activeTab === 'coverage'} />
        </div>
      </div>
    </div>
  );
}

export function AnalysisRightPanel({
  selectedReqId,
  activeTab,
  onTabChange,
}: AnalysisRightPanelProps) {
  if (!selectedReqId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-sy-bg">
        <div className="text-center">
          <Activity className="w-16 h-16 text-sy-text-3 opacity-15 mx-auto mb-4" />
          <p className="text-[15px] text-sy-text-3">从左侧选择需求开始分析</p>
        </div>
      </div>
    );
  }

  return (
    <RightPanelContent
      selectedReqId={selectedReqId}
      activeTab={activeTab}
      onTabChange={onTabChange}
    />
  );
}
