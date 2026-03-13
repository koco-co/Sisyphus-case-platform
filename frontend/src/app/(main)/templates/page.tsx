'use client';

import {
  Clock,
  Copy,
  Edit3,
  Eye,
  Filter,
  LayoutTemplate,
  Loader2,
  Plus,
  Search,
  Star,
  Trash2,
  X,
} from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { CustomSelect } from '@/components/ui/CustomSelect';
import {
  ApiError,
  type TemplateContentPayload,
  type TemplateDetailResponse,
  type TemplateListItem,
  templatesApi,
} from '@/lib/api';

interface TemplateStep {
  step: number;
  action: string;
  expected: string;
}

interface TemplateCardData {
  id: string;
  name: string;
  category: string;
  description: string;
  usageCount: number;
  createdAt: string;
  isBuiltin: boolean;
  status: string;
}

interface TemplatePreviewData extends TemplateCardData {
  precondition: string;
  steps: TemplateStep[];
  tags: string[];
  variableNames: string[];
}

interface TemplateFormState {
  name: string;
  category: string;
  description: string;
}

const emptyForm: TemplateFormState = {
  name: '',
  category: 'functional',
  description: '',
};

const categoryLabels: Record<string, string> = {
  functional: '功能测试',
  performance: '性能测试',
  security: '安全测试',
  compatibility: '兼容性测试',
  api: '接口测试',
};

const categoryPills: Record<string, string> = {
  functional: 'pill-green',
  performance: 'pill-amber',
  security: 'pill-red',
  compatibility: 'pill-blue',
  api: 'pill-purple',
};

const templatePresets: Record<
  string,
  {
    precondition: string;
    tags: string[];
    steps: Array<{ action: string; expected: string }>;
  }
> = {
  functional: {
    precondition: '已完成基础测试数据准备并拥有对应页面访问权限',
    tags: ['功能', '主流程'],
    steps: [
      {
        action: '进入{{template_name}}对应页面并准备测试数据',
        expected: '页面加载成功，基础信息展示完整',
      },
      {
        action: '执行主流程操作并提交',
        expected: '系统处理成功，返回结果符合预期',
      },
      {
        action: '补充异常输入或边界输入再次提交',
        expected: '系统给出明确校验提示，不产生脏数据',
      },
    ],
  },
  api: {
    precondition: '接口鉴权配置完成，已准备可复用请求参数',
    tags: ['API', '参数校验'],
    steps: [
      {
        action: '发送正常请求到{{template_name}}接口',
        expected: '返回 200 且响应体满足约定 Schema',
      },
      {
        action: '移除必填参数后再次请求',
        expected: '返回 4xx，错误字段与提示准确',
      },
      {
        action: '使用越权身份调用接口',
        expected: '请求被拒绝，且无敏感信息泄露',
      },
    ],
  },
  security: {
    precondition: '测试环境已开启审计日志和安全防护策略',
    tags: ['安全', '审计'],
    steps: [
      {
        action: '提交包含脚本注入的输入内容',
        expected: '输入被安全处理，不执行恶意脚本',
      },
      {
        action: '构造非法参数或 SQL 注入载荷',
        expected: '请求被拦截，系统无异常回显',
      },
      {
        action: '检查越权访问或 CSRF 场景',
        expected: '未授权请求被拒绝并记录审计日志',
      },
    ],
  },
  performance: {
    precondition: '已准备压测数据集并确认监控指标可观察',
    tags: ['性能', '稳定性'],
    steps: [
      {
        action: '使用基准并发数执行{{template_name}}主流程',
        expected: '响应时间满足目标阈值',
      },
      {
        action: '逐步提升并发与数据量',
        expected: '系统吞吐稳定，无明显错误率飙升',
      },
      {
        action: '观测关键资源指标并收集瓶颈信息',
        expected: 'CPU、内存、数据库连接等指标可追踪',
      },
    ],
  },
  compatibility: {
    precondition: '已准备多浏览器或多终端测试环境',
    tags: ['兼容性', '终端'],
    steps: [
      {
        action: '在主流浏览器或终端中打开{{template_name}}流程',
        expected: '页面结构、交互与样式展示一致',
      },
      {
        action: '执行相同业务操作并比对结果',
        expected: '功能结果一致，无端侧专属报错',
      },
      {
        action: '验证响应式布局与关键组件交互',
        expected: '布局不溢出，组件行为稳定',
      },
    ],
  },
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message || `请求失败（${error.status}）`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return '发生未知错误，请稍后重试。';
}

function formatDate(value: string): string {
  if (!value) {
    return '--';
  }
  return value.slice(0, 10);
}

