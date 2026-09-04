/** 与后端 AppState 对齐的类型定义（见 backend 会话聚合视图）。 */

export interface Profile {
  weekday_bedtime: string;
  weekday_wake: string;
  weekend_bedtime: string;
  weekend_wake: string;
  preferred_content: string[];
  streak_days: number;
  total_coins: number;
  completed_nights: number;
  last_success_date: string | null;
}

export interface ClockInfo {
  demo_active: boolean;
  virtual_now: string | null;
  real_now: string;
}

export interface HomeInfo {
  phase: string;
  phase_text: string;
  bedtime_hm: string;
  wake_hm: string;
  window_start: string;
  bedtime: string;
  wake: string;
  is_in_window: boolean;
  can_start: boolean;
}

export interface ContentItem {
  id: number;
  type: string;
  title: string;
  subtitle: string;
  duration_min: number;
  icon: string;
  mood: string;
}

export interface MessageInfo {
  text: string;
  suggestion: string;
  source: string;
}

export interface SleepInfo {
  started_at: string | null;
  remaining_sec: number | null;
  elapsed_min: number | null;
}

export interface SessionInfo {
  session_id: number;
  date: string;
  state: string;
  stage: number | null;
  stage_label: string;
  scenario: string | null;
  scenario_name: string;
  scenario_icon: string;
  content: ContentItem | null;
  message: MessageInfo;
  can_act: string[];
  sleep: SleepInfo;
  updated_at: string;
  reward_ready: boolean;
}

export interface AppState {
  profile: Profile;
  clock: ClockInfo;
  home: HomeInfo;
  session: SessionInfo | null;
  meta: { needs_setup: boolean };
}

export interface RewardData {
  already: boolean;
  id: number;
  session_id: number;
  date: string;
  coins: number;
  streak_days: number;
  total_coins: number;
  message: string;
}

export interface ContentsResponse {
  type_labels: Record<string, string>;
  groups: Array<{ type: string; label: string; items: ContentItem[] }>;
}

/* ---------------- 睡眠记录 ---------------- */
export interface HistoryItem {
  kind?: "sleep" | "miss";
  session_id: number | null;
  date: string;
  state: string;
  result: string;
  scenario: string | null;
  scenario_name: string;
  scenario_icon: string;
  stage: number | null;
  coins: number | null;
  streak: number | null;
  total_coins: number | null;
  reward_message: string | null;
}

export interface HistoryResponse {
  items: HistoryItem[];
}

/* ---------------- 积分兑换 ---------------- */
export interface ShopProduct {
  id: number;
  name: string;
  brand: string;
  desc: string;
  icon: string;
  price_coins: number;
  tag: string;
  stock: number;
  custom?: boolean;
  kind?: string;
}

export interface ShopItemsResponse {
  items: ShopProduct[];
}

export interface ShopOrder {
  id: number;
  item_name: string;
  item_icon: string | null;
  coins_spent: number;
  date: string;
  status: string;
}

export interface OrdersResponse {
  items: ShopOrder[];
}

export interface RedeemResult {
  id: number;
  item_id: number;
  item_name: string;
  item_icon: string | null;
  coins_spent: number;
  coins_left: number;
  status: string;
  message: string;
}

/* ---------------- 深夜计划（工作/服务 Agent） ---------------- */
export interface WorkTaskType {
  key: string;
  name: string;
  icon: string;
  desc: string;
  duration_min: number;
}

export interface WorkTasksResp {
  items: WorkTaskType[];
}

export interface WorkTaskItem {
  id: number;
  kind: string;
  name: string;
  icon: string | null;
  status: "queued" | "running" | "done";
  progress: number;
  result: string | null;
  created_at: string;
}

export interface TasksResponse {
  items: WorkTaskItem[];
}

export interface FoodOrderItem {
  id: number;
  source: string;
  item_name: string;
  note: string | null;
  stage_key: string;
  stage_label: string;
  stage_index: number;
  message: string;
  progress: number;
  placed_at: string;
  delivered: boolean;
}

export interface FoodOrdersResponse {
  items: FoodOrderItem[];
}

/* ---------------- 深夜计划（首页表格配置 / Stage3 启动 / 次日交付） ---------------- */
export interface PlanParamMeta {
  key: string;
  label: string;
  type: string;
  default: string;
}

export interface PlanTaskType {
  key: string;
  category: string;
  name: string;
  icon: string;
  desc: string;
  params: PlanParamMeta[];
}

export interface SpecDoc {
  key: string;
  name: string;
  summary: string;
}

export interface PlanCategory {
  key: string;
  name: string;
}

export interface PlanCatalog {
  categories: PlanCategory[];
  task_types: PlanTaskType[];
  spec_docs: SpecDoc[];
  default_tasks: Array<{
    category: string;
    task_type: string;
    title: string;
    params: Record<string, string>;
  }>;
}

export interface PlanDraftTask {
  task_id: number;
  category: string;
  category_name: string;
  task_type: string;
  title: string;
  icon: string;
  point: string;
  params: Record<string, string>;
}

export interface PlanDraftResp {
  plan_id: number | null;
  status: string;
  tasks: PlanDraftTask[];
}

export interface PlanConfigIn {
  tasks: Array<{
    category: string;
    task_type: string;
    title?: string;
    params?: Record<string, string>;
  }>;
}

export interface PlanActivateResp {
  plan_id: number;
  session_id: number | null;
  date: string | null;
  status: string;
  tasks: PlanDraftTask[];
}

export interface SessionPlanResp {
  has_plan: boolean;
  plan_id?: number;
  task_count?: number;
  tasks?: PlanDraftTask[];
  points?: string[];
}

export interface PlanArtifact {
  kind: string;
  title: string;
  body: string;
}

export interface PlanReportItem {
  task_id: number;
  category: string;
  category_name: string;
  task_type: string;
  title: string;
  icon: string;
  status: string;
  label: string;
  progress: number;
  artifact: PlanArtifact | null;
}

export interface PlanReportResp {
  has_plan: boolean;
  plan_date: string | null;
  plan_id?: number;
  items: PlanReportItem[];
}

export type Screen =
  | { name: "home" }
  | { name: "scenario" }
  | { name: "intervention" }
  | { name: "sleep" }
  | { name: "reward"; data: RewardData }
  | { name: "record" }
  | { name: "shop" }
  | { name: "phone" };
