'use client';

interface TableSkeletonProps {
  rows?: number;
  cols?: number;
}

export function TableSkeleton({ rows = 5, cols = 4 }: TableSkeletonProps) {
  return (
    <div className="p-4 space-y-3 animate-pulse">
      {/* Header */}
      <div className="flex gap-4 pb-3 border-b border-border">
        {Array.from({ length: cols }).map((_, i) => (
          <div
            key={`h-${i.toString()}`}
            className="h-3 bg-bg3 rounded"
            style={{ width: `${60 + Math.random() * 80}px` }}
          />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, ri) => (
        <div key={`r-${ri.toString()}`} className="flex gap-4 py-2">
          {Array.from({ length: cols }).map((_, ci) => (
            <div
              key={`c-${ci.toString()}`}
              className="h-3 bg-bg3/60 rounded"
              style={{ width: `${40 + Math.random() * 100}px` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
