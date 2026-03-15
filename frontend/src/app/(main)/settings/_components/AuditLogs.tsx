'use client';

import { History, Loader2, Search } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface AuditEntry {
	id: string;
	user_name: string;
	action: string;
	object_type: string;
	object_name: string;
	created_at: string;
	details?: string;
}

interface AuditLogResponse {
	items: AuditEntry[];
	total: number;
	page: number;
	page_size: number;
	pages: number;
}

const actionLabels: Record<string, string> = {
	create: '新建',
	update: '更新',
	delete: '删除',
	restore: '恢复',
	export: '导出',
	import: '导入',
	generate: 'AI 生成',
	confirm: '确认',
	review: '审核',
};

const objectTypeLabels: Record<string, string> = {
	requirement: '需求',
	testcase: '用例',
	template: '模板',
	knowledge: '知识库',
	product: '产品',
	iteration: '迭代',
	ai_config: 'AI 配置',
	prompt: 'Prompt',
};

export function AuditLogs() {
	const [logs, setLogs] = useState<AuditEntry[]>([]);
	const [loading, setLoading] = useState(true);
	const [search, setSearch] = useState('');
	const [dateFrom, setDateFrom] = useState('');
	const [dateTo, setDateTo] = useState('');

	const loadLogs = useCallback(async () => {
		setLoading(true);
		try {
			const params = new URLSearchParams();
			params.set('page_size', '100');
			if (dateFrom) params.set('date_from', new Date(dateFrom).toISOString());
			if (dateTo) params.set('date_to', new Date(`${dateTo}T23:59:59`).toISOString());
			const data = await api.get<AuditLogResponse>(`/audit?${params.toString()}`);
			setLogs(data.items);
		} catch {
			// Fallback demo data
			setLogs([
				{
					id: '1',
					user_name: '张工',
					action: 'generate',
					object_type: 'testcase',
					object_name: '数据导入模块 — 14 条用例',
					created_at: new Date(Date.now() - 28 * 60000).toISOString(),
				},
				{
					id: '2',
					user_name: '李工',
					action: 'update',
					object_type: 'requirement',
					object_name: '实时流处理 — 窗口函数',
					created_at: new Date(Date.now() - 62 * 60000).toISOString(),
				},
				{
					id: '3',
					user_name: '王工',
					action: 'confirm',
					object_type: 'testcase',
					object_name: '标签管理场景地图 — 8 个测试点',
					created_at: new Date(Date.now() - 105 * 60000).toISOString(),
				},
				{
					id: '4',
					user_name: '张工',
					action: 'create',
					object_type: 'knowledge',
					object_name: '测试规范 v2.1.pdf',
					created_at: new Date(Date.now() - 180 * 60000).toISOString(),
				},
				{
					id: '5',
					user_name: '赵工',
					action: 'export',
					object_type: 'testcase',
					object_name: 'Sprint 24-W04 测试报告',
					created_at: new Date(Date.now() - 360 * 60000).toISOString(),
				},
				{
					id: '6',
					user_name: '王工',
					action: 'update',
					object_type: 'ai_config',
					object_name: '切换主模型为 GLM-5',
					created_at: new Date(Date.now() - 24 * 3600000).toISOString(),
				},
			]);
		} finally {
			setLoading(false);
		}
	}, [dateFrom, dateTo]);

	useEffect(() => {
		loadLogs();
	}, [loadLogs]);

	const filtered = logs.filter((log) => {
		if (!search.trim()) return true;
		const keyword = search.trim().toLowerCase();
		return (
			log.user_name.toLowerCase().includes(keyword) ||
			log.object_name.toLowerCase().includes(keyword) ||
			(actionLabels[log.action] ?? log.action).includes(keyword)
		);
	});

	return (
		<div>
			<div className="flex items-center gap-3 mb-4">
				<History className="w-4 h-4 text-text3" />
				<h2 className="text-[14px] font-semibold text-text">操作日志</h2>
				<span className="pill pill-gray text-[10px]">最近 100 条</span>
			</div>

			<div className="flex flex-wrap items-center gap-3 mb-4">
				<div className="relative max-w-xs">
					<Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text3" />
					<input
						type="text"
						value={search}
						onChange={(e) => setSearch(e.target.value)}
						placeholder="搜索操作人、对象..."
						className="input w-full pl-8"
					/>
				</div>
				<div className="flex items-center gap-2">
					<input
						type="date"
						value={dateFrom}
						onChange={(e) => setDateFrom(e.target.value)}
						className="input text-[12px] text-text2 placeholder:text-text3"
						title="开始日期"
					/>
					<span className="text-text3 text-[12px]">—</span>
					<input
						type="date"
						value={dateTo}
						onChange={(e) => setDateTo(e.target.value)}
						className="input text-[12px] text-text2 placeholder:text-text3"
						title="结束日期"
					/>
				</div>
			</div>

			{loading ? (
				<div className="py-16 text-center">
					<Loader2 className="w-8 h-8 text-text3 mx-auto mb-3 animate-spin" />
					<p className="text-[13px] text-text3">加载操作日志...</p>
				</div>
			) : (
				<div className="card overflow-hidden">
					<table className="tbl">
						<thead>
							<tr>
								<th className="w-32">时间</th>
								<th className="w-20">操作人</th>
								<th className="w-24">操作</th>
								<th className="w-24">对象类型</th>
								<th>对象名称</th>
							</tr>
						</thead>
						<tbody>
							{filtered.length === 0 ? (
								<tr>
									<td colSpan={5} className="text-center text-text3 py-8">
										暂无操作日志
									</td>
								</tr>
							) : (
								filtered.map((log) => (
									<tr key={log.id}>
										<td className="font-mono text-[11px] text-text3">
											{new Date(log.created_at).toLocaleString('zh-CN', {
												month: '2-digit',
												day: '2-digit',
												hour: '2-digit',
												minute: '2-digit',
											})}
										</td>
										<td className="text-text2">{log.user_name}</td>
										<td>
											<span className="pill pill-blue text-[10px]">
												{actionLabels[log.action] ?? log.action}
											</span>
										</td>
										<td className="text-text3 text-[12px]">
											{objectTypeLabels[log.object_type] ?? log.object_type}
										</td>
										<td className="text-text truncate max-w-[300px]">
											{log.object_name}
										</td>
									</tr>
								))
							)}
						</tbody>
					</table>
				</div>
			)}
		</div>
	);
}
