'use client';

import { Check, Database, Loader2, Save } from 'lucide-react';
import { useState } from 'react';
import { ConnectionTestButton } from '@/components/ui/ConnectionTestButton';

interface VectorModelSettingsProps {
  vectorConfig: {
    provider?: string;
    model?: string;
    dimensions?: number;
    collection?: string;
  } | null;
  onSave: (config: Record<string, unknown>) => Promise<boolean>;
  saving?: boolean;
}

const vectorProviders = [
  { id: 'qdrant', name: 'Qdrant', desc: '本地/自建向量库' },
  { id: 'dashscope', name: '阿里 DashScope', desc: 'text-embedding-v3' },
];

export function VectorModelSettings({
  vectorConfig,
  onSave,
  saving = false,
}: VectorModelSettingsProps) {
  const [provider, setProvider] = useState(vectorConfig?.provider || 'qdrant');
  const [model, setModel] = useState(vectorConfig?.model || 'text-embedding-v3');
  const [dimensions, setDimensions] = useState(vectorConfig?.dimensions || 1024);
  const [collection, setCollection] = useState(vectorConfig?.collection || 'knowledge_chunks');
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    const ok = await onSave({
      vector_config: { provider, model, dimensions, collection },
    });
    if (ok) {
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    }
  };

  return (
    <div>
      <div className="sec-header">
        <Database className="w-4 h-4 text-sy-purple" />
        <span className="sec-title">向量模型配置</span>
      </div>

      <div className="card flex flex-col gap-4">
        <div>
          <span className="text-[12px] text-sy-text-2 mb-1 block">向量库提供者</span>
          <div className="flex gap-2">
            {vectorProviders.map((vp) => (
              <button
                key={vp.id}
                type="button"
                className={`px-3 py-1.5 rounded-md text-[12px] border transition-all ${
                  provider === vp.id
                    ? 'border-sy-purple/50 bg-sy-purple/10 text-sy-purple'
                    : 'border-sy-border bg-sy-bg-2 text-sy-text-3 hover:text-sy-text-2'
                }`}
                onClick={() => setProvider(vp.id)}
              >
                {vp.name}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label htmlFor="vec-model" className="text-[12px] text-sy-text-2 mb-1 block">
            Embedding 模型
          </label>
          <input
            id="vec-model"
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-1.5 rounded-md bg-sy-bg-2 border border-sy-border text-[12.5px] text-sy-text focus:border-sy-accent/50 outline-none"
            placeholder="e.g. text-embedding-v3"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="vec-dims" className="text-[12px] text-sy-text-2 mb-1 block">
              维度
            </label>
            <input
              id="vec-dims"
              type="number"
              value={dimensions}
              onChange={(e) => setDimensions(Number(e.target.value))}
              className="w-full px-3 py-1.5 rounded-md bg-sy-bg-2 border border-sy-border text-[12.5px] text-sy-text font-mono outline-none"
              min={128}
              max={4096}
              step={128}
            />
          </div>
          <div>
            <label htmlFor="vec-collection" className="text-[12px] text-sy-text-2 mb-1 block">
              Collection
            </label>
            <input
              id="vec-collection"
              type="text"
              value={collection}
              onChange={(e) => setCollection(e.target.value)}
              className="w-full px-3 py-1.5 rounded-md bg-sy-bg-2 border border-sy-border text-[12.5px] text-sy-text font-mono outline-none"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <ConnectionTestButton testUrl="/api/ai-config/test-embedding" label="测试向量连接" />
          <button
            type="button"
            className="btn btn-sm btn-primary"
            onClick={() => void handleSave()}
            disabled={saving}
          >
            {saving ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : saved ? (
              <Check className="w-3.5 h-3.5" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            {saved ? '已保存' : saving ? '保存中...' : '保存'}
          </button>
        </div>
      </div>
    </div>
  );
}
