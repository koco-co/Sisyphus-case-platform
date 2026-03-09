export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// ── Domain types matching backend schemas ──

export interface Product {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Iteration {
  id: string;
  product_id: string;
  name: string;
  start_date: string | null;
  end_date: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Requirement {
  id: string;
  iteration_id: string;
  req_id: string;
  title: string;
  status: string;
  version: number;
  content_ast: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface SceneMap {
  id: string;
  requirement_id: string;
  status: string;
  confirmed_at: string | null;
  test_points: TestPoint[];
  created_at: string;
  updated_at: string;
}

export interface TestPoint {
  id: string;
  scene_map_id: string;
  group_name: string;
  title: string;
  description: string | null;
  priority: string;
  status: string;
  estimated_cases: number;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface GenerationSession {
  id: string;
  requirement_id: string;
  mode: string;
  status: string;
  model_used: string;
  created_at: string;
  updated_at: string;
}

export interface TestCase {
  id: string;
  requirement_id: string;
  test_point_id: string | null;
  case_id: string;
  title: string;
  priority: string;
  status: string;
  case_type: string;
  source: string;
  ai_score: number | null;
  precondition: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface TestCaseStep {
  no: number;
  action: string;
  expected_result: string;
}