function normalizeSummary(item: TemplateListItem): TemplateCardData {
  return {
    id: item.id,
    name: item.name,
    category: item.category,
    description: item.description ?? '',
    usageCount: item.usage_count,
    createdAt: item.created_at,
    isBuiltin: item.is_builtin ?? false,
    status: item.status ?? 'active',
  };
}

function normalizePreview(item: TemplateDetailResponse): TemplatePreviewData {
  const rawSteps = Array.isArray(item.template_content.steps) ? item.template_content.steps : [];
  const steps = rawSteps
    .map((step, index) => ({
      step:
        typeof step.step === 'number'
          ? step.step
          : typeof step.step_num === 'number'
            ? step.step_num
            : index + 1,
      action: typeof step.action === 'string' ? step.action : '',
      expected:
        typeof step.expected === 'string'
          ? step.expected
          : typeof step.expected_result === 'string'
            ? step.expected_result
            : '',
    }))
    .filter((step) => step.action || step.expected);

  const rawTags = Array.isArray(item.template_content.tags)
    ? item.template_content.tags.filter(
        (tag): tag is string => typeof tag === 'string' && tag.length > 0,
      )
    : [];
  const variableNames = Object.keys(item.variables ?? {}).filter(Boolean);

  return {
    ...normalizeSummary(item),
    precondition:
      typeof item.template_content.precondition === 'string'
        ? item.template_content.precondition
        : '',
    steps,
    tags: rawTags.length > 0 ? rawTags : variableNames.slice(0, 3),
    variableNames,
  };
}

