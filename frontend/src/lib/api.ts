export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Moderation endpoints are key-gated in prod (blocklist writes must not be
// open to anyone with the URL). The key lives only in this browser; on a 401
// we ask once, store, and retry.
function modKey(): string {
  try {
    return localStorage.getItem("dhaal-mod-key") ?? "";
  } catch {
    return "";
  }
}
function askModKey(): string {
  const k = window.prompt("Moderator key (टीम से लें):") ?? "";
  try {
    if (k) localStorage.setItem("dhaal-mod-key", k.trim());
  } catch {}
  return k.trim();
}

export async function api<T = unknown>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const doFetch = () =>
    fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(modKey() ? { "X-Mod-Key": modKey() } : {}),
        ...(init?.headers ?? {}),
      },
      ...init,
    });
  let res = await doFetch();
  if (res.status === 401 && typeof window !== "undefined" && askModKey()) {
    res = await doFetch();
  }
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// Multipart variant (e.g. /api/transcribe audio upload) — the browser must set the
// Content-Type boundary itself, so no JSON header here.
export async function apiForm<T = unknown>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: form });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }
  return res.json() as Promise<T>;
}
