export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api/backend${path}`, {
    ...options, headers: { "Content-Type": "application/json", ...options?.headers },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error?.message || `Request failed (${response.status}).`);
  return data as T;
}
