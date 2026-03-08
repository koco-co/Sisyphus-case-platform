import { create } from 'zustand';

interface WorkspaceState {
  selectedProductId: string | null;
  selectedIterationId: string | null;
  setProduct: (id: string | null) => void;
  setIteration: (id: string | null) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  selectedProductId: null,
  selectedIterationId: null,
  setProduct: (id) => set({ selectedProductId: id }),
  setIteration: (id) => set({ selectedIterationId: id }),
}));
