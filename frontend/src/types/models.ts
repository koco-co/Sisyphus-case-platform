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
  created_at: string;
  updated_at: string;
}

export interface SceneNode {
  id: string;
  map_id: string;
  parent_id: string | null;
  scenario_type: string;
  title: string;
  source: string;
  status: string;
  estimated_cases: number;
}

export interface TestCase {
  id: string;
  tc_id: string;
  title: string;
  tc_type: string;
  priority: string;
  status: string;
  requirement_id: string | null;
  scene_node_id: string | null;
  created_at: string;
  updated_at: string;
}
