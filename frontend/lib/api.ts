export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/backend${path}`, {
      ...options, headers: { "Content-Type": "application/json", ...options?.headers },
    });
  } catch {
    throw new ApiError("Connection lost. The backend may be waking up or restarting. Retry shortly.", 0);
  }
  const data = await response.json().catch(() => null);
  if (response.status === 401) {
    window.dispatchEvent(new Event("codeatlas:session-expired"));
    throw new ApiError("Your session expired. Sign in again to continue.", 401);
  }
  if (!response.ok || data === null) {
    const fallback = response.status === 429
      ? "Request limit reached. Please wait before retrying."
      : [502, 503, 504].includes(response.status) || data === null
        ? "The backend is waking up or restarting. Please retry in a moment."
        : `Request failed (${response.status}).`;
    throw new ApiError(data?.error?.message || fallback, response.status);
  }
  return data as T;
}
