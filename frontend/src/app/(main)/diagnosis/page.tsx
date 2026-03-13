'use client';

import {
  Activity,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  FileText,
  FolderOpen,
  IterationCw,
  Loader2,
  Play,
} from 'lucide-react';
import { ThreeColLayout } from '@/components/layout/ThreeColLayout';
import { useDiagnosis } from '@/hooks/useDiagnosis';
import { useRequirementTree } from '@/hooks/useRequirementTree';
import { useDiagnosisStore } from '@/stores/diagnosis-store';
import { ChatInput } from './_components/ChatInput';
import { DiagnosisChat } from './_components/DiagnosisChat';
import { FlowSteps } from './_components/FlowSteps';
import { ReportList } from './_components/ReportList';
import { ScenePreview } from './_components/ScenePreview';

export default function DiagnosisPage() {
  const tree = useRequirementTree();
  const { currentStep } = useDiagnosisStore();
  const {
    report,
    messages,
    sceneMap,
    loading,
    sse,
    sendMessage,
    startDiagnosis,
    completeDiagnosis,
  } = useDiagnosis(tree.selectedReqId);

  const left = (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-3.5 py-2.5 border-b border-border flex items-center gap-2 sticky top-0 bg-bg1 z-5">
        <Activity className="w-3.5 h-3.5 text-accent" />
        <span className="text-[12px] font-semibold text-text2">需求需求分析</span>
      </div>

      {/* Flow Steps */}
      <div className="border-b border-border">
        <FlowSteps currentStep={currentStep} />
      </div>

      {/* Requirement Tree */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        <div className="text-[10px] font-semibold text-text3 uppercase tracking-wider px-2 mb-1.5">
          需求列表
        </div>
        {tree.products.map((product) => (
          <div key={product.id}>
            <button
              type="button"
              onClick={() => tree.toggleProduct(product.id)}
              className="w-full flex items-center gap-1.5 px-2 py-1.5 rounded-md hover:bg-bg2 transition-colors text-text text-[12.5px]"
            >
              {tree.expandedProducts.has(product.id) ? (
                <ChevronDown className="w-3.5 h-3.5 text-text3 flex-shrink-0" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-text3 flex-shrink-0" />
              )}
              <FolderOpen className="w-3.5 h-3.5 text-accent flex-shrink-0" />
              <span className="truncate">{product.name}</span>
            </button>
            {tree.expandedProducts.has(product.id) &&
              (tree.iterations[product.id] || []).map((iter) => (
                <div key={iter.id} className="pl-5">
                  <button
                    type="button"
                    onClick={() => tree.toggleIteration(product.id, iter.id)}
                    className="w-full flex items-center gap-1.5 px-2 py-1 rounded-md hover:bg-bg2 transition-colors text-text3 text-[12px]"
                  >
                    {tree.expandedIterations.has(iter.id) ? (
                      <ChevronDown className="w-3 h-3 flex-shrink-0" />
                    ) : (
                      <ChevronRight className="w-3 h-3 flex-shrink-0" />
                    )}
                    <IterationCw className="w-3 h-3 flex-shrink-0" />
                    <span className="truncate">{iter.name}</span>
                  </button>
                  {tree.expandedIterations.has(iter.id) &&
                    (tree.requirements[iter.id] || []).map((req) => (
                      <button
                        type="button"
                        key={req.id}
                        onClick={() => tree.selectRequirement(req)}
                        className={`w-full flex items-center gap-1.5 px-2 py-1 ml-5 rounded-md text-[12px] transition-colors ${
                          tree.selectedReqId === req.id
                            ? 'bg-accent-d text-accent'
                            : 'text-text3 hover:bg-bg2 hover:text-text2'
                        }`}
                      >
                        <FileText className="w-3 h-3 flex-shrink-0" />
                        <span className="truncate">{req.title || req.req_id}</span>
                      </button>
                    ))}
                </div>
              ))}
          </div>
        ))}
        {tree.products.length === 0 && (
          <div className="text-center py-6 text-text3 text-[13px]">暂无产品数据</div>
        )}
      </div>

      {/* Report Summary */}
      {tree.selectedReqId && (
        <div className="border-t border-border">
          <ReportList report={report} loading={loading} />
        </div>
      )}
    </div>
  );

  const center = (
    <div className="flex flex-col h-full">
      {/* Start Diagnosis Button */}
      {tree.selectedReqId &&
        currentStep === 'scan' &&
        messages.length === 0 &&
        !sse.isStreaming && (
          <div className="flex-shrink-0 px-4 py-3 border-b border-border">
            <button
              type="button"
              onClick={startDiagnosis}
              disabled={sse.isStreaming}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-accent text-white dark:text-black font-semibold text-[13px] hover:bg-accent2 transition-colors disabled:opacity-50"
            >
              {sse.isStreaming ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  分析进行中...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  开始分析
                </>
              )}
            </button>
          </div>
        )}

      <DiagnosisChat
        messages={messages}
        isStreaming={sse.isStreaming}
        streamContent={sse.content}
        streamThinking={sse.thinking}
        reqTitle={tree.selectedReqTitle}
        hasRequirement={!!tree.selectedReqId}
      />

      {tree.selectedReqId && (
        <ChatInput
          onSend={sendMessage}
          isStreaming={sse.isStreaming}
          disabled={!tree.selectedReqId}
        />
      )}
    </div>
  );

  const right = (
    <div className="flex flex-col h-full">
      <ScenePreview sceneMap={sceneMap} loading={loading} />

      {/* Quick Actions */}
      {tree.selectedReqId && (
        <div className="mt-auto p-4 border-t border-border">
          <button
            type="button"
            onClick={completeDiagnosis}
            disabled={sse.isStreaming || report?.status === 'completed'}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-accent text-white dark:text-black font-semibold text-[12.5px] hover:bg-accent2 transition-colors disabled:opacity-40"
          >
            <CheckCircle className="w-4 h-4" />
            {report?.status === 'completed' ? '分析已完成' : '完成分析'}
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div className="p-4">
      <ThreeColLayout
        left={left}
        center={center}
        right={right}
        leftWidth="280px"
        rightWidth="320px"
        subNavHeight={32}
      />
    </div>
  );
}
