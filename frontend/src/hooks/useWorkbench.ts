'use client';

import { useCallback } from 'react';
import { useSSE } from '@/hooks/useSSE';
import { API_BASE, api } from '@/lib/api';
import {
  type GenSession,
  useWorkspaceStore,
  type WorkbenchMessage,
  type WorkbenchTestCase,
} from '@/stores/workspace-store';

export function useWorkbench() {
  const store = useWorkspaceStore();
  const sse = useSSE();

  const loadSessions = useCallback(
    async (reqId: string) => {
      try {
        const data = await api.get<GenSession[]>(`/generation/sessions/by-requirement/${reqId}`);
        store.setSessions(Array.isArray(data) ? data : []);
      } catch {
        store.setSessions([]);
      }
    },
    [store],
  );

  const loadTestCases = useCallback(
    async (reqId: string) => {
      try {
        const data = await api.get<{ items: WorkbenchTestCase[] }>(
          `/testcases/?requirement_id=${reqId}`,
        );
        store.setTestCases(data.items ?? []);
      } catch {
        store.setTestCases([]);
      }
    },
    [store],
  );

  const loadMessages = useCallback(
    async (sessionId: string) => {
      try {
        const data = await api.get<WorkbenchMessage[]>(
          `/generation/sessions/${sessionId}/messages`,
        );
        store.setMessages(Array.isArray(data) ? data : []);
      } catch {
        store.setMessages([]);
      }
    },
    [store],
  );

  const selectRequirement = useCallback(
    async (reqId: string, title: string) => {
      store.setSelectedReq(reqId, title);
      store.setActiveSessionId(null);
      store.setMessages([]);
      await Promise.all([loadSessions(reqId), loadTestCases(reqId)]);
    },
    [store, loadSessions, loadTestCases],
  );

  const createSession = useCallback(async () => {
    if (!store.selectedReqId) return;
    try {
      const data = await api.post<GenSession>('/generation/sessions', {
        requirement_id: store.selectedReqId,
        mode: store.selectedMode,
      });
      store.addSession(data);
      store.setActiveSessionId(data.id);
      store.setMessages([]);
    } catch (e) {
      console.error('Failed to create session:', e);
    }
  }, [store]);

  const selectSession = useCallback(
    async (sessionId: string) => {
      store.setActiveSessionId(sessionId);
      await loadMessages(sessionId);
    },
    [store, loadMessages],
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || !store.activeSessionId || sse.isStreaming) return;

      const userMsg: WorkbenchMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: text.trim(),
        created_at: new Date().toISOString(),
      };
      store.addMessage(userMsg);

      const fullText = await sse.startStream(`/generation/sessions/${store.activeSessionId}/chat`, {
        body: { message: text.trim() },
      });

      if (fullText) {
        await loadMessages(store.activeSessionId);
      } else {
        store.addMessage({
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: sse.error ? `⚠️ ${sse.error}` : '⚠️ AI 未返回有效内容，请检查模型配置后重试。',
          created_at: new Date().toISOString(),
        });
      }

      if (store.selectedReqId) {
        await loadTestCases(store.selectedReqId);
      }
    },
    [store, sse, loadMessages, loadTestCases],
  );

  const stopStream = useCallback(() => {
    sse.stopStream();
  }, [sse]);

  const exportCases = useCallback(
    async (format: 'excel' | 'json') => {
      if (!store.selectedReqId) return;
      try {
        const url = `${API_BASE}/export/${format}?requirement_id=${store.selectedReqId}`;
        window.open(url, '_blank');
      } catch (e) {
        console.error('Export failed:', e);
      }
    },
    [store.selectedReqId],
  );

  return {
    ...store,
    sse,
    loadSessions,
    loadTestCases,
    loadMessages,
    selectRequirement,
    createSession,
    selectSession,
    sendMessage,
    stopStream,
    exportCases,
  };
}