function buildTemplateContent(form: TemplateFormState): TemplateContentPayload {
  const preset = templatePresets[form.category] ?? templatePresets.functional;
  const templateName = form.name.trim() || '测试模板';

  return {
    precondition: preset.precondition,
    tags: preset.tags,
    steps: preset.steps.map((step, index) => ({
      step: index + 1,
      action: step.action.replace('{{template_name}}', templateName),
      expected: step.expected,
    })),
  };
}

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<TemplateCardData[]>([]);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  const [previewId, setPreviewId] = useState<string | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<TemplatePreviewData | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [copiedTemplateId, setCopiedTemplateId] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formState, setFormState] = useState<TemplateFormState>(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const pendingDeleteTemplate = useRef<TemplateCardData | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadTemplates() {
      setLoading(true);
      setPageError(null);
      try {
        const data = await templatesApi.list();
        if (!cancelled) {
          setTemplates(data.items.map(normalizeSummary));
          setTotalCount(data.total);
        }
      } catch (error) {
        if (!cancelled) {
          setPageError(getErrorMessage(error));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadTemplates();

    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return templates.filter((template) => {
      if (categoryFilter && template.category !== categoryFilter) {
        return false;
      }
      if (keyword && !`${template.name} ${template.description}`.toLowerCase().includes(keyword)) {
        return false;
      }
      return true;
    });
  }, [categoryFilter, search, templates]);

  async function openPreview(templateId: string) {
    setPreviewId(templateId);
    setPreviewLoading(true);
    setPreviewError(null);
    try {
      const detail = await templatesApi.get(templateId);
      setPreviewTemplate(normalizePreview(detail));
    } catch (error) {
      setPreviewTemplate(null);
      setPreviewError(getErrorMessage(error));
    } finally {
      setPreviewLoading(false);
    }
  }

  function resetForm() {
    setEditingId(null);
    setFormState(emptyForm);
    setFormError(null);
  }

  function openCreateForm() {
    resetForm();
    setShowForm(true);
  }

  function openEditForm(template: TemplateCardData) {
    setEditingId(template.id);
    setFormState({
      name: template.name,
      category: template.category,
      description: template.description,
    });
    setFormError(null);
    setShowForm(true);
  }

  async function submitForm() {
    if (!formState.name.trim()) {
      setFormError('请输入模板名称。');
      return;
    }

    setSaving(true);
    setFormError(null);

    try {
      const payload = {
        name: formState.name.trim(),
        category: formState.category,
        description: formState.description.trim() || null,
      };

      const response = editingId
        ? await templatesApi.update(editingId, payload)
        : await templatesApi.create({
            ...payload,
            template_content: buildTemplateContent(formState),
            variables: {},
          });

      const nextSummary = normalizeSummary(response);
      setTemplates((prev) => {
        const exists = prev.some((item) => item.id === nextSummary.id);
        if (exists) {
          return prev.map((item) => (item.id === nextSummary.id ? nextSummary : item));
        }
        return [nextSummary, ...prev];
      });
      setTotalCount((prev) => (editingId ? prev : prev + 1));

      setPreviewId(response.id);
      setPreviewTemplate(normalizePreview(response));
      setPreviewError(null);
      setShowForm(false);
      resetForm();
    } catch (error) {
      setFormError(getErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  function handleDelete(template: TemplateCardData) {
    if (template.isBuiltin) {
      return;
    }
    pendingDeleteTemplate.current = template;
    setDeleteConfirmOpen(true);
  }

  async function executeDelete() {
    const template = pendingDeleteTemplate.current;
    setDeleteConfirmOpen(false);
    pendingDeleteTemplate.current = null;
    if (!template) {
      return;
    }

    setDeletingId(template.id);
    setPageError(null);
    try {
      await templatesApi.delete(template.id);
      setTemplates((prev) => prev.filter((item) => item.id !== template.id));
      setTotalCount((prev) => Math.max(prev - 1, 0));
      if (previewId === template.id) {
        setPreviewId(null);
        setPreviewTemplate(null);
        setPreviewError(null);
      }
    } catch (error) {
      setPageError(getErrorMessage(error));
    } finally {
      setDeletingId(null);
    }
  }

  async function handleCopyTemplateId() {
    if (!previewTemplate) {
      return;
    }

    try {
      await navigator.clipboard.writeText(previewTemplate.id);
      setCopiedTemplateId(previewTemplate.id);
      window.setTimeout(() => {
        setCopiedTemplateId((current) => (current === previewTemplate.id ? null : current));
      }, 2000);
    } catch {
      setPreviewError('浏览器未允许复制剪贴板，请手动复制模板 ID。');
    }
  }

  const [activeTab, setActiveTab] = useState<'case' | 'prompt'>('case');

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <LayoutTemplate className="w-5 h-5 text-accent" />
          <h1 className="font-display text-lg font-bold text-text">模板库</h1>
          <span className="pill pill-gray text-[10px]">{totalCount} 个模板</span>
          <div className="flex items-center bg-bg2 rounded-lg p-0.5 ml-2">
            <button
              type="button"
              className={`px-3 py-1 rounded-md text-[12px] transition-colors ${
                activeTab === 'case'
                  ? 'bg-bg1 text-text font-medium shadow-sm'
                  : 'text-text3 hover:text-text2'
              }`}
              onClick={() => setActiveTab('case')}
            >
              用例结构模板
            </button>
            <button
              type="button"
              className={`px-3 py-1 rounded-md text-[12px] transition-colors ${
                activeTab === 'prompt'
                  ? 'bg-bg1 text-text font-medium shadow-sm'
                  : 'text-text3 hover:text-text2'
              }`}
              onClick={() => setActiveTab('prompt')}
            >
              Prompt 模板
            </button>
          </div>
        </div>
        <button type="button" className="btn btn-primary" onClick={openCreateForm}>
          <Plus className="w-3.5 h-3.5" />
          新建模板
        </button>
      </div>

      {activeTab === 'prompt' && (
        <div className="card p-6 text-center">
          <LayoutTemplate className="w-12 h-12 text-text3 mx-auto mb-3 opacity-20" />
          <p className="text-[13px] text-text3">Prompt 模板功能即将上线</p>
          <p className="text-[12px] text-text3/60 mt-1">
            在「设置 → Prompt 管理」中可编辑系统级 Prompt
          </p>
        </div>
      )}

      {activeTab === 'case' && (
      <>
      {pageError && (
        <div className="alert-banner mb-6">
          <LayoutTemplate className="w-4 h-4" />
          <span>{pageError}</span>
        </div>
      )}

      {showForm && (
        <div className="card p-4 mb-6">
          <div className="flex items-center justify-between gap-3 mb-4">
            <div>
              <h2 className="text-[14px] font-semibold text-text">
                {editingId ? '编辑模板' : '新建模板'}
              </h2>
              <p className="text-[12px] text-text3 mt-1">
                {editingId
                  ? '可调整模板名称、分类与描述，模板内容将保留现有结构。'
                  : '新建模板会自动生成一份可预览的基础步骤草稿，便于后续补充。'}
              </p>
            </div>
            <button
              type="button"
              className="text-text3 hover:text-text transition-colors"
              onClick={() => {
                setShowForm(false);
                resetForm();
              }}
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex gap-3 mb-3">
            <input
              value={formState.name}
              onChange={(event) =>
                setFormState((prev) => ({
                  ...prev,
                  name: event.target.value,
                }))
              }
              placeholder="模板名称"
              className="input flex-1"
            />
            <CustomSelect
              value={formState.category}
              onChange={(value) =>
                setFormState((prev) => ({
                  ...prev,
                  category: value,
                }))
              }
              options={Object.entries(categoryLabels).map(([key, label]) => ({
                value: key,
                label,
              }))}
              className="min-w-[120px]"
            />
          </div>

          <textarea
            value={formState.description}
            onChange={(event) =>
              setFormState((prev) => ({
                ...prev,
                description: event.target.value,
              }))
            }
            placeholder="模板描述..."
            rows={3}
            className="input w-full resize-y mb-3"
          />

          {formError && <p className="text-[12px] text-red mb-3">{formError}</p>}

          <div className="flex gap-2">
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={submitForm}
              disabled={saving}
            >
              {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
              {editingId ? '保存修改' : '新建模板'}
            </button>
            <button
              type="button"
              className="btn btn-sm"
              onClick={() => {
                setShowForm(false);
                resetForm();
              }}
            >
              取消
            </button>
          </div>
        </div>
      )}

      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text3" />
          <input
            type="text"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="搜索模板..."
            className="input w-full pl-8"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <Filter className="w-3.5 h-3.5 text-text3" />
          <button
            type="button"
            className={`px-2.5 py-1 rounded-full text-[11px] font-medium transition-colors ${
              !categoryFilter
                ? 'bg-accent/10 text-accent border border-accent/25'
                : 'text-text3 hover:bg-bg2 border border-transparent'
            }`}
            onClick={() => setCategoryFilter('')}
          >
            全部
          </button>
          {Object.entries(categoryLabels).map(([key, label]) => (
            <button
              type="button"
              key={key}
              className={`px-2.5 py-1 rounded-full text-[11px] font-medium transition-colors ${
                categoryFilter === key
                  ? 'bg-accent/10 text-accent border border-accent/25'
                  : 'text-text3 hover:bg-bg2 border border-transparent'
              }`}
              onClick={() => setCategoryFilter(key)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-6">
        <div className="flex-1">
          <div className="grid-3">
            {loading && (
              <div className="card py-12 text-center text-text3" style={{ gridColumn: '1 / -1' }}>
                <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin" />
                <p className="text-[13px]">正在加载模板数据...</p>
              </div>
            )}

            {!loading &&
              filtered.map((template) => (
                <div key={template.id} className="card card-hover flex flex-col">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="text-sm font-semibold text-text leading-tight flex-1">
                      {template.name}
                    </h4>
                    <span
                      className="shrink-0 ml-2"
                      title={template.isBuiltin ? '内置模板' : '自定义模板'}
                    >
                      <Star
                        className={`w-3.5 h-3.5 ${
                          template.isBuiltin ? 'text-amber fill-amber' : 'text-text3'
                        }`}
                      />
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-1.5 mb-2">
                    <span
                      className={`pill ${categoryPills[template.category] || 'pill-gray'} text-[10px] self-start`}
                    >
                      {categoryLabels[template.category] || template.category}
                    </span>
                    <span className="tag text-[10px]">
                      {template.isBuiltin ? '内置' : '自定义'}
                    </span>
                  </div>

                  {template.description && (
                    <p className="text-[11.5px] text-text3 leading-relaxed mb-3 line-clamp-2 flex-1">
                      {template.description}
                    </p>
                  )}

                  {!template.description && (
                    <p className="text-[11.5px] text-text3 leading-relaxed mb-3 flex-1">
                      暂无描述，可通过编辑补充模板适用范围与关键约束。
                    </p>
                  )}

                  <div className="flex items-center justify-between mt-auto pt-2 border-t border-border/50">
                    <div className="flex items-center gap-3 text-[11px] text-text3">
                      <span className="flex items-center gap-1">
                        <Copy className="w-3 h-3" />
                        {template.usageCount}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(template.createdAt)}
                      </span>
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        className="btn btn-sm btn-ghost"
                        onClick={() => void openPreview(template.id)}
                        title="预览"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm btn-ghost"
                        title="编辑"
                        onClick={() => openEditForm(template)}
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm btn-ghost text-red disabled:opacity-40"
                        onClick={() => void handleDelete(template)}
                        title={template.isBuiltin ? '内置模板不可删除' : '删除'}
                        disabled={template.isBuiltin || deletingId === template.id}
                      >
                        {deletingId === template.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              ))}

            {!loading && filtered.length === 0 && (
              <div className="card py-12 text-center text-text3" style={{ gridColumn: '1 / -1' }}>
                <LayoutTemplate className="w-12 h-12 mx-auto mb-3 opacity-20" />
                <p className="text-[13px]">暂无匹配模板</p>
              </div>
            )}
          </div>
        </div>

        {(previewId || previewLoading || previewError) && (
          <div className="w-80 shrink-0">
            <div className="card sticky top-16">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-[13px] font-semibold text-text">模板预览</h3>
                <button
                  type="button"
                  className="text-text3 hover:text-text2 transition-colors"
                  onClick={() => {
                    setPreviewId(null);
                    setPreviewTemplate(null);
                    setPreviewError(null);
                  }}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {previewLoading && (
                <div className="py-12 text-center text-text3">
                  <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin" />
                  <p className="text-[12px]">正在加载模板详情...</p>
                </div>
              )}

              {!previewLoading && previewError && (
                <div className="text-[12px] text-red leading-relaxed">{previewError}</div>
              )}

              {!previewLoading && !previewError && previewTemplate && (
                <>
                  <h4 className="text-sm font-semibold text-text mb-2">{previewTemplate.name}</h4>
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    <span
                      className={`pill ${
                        categoryPills[previewTemplate.category] || 'pill-gray'
                      } text-[10px]`}
                    >
                      {categoryLabels[previewTemplate.category] || previewTemplate.category}
                    </span>
                    <span className="tag text-[10px]">
                      {previewTemplate.isBuiltin ? '内置模板' : '自定义模板'}
                    </span>
                  </div>

                  <p className="text-[12px] text-text3 leading-relaxed mb-4">
                    {previewTemplate.description || '暂无模板描述。'}
                  </p>

                  {previewTemplate.precondition && (
                    <>
                      <div className="text-[11px] font-semibold text-text2 mb-2 uppercase tracking-wider">
                        前置条件
                      </div>
                      <div className="p-2.5 bg-bg2 border border-border rounded-lg text-[11px] text-text3 mb-4 leading-relaxed">
                        {previewTemplate.precondition}
                      </div>
                    </>
                  )}

                  {previewTemplate.tags.length > 0 && (
                    <>
                      <div className="text-[11px] font-semibold text-text2 mb-2 uppercase tracking-wider">
                        标签
                      </div>
                      <div className="flex flex-wrap gap-1 mb-4">
                        {previewTemplate.tags.map((tag) => (
                          <span key={tag} className="tag text-[10px]">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </>
                  )}

                  {previewTemplate.variableNames.length > 0 && (
                    <>
                      <div className="text-[11px] font-semibold text-text2 mb-2 uppercase tracking-wider">
                        可替换变量
                      </div>
                      <div className="flex flex-wrap gap-1 mb-4">
                        {previewTemplate.variableNames.map((variable) => (
                          <span key={variable} className="tag text-[10px]">
                            {variable}
                          </span>
                        ))}
                      </div>
                    </>
                  )}

                  <div className="text-[11px] font-semibold text-text2 mb-2 uppercase tracking-wider">
                    步骤预览
                  </div>
                  <div className="flex flex-col gap-2 mb-4">
                    {previewTemplate.steps.length > 0 ? (
                      previewTemplate.steps.map((step) => (
                        <div
                          key={`${step.step}-${step.action}`}
                          className="p-2.5 bg-bg2 border border-border rounded-lg"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span className="w-5 h-5 rounded-full bg-accent/15 text-accent text-[10px] font-mono font-bold flex items-center justify-center shrink-0">
                              {step.step}
                            </span>
                            <span className="text-[12px] text-text">{step.action}</span>
                          </div>
                          <div className="pl-7 text-[11px] text-accent/80">→ {step.expected}</div>
                        </div>
                      ))
                    ) : (
                      <div className="p-3 bg-bg2 border border-dashed border-border rounded-lg text-[12px] text-text3">
                        当前模板还没有配置步骤内容。
                      </div>
                    )}
                  </div>

                  <button
                    type="button"
                    className="btn btn-primary btn-sm w-full justify-center"
                    onClick={() => void handleCopyTemplateId()}
                  >
                    <Copy className="w-3.5 h-3.5" />
                    {copiedTemplateId === previewTemplate.id ? '模板 ID 已复制' : '复制模板 ID'}
                  </button>
                  <p className="text-[11px] text-text3 mt-2 leading-relaxed">
                    可将模板 ID 用于模板驱动接口联调，或后续工作台模板生成链路。
                  </p>
                </>
              )}
            </div>
          </div>
        )}
      </div>
      <ConfirmDialog
        open={deleteConfirmOpen}
        onConfirm={() => void executeDelete()}
        onCancel={() => {
          setDeleteConfirmOpen(false);
          pendingDeleteTemplate.current = null;
        }}
        title="删除模板"
        description={`确认删除模板\u201c${pendingDeleteTemplate.current?.name ?? ''}\u201d吗？`}
        confirmText="删除"
        variant="danger"
      />
      </>
      )}
    </div>
  );
}
