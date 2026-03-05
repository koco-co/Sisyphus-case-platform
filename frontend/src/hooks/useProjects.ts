import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

export interface Requirement {
  id: string;
  title: string;
  projectId: string;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  parentId?: number;
  createdAt: string;
  requirements: Requirement[];
}

interface ApiProject {
  id: number;
  name: string;
  description?: string;
  parent_id?: number;
  created_at: string;
}

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const response = await api.get<ApiProject[]>('/projects');
      // Transform API response to match frontend interface
      return response.data.map((p) => ({
        id: p.id,
        name: p.name,
        description: p.description,
        parentId: p.parent_id,
        createdAt: p.created_at,
        // Requirements will be loaded separately when needed
        requirements: [] as Requirement[],
      }));
    },
  });
}

export function useProject(projectId: number | null) {
  return useQuery({
    queryKey: ['projects', projectId],
    queryFn: async () => {
      if (!projectId) return null;
      const response = await api.get<ApiProject>(`/projects/${projectId}`);
      const p = response.data;
      return {
        id: p.id,
        name: p.name,
        description: p.description,
        parentId: p.parent_id,
        createdAt: p.created_at,
        requirements: [] as Requirement[],
      } as Project;
    },
    enabled: !!projectId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { name: string; description?: string; parentId?: number }) => {
      const response = await api.post<ApiProject>('/projects', {
        name: data.name,
        description: data.description,
        parent_id: data.parentId,
      });
      const p = response.data;
      return {
        id: p.id,
        name: p.name,
        description: p.description,
        parentId: p.parent_id,
        createdAt: p.created_at,
        requirements: [] as Requirement[],
      } as Project;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (projectId: number) => {
      await api.delete(`/projects/${projectId}`);
      return projectId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}
