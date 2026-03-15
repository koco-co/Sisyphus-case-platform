'use client';

import { Bot, Settings2 } from 'lucide-react';
import Link from 'next/link';

export function AiConfigBanner() {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-sy-warn/30 bg-sy-warn/10 px-4 py-2.5">
      <div className="flex items-center gap-2 text-[12px]">
        <Bot className="h-3.5 w-3.5 flex-shrink-0 text-sy-warn" />
        <p className="text-sy-text">
          <span className="font-semibold text-sy-warn">尚未配置可用 AI 模型</span>
          <span className="ml-1 text-sy-text-2">分析与用例生成可能不可用，请先完成设置。</span>
        </p>
      </div>
      <Link
        href="/settings"
        className="inline-flex items-center gap-1.5 rounded-md border border-sy-warn/30 bg-sy-bg-2 px-3 py-1.5 text-[12px] font-medium text-sy-warn transition-colors hover:border-sy-warn/50 hover:bg-sy-warn/10"
      >
        <Settings2 className="h-3.5 w-3.5" />
        前往设置
      </Link>
    </div>
  );
}
