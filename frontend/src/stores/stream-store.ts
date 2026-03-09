import { create } from 'zustand';

interface StreamState {
  thinkingText: string;
  contentText: string;
  isStreaming: boolean;
  isThinkingDone: boolean;
  reset: () => void;
  appendThinking: (delta: string) => void;
  appendContent: (delta: string) => void;
  setDone: () => void;
}

export const useStreamStore = create<StreamState>((set) => ({
  thinkingText: '',
  contentText: '',
  isStreaming: false,
  isThinkingDone: false,
  reset: () =>
    set({
      thinkingText: '',
      contentText: '',
      isStreaming: false,
      isThinkingDone: false,
    }),
  appendThinking: (delta) =>
    set((s) => ({
      thinkingText: s.thinkingText + delta,
      isStreaming: true,
    })),
  appendContent: (delta) =>
    set((s) => ({
      contentText: s.contentText + delta,
      isStreaming: true,
      isThinkingDone: true,
    })),
  setDone: () => set({ isStreaming: false }),
}));
