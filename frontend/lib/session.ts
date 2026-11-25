import { createHmac, timingSafeEqual } from "node:crypto";

export function equal(left: string, right: string) {
  const a = Buffer.from(left), b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}
export function sign(value: string) {
  return createHmac("sha256", process.env.FRONTEND_PASSWORD || "development").update(value).digest("hex");
}
export function authenticated(cookie: string | undefined) {
  if (!process.env.FRONTEND_PASSWORD) return process.env.NODE_ENV !== "production";
  if (!cookie) return false;
  const [expiry, signature] = cookie.split(".");
  return Number(expiry) > Date.now() && equal(signature || "", sign(expiry));
}
