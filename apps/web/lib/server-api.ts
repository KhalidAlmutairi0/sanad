import "server-only";
import { cookies } from "next/headers";

// Server-side only. The JWT lives in an httpOnly cookie and is attached here; it is never
// exposed to client JS or web storage (AGENTS.md: no localStorage for sensitive data).
const BASE = (process.env.API_BASE_URL ?? "http://api:8000") + "/api/v1";
export const SESSION_COOKIE = "sanad_session";

export function getToken(): string | undefined {
  return cookies().get(SESSION_COOKIE)?.value;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiRequestError(res.status, body?.error?.code ?? "error", body);
  }
  return (await res.json()) as T;
}

export const serverGet = <T>(path: string) => request<T>(path);
export const serverPost = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

export class ApiRequestError extends Error {
  constructor(public status: number, public code: string, public body: unknown) {
    super(code);
  }
}
