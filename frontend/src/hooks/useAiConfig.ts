import { useCallback, useEffect, useState } from 'react';
import {
  type AiConfigRecord,
  aiConfigApi,
  type EffectiveAiConfig,
  getApiErrorMessage,
} from '@/lib/api';

function pickGlobalConfig(configs: AiConfigRecord[]) {
  return configs
    .filter((config) => config.scope === 'global' && !config.scope_id)
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at))[0];
}

export function useAiConfig() {
  const [config, setConfig] = useState<AiConfigRecord | null>(null);
  const [effectiveConfig, setEffectiveConfig] = useState<EffectiveAiConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [configs, effective] = await Promise.all([aiConfigApi.list(), aiConfigApi.effective()]);
      setConfig(pickGlobalConfig(configs) ?? null);
      setEffectiveConfig(effective);
    } catch (err) {
      setError(getApiErrorMessage(err, '加载 AI 配置失败'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const saveGlobalConfig = useCallback(
    async (payload: {
      team_standard_prompt?: string | null;
      output_preference?: Record<string, unknown> | null;
      llm_model?: string | null;
      llm_temperature?: number | null;
      api_keys?: Record<string, string> | null;
    }) => {
      setSaving(true);
      setError(null);
      try {
        if (config) {
          await aiConfigApi.update(config.id, payload);
        } else {
          await aiConfigApi.create({
            scope: 'global',
            ...payload,
          });
        }
        await refresh();
        return true;
      } catch (err) {
        setError(getApiErrorMessage(err, '保存 AI 配置失败'));
        return false;
      } finally {
        setSaving(false);
      }
    },
    [config, refresh],
  );

  return {
    config,
    effectiveConfig,
    loading,
    saving,
    error,
    refresh,
    saveGlobalConfig,
  };
}
