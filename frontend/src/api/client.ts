/** 极简 REST 客户端（无第三方依赖，保证稳定）。 */

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(message: string, code = "error", status = 400) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(`${BASE}${path}`, {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("无法连接后端服务，请确认 FastAPI 已在 8000 端口启动", "network", 0);
  }

  let data: unknown = null;
  try {
    data = await resp.json();
  } catch {
    /* 空响应体 */
  }
  if (!resp.ok) {
    const detail = (data as { detail?: { code?: string; message?: string } } | null)?.detail;
    throw new ApiError(
      detail?.message ?? `请求失败（HTTP ${resp.status}）`,
      detail?.code ?? "http_error",
      resp.status
    );
  }
  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
};
