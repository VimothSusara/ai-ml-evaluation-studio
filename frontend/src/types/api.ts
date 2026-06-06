export type JobStatus = "queued" | "running" | "completed" | "failed";

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface JobContext {
  label?: string;
  dataset_id?: string;
  dataset_name?: string;
  dataset_status?: string;
  experiment_id?: string;
  target_column?: string;
  problem_type?: string;
  best_model?: string;
}

export interface Job {
  id: string;
  job_type: string;
  status: JobStatus;
  celery_task_id: string;
  payload: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  error: string | null;
  created_at?: string;
  context?: JobContext;
}

export interface Dataset {
  id: string;
  name: string;
  status: string;
  profile: Record<string, unknown> | null;
  validation: Record<string, unknown> | null;
  created_at?: string;
}

export interface ModelRecommendation {
  model_code: string;
  display_name: string;
  priority: number;
  is_default: boolean;
  reason: string | null;
  estimator_key: string;
}

export interface RecommendationsResponse {
  target_column: string;
  inferred_problem_type: string;
  problem_type: string;
  pipeline_kind?: string;
  target_validation: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
  };
  recommendations: ModelRecommendation[];
}

export interface ValidationResponse {
  dataset_id: string;
  inferred_problem_type: string;
  problem_type: string;
  dataset_validation: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
  };
  target_validation: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
  };
  ready_to_train: boolean;
}

export interface ModelRun {
  id: string;
  model_code: string;
  status: JobStatus;
  metrics: Record<string, number> | null;
  evaluation: ModelEvaluation | null;
  error: string | null;
  train_duration_ms: number | null;
  model_s3_key?: string | null;
}

export interface Experiment {
  id: string;
  dataset_id: string;
  target_column: string;
  problem_type: string;
  problem_type_override: string | null;
  pipeline_kind?: string | null;
  status: JobStatus | string;
  metrics: Record<string, number> | null;
  evaluation: ModelEvaluation | null;
  explanation: string | null;
  model_s3_key: string | null;
  model_runs: ModelRun[];
  created_at?: string;
}

export interface UploadResponse {
  dataset_id: string;
  job_id: string;
  task_id: string;
}

export interface TrainResponse {
  experiment_id: string;
  job_id: string;
  task_id: string;
  problem_type: string;
}

export interface ProblemType {
  code: string;
  name: string;
  description: string | null;
  pipeline_kind?: string;
}

export interface EvaluationSplit {
  test_size: number;
  random_state: number;
  n_train: number;
  n_test: number;
}

export interface ModelEvaluation {
  schema_version: number;
  problem_type: string;
  evaluator: string;
  split: EvaluationSplit;
  metrics: Record<string, number>;
  tables: Record<string, unknown>;
  plots: Record<string, unknown>;
  warnings: string[];
}

export interface InferenceSchema {
  model_run_id: string;
  model_code: string;
  problem_type: string;
  target_column: string;
  feature_columns: string[];
  dataset_id?: string;
}

export interface PredictionItem {
  prediction: string | number | boolean;
  probabilities?: Record<string, number> | null;
}

export interface PredictResponse {
  model_run_id: string;
  model_code: string;
  problem_type: string;
  predictions: PredictionItem[];
}

export interface ModelExportResponse {
  model_run_id: string;
  model_code: string;
  format: string;
  download_url?: string | null;
  expires_in_seconds?: number | null;
  filename?: string | null;
  manifest?: Record<string, unknown> | null;
}
