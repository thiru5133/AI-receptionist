const BASE = "/api";

function token(): string | null {
  return localStorage.getItem("token");
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  const t = token();
  if (t) headers.Authorization = `Bearer ${t}`;

  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export function setToken(t: string) {
  localStorage.setItem("token", t);
}

export function clearToken() {
  localStorage.removeItem("token");
}

export function isAuthed(): boolean {
  return !!token();
}
