'use client';

import { Bot, Check, Loader2, Save, Star, Zap } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { ConnectionTestButton } from '@/components/ui/ConnectionTestButton';
import { ParamTooltip } from '@/components/ui/ParamTooltip';
import { useAiConfig } from '@/hooks/useAiConfig';

interface ModelInfo {
  name: string;
  provider: string;
  id: string;
  speed: number;
  quality: number;
  cost: number;
  scene: string;
}

const models: ModelInfo[] = [
  {
    name: 'GLM-4-Flash',
    provider: '智谱AI',
    id: 'glm-4-flash',
    speed: 5,
    quality: 4,
    cost: 5,
    scene: '需求诊断 / 苏格拉底追问',
  },
  {
    name: 'Qwen-Max',
    provider: '阿里云',
    id: 'qwen-max',
    speed: 3,
    quality: 5,
    cost: 3,
    scene: '复杂用例 CoT 生成',
  },
  {
    name: 'GPT-4o',
    provider: 'OpenAI',
    id: 'gpt-4o-2024-08-06',
    speed: 3,
    quality: 5,
    cost: 2,
    scene: '备用模型',
  },
];

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
      '单次生成的最大 token 数。用例生成建议 4096+，诊断对话 2048 即可。过大会增加响应时间和费用。',
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

const starKeys = ['s1', 's2', 's3', 's4', 's5'] as const;

function StarsRow({ label, count }: { label: string; count: number }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[11.5px] text-text3 w-9">{label}</span>
      <span className="flex gap-0.5">
        {starKeys.map((key, i) => (
          <Star
            key={`${label}-${key}`}
            className={`w-3 h-3 ${i < count ? 'text-accent fill-accent' : 'text-text3/30'}`}
          />
        ))}
      </span>
    </div>
  );
}

export function AIModelSettings() {
  const { effectiveConfig, loading, saving, error, saveGlobalConfig } = useAiConfig();
  const [activeModelId, setActiveModelId] = useState(models[0].id);
  const [paramVals, setParamVals] = useState<Record<SliderParam['key'], number>>({
    temperature: 0.7,
    maxTokens: 4096,
    topP: 0.95,
    concurrency: 3,
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!effectiveConfig) {
      return;
    }

    const outputPreference = effectiveConfig.output_preference ?? {};
    setActiveModelId(effectiveConfig.llm_model ?? models[0].id);
    setParamVals({
      temperature: effectiveConfig.llm_temperature ?? 0.7,
      maxTokens: Number(outputPreference.max_tokens ?? 4096),
      topP: Number(outputPreference.top_p ?? 0.95),
      concurrency: Number(outputPreference.concurrency ?? 3),
    });
  }, [effectiveConfig]);

  const activeModel = useMemo(
    () => models.find((model) => model.id === activeModelId) ?? models[0],
    [activeModelId],
  );

  const handleSave = async () => {
    const ok = await saveGlobalConfig({
      llm_model: activeModel.id,
      llm_temperature: paramVals.temperature,
      output_preference: {
        max_tokens: paramVals.maxTokens,
        top_p: paramVals.topP,
        concurrency: paramVals.concurrency,
      },
    });
    if (!ok) return;

    setSaved(true);
    window.setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div>
      <div className="sec-header">
        <Bot className="w-4 h-4 text-accent" />
        <span className="sec-title">AI 模型配置</span>
      </div>

      {error && (
        <div className="mb-4 px-3 py-2 rounded-md bg-red/8 border border-red/20 text-red text-[12.5px]">
          {error}
        </div>
      )}

      <div className="grid-3 mb-6">
        {models.map((model) => (
          <button
            type="button"
            key={model.name}
            className={`model-card text-left w-full relative ${activeModelId === model.id ? 'active' : ''}`}
            onClick={() => setActiveModelId(model.id)}
            disabled={loading || saving}
          >
            {activeModelId === model.id && (
              <div className="absolute top-3 right-3">
                <Check className="w-4 h-4 text-accent" />
              </div>
            )}
            <div className="mb-2.5">
              <div className="text-sm font-semibold text-text">{model.name}</div>
              <div className="text-[11.5px] text-text3 mt-0.5">{model.provider}</div>
            </div>
            <div className="flex flex-col gap-1.5 mb-2.5">
              <StarsRow label="速度" count={model.speed} />
              <StarsRow label="质量" count={model.quality} />
              <StarsRow label="成本" count={model.cost} />
            </div>
            <div className="text-[11px] text-text3 mb-2">{model.scene}</div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10.5px] text-text3">{model.id}</span>
              {activeModelId === model.id && (
                <span className="pill pill-green text-[10px]">当前生效</span>
              )}
            </div>
          </button>
        ))}
      </div>

      <hr className="divider" />

      <div className="sec-header">
        <Zap className="w-4 h-4 text-accent" />
        <span className="sec-title">参数调整</span>
      </div>
      <div className="card flex flex-col gap-5">
        {sliderParams.map((param) => (
          <div key={param.key}>
            <div className="flex justify-between mb-1.5">
              <span className="text-[12.5px] text-text2 flex items-center gap-1">
                {param.label}
                <ParamTooltip content={param.tooltip} />
              </span>
              <span className="font-mono text-xs text-accent">
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
              className="w-full accent-accent"
              disabled={loading || saving}
            />
          </div>
        ))}

        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-3">
            <p className="text-[12px] text-text3">
              当前模型：<span className="text-text2">{activeModel.name}</span>
            </p>
            <ConnectionTestButton
              testUrl={`/api/ai-config/test-llm?provider=${activeModel.provider === '智谱AI' ? 'zhipu' : activeModel.provider === '阿里云' ? 'dashscope' : 'openai'}`}
              label="测试连接"
            />
          </div>
          <button
            type="button"
            className="btn btn-sm btn-primary"
            onClick={() => void handleSave()}
            disabled={loading || saving}
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
  );
}
