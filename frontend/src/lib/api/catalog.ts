import { apiRequest } from "./client";
import type { ProblemType } from "@/types/api";

export function listProblemTypes() {
  return apiRequest<ProblemType[]>("/catalog/problem-types");
}

export function listModels() {
  return apiRequest<
    { code: string; display_name: string; estimator_key: string }[]
  >("/catalog/models");
}