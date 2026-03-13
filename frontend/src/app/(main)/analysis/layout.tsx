'use client';

import { FileText, GitBranch, Grid3x3, HeartPulse } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const tabs = [
	{
		href: '/analysis',
		label: '需求列表',
		icon: FileText,
		description: '管理需求文档，查看需求状态',
	},
	{
		href: '/analysis/diagnosis',
		label: 'AI 分析',
		icon: HeartPulse,
		description: '需求需求分析与测试点生成',
	},
	{
		href: '/analysis/scene-map',
		label: '场景地图',
		icon: GitBranch,
		description: '测试点可视化与确认',
	},
	{
		href: '/analysis/coverage',
		label: '覆盖追踪',
		icon: Grid3x3,
		description: '需求覆盖度矩阵',
	},
];

export default function AnalysisLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	const pathname = usePathname();

	return (
		<div className="flex flex-col" style={{ height: 'calc(100vh - 49px)' }}>
			<div className="flex items-center gap-1 px-4 py-2 border-b border-border bg-bg1">
				{tabs.map((tab) => {
					const Icon = tab.icon;
					const isActive =
						tab.href === '/analysis'
							? pathname === '/analysis'
							: pathname.startsWith(tab.href);
					return (
						<Link
							key={tab.href}
							href={tab.href}
							className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[13px] transition-colors ${
								isActive
									? 'bg-accent/10 text-accent font-medium'
									: 'text-text2 hover:text-text hover:bg-bg2'
							}`}
							title={tab.description}
						>
							<Icon className="w-3.5 h-3.5" />
							{tab.label}
						</Link>
					);
				})}
			</div>
			<div className="flex-1 overflow-y-auto">{children}</div>
		</div>
	);
}
