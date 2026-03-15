'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';
import { AiConfigBanner } from '@/components/ui/AiConfigBanner';
import { useAiConfig } from '@/hooks/useAiConfig';
import { AnalysisLeftPanel } from './_components/AnalysisLeftPanel';
import { AnalysisRightPanel } from './_components/AnalysisRightPanel';

function AnalysisPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const aiConfig = useAiConfig();

  const [selectedReqId, setSelectedReqId] = useState<string | null>(searchParams.get('reqId'));
  const [activeTab, setActiveTab] = useState<'detail' | 'analysis' | 'coverage'>(
    (searchParams.get('tab') as 'detail' | 'analysis' | 'coverage') ?? 'detail',
  );

  const hasConfiguredAiModel = Boolean(
    !aiConfig.loading && aiConfig.modelConfigs.some((model) => model.is_enabled && model.model_id),
  );
  const showAiConfigBanner = !aiConfig.loading && !hasConfiguredAiModel;

  const handleSelectRequirement = (reqId: string) => {
    setSelectedReqId(reqId);
    router.push(`/analysis?reqId=${reqId}&tab=${activeTab}`, { scroll: false });
  };

  const handleTabChange = (tab: 'detail' | 'analysis' | 'coverage') => {
    setActiveTab(tab);
    if (selectedReqId) {
      router.push(`/analysis?reqId=${selectedReqId}&tab=${tab}`, { scroll: false });
    }
  };

  return (
    <div className="flex flex-col overflow-hidden" style={{ height: 'calc(100vh - 49px)' }}>
      {showAiConfigBanner && <AiConfigBanner />}
      <div className="flex flex-1 overflow-hidden">
        <AnalysisLeftPanel
          selectedReqId={selectedReqId}
          onSelectRequirement={handleSelectRequirement}
        />
        <AnalysisRightPanel
          selectedReqId={selectedReqId}
          activeTab={activeTab}
          onTabChange={handleTabChange}
        />
      </div>
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <Suspense>
      <AnalysisPageInner />
    </Suspense>
  );
}
