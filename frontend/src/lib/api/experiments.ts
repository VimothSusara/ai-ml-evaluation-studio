import { apiRequest } from "./client";
import type { Experiment, TrainResponse } from "@/types/api";

export function listExperiments() {
  return apiRequest<Experiment[]>("/experiments/");
}

export function getExperiment(id: string) {
  return apiRequest<Experiment>(`/experiments/${id}`);
}

export function trainExperiment(payload: {
  dataset_id: string;
  target_column: string;
  problem_type_override?: string | null;
  model_codes?: string[] | null;
}) {
  return apiRequest<TrainResponse>("/experiments/train", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}