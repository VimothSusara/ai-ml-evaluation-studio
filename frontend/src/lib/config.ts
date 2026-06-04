export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX || "/api/v1";

export function apiPath(path: string) {
  return `${API_URL}${API_PREFIX}${path}`;
}

export function googleOAuthStartUrl() {
  return apiPath("/auth/oauth/google/start");
}
