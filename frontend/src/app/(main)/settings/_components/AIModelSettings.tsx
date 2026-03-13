'use client';

import { Bot, Check, ChevronDown, Eye, EyeOff, Key, Loader2, Save, Zap } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { ConnectionTestButton } from '@/components/ui/ConnectionTestButton';
import { ParamTooltip } from '@/components/ui/ParamTooltip';
import { useAiConfig } from '@/hooks/useAiConfig';
import { api } from '@/lib/api';
import { VectorModelSettings } from './VectorModelSettings';

// ─── Provider / Model 类型 ─────────────────────────────────────────

interface ModelOption {
  id: string;
  name: string;
  description: string;
  recommended?: boolean;
}

interface ProviderInfo {
  id: string;
  name: string;
  description: string;
  api_key_placeholder: string;
  requires_base_url?: boolean;
  default_base_url?: string;
  models: ModelOption[];
}

// ─── 参数滑块配置 ─────────────────────────────────────────────────

interface SliderParam {
  label: string;
  key: 'temperature' | 'maxTokens' | 'topP' | 'concurrency';
  min: number;
  max: number;
  step: number;
  initial: number;
  fmt: (v: number) => string;
  tooltip: string;
}

const sliderParams: SliderParam[] = [
  {
    label: 'Temperature',
    key: 'temperature',
    min: 0,
    max: 2,
    step: 0.1,
    initial: 0.7,
    fmt: (v) => v.toFixed(1),
    tooltip:
      '控制输出随机性。0 = 确定性最高，适合结构化输出；1+ = 更有创造性。推荐用例生成场景使用 0.3~0.7。',
  },
  {
    label: 'Max Tokens',
    key: 'maxTokens',
    min: 256,
    max: 8192,
    step: 256,
    initial: 4096,
    fmt: (v) => String(v),
    tooltip:
      '单次生成的最大 token 数。用例生成建议 4096+，分析对话 2048 即可。过大会增加响应时间和费用。',
  },
  {
    label: 'Top-P',
    key: 'topP',
    min: 0,
    max: 1,
    step: 0.05,
    initial: 0.95,
    fmt: (v) => v.toFixed(2),
    tooltip:
      '核采样参数。0.95 表示从概率前 95% 的 token 中采样。配合 temperature 使用，一般保持 0.9~0.95 即可。',
  },
  {
    label: '并发数',
    key: 'concurrency',
    min: 1,
    max: 10,
    step: 1,
    initial: 3,
    fmt: (v) => String(v),
    tooltip: '同时发送给 LLM 的请求数。过高可能触发 API 限流。建议智谱 ≤5，DashScope ≤3。',
  },
];

// ─── Provider 选择卡片 ────────────────────────────────────────────

