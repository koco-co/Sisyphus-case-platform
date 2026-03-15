import { useCallback, useEffect, useState } from 'react';
import {
  type AiConfigRecord,
  aiConfigApi,
  type EffectiveAiConfig,
  getApiErrorMessage,
  type ModelConfigPayload,
  type ModelConfigRecord,
} from '@/lib/api';

function pickGlobalConfig(configs: AiConfigRecord[]) {
  return configs
    .filter((config) => config.scope === 'global' && !config.scope_id)
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at))[0];
}

export function useAiConfig() {
  const [config, setConfig] = useState<AiConfigRecord | null>(null);
  const [effectiveConfig, setEffectiveConfig] = useState<EffectiveAiConfig | null>(null);
  const [modelConfigs, setModelConfigs] = useState<ModelConfigRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [configs, effective, models] = await Promise.all([
        aiConfigApi.list(),
        aiConfigApi.effective(),
        aiConfigApi.listModels(),
      ]);
      setConfig(pickGlobalConfig(configs) ?? null);
      setEffectiveConfig(effective);
      setModelConfigs(models);
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

  const createModelConfig = useCallback(
    async (payload: ModelConfigPayload) => {
      setSaving(true);
      setError(null);
      try {
        const created = await aiConfigApi.createModel(payload);
        await refresh();
        return created;
      } catch (err) {
        setError(getApiErrorMessage(err, '创建模型配置失败'));
        return null;
      } finally {
        setSaving(false);
      }
    },
    [refresh],
  );

  const updateModelConfig = useCallback(
    async (id: string, payload: Partial<ModelConfigPayload>) => {
      setSaving(true);
      setError(null);
      try {
        const updated = await aiConfigApi.updateModel(id, payload);
        await refresh();
        return updated;
      } catch (err) {
        setError(getApiErrorMessage(err, '更新模型配置失败'));
        return null;
      } finally {
        setSaving(false);
      }
    },
    [refresh],
  );

  const deleteModelConfig = useCallback(
    async (id: string) => {
      setSaving(true);
      setError(null);
      try {
        await aiConfigApi.deleteModel(id);
        await refresh();
        return true;
      } catch (err) {
        setError(getApiErrorMessage(err, '删除模型配置失败'));
        return false;
      } finally {
        setSaving(false);
      }
    },
    [refresh],
  );

  return {
    config,
    effectiveConfig,
    modelConfigs,
    loading,
    saving,
    error,
    refresh,
    saveGlobalConfig,
    createModelConfig,
    updateModelConfig,
    deleteModelConfig,
  };
}
