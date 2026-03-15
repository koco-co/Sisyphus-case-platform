import { useCallback } from 'react';
import { API_BASE, sceneMapApi } from '@/lib/api';
import {
  type TestPointItem,
  type TestPointSource,
  useSceneMapStore,
} from '@/stores/scene-map-store';
import { useSSE } from './useSSE';

function normalizeSource(source: string): TestPointSource {
  if (['document', 'supplemented', 'missing', 'pending'].includes(source)) {
    return source as TestPointSource;
  }
  if (source === 'ai') return 'supplemented';
  if (source === 'manual') return 'document';
  return 'pending';
}

export function useSceneMap() {
  const store = useSceneMapStore();
  const sse = useSSE();

  const loadTestPoints = useCallback(
    async (reqId: string) => {
      try {
        const data = await sceneMapApi.listTestPoints(reqId);
        const points: TestPointItem[] = (Array.isArray(data) ? data : []).map((tp) => ({
          ...tp,
          description: tp.description ?? null,
          source: normalizeSource(tp.source),
          estimated_cases: tp.estimated_cases ?? 0,
        }));
        store.setTestPoints(points);
        if (points.length > 0) store.setStep('confirm');
      } catch {
        store.setTestPoints([]);
      }
    },
    [store],
  );

  const selectRequirement = useCallback(
    async (reqId: string, title: string) => {
      store.setSelectedReq(reqId, title);
      store.setStep('select');
      await loadTestPoints(reqId);
    },
    [store, loadTestPoints],
  );

  const generateTestPoints = useCallback(async () => {
    const reqId = store.selectedReqId;
    if (!reqId || sse.isStreaming) return;
    store.setStep('analyzing');

    await sse.startStream(`/scene-map/${reqId}/generate`, {
      method: 'POST',
      onDone: async () => {
        store.setStep('confirm');
        await loadTestPoints(reqId);
      },
      onError: () => {
        store.setStep('select');
      },
    });
  }, [store, sse, loadTestPoints]);

  const confirmPoint = useCallback(
    async (pointId: string) => {
      try {
        await sceneMapApi.confirmPoint(pointId);
        store.confirmPoint(pointId);
      } catch (e) {
        console.error('Failed to confirm point:', e);
      }
    },
    [store],
  );

  const ignorePoint = useCallback(
    async (pointId: string) => {
      try {
        await fetch(`${API_BASE}/scene-map/test-points/${pointId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: 'ignored' }),
        });
        store.ignorePoint(pointId);
      } catch (e) {
        console.error('Failed to ignore point:', e);
      }
    },
    [store],
  );

  const deletePoint = useCallback(
    async (pointId: string) => {
      try {
        await sceneMapApi.deletePoint(pointId);
        store.removePoint(pointId);
      } catch (e) {
        console.error('Failed to delete point:', e);
      }
    },
    [store],
  );

  const updatePoint = useCallback(
    async (pointId: string, updates: Partial<TestPointItem>) => {
      try {
        await fetch(`${API_BASE}/scene-map/test-points/${pointId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates),
        });
        store.updatePoint(pointId, updates);
      } catch (e) {
        console.error('Failed to update point:', e);
      }
    },
    [store],
  );

  const addPoint = useCallback(
    async (point: Omit<TestPointItem, 'id'>) => {
      const reqId = store.selectedReqId;
      if (!reqId) return;
      try {
        const res = await fetch(`${API_BASE}/scene-map/${reqId}/test-points`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(point),
        });
        if (res.ok) {
          const created = await res.json();
          store.addPoint({
            ...point,
            id: created.id,
            source: normalizeSource(point.source),
          });
        }
      } catch (e) {
        console.error('Failed to add point:', e);
      }
    },
    [store],
  );

  const confirmAll = useCallback(async () => {
    const reqId = store.selectedReqId;
    if (!reqId) return;
    try {
      await sceneMapApi.confirmAll(reqId);
      store.checkAllPoints();
      store.setTestPoints(store.testPoints.map((tp) => ({ ...tp, status: 'confirmed' })));
      store.lockMap();
    } catch (e) {
      console.error('Failed to confirm all:', e);
    }
  }, [store]);

  // Derived stats
  const stats = {
    total: store.testPoints.length,
    document: store.testPoints.filter((p) => p.source === 'document').length,
    supplemented: store.testPoints.filter((p) => p.source === 'supplemented').length,
    missing: store.testPoints.filter((p) => p.source === 'missing').length,
    pending: store.testPoints.filter((p) => p.source === 'pending').length,
    confirmed: store.testPoints.filter((p) => p.status === 'confirmed').length,
    unhandledMissing: store.testPoints.filter(
      (p) => p.source === 'missing' && p.status !== 'confirmed' && p.status !== 'ignored',
    ).length,
  };

  return {
    ...store,
    sse,
    stats,
    selectRequirement,
    generateTestPoints,
    confirmPoint,
    ignorePoint,
    deletePoint,
    updatePoint,
    addPoint,
    confirmAll,
    loadTestPoints,
  };
}
