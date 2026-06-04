"use client";

import { StatCard } from "@/components/shared/stat-card";
import { JsonCollapse } from "@/components/shared/json-collapse";
import { ModelComparisonBars } from "./model-comparison-bars";
import { ModelRunsTable } from "./model-runs-table";
import type { Experiment } from "@/types/api";
import {
  formatMetricLabel,
  formatMetricValue,
  metricKeysForProblem,
  pickBestRun,
} from "@/lib/experiments/metrics";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EvaluationCharts } from "@/components/experiments/evaluation-charts";
import { ModelInferencePanel } from "@/components/experiments/model-inference-panel";

export function ExperimentResults({ experiment }: { experiment: Experiment }) {
  const best = pickBestRun(experiment);
  const keys = metricKeysForProblem(experiment.problem_type);

  return (
    <div className="space-y-6">
      {experiment.explanation && (
        <Card>
          <CardHeader>
            <CardTitle>AI summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed text-zinc-700">
              {experiment.explanation}
            </p>
          </CardContent>
        </Card>
      )}

      {best?.metrics && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {keys.map((k) => (
            <StatCard
              key={k}
              label={formatMetricLabel(k)}
              value={formatMetricValue(k, best.metrics![k] ?? 0)}
              hint={`Best: ${best.model_code}`}
            />
          ))}
          <StatCard
            label="Models trained"
            value={
              experiment.model_runs.filter((r) => r.status === "completed")
                .length
            }
            hint={`of ${experiment.model_runs.length} runs`}
          />
        </div>
      )}

      <ModelComparisonBars experiment={experiment} />
      {(experiment.evaluation ?? pickBestRun(experiment)?.evaluation) && (
        <EvaluationCharts
          evaluation={
            (experiment.evaluation ??
              pickBestRun(experiment)!.evaluation!) as import("@/types/api").ModelEvaluation
          }
        />
      )}
      <ModelInferencePanel experiment={experiment} />
      <ModelRunsTable experiment={experiment} />
      <JsonCollapse title="Advanced: raw experiment JSON" data={experiment} />
    </div>
  );
}
