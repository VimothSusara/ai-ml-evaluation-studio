import { apiRequest } from "./client";
import type {
  InferenceSchema,
  ModelExportResponse,
  PredictResponse,
} from "@/types/api";

export function getExperimentInferenceSchema(experimentId: string) {
  return apiRequest<InferenceSchema>(
    `/experiments/${experimentId}/inference-schema`,
  );
}

export function exportExperimentModel(
  experimentId: string,
  format: "joblib" | "manifest",
) {
  return apiRequest<ModelExportResponse>(
    `/experiments/${experimentId}/export?format=${format}`,
  );
}

export function predictExperiment(
  experimentId: string,
  rows: Record<string, string | number>[],
) {
  return apiRequest<PredictResponse>(`/experiments/${experimentId}/predict`, {
    method: "POST",
    body: JSON.stringify({ rows }),
  });
}