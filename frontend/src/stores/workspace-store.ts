import { create } from 'zustand';

// ── Types ──

export type WorkbenchMode = 'test_point_driven' | 'document_driven' | 'dialogue' | 'template';

export interface GenSession {
  id: string;
  mode: string;
  status: string;
  created_at: string;
}

export interface WorkbenchMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  thinking_content?: string;
  cases?: WorkbenchTestCase[];
  created_at: string;
}

export interface WorkbenchTestCase {
  id: string;
  case_id: string;
  title: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  case_type: string;
  status: string;
  precondition?: string;
  source: string;
  test_point_id?: string;
  steps: { no: number; action: string; expected_result: string }[];
  ai_score?: number;
}

export interface ContextItem {
  id: string;
  type: 'knowledge' | 'requirement' | 'test_point' | 'document';
  label: string;
}

// ── Store ──

interface WorkspaceState {
  selectedProductId: string | null;
  selectedIterationId: string | null;
  setProduct: (id: string | null) => void;
  setIteration: (id: string | null) => void;

  selectedMode: WorkbenchMode;
  setMode: (mode: WorkbenchMode) => void;

  sessions: GenSession[];
  activeSessionId: string | null;
  setSessions: (sessions: GenSession[]) => void;
  addSession: (session: GenSession) => void;
  setActiveSessionId: (id: string | null) => void;

  messages: WorkbenchMessage[];
  setMessages: (messages: WorkbenchMessage[]) => void;
  addMessage: (message: WorkbenchMessage) => void;

  testCases: WorkbenchTestCase[];
  setTestCases: (cases: WorkbenchTestCase[]) => void;
  appendTestCases: (cases: WorkbenchTestCase[]) => void;

  appendedTestPointIds: Set<string>;
  lastGeneratedPointIds: Set<string>;
  setAppendedPointIds: (ids: Set<string>) => void;
  setLastGeneratedPointIds: (ids: Set<string>) => void;

  contextItems: ContextItem[];
  addContextItem: (item: ContextItem) => void;
  removeContextItem: (id: string) => void;

  priorityFilter: string | null;
  typeFilter: string | null;
  setPriorityFilter: (f: string | null) => void;
  setTypeFilter: (f: string | null) => void;

  selectedReqId: string | null;
  selectedReqTitle: string;
  setSelectedReq: (id: string | null, title: string) => void;

  resetWorkbench: () => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  selectedProductId: null,
  selectedIterationId: null,
  setProduct: (id) => set({ selectedProductId: id }),
  setIteration: (id) => set({ selectedIterationId: id }),

  selectedMode: 'test_point_driven',
  setMode: (mode) => set({ selectedMode: mode }),

  sessions: [],
  activeSessionId: null,
  setSessions: (sessions) => set({ sessions }),
  addSession: (session) => set((s) => ({ sessions: [session, ...s.sessions] })),
  setActiveSessionId: (id) => set({ activeSessionId: id }),

  messages: [],
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((s) => ({ messages: [...s.messages, message] })),

  testCases: [],
  setTestCases: (cases) => set({ testCases: cases }),
  appendTestCases: (cases) => set((s) => ({ testCases: [...s.testCases, ...cases] })),

  appendedTestPointIds: new Set(),
  lastGeneratedPointIds: new Set(),
  setAppendedPointIds: (ids) => set({ appendedTestPointIds: ids }),
  setLastGeneratedPointIds: (ids) => set({ lastGeneratedPointIds: ids }),

  contextItems: [],
  addContextItem: (item) =>
    set((s) => {
      if (s.contextItems.some((c) => c.id === item.id)) return s;
      return { contextItems: [...s.contextItems, item] };
    }),
  removeContextItem: (id) =>
    set((s) => ({ contextItems: s.contextItems.filter((c) => c.id !== id) })),

  priorityFilter: null,
  typeFilter: null,
  setPriorityFilter: (f) => set({ priorityFilter: f }),
  setTypeFilter: (f) => set({ typeFilter: f }),

  selectedReqId: null,
  selectedReqTitle: '',
  setSelectedReq: (id, title) => set({ selectedReqId: id, selectedReqTitle: title }),

  resetWorkbench: () =>
    set({
      sessions: [],
      activeSessionId: null,
      messages: [],
      testCases: [],
      contextItems: [],
      priorityFilter: null,
      typeFilter: null,
    }),
}));
