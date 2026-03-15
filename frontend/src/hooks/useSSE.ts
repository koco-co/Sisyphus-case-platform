import { useCallback, useRef, useState } from 'react';
import { API_BASE } from '@/lib/api';

interface SSEOptions {
  onThinking?: (text: string) => void;
  onContent?: (delta: string, fullText: string) => void;
  onDone?: (fullText: string) => void;
  onError?: (error: Error) => void;
}

export interface SSEStreamingCase {
  _idx: number;
  title: string;
  priority: string;
  case_type: string;
  precondition?: string;
  steps: { step_num?: number; action: string; expected_result: string }[];
}

export interface SSEState {
  isStreaming: boolean;
  content: string;
  thinking: string;
  cases: SSEStreamingCase[];
  error: string | null;
}

export function useSSE() {
  const [state, setState] = useState<SSEState>({
    isStreaming: false,
    content: '',
    thinking: '',
    cases: [],
    error: null,
  });
  const abortRef = useRef<AbortController | null>(null);
  const contentRef = useRef('');
  const thinkingRef = useRef('');
  const casesRef = useRef<SSEStreamingCase[]>([]);

  const startStream = useCallback(
    async (path: string, options?: { method?: string; body?: unknown } & SSEOptions) => {
      // Reset state
      contentRef.current = '';
      thinkingRef.current = '';
      casesRef.current = [];
      setState({ isStreaming: true, content: '', thinking: '', cases: [], error: null });

      abortRef.current = new AbortController();

      try {
        const res = await fetch(`${API_BASE}${path}`, {
          method: options?.method || 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: options?.body ? JSON.stringify(options.body) : undefined,
          signal: abortRef.current.signal,
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const reader = res.body?.getReader();
        if (!reader) throw new Error('No reader');

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          let eventType = '';
          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                if (eventType === 'thinking' && data.delta) {
                  thinkingRef.current += data.delta;
                  setState((s) => ({ ...s, thinking: thinkingRef.current }));
                  options?.onThinking?.(thinkingRef.current);
                } else if (eventType === 'content' && data.delta) {
                  contentRef.current += data.delta;
                  setState((s) => ({ ...s, content: contentRef.current }));
                  options?.onContent?.(data.delta, contentRef.current);
                } else if (eventType === 'case' && data.title) {
                  const newCase = data as SSEStreamingCase;
                  casesRef.current = [...casesRef.current, newCase];
                  setState((s) => ({ ...s, cases: casesRef.current }));
                } else if (eventType === 'error') {
                  const errMsg = data.message || 'AI 服务异常';
                  setState((s) => ({ ...s, error: errMsg }));
                  options?.onError?.(new Error(errMsg));
                } else if (eventType === 'done') {
                  options?.onDone?.(contentRef.current);
                }
              } catch {
                // Non-JSON data line, accumulate as content
                const text = line.slice(6);
                if (text && text !== '[DONE]') {
                  contentRef.current += text;
                  setState((s) => ({ ...s, content: contentRef.current }));
                }
              }
              eventType = '';
            }
          }
        }

        // Final callback if not already triggered by done event
        if (contentRef.current) {
          options?.onDone?.(contentRef.current);
        }

        return contentRef.current;
      } catch (e: unknown) {
        if (e instanceof Error && e.name === 'AbortError') return '';
        const msg = e instanceof Error ? e.message : 'Stream error';
        setState((s) => ({ ...s, error: msg }));
        options?.onError?.(e instanceof Error ? e : new Error(msg));
        return '';
      } finally {
        setState((s) => ({ ...s, isStreaming: false }));
      }
    },
    [],
  );

  const stopStream = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { ...state, startStream, stopStream };
}
