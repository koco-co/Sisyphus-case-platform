import { API_BASE } from '@/lib/api';
import { useStreamStore } from '@/stores/stream-store';

export function useSSEStream() {
  const { reset, appendThinking, appendContent, setDone } = useStreamStore();

  async function streamSSE(path: string, body: object) {
    reset();
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.body) return;
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    for (;;) {
      const { done, value } = await reader.read();
      if (done) {
        setDone();
        break;
      }
      buffer += decoder.decode(value, { stream: true });

      const messages = buffer.split('\n\n');
      buffer = messages.pop() ?? '';

      for (const msg of messages) {
        const eventMatch = msg.match(/^event: (\w+)/m);
        const dataMatch = msg.match(/^data: (.+)/m);
        if (!eventMatch || !dataMatch) continue;

        const eventType = eventMatch[1];
        try {
          const payload = JSON.parse(dataMatch[1]);
          if (eventType === 'thinking') appendThinking(payload.delta ?? '');
          else if (eventType === 'content') appendContent(payload.delta ?? '');
          else if (eventType === 'done') setDone();
        } catch {
          /* ignore parse errors */
        }
      }
    }
  }

  return { streamSSE };
}
