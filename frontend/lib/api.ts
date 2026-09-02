import type { CategoryCount, Outlet, Status, StoryDetail, StoryListItem, User } from "./types";

// Server-side: call the backend directly. Browser-side: use a relative path that
// the Next rewrite (next.config.mjs) proxies to the backend, so there's no CORS
// and the auth cookie is same-origin.
const SSR_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function resolve(path: string, params?: Record<string, string | number | undefined>) {
  const base = typeof window === "undefined" ? SSR_BASE : window.location.origin;
  const url = new URL(path, base);
  for (const [k, v] of Object.entries(params ?? {})) {
    if (v !== undefined && v !== "") url.searchParams.set(k, String(v));
  }
  return url;
}

async function get<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
  cookie?: string,
  revalidate?: number,
): Promise<T> {
  const url = resolve(path, params);
  const init: RequestInit & { next?: { revalidate: number } } = {
    // Personalised or fast-changing responses stay uncached; list/reference
    // data is cached briefly so repeat navigation doesn't re-hit the DB.
    ...(revalidate ? { next: { revalidate } } : { cache: "no-store" as const }),
    headers: cookie ? { cookie } : undefined,
  };
  // The DB (Neon free tier) scales to zero when idle; the first request after
  // that can drop a stale pooled connection and 5xx. One retry turns that blip
  // into a ~1s delay instead of an error screen.
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetch(url, init);
      if (res.ok) return res.json() as Promise<T>;
      if (res.status < 500 || attempt >= 1) throw new Error(`${path} -> ${res.status}`);
    } catch (err) {
      if (attempt >= 1) throw err;
    }
    await new Promise((r) => setTimeout(r, 900));
  }
}

async function send<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(resolve(path), {
    method,
    credentials: "include",
    headers: body ? { "content-type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `${path} -> ${res.status}`);
  }
  return res.json().catch(() => ({})) as Promise<T>;
}

export type StoryQuery = {
  country?: string;
  category?: string;
  q?: string;
  min_outlets?: number;
  sort?: "hot" | "new";
};

export type Country = { code: string; name: string };

export const PAGE_SIZE = 24;

export const listStories = (q: StoryQuery, offset = 0) =>
  get<StoryListItem[]>("/api/stories", { ...q, limit: PAGE_SIZE, offset }, undefined, 30);

// No cookie / cacheable — per-user liked & saved come from getMyFlags client-side.
export const getStory = (id: string | number) =>
  get<StoryDetail>(`/api/stories/${id}`, undefined, undefined, 60);
export const getMyFlags = (id: number) =>
  get<{ liked: boolean; saved: boolean }>(`/api/stories/${id}/me`);

export const listCategories = (country?: string, minOutlets?: number) =>
  get<CategoryCount[]>("/api/categories", { country, min_outlets: minOutlets }, undefined, 120);
export const listCountries = () => get<Country[]>("/api/countries", undefined, undefined, 600);
export const listOutlets = (country?: string) =>
  get<Outlet[]>("/api/outlets", { country }, undefined, 600);
export const getStatus = (country?: string) => get<Status>("/api/status", { country });

// --- auth ---
export const authMe = () => get<User>("/api/auth/me");
export const signup = (username: string, password: string) =>
  send<User>("POST", "/api/auth/signup", { username, password });
export const login = (username: string, password: string) =>
  send<User>("POST", "/api/auth/login", { username, password });
export const logout = () => send<unknown>("POST", "/api/auth/logout");

// --- user lists + actions ---
export const myLikes = () => get<StoryListItem[]>("/api/me/likes");
export const mySaves = () => get<StoryListItem[]>("/api/me/saves");
export const myHistory = () => get<StoryListItem[]>("/api/me/history");
export const setLike = (id: number, on: boolean) =>
  send<{ on: boolean }>("PUT", `/api/stories/${id}/like?on=${on}`);
export const setSave = (id: number, on: boolean) =>
  send<{ on: boolean }>("PUT", `/api/stories/${id}/save?on=${on}`);
export const recordVisit = (id: number) =>
  send<unknown>("POST", `/api/stories/${id}/visit`);
