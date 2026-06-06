import type { Experiment, ModelRun } from "@/types/api";

export function isClassification(problemType: string) {
  return problemType === "classification";
}

export function primaryMetricKey(problemType: string): "f1_weighted" | "r2" {
  return isClassification(problemType) ? "f1_weighted" : "r2";
}

export function formatMetricLabel(key: string) {
  const labels: Record<string, string> = {
    accuracy: "Accuracy",
    f1_weighted: "F1 (weighted)",
    precision_weighted: "Precision (weighted)",
    recall_weighted: "Recall (weighted)",
    roc_auc: "ROC AUC",
    rmse: "RMSE",
    r2: "R²",
    mae: "MAE",
    train_duration_ms: "Train time",
  };
  return labels[key] ?? key;
}

const THREE_DECIMAL_METRICS = new Set([
  "accuracy",
  "f1_weighted",
  "precision_weighted",
  "recall_weighted",
  "roc_auc",
  "r2",
  "rmse",
  "mae",
]);

export function formatMetricValue(key: string, value: number) {
  if (THREE_DECIMAL_METRICS.has(key)) {
    return value.toFixed(3);
  }
  return String(value);
}

export function pickBestRun(exp: Experiment): ModelRun | null {
  const completed = exp.model_runs.filter(
    (r) => r.status === "completed" && r.metrics,
  );
  if (!completed.length) return null;

  const key = primaryMetricKey(exp.problem_type);
  return completed.reduce((best, cur) => {
    const b = best.metrics?.[key] ?? -Infinity;
    const c = cur.metrics?.[key] ?? -Infinity;
    return c > b ? cur : best;
  });
}

export function metricKeysForProblem(problemType: string): string[] {
  return isClassification(problemType)
    ? ["accuracy", "f1_weighted", "precision_weighted", "recall_weighted"]
    : ["rmse", "r2", "mae"];
}