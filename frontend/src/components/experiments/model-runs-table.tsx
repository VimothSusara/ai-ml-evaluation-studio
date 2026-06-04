"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "@/components/shared/status-badge";
import { Badge } from "@/components/ui/badge";
import type { Experiment } from "@/types/api";
import {
  formatMetricLabel,
  formatMetricValue,
  metricKeysForProblem,
  pickBestRun,
} from "@/lib/experiments/metrics";

export function ModelRunsTable({ experiment }: { experiment: Experiment }) {
  const keys = metricKeysForProblem(experiment.problem_type);
  const best = pickBestRun(experiment);

  return (
    <div className="rounded-lg border bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Model</TableHead>
            <TableHead>Status</TableHead>
            {keys.map((k) => (
              <TableHead key={k}>{formatMetricLabel(k)}</TableHead>
            ))}
            <TableHead>Time (ms)</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {experiment.model_runs.map((run) => {
            const isBest = best?.id === run.id;
            return (
              <TableRow
                key={run.id}
                className={isBest ? "bg-emerald-50/50" : undefined}
              >
                <TableCell className="font-medium">
                  <span className="flex items-center gap-2">
                    {run.model_code}
                    {isBest && (
                      <Badge className="bg-emerald-600 text-white">Best</Badge>
                    )}
                  </span>
                </TableCell>
                <TableCell>
                  <StatusBadge status={run.status} />
                </TableCell>
                {keys.map((k) => (
                  <TableCell key={k}>
                    {run.metrics?.[k] != null
                      ? formatMetricValue(k, run.metrics[k])
                      : "—"}
                  </TableCell>
                ))}
                <TableCell>{run.train_duration_ms ?? "—"}</TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      {experiment.model_runs.some((r) => r.error) && (
        <div className="border-t p-4 text-sm text-red-600">
          {experiment.model_runs
            .filter((r) => r.error)
            .map((r) => (
              <p key={r.id}>
                <strong>{r.model_code}:</strong> {r.error}
              </p>
            ))}
        </div>
      )}
    </div>
  );
}
