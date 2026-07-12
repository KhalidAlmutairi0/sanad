import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/server-api";

const BASE = (process.env.API_BASE_URL ?? "http://api:8000") + "/api/v1";

// Proxy login and store the JWT in an httpOnly cookie. The token never reaches client JS.
export async function POST(req: Request) {
  const body = await req.json();
  // Propagate the real client IP so the backend rate limiter keys per user, not per this
  // proxy (Caddy sets X-Forwarded-For on the request that reaches us).
  const fwd = req.headers.get("x-forwarded-for");
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "content-type": "application/json", ...(fwd ? { "x-forwarded-for": fwd } : {}) },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    return NextResponse.json(data ?? { error: { code: "error" } }, { status: res.status });
  }
  const response = NextResponse.json({ user: data.user });
  response.cookies.set(SESSION_COOKIE, data.token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 8,
  });
  return response;
}
