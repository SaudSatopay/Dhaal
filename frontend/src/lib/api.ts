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
export function askModKey(): string {
  let k = "";
  try {
    k = window.prompt("Moderator key (टीम से लें):") ?? "";
  } catch {
    return ""; // prompt unavailable (embedded/automated context)
  }
  try {
    if (k) localStorage.setItem("dhaal-mod-key", k.trim());
  } catch {}
  return k.trim();
}

// Typed failure: callers must be able to tell "you are not authorized" from
// "the service is down" — an auth refusal shown as an outage banner is a lie
// (H17 external review caught exactly that on /intel).
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export type ApiInit = RequestInit & {
  // Opt-in ONLY for explicit moderator ACTIONS (verify/reject). Background
  // polls must never pop a key prompt — they throw ApiError(401) instead.
  promptModKey?: boolean;
};

export async function api<T = unknown>(
  path: string,
  init?: ApiInit
): Promise<T> {
  const { promptModKey, ...rest } = init ?? {};
  const doFetch = () =>
    fetch(`${API_BASE}${path}`, {
      // init first, merged headers LAST — otherwise a caller passing its own
      // headers (e.g. X-Guardian-Token) silently wipes Content-Type and the
      // backend sees a JSON string instead of an object (422).
      ...rest,
      headers: {
        "Content-Type": "application/json",
        ...(modKey() ? { "X-Mod-Key": modKey() } : {}),
        ...(rest.headers ?? {}),
      },
    });
  let res = await doFetch();
  // the mod-key prompt belongs to MODERATION endpoints only — a guardian/ward
  // 401 means a dead pairing token and must surface to the caller, not open
  // a moderator-key dialog (H14).
  if (
    res.status === 401 &&
    promptModKey &&
    typeof window !== "undefined" &&
    path.startsWith("/api/reports") &&
    askModKey()
  ) {
    res = await doFetch();
  }
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, `API ${res.status}: ${body || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// Multipart variant (e.g. /api/transcribe audio upload) — the browser must set the
// Content-Type boundary itself, so no JSON header here.
export async function apiForm<T = unknown>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: form });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, `API ${res.status}: ${body || res.statusText}`);
  }
  return res.json() as Promise<T>;
}
