"use client";

// Client-side calls go through the Next BFF (/api/backend/*), which attaches the httpOnly
// session token server-side. Client code never sees the JWT.

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`/api/backend${path}`, { cache: "no-store" });
  if (!res.ok) throw await toError(res);
  return (await res.json()) as T;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api/backend${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) throw await toError(res);
  return (await res.json()) as T;
}

export async function login(email: string, password: string): Promise<void> {
  const res = await fetch(`/api/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw await toError(res);
}

export async function register(email: string, password: string, code: string): Promise<void> {
  const res = await fetch(`/api/register`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email, password, code }),
  });
  if (!res.ok) throw await toError(res);
}

export async function logout(): Promise<void> {
  await fetch(`/api/logout`, { method: "POST" });
}

async function toError(res: Response): Promise<Error> {
  const body = await res.json().catch(() => null);
  const err = new Error(body?.error?.code ?? `http_${res.status}`) as Error & { code?: string };
  err.code = body?.error?.code ?? `http_${res.status}`;
  return err;
}
