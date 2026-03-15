'use client';

import {
  ChevronDown,
  ChevronRight,
  FileText,
  FolderOpen,
  MessageSquare,
  Plus,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { useRequirementTree } from '@/hooks/useRequirementTree';
import type { Requirement } from '@/lib/api';
import type { GenSession } from '@/stores/workspace-store';

interface RequirementNavProps {
  sessions: GenSession[];
  activeSessionId: string | null;
  selectedReqId: string | null;
  onSelectRequirement: (req: Requirement) => void;
  onSelectSession: (sessionId: string) => void;
  onCreateSession: () => void;
}

function statusDot(status: string) {
  if (status === 'generated') return 'bg-accent';
  if (status === 'partial') return 'bg-amber';
  return 'bg-text3/40';
}

export function RequirementNav({
  sessions,
  activeSessionId,
  selectedReqId,
  onSelectRequirement,
  onSelectSession,
  onCreateSession,
}: RequirementNavProps) {
  const tree = useRequirementTree();

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-accent" />
        <h3 className="text-[13px] font-semibold text-text">生成工作台</h3>
      </div>

      {/* Requirement tree */}
      <div className="flex-1 overflow-y-auto p-2">
        {tree.products.length === 0 && (
          <div className="text-center py-8 text-[12px] text-text3">暂无子产品数据</div>
        )}
        {tree.products.map((product) => (
          <div key={product.id}>
            <button
              type="button"
              onClick={() => tree.toggleProduct(product.id)}
              className="w-full flex items-center gap-1.5 px-2.5 py-2 rounded-md text-[13px] text-text hover:bg-bg2 transition-colors"
            >
              {tree.expandedProducts.has(product.id) ? (
                <ChevronDown className="w-3.5 h-3.5 text-text3 shrink-0" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-text3 shrink-0" />
              )}
              <FolderOpen className="w-3.5 h-3.5 text-accent shrink-0" />
              <span className="truncate">{product.name}</span>
            </button>

            {tree.expandedProducts.has(product.id) &&
              (tree.iterationsLoading[product.id] ? (
                <div className="pl-8 py-1 text-[11px] text-text3">迭代加载中...</div>
              ) : (tree.iterations[product.id] || []).length === 0 ? (
                <div className="pl-8 py-1 text-[11px] text-text3">当前产品暂无迭代</div>
              ) : (
                (tree.iterations[product.id] || []).map((iter) => (
                  <div key={iter.id} className="pl-4">
                    <button
                      type="button"
                      onClick={() => tree.toggleIteration(product.id, iter.id)}
                      className="w-full flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[12px] text-text2 hover:bg-bg2 transition-colors"
                    >
                      {tree.expandedIterations.has(iter.id) ? (
                        <ChevronDown className="w-3 h-3 text-text3 shrink-0" />
                      ) : (
                        <ChevronRight className="w-3 h-3 text-text3 shrink-0" />
                      )}
                      <RefreshCw className="w-3 h-3 shrink-0" />
                      <span className="truncate">{iter.name}</span>
                    </button>

                    {tree.expandedIterations.has(iter.id) &&
                      (tree.requirementsLoading[iter.id] ? (
                        <div className="pl-8 py-1 text-[11px] text-text3">需求加载中...</div>
                      ) : (tree.requirements[iter.id] || []).length === 0 ? (
                        <div className="pl-8 py-1 text-[11px] text-text3">当前迭代暂无需求</div>
                      ) : (
                        (tree.requirements[iter.id] || []).map((req) => (
                          <button
                            type="button"
                            key={req.id}
                            onClick={() => onSelectRequirement(req)}
                            className={`w-full flex items-center gap-1.5 pl-8 pr-2.5 py-1.5 rounded-md text-[12px] transition-colors ${
                              selectedReqId === req.id
                                ? 'bg-accent/10 text-accent'
                                : 'text-text2 hover:bg-bg2'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full shrink-0 ${statusDot(req.status ?? '')}`}
                            />
                            <FileText className="w-3 h-3 shrink-0" />
                            <span className="truncate">{req.title || req.req_id}</span>
                          </button>
                        ))
                      ))}
                  </div>
                ))
              ))}
          </div>
        ))}
      </div>

      {/* Session list */}
      {selectedReqId && (
        <div className="border-t border-border max-h-[35%] overflow-y-auto p-2">
          <div className="flex items-center justify-between px-2 py-1 mb-1">
            <span className="text-[11px] font-semibold text-text2 uppercase tracking-wider">
              会话列表
            </span>
            <button
              type="button"
              onClick={onCreateSession}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium text-accent hover:bg-accent/10 transition-colors"
            >
              <Plus className="w-3 h-3" />
              新建
            </button>
          </div>
          {sessions.map((session) => (
            <button
              type="button"
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              className={`w-full flex items-center gap-1.5 px-2.5 py-2 rounded-md text-[12px] mb-0.5 transition-colors ${
                activeSessionId === session.id
                  ? 'bg-accent/10 text-accent'
                  : 'text-text2 hover:bg-bg2'
              }`}
            >
              <MessageSquare className="w-3 h-3 shrink-0" />
              <span className="truncate flex-1 text-left">
                {session.mode === 'test_point_driven'
                  ? '测试点驱动'
                  : session.mode === 'document_driven'
                    ? '文档驱动'
                    : session.mode === 'dialogue'
                      ? '对话引导'
                      : session.mode === 'template'
                        ? '模板填充'
                        : session.mode}
              </span>
              <span className="text-[10px] text-text3 font-mono shrink-0">
                {session.created_at?.slice(5, 16)}
              </span>
            </button>
          ))}
          {sessions.length === 0 && (
            <div className="text-center py-4 text-[11px] text-text3">无会话，点击新建</div>
          )}
        </div>
      )}
    </div>
  );
}
