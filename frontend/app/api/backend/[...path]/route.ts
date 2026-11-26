import { NextRequest, NextResponse } from "next/server";
import { authenticated, sameOrigin } from "@/lib/session";

export const maxDuration = 300;
async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  if (!authenticated(request.cookies.get("codeatlas-session")?.value)) return NextResponse.json({ error: { message: "Sign in to the workspace first." } }, { status: 401 });
  if (request.method !== "GET" && !sameOrigin(request)) return NextResponse.json({ error: { message: "Invalid origin." } }, { status: 403 });
  const { path } = await context.params;
  const route = "/" + path.join("/");
  if (!/^\/api\/(repositories(\/[a-zA-Z0-9]+(\/(tree|source|overview|impact|questions))?)?|jobs\/[a-zA-Z0-9]+|readiness)$/.test(route)) return NextResponse.json({ error: { message: "Unknown endpoint." } }, { status: 404 });
  if (process.env.NODE_ENV === "production" && !process.env.CODEATLAS_API_TOKEN) return NextResponse.json({ error: { message: "Backend authentication is not configured." } }, { status: 503 });
  const body = request.method === "POST" ? await request.text() : undefined;
  if (body && Buffer.byteLength(body) > 32768) return NextResponse.json({ error: { message: "Request too large." } }, { status: 413 });
  try {
    const response = await fetch(`${process.env.CODEATLAS_API_URL || "http://127.0.0.1:8000"}${route}${request.nextUrl.search}`, {
      method: request.method, body, cache: "no-store", signal: AbortSignal.timeout(240000),
      headers: { "Content-Type": "application/json", ...(process.env.CODEATLAS_API_TOKEN ? { Authorization: `Bearer ${process.env.CODEATLAS_API_TOKEN}` } : {}) },
    });
    if (response.status === 401) return NextResponse.json({ error: { message: "Backend authentication failed. Check that the Vercel API token matches Render's API_TOKEN." } }, { status: 503 });
    if (!response.headers.get("content-type")?.includes("application/json")) return NextResponse.json({ error: { message: "The backend is waking up or restarting. Please retry in a moment." } }, { status: 503 });
    return new NextResponse(await response.text(), { status: response.status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...(response.headers.get("retry-after") ? { "Retry-After": response.headers.get("retry-after")! } : {}) } });
  } catch { return NextResponse.json({ error: { message: "Backend unavailable. Check the API server and provider configuration." } }, { status: 503 }); }
}
export { proxy as GET, proxy as POST, proxy as DELETE };
