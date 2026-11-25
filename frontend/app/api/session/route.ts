import { NextRequest, NextResponse } from "next/server";
import { equal, sign } from "@/lib/session";

const attempts = new Map<string, { count: number; until: number }>();
export async function POST(request: NextRequest) {
  if (request.headers.get("origin") !== request.nextUrl.origin) return NextResponse.json({ error: "Invalid origin" }, { status: 403 });
  const expected = process.env.FRONTEND_PASSWORD;
  if (!expected || expected.length < 16) return NextResponse.json({ error: "Configure FRONTEND_PASSWORD (at least 16 characters)." }, { status: 503 });
  const key = request.headers.get("x-forwarded-for")?.split(",")[0] || "local";
  const now = Date.now();
  for (const [k, v] of attempts) if (v.until < now) attempts.delete(k);
  const attempt = attempts.get(key) || { count: 0, until: now + 60000 };
  if (attempt.count >= 5 || attempts.size > 10000) return NextResponse.json({ error: "Try again in a minute." }, { status: 429 });
  attempt.count++; attempts.set(key, attempt);
  try {
    const { password } = await request.json();
    if (typeof password !== "string" || !equal(password, expected)) return NextResponse.json({ error: "Incorrect workspace password." }, { status: 401 });
    const expires = String(now + 8 * 60 * 60 * 1000);
    const response = NextResponse.json({ ok: true });
    response.cookies.set("codeatlas-session", `${expires}.${sign(expires)}`, { httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: "strict", path: "/", maxAge: 28800 });
    return response;
  } catch { return NextResponse.json({ error: "Invalid request." }, { status: 400 }); }
}
