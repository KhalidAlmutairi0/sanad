import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/server-api";

const BASE = (process.env.API_BASE_URL ?? "http://api:8000") + "/api/v1";

// Public "try it now" access: mint a guest session and store its JWT in the httpOnly cookie,
// exactly like login. The token never reaches client JS. No body is sent to the backend.
export async function POST(req: Request) {
  const fwd = req.headers.get("x-forwarded-for");
  const res = await fetch(`${BASE}/auth/guest`, {
    method: "POST",
    headers: { "content-type": "application/json", ...(fwd ? { "x-forwarded-for": fwd } : {}) },
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
  // Non-sensitive role hint (NOT the token) so the client can tailor nav. Readable by JS.
  response.cookies.set("sanad_role", String(data.user?.role ?? ""), {
    httpOnly: false, sameSite: "lax", secure: process.env.NODE_ENV === "production",
    path: "/", maxAge: 60 * 60 * 8,
  });
  return response;
}
