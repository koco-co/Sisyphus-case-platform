import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export interface TestStep {
  step: number;
  action: string;
  expected: string;
}

export interface TestCase {
  id: string;
  requirementId: string;
  title: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  preconditions: string;
  steps: TestStep[];
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

export interface TestCaseCreateInput {
  title: string;
  priority: string;
  preconditions?: string;
  steps: TestStep[];
  tags?: string[];
}

export interface TestCaseBatchCreateInput {
  requirementId: string;
  testCases: TestCaseCreateInput[];
}

export function useTestCase(id: string) {
  return useQuery({
    queryKey: ['testcase', id],
    queryFn: async () => {
      const response = await api.get<TestCase>(`/testcases/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useTestCases(requirementId: string) {
  return useQuery({
    queryKey: ['testcases', requirementId],
    queryFn: async () => {
      const response = await api.get<TestCase[]>(`/testcases/requirement/${requirementId}`);
      return response.data;
    },
    enabled: !!requirementId,
  });
}

export function useCreateTestCases() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: TestCaseBatchCreateInput) => {
      const response = await api.post<TestCase[]>('/testcases/', {
        requirement_id: data.requirementId,
        test_cases: data.testCases,
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      // Invalidate the testcases query for this requirement
      queryClient.invalidateQueries({
        queryKey: ['testcases', variables.requirementId]
      });
    },
  });
}
