import { apiRequest } from "./client";
import type { Job } from "@/types/api";

export function getJob(id: string) {
  return apiRequest<Job>(`/jobs/${id}`);
}

export function listJobs(params?: {
  active_only?: boolean;
  status?: string;
  limit?: number;
}) {
  const search = new URLSearchParams();
  if (params?.active_only) search.set("active_only", "true");
  if (params?.status) search.set("status", params.status);
  if (params?.limit) search.set("limit", String(params.limit));
  const qs = search.toString();
  return apiRequest<Job[]>(`/jobs/${qs ? `?${qs}` : ""}`);
}