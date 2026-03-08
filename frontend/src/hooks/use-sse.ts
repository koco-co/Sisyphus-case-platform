'use client';

import { useCallback, useRef, useState } from 'react';

export function useSSE<T>() {
  const [data, setData] = useState<T[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);

  const start = useCallback((url: string) => {
    setIsStreaming(true);
    setData([]);
    const source = new EventSource(url);
    sourceRef.current = source;
    source.onmessage = (event: MessageEvent) => {
      const parsed = JSON.parse(event.data as string) as T;
      setData((prev) => [...prev, parsed]);
    };
    source.onerror = () => {
      source.close();
      setIsStreaming(false);
    };
  }, []);

  const stop = useCallback(() => {
    sourceRef.current?.close();
    setIsStreaming(false);
  }, []);

  return { data, isStreaming, start, stop };
}
