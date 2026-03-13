'use client';

import { AlertTriangle, History, Loader2, RotateCcw, Save } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface PromptConfig {
	module_key: string;
	prompt_text: string;
	updated_at: string | null;
	is_default?: boolean;
}

interface PromptHistoryItem {
	id: string;
	prompt_text: string;
	created_at: string;
	version: number;
}

const modules = [
	{
		key: 'diagnosis',
		label: '需求分析',
		description: '需求分析时的 AI 系统提示词',
	},
	{
		key: 'scene_map',
		label: '场景地图',
		description: '测试点提取与场景分类时的 AI 系统提示词',
	},
	{
		key: 'generation',
		label: '用例生成',
		description: '根据测试点生成用例步骤时的 AI 系统提示词',
	},
	{
		key: 'diagnosis_followup',
		label: '苏格拉底追问',
		description: '追问式对话时的 AI 系统提示词',
	},
	{
		key: 'diff',
		label: '需求 Diff 分析',
		description: '需求版本变更的测试影响分析时的 AI 系统提示词',
	},
	{
		key: 'exploratory',
		label: '探索性测试',
		description: '探索性测试建议生成时的 AI 系统提示词',
	},
];

export function PromptManager() {
	const [activeModule, setActiveModule] = useState(modules[0].key);
	const [prompts, setPrompts] = useState<Record<string, string>>({});
	const [originalPrompts, setOriginalPrompts] = useState<Record<string, string>>({});
	const [history, setHistory] = useState<PromptHistoryItem[]>([]);
	const [defaultModules, setDefaultModules] = useState<Set<string>>(new Set());
	const [loading, setLoading] = useState(true);
	const [saving, setSaving] = useState(false);
	const [showHistory, setShowHistory] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const loadPrompts = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const data = await api.get<PromptConfig[]>('/ai-config/prompts');
			const promptMap: Record<string, string> = {};
			for (const p of data) {
				promptMap[p.module_key] = p.prompt_text;
			}
			const defaults = new Set(data.filter((p) => p.is_default).map((p) => p.module_key));
			setDefaultModules(defaults);
			setPrompts(promptMap);
			setOriginalPrompts(promptMap);
		} catch {
			setError('加载 Prompt 配置失败');
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		loadPrompts();
	}, [loadPrompts]);

	const loadHistory = useCallback(async (moduleKey: string) => {
		try {
			const data = await api.get<PromptHistoryItem[]>(
				`/ai-config/prompts/${moduleKey}/history`,
			);
			setHistory(data);
		} catch {
			setHistory([]);
		}
	}, []);

	const handleSave = async () => {
		const currentText = prompts[activeModule];
		if (!currentText || currentText === originalPrompts[activeModule]) return;
		setSaving(true);
		setError(null);
		try {
			await api.put(`/ai-config/prompts/${activeModule}`, {
				prompt_text: currentText,
			});
			setOriginalPrompts((prev) => ({ ...prev, [activeModule]: currentText }));
		} catch {
			setError('保存失败，请重试');
		} finally {
			setSaving(false);
		}
	};

	const handleReset = async () => {
		try {
			await api.post(`/ai-config/prompts/${activeModule}/reset`);
			await loadPrompts();
		} catch {
			setError('重置失败');
		}
	};

	const handleRollback = async (historyId: string) => {
		try {
			await api.post(`/ai-config/prompts/${activeModule}/rollback/${historyId}`);
			await loadPrompts();
			setShowHistory(false);
		} catch {
			setError('回滚失败');
		}
	};

	const currentModule = modules.find((m) => m.key === activeModule) ?? modules[0];
	const currentText = prompts[activeModule] ?? '';
	const hasChanges = currentText !== (originalPrompts[activeModule] ?? '');

	if (loading) {
		return (
			<div className="py-16 text-center">
				<Loader2 className="w-8 h-8 text-text3 mx-auto mb-3 animate-spin" />
				<p className="text-[13px] text-text3">加载 Prompt 配置...</p>
			</div>
		);
	}

	return (
		<div>
			<div className="alert-banner mb-4">
				<AlertTriangle className="w-4 h-4" />
				<span className="text-[12.5px]">
				修改 System Prompt 会直接影响 AI 输出质量，建议在测试环境验证后再用于生产。每个模块保留最近 5
					次修改记录，可随时回滚。
				</span>
			</div>

			{error && (
				<div className="alert-banner mb-4">
					<AlertTriangle className="w-4 h-4" />
					<span>{error}</span>
				</div>
			)}

			{/* Module tabs */}
			<div className="flex flex-wrap gap-1.5 mb-4">
				{modules.map((m) => (
					<button
						key={m.key}
						type="button"
						className={`px-3 py-1.5 rounded-md text-[12px] transition-colors ${
							activeModule === m.key
								? 'bg-accent/10 text-accent font-medium border border-accent/25'
								: 'text-text3 hover:text-text2 hover:bg-bg2 border border-transparent'
						}`}
						onClick={() => {
							setActiveModule(m.key);
							setShowHistory(false);
						}}
					>
						{m.label}
					</button>
				))}
			</div>

			{/* Editor */}
			<div className="card p-4">
				<div className="flex items-center justify-between mb-3">
					<div>
						<h3 className="text-[14px] font-semibold text-text">
							{currentModule.label}
						</h3>
						<p className="text-[12px] text-text3 mt-0.5">
							{currentModule.description}
						</p>
						{defaultModules.has(activeModule) && (
							<span className="text-[10px] text-text3 bg-bg2 px-1.5 py-0.5 rounded font-mono">默认值</span>
						)}
					</div>
					<div className="flex items-center gap-2">
						<button
							type="button"
							className="btn btn-sm btn-ghost"
							onClick={() => {
								setShowHistory(!showHistory);
								if (!showHistory) loadHistory(activeModule);
							}}
						>
							<History className="w-3.5 h-3.5" />
							历史版本
						</button>
						<button
							type="button"
							className="btn btn-sm btn-ghost"
							onClick={handleReset}
						>
							<RotateCcw className="w-3.5 h-3.5" />
							重置为默认
						</button>
						<button
							type="button"
							className="btn btn-sm btn-primary"
							onClick={handleSave}
							disabled={!hasChanges || saving}
						>
							{saving ? (
								<Loader2 className="w-3.5 h-3.5 animate-spin" />
							) : (
								<Save className="w-3.5 h-3.5" />
							)}
							{saving ? '保存中...' : '保存'}
						</button>
					</div>
				</div>

				<textarea
					value={currentText}
					onChange={(e) =>
						setPrompts((prev) => ({
							...prev,
							[activeModule]: e.target.value,
						}))
					}
					className="input w-full font-mono text-[12px] leading-relaxed"
					style={{ minHeight: 320, resize: 'vertical' }}
					placeholder="输入系统 Prompt..."
				/>

				<div className="flex items-center justify-between mt-2">
					<span className="text-[11px] text-text3">
						{currentText.length} 字符
					</span>
					{hasChanges && (
						<span className="text-[11px] text-amber">有未保存的修改</span>
					)}
				</div>
			</div>

			{/* History panel */}
			{showHistory && (
				<div className="card p-4 mt-4">
					<h4 className="text-[13px] font-medium text-text mb-3">
						历史版本（最近 5 条）
					</h4>
					{history.length === 0 ? (
						<p className="text-[12px] text-text3">暂无历史版本</p>
					) : (
						<div className="flex flex-col gap-2">
							{history.map((h) => (
								<div
									key={h.id}
									className="flex items-center justify-between p-3 bg-bg2 rounded-md"
								>
									<div>
										<span className="text-[12px] font-mono text-text2">
											v{h.version}
										</span>
										<span className="text-[11px] text-text3 ml-3">
											{new Date(h.created_at).toLocaleString('zh-CN')}
										</span>
										<p className="text-[10.5px] text-text3 mt-0.5 font-mono truncate max-w-[400px]">
											{h.prompt_text?.slice(0, 80)}...
										</p>
									</div>
									<button
										type="button"
										className="btn btn-sm btn-ghost"
										onClick={() => handleRollback(h.id)}
									>
										<RotateCcw className="w-3 h-3" />
										回滚
									</button>
								</div>
							))}
						</div>
					)}
				</div>
			)}
		</div>
	);
}
