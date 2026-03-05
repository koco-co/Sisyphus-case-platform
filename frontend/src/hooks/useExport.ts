import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export interface ExportTemplate {
  id: string;
  name: string;
  fieldConfig: {
    fields: string[];
  };
  formatConfig: {
    delimiter?: string;
    headerNames?: Record<string, string>;
  };
  filterConfig: {
    priority?: string[];
  };
  isDefault: boolean;
  createdAt: string;
}

export interface CreateTemplateRequest {
  name: string;
  fieldConfig: {
    fields: string[];
  };
  formatConfig?: {
    delimiter?: string;
    headerNames?: Record<string, string>;
  };
  filterConfig?: {
    priority?: string[];
  };
  isDefault?: boolean;
}

export function useExportTemplates() {
  return useQuery({
    queryKey: ['export-templates'],
    queryFn: async () => {
      const response = await api.get<ExportTemplate[]>('/export/templates');
      return response.data;
    },
  });
}

export function useCreateExportTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateTemplateRequest) => {
      const response = await api.post<ExportTemplate>('/export/templates', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['export-templates'] });
    },
  });
}

export function useExportTestCases(testCaseIds: string[], templateId: string) {
  return useMutation({
    mutationFn: async () => {
      const response = await api.post('/export', {
        test_case_ids: testCaseIds,
        template_id: templateId,
      }, {
        responseType: 'blob',
      });
      return response.data;
    },
  });
}
