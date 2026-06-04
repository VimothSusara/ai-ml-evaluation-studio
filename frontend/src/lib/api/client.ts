import { apiPath } from "@/lib/config";
import { clearToken, getToken } from "@/lib/auth/token";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = RequestInit & { auth?: boolean };

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const h = new Headers(headers);

  if (auth) {
    const token = getToken();
    if (token) h.set("Authorization", `Bearer ${token}`);
  }

  if (!(rest.body instanceof FormData)) {
    if (!h.has("Content-Type") && rest.body) {
      h.set("Content-Type", "application/json");
    }
  }

  const res = await fetch(apiPath(path), { ...rest, headers: h });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }

  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = await res.text();
    }
    const msg =
      typeof body === "object" && body && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `Request failed (${res.status})`;
    throw new ApiError(msg, res.status, body);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}