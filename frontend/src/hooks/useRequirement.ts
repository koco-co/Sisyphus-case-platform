import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export interface StructuredRequirement {
  modules: Module[];
}

export interface Module {
  name: string;
  description: string;
  features: Feature[];
}

export interface Feature {
  name: string;
  description: string;
  input: string;
  output: string;
  exceptions: string;
}

export interface Requirement {
  id: string;
  projectId: string;
  title: string;
  content: StructuredRequirement;
  createdAt: string;
  updatedAt: string;
}

export function useRequirement(id: string) {
  return useQuery({
    queryKey: ['requirement', id],
    queryFn: async () => {
      const response = await api.get<Requirement>(`/requirements/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}
