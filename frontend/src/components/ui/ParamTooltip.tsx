'use client';

import { HelpCircle } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

interface ParamTooltipProps {
  content: string;
  className?: string;
}

export function ParamTooltip({ content, className = '' }: ParamTooltipProps) {
  const [show, setShow] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!show) return;
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setShow(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [show]);

  return (
    <div className={`relative inline-flex ${className}`} ref={ref}>
      <button
        type="button"
        className="text-sy-text-3 hover:text-sy-text-2 transition-colors"
        onClick={() => setShow(!show)}
        aria-label="参数说明"
      >
        <HelpCircle className="w-3.5 h-3.5" />
      </button>
      {show && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 rounded-lg bg-sy-bg-3 border border-sy-border text-[11.5px] text-sy-text-2 whitespace-pre-line z-50 min-w-[200px] max-w-[280px] shadow-lg">
          {content}
          <div className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-sy-bg-3 border-r border-b border-sy-border rotate-45 -mt-1" />
        </div>
      )}
    </div>
  );
}
