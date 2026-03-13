/**
 * Unified API client and module-specific API wrappers.
 *
 * Every hook / page should import from '@/lib/api' for consistency.
 */

// ─── Base ────────────────────────────────────────────────────────────────────

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api';

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API ${status}: ${detail}`);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

/**
 * Generic REST helper used by hooks that call `api.get(...)` / `api.post(...)`.
 */
export const api = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};

// ─── Utility ─────────────────────────────────────────────────────────────────

export function getApiErrorMessage(err: unknown, fallback = '操作失败'): string {
  if (err instanceof ApiError) return err.detail;
  if (err instanceof Error) return err.message;
  return fallback;
}

// ─── Common Types ────────────────────────────────────────────────────────────

export interface Product {
  id: string;
  name: string;
  description?: string;
  status?: string;
  created_at: string;
  updated_at: string;
}

export interface Iteration {
  id: string;
  product_id: string;
  name: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  created_at: string;
  updated_at: string;
}

export interface Requirement {
  id: string;
  iteration_id: string;
  title: string;
  req_id?: string;
  status?: string;
  priority?: string;
  content?: string;
  created_at: string;
  updated_at: string;
}

export interface RequirementDetail extends Requirement {
  product_id?: string;
  product_name?: string;
  iteration_name?: string;
  raw_content?: string;
  frontmatter?: Record<string, unknown>;
  content_ast?: Record<string, unknown>;
  version?: number;
  health_score?: number | null;
  diagnosis_status?: string;
  scene_map_status?: string;
}

export interface RequirementVersion {
  id: string;
  requirement_id: string;
  version: number;
  content: string;
  content_ast?: Record<string, unknown>;
  change_summary: string | null;
  created_at: string;
}

// Diagnosis
export interface DiagnosisReport {
  id: string;
  requirement_id: string;
  status: string;
  health_score?: number | null;
  overall_score?: number | null;
  risk_count?: number;
  risk_count_high?: number;
  risk_count_medium?: number;
  summary?: string;
  risks?: DiagnosisRisk[];
  created_at: string;
  updated_at: string;
}

export interface DiagnosisRisk {
  id: string;
  category: string;
  severity: string;
  description: string;
  suggestion?: string;
  status?: string; // 'open' | 'acknowledged' | 'accepted' | 'ignored'
  title?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  metadata?: Record<string, unknown>;
}

// Scene Map
export interface SceneMapData {
  id?: string;
  requirement_id: string;
  status?: string;
  test_points: TestPoint[];
  created_at?: string;
  updated_at?: string;
}

export interface TestPoint {
  id: string;
  title: string;
  group_name: string;
  description?: string | null;
  source: string;
  priority: string;
  status: string;
  risk_level?: string;
  preconditions?: string;
  estimated_cases?: number;
}

// Notifications
export interface NotificationRecord {
  id: string;
  user_id: string;
  title: string;
  message: string;
  content?: string | null;
  notification_type: string;
  severity: string;
  is_read: boolean;
  related_type?: string | null;
  related_id?: string | null;
  created_at: string;
}

// Recycle
export interface RecycleItemResponse {
  items: RecycleItem[];
  total: number;
}

export interface RecycleItem {
  id: string;
  entity_type: string;
  entity_id: string;
  name: string;
  title: string;
  deleted_at: string;
  deleted_by?: string;
}

// Search
export interface SearchResultItem {
  id: string;
  type: string;
  entity_type?: string;
  title: string;
  content?: string;
  summary?: string;
  highlight?: string;
  score?: number;
  created_at?: string;
  updated_at?: string;
}

// AI Config
export interface AiConfigRecord {
  id: string;
  scope: string;
  scope_id?: string | null;
  provider: string;
  model_name: string;
  temperature?: number;
  max_tokens?: number;
  custom_rules?: string;
  test_standard_prompt?: string;
  team_standard_prompt?: string | null;
  output_preference?: Record<string, unknown> | null;
  llm_model?: string | null;
  llm_temperature?: number | null;
  api_keys?: Record<string, string> | null;
  vector_config?: Record<string, unknown> | null;
  updated_at: string;
  created_at: string;
}

export interface EffectiveAiConfig {
  provider: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  custom_rules: string;
  test_standard_prompt: string;
  team_standard_prompt?: string;
  output_preference?: Record<string, unknown>;
  llm_model?: string;
  llm_temperature?: number;
  api_keys?: Record<string, string> | null;
  vector_config?: Record<string, unknown> | null;
}

// Templates
export interface TemplateListItem {
  id: string;
  name: string;
  category: string;
  description?: string;
  usage_count: number;
  is_builtin?: boolean;
  status?: string;
  created_at: string;
  updated_at: string;
}

export interface TemplateDetailResponse extends TemplateListItem {
  content: TemplateContentPayload;
  template_content: TemplateContentPayload;
  variables?: Record<string, unknown>;
}

export interface TemplateContentPayload {
  steps: {
    step: number;
    action: string;
    expected: string;
    step_num?: number;
    expected_result?: string;
  }[];
  preconditions?: string;
  precondition?: string;
  tags?: string[];
}

// Collaboration / Review
export interface SharedReviewPayload {
  id: string;
  entity_type: string;
  entity_id: string;
  entity_snapshot?: {
    test_points?: TestPoint[];
    requirement_title?: string;
    reviewer_names?: string[];
    req_id?: string;
    [key: string]: unknown;
  };
  review: {
    title: string;
    status: string;
    description?: string;
    reviewer_ids?: string[];
    created_at: string;
    [key: string]: unknown;
  };
  decisions: ReviewDecisionRecord[];
  status: string;
  created_at: string;
  expires_at?: string;
}

export interface ReviewDecisionRecord {
  id: string;
  decision: string;
  comment?: string;
  created_at: string;
}

export type ReviewDecision = ReviewDecisionRecord | 'approved' | 'rejected' | 'needs_changes';

// ─── Module APIs ─────────────────────────────────────────────────────────────

export const productsApi = {
  list: () => api.get<Product[]>('/products/'),
  listIterations: (productId: string) => api.get<Iteration[]>(`/products/${productId}/iterations`),
  listRequirements: (productId: string, iterationId: string) =>
    api.get<Requirement[]>(`/products/${productId}/iterations/${iterationId}/requirements`),
};

export const requirementsApi = {
  update: (reqId: string, data: Partial<RequirementDetail>) =>
    api.put<RequirementDetail>(`/products/requirements/${reqId}`, data),
  delete: (reqId: string) => api.delete<void>(`/products/requirements/${reqId}`),
};

export const diagnosisApi = {
  createReport: (reqId: string) => api.post<DiagnosisReport>(`/diagnosis/${reqId}/create`),
  getReport: (reqId: string) => api.get<DiagnosisReport>(`/diagnosis/${reqId}`),
  listMessages: (reqId: string) => api.get<ChatMessage[]>(`/diagnosis/${reqId}/messages`),
};

export const sceneMapApi = {
  get: (reqId: string) => api.get<SceneMapData>(`/scene-map/${reqId}`),
  listTestPoints: (reqId: string) => api.get<TestPoint[]>(`/scene-map/${reqId}/test-points`),
  confirmPoint: (pointId: string) => api.post<void>(`/scene-map/test-points/${pointId}/confirm`),
  confirmAll: (reqId: string) => api.post<void>(`/scene-map/${reqId}/confirm`),
  deletePoint: (pointId: string) => api.delete<void>(`/scene-map/test-points/${pointId}`),
};

export const notificationsApi = {
  list: (params: { userId: string; pageSize?: number }) =>
    api.get<{ items: NotificationRecord[]; total: number }>(
      `/notifications?user_id=${params.userId}&page_size=${params.pageSize ?? 20}`,
    ),
  unreadCount: (userId: string) =>
    api.get<{ count: number }>(`/notifications/unread-count?user_id=${userId}`),
  markRead: (notificationId: string) => api.post<void>(`/notifications/${notificationId}/read`),
  markAllRead: (userId: string) => api.post<void>(`/notifications/mark-all-read?user_id=${userId}`),
  delete: (notificationId: string) => api.delete<void>(`/notifications/${notificationId}`),
};

export const recycleApi = {
  list: (params: { entityType?: string; pageSize?: number }) => {
    const qs = new URLSearchParams();
    if (params.entityType) qs.set('entity_type', params.entityType);
    if (params.pageSize) qs.set('page_size', String(params.pageSize));
    return api.get<RecycleItemResponse>(`/recycle/?${qs.toString()}`);
  },
  restore: (entityType: string, id: string) =>
    api.post<void>(`/recycle/${entityType}/${id}/restore`),
  batchRestore: (items: { entity_type: string; id: string }[]) =>
    api.post<void>('/recycle/batch-restore', { items }),
  permanentDelete: (entityType: string, id: string) =>
    api.delete<void>(`/recycle/${entityType}/${id}`),
};

export const searchApi = {
  search: (query: string, types?: string[], page = 1, pageSize = 20) => {
    const qs = new URLSearchParams({ q: query, page: String(page), page_size: String(pageSize) });
    if (types?.length) qs.set('types', types.join(','));
    return api.get<{ items: SearchResultItem[]; total: number }>(`/search?${qs.toString()}`);
  },
};

export const authApi = {
  login: (data: { username: string; password: string }) =>
    api.post<{
      access_token: string;
      user: { id: string; username: string; email: string; role?: string; full_name?: string };
    }>('/auth/login', data),
  register: (data: { username: string; email: string; password: string }) =>
    api.post<{ id: string; username: string; email: string; role?: string; full_name?: string }>(
      '/auth/register',
      data,
    ),
};

export const aiConfigApi = {
  list: () => api.get<AiConfigRecord[]>('/ai-config'),
  effective: () => api.get<EffectiveAiConfig>('/ai-config/effective'),
  create: (data: Partial<AiConfigRecord>) => api.post<AiConfigRecord>('/ai-config', data),
  update: (id: string, data: Partial<AiConfigRecord>) =>
    api.patch<AiConfigRecord>(`/ai-config/${id}`, data),
};

export const templatesApi = {
  list: () => api.get<{ items: TemplateListItem[]; total: number }>('/templates/'),
  get: (id: string) => api.get<TemplateDetailResponse>(`/templates/${id}`),
  create: (data: {
    name: string;
    category: string;
    description?: string | null;
    content?: TemplateContentPayload;
    template_content?: TemplateContentPayload;
    variables?: Record<string, unknown>;
  }) => api.post<TemplateDetailResponse>('/templates/', data),
  update: (
    id: string,
    data: Partial<{
      name: string;
      category: string;
      description?: string | null;
      content: TemplateContentPayload;
      template_content: TemplateContentPayload;
    }>,
  ) => api.put<TemplateDetailResponse>(`/templates/${id}`, data),
  delete: (id: string) => api.delete<void>(`/templates/${id}`),
};

export const collaborationApi = {
  getSharedReview: (token: string) =>
    api.get<SharedReviewPayload>(`/collaboration/shared-reviews/${token}`),
};
