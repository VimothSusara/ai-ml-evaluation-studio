import { apiRequest } from "./client";
import type {
  Dataset,
  RecommendationsResponse,
  UploadResponse,
  ValidationResponse,
} from "@/types/api";

export function listDatasets() {
  return apiRequest<Dataset[]>("/datasets/");
}

export function getDataset(id: string) {
  return apiRequest<Dataset>(`/datasets/${id}`);
}

export function getDatasetColumns(id: string) {
  return apiRequest<{
    dataset_id: string;
    columns: string[];
    dtypes: Record<string, string>;
    missing: Record<string, number>;
    column_stats?: Record<string, unknown>;
  }>(`/datasets/${id}/columns`);
}

export async function uploadDataset(file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiRequest<UploadResponse>("/datasets/upload", {
    method: "POST",
    body: form,
  });
}

export function validateDataset(
  id: string,
  payload: { target_column: string; problem_type_override?: string | null },
) {
  return apiRequest<ValidationResponse>(`/datasets/${id}/validate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getRecommendations(
  id: string,
  payload: { target_column: string; problem_type_override?: string | null },
) {
  return apiRequest<RecommendationsResponse>(`/datasets/${id}/recommendations`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}