import { useCallback, useEffect, useState } from 'react';
import {
  API_BASE,
  type ChatMessage,
  type DiagnosisReport,
  diagnosisApi,
  type SceneMapData,
  sceneMapApi,
} from '@/lib/api';
import { useDiagnosisStore } from '@/stores/diagnosis-store';
import { useSSE } from './useSSE';

export function useDiagnosis(reqId: string | null) {
  const sse = useSSE();
  const { setStep, setRunning } = useDiagnosisStore();
  const [report, setReport] = useState<DiagnosisReport | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sceneMap, setSceneMap] = useState<SceneMapData | null>(null);
  const [loading, setLoading] = useState(false);

  // biome-ignore lint/correctness/useExhaustiveDependencies: only reload on reqId change
  useEffect(() => {
    if (!reqId) {
      setReport(null);
      setMessages([]);
      setSceneMap(null);
      setStep('select');
      return;
    }

    setMessages([]);
    setReport(null);
    setSceneMap(null);
    setLoading(true);

    (async () => {
      try {
        const r = await diagnosisApi.createReport(reqId);
        setReport(r);

        const msgs = await diagnosisApi.listMessages(reqId);
        setMessages(Array.isArray(msgs) ? msgs : []);

        if (r.status === 'completed') {
          setStep('report');
          try {
            const sm = await sceneMapApi.get(reqId);
            setSceneMap(sm);
          } catch {
            /* scene map may not exist yet */
          }
        } else if (Array.isArray(msgs) && msgs.length > 0) {
          setStep('probe');
        } else {
          setStep('scan');
        }
      } catch (e) {
        console.error('Failed to load diagnosis:', e);
        setStep('scan');
      } finally {
        setLoading(false);
      }
    })();
  }, [reqId]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || !reqId || sse.isStreaming) return;

      const userMsg = text.trim();
      setMessages((prev) => [
        ...prev,
        {
          id: `user-${Date.now()}`,
          role: 'user',
          content: userMsg,
          created_at: new Date().toISOString(),
        },
      ]);

      setStep('probe');

      await sse.startStream(`/diagnosis/${reqId}/chat`, {
        method: 'POST',
        body: { message: userMsg },
        onDone: (fullText) => {
          setMessages((prev) => [
            ...prev,
            {
              id: `ai-${Date.now()}`,
              role: 'assistant',
              content: fullText || '分析完成',
              created_at: new Date().toISOString(),
            },
          ]);
        },
        onError: (err) => {
          setMessages((prev) => [
            ...prev,
            {
              id: `err-${Date.now()}`,
              role: 'assistant',
              content: `错误: ${err.message}`,
              created_at: new Date().toISOString(),
            },
          ]);
        },
      });
    },
    [reqId, sse, setStep],
  );

  const startDiagnosis = useCallback(async () => {
    if (!reqId || sse.isStreaming) return;

    setStep('scan');
    setRunning(true);

    await sse.startStream(`/diagnosis/${reqId}/run`, {
      method: 'POST',
      body: {},
      onDone: async (fullText) => {
        setMessages((prev) => [
          ...prev,
          {
            id: `scan-${Date.now()}`,
            role: 'assistant',
            content: fullText || '广度扫描完成，请查看风险清单',
            created_at: new Date().toISOString(),
          },
        ]);
        setStep('probe');
        setRunning(false);

        try {
          const r = await diagnosisApi.getReport(reqId);
          setReport(r);
        } catch {
          /* ignore */
        }
      },
      onError: () => {
        setRunning(false);
      },
    });
  }, [reqId, sse, setStep, setRunning]);

  const completeDiagnosis = useCallback(async () => {
    if (!reqId) return;
    setRunning(true);
    try {
      const res = await fetch(`${API_BASE}/diagnosis/${reqId}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (res.ok) {
        const data = await res.json();
        setReport(data);
        setStep('report');

        try {
          const sm = await sceneMapApi.get(reqId);
          setSceneMap(sm);
        } catch {
          /* scene map may not exist */
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setRunning(false);
    }
  }, [reqId, setStep, setRunning]);

  return {
    report,
    messages,
    sceneMap,
    loading,
    sse,
    sendMessage,
    startDiagnosis,
    completeDiagnosis,
  };
}
