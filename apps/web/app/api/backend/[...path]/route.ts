import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { SESSION_COOKIE } from "@/lib/server-api";

const BASE = (process.env.API_BASE_URL ?? "http://api:8000") + "/api/v1";

// Generic BFF proxy: forwards client requests to the backend, attaching the httpOnly
// session token as a Bearer header server-side. No business logic here.
async function forward(req: Request, path: string[]) {
  const token = cookies().get(SESSION_COOKIE)?.value;
  const url = new URL(req.url);
  const target = `${BASE}/${path.join("/")}${url.search}`;
  const init: RequestInit = {
    method: req.method,
    headers: {
      "content-type": "application/json",
      ...(token ? { authorization: `Bearer ${token}` } : {}),
    },
    cache: "no-store",
  };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }
  const res = await fetch(target, init);
  const data = await res.json().catch(() => null);
  return NextResponse.json(data, { status: res.status });
}

export async function GET(req: Request, { params }: { params: { path: string[] } }) {
  return forward(req, params.path);
}
export async function POST(req: Request, { params }: { params: { path: string[] } }) {
  return forward(req, params.path);
}
export async function PUT(req: Request, { params }: { params: { path: string[] } }) {
  return forward(req, params.path);
}
