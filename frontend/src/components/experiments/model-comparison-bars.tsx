"use client";

import type { Experiment, ModelRun } from "@/types/api";
import {
  formatMetricLabel,
  formatMetricValue,
  primaryMetricKey,
  pickBestRun,
} from "@/lib/experiments/metrics";

export function ModelComparisonBars({
  experiment,
}: {
  experiment: Experiment;
}) {
  const key = primaryMetricKey(experiment.problem_type);
  const best = pickBestRun(experiment);
  const runs = experiment.model_runs.filter(
    (r) => r.status === "completed" && r.metrics?.[key] != null,
  );
  if (!runs.length) return null;

  const max = Math.max(...runs.map((r) => r.metrics![key] ?? 0));

  return (
    <div className="rounded-lg border bg-white p-4">
      <h3 className="mb-4 text-sm font-semibold">
        Model comparison ({formatMetricLabel(key)})
      </h3>
      <div className="space-y-3">
        {runs.map((run) => {
          const value = run.metrics![key] ?? 0;
          const width = max > 0 ? (value / max) * 100 : 0;
          const isBest = best?.id === run.id;
          return (
            <div key={run.id}>
              <div className="mb-1 flex justify-between text-sm">
                <span
                  className={isBest ? "font-semibold text-emerald-700" : ""}
                >
                  {run.model_code}
                  {isBest && " · Best"}
                </span>
                <span>{formatMetricValue(key, value)}</span>
              </div>
              <div className="h-3 rounded-full bg-zinc-100">
                <div
                  className={`h-3 rounded-full ${isBest ? "bg-emerald-500" : "bg-zinc-500"}`}
                  style={{ width: `${width}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
