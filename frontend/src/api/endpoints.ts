/** 类型化端点封装。 */
import { api } from "./client";
import type {
  AppState,
  ContentsResponse,
  FoodOrdersResponse,
  HistoryResponse,
  OrdersResponse,
  PlanActivateResp,
  PlanCatalog,
  PlanConfigIn,
  PlanDraftResp,
  PlanReportResp,
  Profile,
  RedeemResult,
  RewardData,
  SessionPlanResp,
  ShopItemsResponse,
  TasksResponse,
  WorkTasksResp,
} from "../types";

export const loadAppState = () => api.get<AppState>("/api/session/current");
export const startSession = () => api.post<AppState>("/api/session/start");

export const chooseScenario = (scenario: string, contentType?: string | null) =>
  api.post<AppState>("/api/agent/start", {
    scenario,
    content_type: contentType ?? undefined,
  });

export const sendAction = (action: string, contentType?: string | null) =>
  api.post<AppState>("/api/agent/act", {
    action,
    content_type: contentType ?? undefined,
  });

/** 作息设置（工作日入睡/起床时间等）。 */
export const updateProfile = (patch: Partial<Profile>) =>
  api.put<Profile>("/api/user/profile", patch);

/** 首次配置向导完成标记。 */
export const completeOnboarding = () =>
  api.post<{ ok: boolean; needs_setup: boolean }>("/api/user/onboarding", { done: true });

// Demo Control
export const demoEnterWindow = () => api.post<AppState>("/api/demo/enter-window");
export const demoAdvance = (minutes: number) =>
  api.post<AppState>("/api/demo/advance", { minutes });
export const demoNextDay = () => api.post<AppState>("/api/demo/next-day");
export const demoReset = () => api.post<AppState>("/api/demo/reset");

// 内容 / 奖励
export const fetchContents = () => api.get<ContentsResponse>("/api/agent/contents");
export const settleReward = (sessionId?: number) =>
  api.post<RewardData>("/api/reward/settle", { session_id: sessionId });
export const fetchHistory = () => api.get<HistoryResponse>("/api/reward/history");
export const recordMiss = (scenario?: string) =>
  api.post<{ coins_deducted: number; coins_left: number; message: string }>(
    "/api/reward/miss",
    { scenario }
  );

// 积分兑换
export const fetchShopItems = () => api.get<ShopItemsResponse>("/api/shop/items");
export const redeemShopItem = (itemId: number, customNote?: string) =>
  api.post<RedeemResult>("/api/shop/redeem", {
    item_id: itemId,
    custom_note: customNote,
  });
export const fetchOrders = () => api.get<OrdersResponse>("/api/shop/orders");

// 深夜计划：工作型 Agent 任务 / 服务型 Agent 外卖
export const fetchWorkTypes = () => api.get<WorkTasksResp>("/api/work/types");
export const startWorkTask = (kind: string, sessionId?: number) =>
  api.post<{ id: number; kind: string }>("/api/work/start", {
    kind,
    session_id: sessionId,
  });
export const fetchWorkTasks = (sessionId: number) =>
  api.get<TasksResponse>(`/api/work/tasks?session_id=${sessionId}`);
export const placeFoodOrder = (
  source: "redeem_breakfast" | "work_agent",
  itemName?: string,
  note?: string
) =>
  api.post<{ id: number }>("/api/food/order", {
    source,
    item_name: itemName,
    note,
  });
export const fetchFoodOrders = () => api.get<FoodOrdersResponse>("/api/food/orders");

// 深夜计划
export const fetchPlanCatalog = () => api.get<PlanCatalog>("/api/plan/types");
export const fetchPlanDraft = () => api.get<PlanDraftResp>("/api/plan/draft");
export const savePlanDraft = (tasks: PlanConfigIn["tasks"]) =>
  api.post<PlanDraftResp>("/api/plan/config", { tasks });
export const activatePlan = (sessionId: number) =>
  api.post<PlanActivateResp>("/api/plan/activate", { session_id: sessionId });
export const fetchSessionPlan = (sessionId: number) =>
  api.get<SessionPlanResp>(`/api/plan/session?session_id=${sessionId}`);
export const fetchPlanReport = (sessionId: number) =>
  api.get<PlanReportResp>(`/api/plan/report?session_id=${sessionId}`);
