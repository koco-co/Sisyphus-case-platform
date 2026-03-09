'use client';
import { useQuery } from '@tanstack/react-query';
import { StatCard } from '@/components/ui';
import { ProjectCard } from './_components/ProjectCard';
import { apiClient } from '@/lib/api-client';

export default function ProjectListPage() {
  const { data: products = [] } = useQuery({
    queryKey: ['products'],
    queryFn: () => apiClient<{ id: string; name: string; slug: string }[]>('/products'),
  });

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div>
          <div className="font-mono text-[10px] text-text3 uppercase tracking-wide">TESTGEN PRO · 项目列表</div>
          <h1 className="font-display font-bold text-[20px]">全部项目</h1>
          <div className="text-text3 text-[12px]">{products.length} 个子产品</div>
        </div>
        <div className="flex-1" />
        <input className="bg-bg2 border border-border rounded-md px-3 py-1.5 text-[13px] text-text outline-none focus:border-accent w-[220px] placeholder:text-text3" placeholder="🔍  搜索项目..." />
        <button className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-[12.5px] font-semibold bg-accent text-black border border-accent hover:bg-accent2 transition-colors">
          ＋ 新建项目
        </button>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-6">
        <StatCard value="847" label="本周生成用例" delta="↑ 23% 较上周" highlighted />
        <StatCard value="12" label="进行中迭代" delta="3 个 Sprint 本周截止" deltaColor="text-amber" />
        <StatCard value="94%" label="平均用例覆盖率" progress={94} />
        <StatCard value="18" label="待处理健康诊断" delta="需要补充场景" deltaColor="text-red" />
      </div>

      <div className="grid grid-cols-3 gap-4">
        {products.map((p) => (
          <ProjectCard
            key={p.id}
            id={p.id}
            name={p.name}
            iteration="当前迭代"
            status="active"
            totalCases={0}
            coverage={0}
            pending={0}
            members={[]}
          />
        ))}
        <div className="bg-bg1 border border-dashed border-border2 rounded-[10px] p-4 flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-accent hover:text-accent transition-colors text-text3 min-h-[180px]">
          <span className="text-2xl">＋</span>
          <span className="text-[12.5px]">新建项目</span>
        </div>
      </div>
    </div>
  );
}
