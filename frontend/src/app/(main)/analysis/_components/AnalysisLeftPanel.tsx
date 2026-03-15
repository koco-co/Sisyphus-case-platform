'use client';

import { ChevronDown, ChevronRight, Loader2, Search } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useRequirementTree } from '@/hooks/useRequirementTree';
import type { Requirement } from '@/lib/api';

interface AnalysisLeftPanelProps {
  selectedReqId: string | null;
  onSelectRequirement: (reqId: string) => void;
}

function getStatusVariant(status: string): 'gray' | 'warning' | 'success' | 'info' {
  if (status === 'completed') return 'success';
  if (status === 'processing') return 'warning';
  return 'gray';
}

function getStatusLabel(status: string): string {
  if (status === 'completed') return '已完成';
  if (status === 'processing') return '分析中';
  return '未分析';
}

export function AnalysisLeftPanel({ selectedReqId, onSelectRequirement }: AnalysisLeftPanelProps) {
  const [panelWidth, setPanelWidth] = useState(260);
  const [searchQuery, setSearchQuery] = useState('');
  const isDragging = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(0);

  const {
    products,
    expandedProducts,
    iterations,
    iterationsLoading,
    expandedIterations,
    requirements,
    requirementsLoading,
    toggleProduct,
    toggleIteration,
  } = useRequirementTree();

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      isDragging.current = true;
      startX.current = e.clientX;
      startWidth.current = panelWidth;
    },
    [panelWidth],
  );

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return;
      const delta = e.clientX - startX.current;
      const newWidth = Math.min(320, Math.max(200, startWidth.current + delta));
      setPanelWidth(newWidth);
    };

    const handleMouseUp = () => {
      isDragging.current = false;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const matchesSearch = useCallback(
    (req: Requirement) => {
      if (!searchQuery) return true;
      return req.title.toLowerCase().includes(searchQuery.toLowerCase());
    },
    [searchQuery],
  );

  return (
    <div
      className="relative flex-shrink-0 flex flex-col bg-sy-bg-1 border-r border-sy-border overflow-hidden"
      style={{ width: panelWidth, height: 'calc(100vh - 49px)' }}
    >
      {/* Search header */}
      <div className="flex-shrink-0 px-3 py-2.5 border-b border-sy-border">
        <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-sy-bg-2 border border-sy-border">
          <Search className="w-3.5 h-3.5 text-sy-text-3 flex-shrink-0" />
          <input
            type="text"
            placeholder="搜索需求..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 bg-transparent text-[12px] text-sy-text placeholder:text-sy-text-3 outline-none min-w-0"
          />
        </div>
      </div>

      {/* Tree list */}
      <div className="flex-1 overflow-y-auto">
        {products.length === 0 ? (
          <div className="flex items-center justify-center h-20">
            <span className="text-[12px] text-sy-text-3">暂无产品数据</span>
          </div>
        ) : (
          products.map((product) => {
            const isProductExpanded = expandedProducts.has(product.id);
            const productIterations = iterations[product.id] ?? [];
            const isIterLoading = iterationsLoading[product.id];

            return (
              <div key={product.id}>
                {/* Product header */}
                <button
                  type="button"
                  onClick={() => toggleProduct(product.id)}
                  className="w-full flex items-center gap-1.5 px-3 py-2 text-left hover:bg-sy-bg-2 transition-colors"
                >
                  {isProductExpanded ? (
                    <ChevronDown className="w-3.5 h-3.5 text-sy-text-3 flex-shrink-0" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-sy-text-3 flex-shrink-0" />
                  )}
                  <span className="text-[12px] font-semibold text-sy-text-2 truncate">
                    {product.name}
                  </span>
                </button>

                {/* Iterations */}
                {isProductExpanded && (
                  <div>
                    {isIterLoading ? (
                      <div className="flex items-center gap-2 px-6 py-2">
                        <Loader2 className="w-3 h-3 text-sy-text-3 animate-spin" />
                        <span className="text-[11px] text-sy-text-3">加载中...</span>
                      </div>
                    ) : (
                      productIterations.map((iteration) => {
                        const isIterExpanded = expandedIterations.has(iteration.id);
                        const iterReqs = requirements[iteration.id] ?? [];
                        const isReqLoading = requirementsLoading[iteration.id];
                        const filteredReqs = iterReqs.filter(matchesSearch);

                        // If searching and no matches, hide this iteration
                        if (searchQuery && filteredReqs.length === 0) return null;

                        return (
                          <div key={iteration.id}>
                            {/* Iteration header */}
                            <button
                              type="button"
                              onClick={() => toggleIteration(product.id, iteration.id)}
                              className="w-full flex items-center gap-1.5 px-4 py-1.5 text-left hover:bg-sy-bg-2 transition-colors"
                            >
                              {isIterExpanded ? (
                                <ChevronDown className="w-3 h-3 text-sy-text-3 flex-shrink-0" />
                              ) : (
                                <ChevronRight className="w-3 h-3 text-sy-text-3 flex-shrink-0" />
                              )}
                              <span className="text-[11.5px] text-sy-text-2 truncate flex-1">
                                {iteration.name}
                              </span>
                              {iterReqs.length > 0 && (
                                <span className="text-[10px] text-sy-text-3 font-mono flex-shrink-0">
                                  {iterReqs.length}
                                </span>
                              )}
                            </button>

                            {/* Requirements */}
                            {isIterExpanded && (
                              <div>
                                {isReqLoading ? (
                                  <div className="flex items-center gap-2 px-8 py-2">
                                    <Loader2 className="w-3 h-3 text-sy-text-3 animate-spin" />
                                    <span className="text-[11px] text-sy-text-3">加载中...</span>
                                  </div>
                                ) : filteredReqs.length === 0 ? (
                                  <div className="px-8 py-2">
                                    <span className="text-[11px] text-sy-text-3">暂无需求</span>
                                  </div>
                                ) : (
                                  filteredReqs.map((req) => {
                                    const isSelected = req.id === selectedReqId;
                                    const status =
                                      (req as Requirement & { analysis_status?: string })
                                        .analysis_status ?? 'pending';
                                    const highRiskCount =
                                      (
                                        req as Requirement & {
                                          unconfirmed_high_risk_count?: number;
                                        }
                                      ).unconfirmed_high_risk_count ?? 0;

                                    return (
                                      <button
                                        key={req.id}
                                        type="button"
                                        onClick={() => onSelectRequirement(req.id)}
                                        className={`w-full flex items-center gap-2 px-5 py-2 text-left transition-colors ${
                                          isSelected
                                            ? 'bg-sy-bg-2 border-r-2 border-sy-accent'
                                            : 'hover:bg-sy-bg-2/60'
                                        }`}
                                      >
                                        <span className="flex-1 text-[12px] text-sy-text truncate min-w-0">
                                          {req.title.length > 30
                                            ? `${req.title.slice(0, 30)}...`
                                            : req.title}
                                        </span>
                                        <div className="flex items-center gap-1 flex-shrink-0">
                                          <StatusBadge variant={getStatusVariant(status)}>
                                            {getStatusLabel(status)}
                                          </StatusBadge>
                                          {highRiskCount > 0 && (
                                            <span className="bg-sy-danger text-white text-[10px] font-mono rounded-full px-1.5 py-0.5 leading-none">
                                              {highRiskCount}
                                            </span>
                                          )}
                                        </div>
                                      </button>
                                    );
                                  })
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Drag handle */}
      <button
        type="button"
        aria-label="拖拽调整宽度"
        className="absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-sy-accent transition-colors p-0 border-0 bg-transparent"
        onMouseDown={handleMouseDown}
      />
    </div>
  );
}