function ProviderCard({
  provider,
  active,
  onClick,
  disabled,
}: {
  provider: ProviderInfo;
  active: boolean;
  onClick: () => void;
  disabled: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`relative flex flex-col gap-2 p-4 rounded-xl border text-left w-full transition-all
        ${
          active
            ? 'bg-sy-accent/5 border-sy-accent/40 shadow-[0_0_0_1px_rgba(0,217,163,0.2)]'
            : 'bg-sy-bg-2 border-sy-border hover:border-sy-border-2'
        }
        disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      {active && (
        <span className="absolute top-3 right-3 flex items-center justify-center w-5 h-5 rounded-full bg-sy-accent/15">
          <Check className="w-3 h-3 text-sy-accent" />
        </span>
      )}
      <div>
        <div className="text-[13px] font-semibold text-sy-text">{provider.name}</div>
        <div className="font-mono text-[10.5px] text-sy-text-3 mt-0.5">{provider.id}</div>
      </div>
      <p className="text-[11.5px] text-sy-text-3 leading-relaxed line-clamp-2">
        {provider.description}
      </p>
      {active && (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-sy-accent/10 text-sy-accent text-[10px] font-mono w-fit">
          当前生效
        </span>
      )}
    </button>
  );
}

// ─── 主组件 ──────────────────────────────────────────────────────

export function AIModelSettings() {
  const { effectiveConfig, loading, saving, error, saveGlobalConfig } = useAiConfig();

  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [providersLoading, setProvidersLoading] = useState(true);

  const [activeProviderId, setActiveProviderId] = useState<string>('zhipu');
  const [activeModelId, setActiveModelId] = useState<string>('glm-4-flash');
  const [apiKey, setApiKey] = useState('');
  const [keyVisible, setKeyVisible] = useState(false);
  const [baseUrl, setBaseUrl] = useState('');

  const [paramVals, setParamVals] = useState<Record<SliderParam['key'], number>>({
    temperature: 0.7,
    maxTokens: 4096,
    topP: 0.95,
    concurrency: 3,
  });
  const [saved, setSaved] = useState(false);

  // ── 拉取 providers 列表 ──
  useEffect(() => {
    api
      .get<{ providers: ProviderInfo[] }>('/ai-config/providers')
      .then((data) => setProviders(data.providers ?? []))
      .catch(() => setProviders([]))
      .finally(() => setProvidersLoading(false));
  }, []);

  // ── 从 effectiveConfig 初始化表单 ──
  // biome-ignore lint/correctness/useExhaustiveDependencies: activeProviderId intentionally excluded to avoid init loop
  useEffect(() => {
    if (!effectiveConfig || providers.length === 0) return;

    const modelId = effectiveConfig.llm_model ?? 'glm-4-flash';
    // 找到该 model 属于哪个 provider
    const ownerProvider = providers.find((p) => p.models.some((m) => m.id === modelId));
    if (ownerProvider) {
      setActiveProviderId(ownerProvider.id);
    }
    setActiveModelId(modelId);

    const outputPreference = effectiveConfig.output_preference ?? {};
    setParamVals({
      temperature: effectiveConfig.llm_temperature ?? 0.7,
      maxTokens: Number(outputPreference.max_tokens ?? 4096),
      topP: Number(outputPreference.top_p ?? 0.95),
      concurrency: Number(outputPreference.concurrency ?? 3),
    });

    if (effectiveConfig.api_keys) {
      const keys = effectiveConfig.api_keys as Record<string, string>;
      const provId = ownerProvider?.id ?? activeProviderId;
      setApiKey(keys[provId] ?? '');
    }
  }, [effectiveConfig, providers]);

  // ── 当切换提供商时，切换到推荐模型 + 清空 API Key 显示 ──
  const handleProviderChange = (providerId: string) => {
    setActiveProviderId(providerId);
    setKeyVisible(false);
    const prov = providers.find((p) => p.id === providerId);
    if (prov) {
      const recommended = prov.models.find((m) => m.recommended) ?? prov.models[0];
      if (recommended) setActiveModelId(recommended.id);
      setBaseUrl(prov.default_base_url ?? '');
    }
    // 恢复该提供商已保存的 key
    if (effectiveConfig?.api_keys) {
      const keys = effectiveConfig.api_keys as Record<string, string>;
      setApiKey(keys[providerId] ?? '');
    } else {
      setApiKey('');
    }
  };

  const activeProvider = useMemo(
    () => providers.find((p) => p.id === activeProviderId),
    [providers, activeProviderId],
  );

  const handleSave = async () => {
    const apiKeys: Record<string, string> = {};
    const trimmedKey = apiKey.trim();
    // Only send the key if it was actually changed (not a masked value like "sk-a***z789")
    if (trimmedKey && !trimmedKey.includes('***')) {
      apiKeys[activeProviderId] = trimmedKey;
    }

    const ok = await saveGlobalConfig({
      llm_model: activeModelId,
      llm_temperature: paramVals.temperature,
      output_preference: {
        max_tokens: paramVals.maxTokens,
        top_p: paramVals.topP,
        concurrency: paramVals.concurrency,
        ...(baseUrl.trim() ? { base_url: baseUrl.trim() } : {}),
      },
      api_keys: Object.keys(apiKeys).length > 0 ? apiKeys : null,
    });
    if (!ok) return;
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2000);
  };

  const isDisabled = loading || saving || providersLoading;
  type VectorConfig = { provider?: string; model?: string; dimensions?: number; collection?: string } | null;
  const vectorCfg = (effectiveConfig?.vector_config ?? null) as VectorConfig;

  return (
    <>
    <div>
      {/* ── 标题 ── */}
      <div className="sec-header">
        <Bot className="w-4 h-4 text-sy-accent" />
        <span className="sec-title">AI 模型配置</span>
      </div>

      {error && (
        <div className="mb-4 px-3 py-2 rounded-md bg-sy-danger/8 border border-sy-danger/20 text-sy-danger text-[12.5px]">
          {error}
        </div>
      )}

      {/* ── Step 1：选择模型提供商 ── */}
      <div className="mb-1">
        <p className="text-[12px] text-sy-text-3 mb-3">
          <span className="font-mono text-sy-accent mr-1.5">01</span>
          选择模型提供商
          <span className="ml-2 text-[11px]">（平台已完成底层适配，选择后填入 API Key 即可）</span>
        </p>

        {providersLoading ? (
          <div className="flex items-center gap-2 py-6 text-[12px] text-sy-text-3">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> 加载提供商列表...
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            {providers.map((provider) => (
              <ProviderCard
                key={provider.id}
                provider={provider}
                active={activeProviderId === provider.id}
                onClick={() => handleProviderChange(provider.id)}
                disabled={isDisabled}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── Step 2：选择模型版本 ── */}
      {activeProvider && (
        <div className="mb-6">
          <p className="text-[12px] text-sy-text-3 mb-3">
            <span className="font-mono text-sy-accent mr-1.5">02</span>
            选择{activeProvider.name}模型版本
          </p>
          <div className="relative w-full max-w-xs">
            <select
              value={activeModelId}
              onChange={(e) => setActiveModelId(e.target.value)}
              disabled={isDisabled}
              className="w-full appearance-none bg-sy-bg-2 border border-sy-border rounded-lg px-3 py-2 text-[13px] text-sy-text
                         pr-8 focus:border-sy-accent focus:outline-none transition-colors
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {activeProvider.models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                  {model.recommended ? ' ★ 推荐' : ''}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-sy-text-3 pointer-events-none" />
          </div>
          {/* 当前选中模型说明 */}
          {activeProvider.models.find((m) => m.id === activeModelId) && (
            <p className="mt-2 text-[11.5px] text-sy-text-3">
              {activeProvider.models.find((m) => m.id === activeModelId)?.description}
            </p>
          )}
        </div>
      )}

      <hr className="divider" />

      {/* ── Step 3：API Key ── */}
      {activeProvider && (
        <div className="mb-6">
          <div className="sec-header">
            <Key className="w-4 h-4 text-sy-accent" />
            <span className="sec-title">{activeProvider.name} API Key</span>
          </div>
          <div className="card">
            <p className="text-[12.5px] text-sy-text-2 mb-1.5">{activeProvider.name} Secret Key</p>
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <input
                  type={keyVisible ? 'text' : 'password'}
                  className="w-full bg-sy-bg-2 border border-sy-border rounded-md px-3 py-1.5 text-[12.5px] text-sy-text font-mono pr-9
                             focus:border-sy-accent focus:outline-none transition-colors disabled:opacity-50"
                  placeholder={activeProvider.api_key_placeholder}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  disabled={isDisabled}
                />
                <button
                  type="button"
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-sy-text-3 hover:text-sy-text-2 transition-colors"
                  onClick={() => setKeyVisible((v) => !v)}
                >
                  {keyVisible ? (
                    <EyeOff className="w-3.5 h-3.5" />
                  ) : (
                    <Eye className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>
              <ConnectionTestButton
                testUrl={`/api/ai-config/test-llm?provider=${activeProviderId}`}
                label="测试连接"
              />
            </div>
            <p className="mt-2 text-[11px] text-sy-text-3">
              API Key 保存在数据库中（加密存储），优先于 .env 环境变量。留空则使用服务器 .env
              中的配置。
            </p>
            {/* ── Base URL（Ollama 等需要自定义地址的提供商） ── */}
            {activeProvider.requires_base_url && (
              <div className="mt-4 pt-3 border-t border-sy-border">
                <p className="text-[12.5px] text-sy-text-2 mb-1.5">Base URL</p>
                <input
                  type="text"
                  className="w-full bg-sy-bg-2 border border-sy-border rounded-md px-3 py-1.5 text-[12.5px] text-sy-text font-mono
                             focus:border-sy-accent focus:outline-none transition-colors disabled:opacity-50"
                  placeholder={activeProvider.default_base_url ?? 'http://localhost:11434'}
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  disabled={isDisabled}
                />
                <p className="mt-1.5 text-[11px] text-sy-text-3">
                  Ollama 服务地址，默认为 http://localhost:11434。如在远程服务器部署请修改为对应地址。
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      <hr className="divider" />

      {/* ── 参数调整 ── */}
      <div className="sec-header">
        <Zap className="w-4 h-4 text-sy-accent" />
        <span className="sec-title">参数调整</span>
      </div>
      <div className="card flex flex-col gap-5">
        {sliderParams.map((param) => (
          <div key={param.key}>
            <div className="flex justify-between mb-1.5">
              <span className="text-[12.5px] text-sy-text-2 flex items-center gap-1">
                {param.label}
                <ParamTooltip content={param.tooltip} />
              </span>
              <span className="font-mono text-xs text-sy-accent">
                {param.fmt(paramVals[param.key])}
              </span>
            </div>
            <input
              type="range"
              min={param.min}
              max={param.max}
              step={param.step}
              value={paramVals[param.key]}
              onChange={(e) =>
                setParamVals((prev) => ({ ...prev, [param.key]: Number(e.target.value) }))
              }
              className="w-full accent-sy-accent"
              disabled={isDisabled}
            />
          </div>
        ))}

        <div className="flex items-center justify-between pt-2 border-t border-sy-border">
          <div className="text-[12px] text-sy-text-3">
            当前配置：
            <span className="text-sy-text-2 ml-1">
              {activeProvider?.name} / {activeModelId}
            </span>
          </div>
          <button
            type="button"
            className="btn btn-sm btn-primary"
            onClick={() => void handleSave()}
            disabled={isDisabled}
          >
            {saving ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            {saved ? '已保存' : saving ? '保存中...' : '保存配置'}
          </button>
        </div>
      </div>
    </div>
    <VectorModelSettings
      vectorConfig={vectorCfg}
      onSave={saveGlobalConfig}
      saving={saving}
    />
    </>
  );
}
