import { apiRequest } from "./client";
import type { TokenResponse } from "@/types/api";

export async function login(email: string, password: string) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    auth: false,
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
}

export async function register(email: string, password: string) {
  return apiRequest<{ id: string; email: string; role: string }>("/auth/register", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email, password }),
  });
}