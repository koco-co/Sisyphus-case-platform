import Link from 'next/link';
import { StatusPill, ProgressBar } from '@/components/ui';

interface ProjectCardProps {
  id: string;
  name: string;
  iteration: string;
  status: 'active' | 'completed' | 'paused';
  totalCases: number;
  coverage: number;
  pending: number;
  members: string[];
}

const statusMap = {
  active: { variant: 'green' as const, label: '进行中' },
  completed: { variant: 'gray' as const, label: '已完成' },
  paused: { variant: 'amber' as const, label: '暂停' },
};

export function ProjectCard({ id, name, iteration, status, totalCases, coverage, pending, members }: ProjectCardProps) {
  const s = statusMap[status];
  return (
    <Link href={`/requirements?product=${id}`}>
      <div className="bg-bg1 border border-border rounded-[10px] p-4 cursor-pointer hover:border-border2 hover:-translate-y-px transition-all">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="font-semibold text-[13.5px] text-text">{name}</div>
            <div className="text-text3 text-[11.5px] mt-0.5">{iteration}</div>
          </div>
          <StatusPill variant={s.variant}>{s.label}</StatusPill>
        </div>
        <div className="grid grid-cols-3 gap-2 mb-3">
          {[
            { val: totalCases, label: '用例总数' },
            { val: `${coverage}%`, label: '覆盖率', color: 'text-accent' },
            { val: pending, label: '待处理', color: pending > 0 ? 'text-amber' : undefined },
          ].map((stat) => (
            <div key={stat.label} className="text-center p-2 bg-bg2 rounded-md">
              <div className={`font-mono text-[18px] font-semibold ${stat.color ?? 'text-text'}`}>{stat.val}</div>
              <div className="text-[10.5px] text-text3">{stat.label}</div>
            </div>
          ))}
        </div>
        <ProgressBar value={coverage} />
        <div className="mt-2.5 text-[11.5px] text-text3">👥 {members.slice(0, 3).join('  ')}</div>
      </div>
    </Link>
  );
}
