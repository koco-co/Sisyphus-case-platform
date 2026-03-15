import { create } from 'zustand';

export interface DashboardStats {
  product_count: number;
  iteration_count: number;
  requirement_count: number;
  testcase_count: number;
  coverage_rate: number;
  weekly_cases: number;
  pending_diagnosis: number;
  requirement_delta: number;
  testcase_delta: number;
  coverage_delta: number;
  selected_iteration_id: string | null;
  selected_iteration_name: string | null;
  selected_iteration_status: string | null;
  selected_iteration_product_name: string | null;
  previous_iteration_id: string | null;
  previous_iteration_name: string | null;
  available_iterations: DashboardIterationOption[];
}

export interface DashboardIterationOption {
  id: string;
  product_id: string;
  product_name: string;
  name: string;
  status: string;
  start_date: string | null;
  end_date: string | null;
}

export interface PendingItem {
  id: string;
  type: 'unconfirmed_testpoint' | 'pending_review' | 'failed_diagnosis' | 'low_coverage';
  title: string;
  description: string;
  product_name: string;
  priority: 'high' | 'medium' | 'low';
  link: string;
  created_at: string;
}

export interface ActivityItem {
  id: string;
  time: string;
  action: string;
  resource: string;
  resource_id: string;
  title: string;
  user: string;
}

interface DashboardState {
  stats: DashboardStats | null;
  pendingItems: PendingItem[];
  activities: ActivityItem[];

  setStats: (stats: DashboardStats) => void;
  setPendingItems: (items: PendingItem[]) => void;
  setActivities: (activities: ActivityItem[]) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  stats: null,
  pendingItems: [],
  activities: [],

  setStats: (stats) => set({ stats }),
  setPendingItems: (items) => set({ pendingItems: items }),
  setActivities: (activities) => set({ activities: activities }),
}));
