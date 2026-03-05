import { create } from 'zustand';

import type { Project } from '../types';

export interface Requirement {
  id: string;
  title: string;
  projectId: string;
}

interface AppState {
  // Sidebar state
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // Current selection
  selectedProjectId: string | null;
  selectedRequirementId: string | null;
  setSelectedProject: (id: string | null) => void;
  setSelectedRequirement: (id: string | null) => void;

  // Project data
  projects: Project[];
  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  selectedProjectId: null,
  selectedRequirementId: null,
  setSelectedProject: (id) => set({ selectedProjectId: id }),
  setSelectedRequirement: (id) => set({ selectedRequirementId: id }),

  projects: [],
  setProjects: (projects) => set({ projects }),
  addProject: (project) => set((state) => ({ projects: [...state.projects, project] })),
}));
