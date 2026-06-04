"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listExperiments } from "@/lib/api/experiments";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import {
  formatMetricLabel,
  formatMetricValue,
  pickBestRun,
  primaryMetricKey,
} from "@/lib/experiments/metrics";

export default function ExperimentsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["experiments"],
    queryFn: listExperiments,
  });

  const experiments = data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Experiments"
        description="Training runs and model comparisons across your datasets."
      />

      <Card>
        <CardHeader>
          <CardTitle>All experiments</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-3">
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </div>
          )}

          {!isLoading && experiments.length === 0 && (
            <EmptyState
              title="No experiments yet"
              description="Open a profiled dataset, validate a target column, and train models to see results here."
            />
          )}

          {!isLoading && experiments.length > 0 && (
            <ul className="divide-y">
              {experiments.map((exp) => {
                const best = pickBestRun(exp);
                const metricKey = primaryMetricKey(exp.problem_type);
                const bestValue = best?.metrics?.[metricKey];

                return (
                  <li
                    key={exp.id}
                    className="flex flex-wrap items-center justify-between gap-3 py-4 first:pt-0"
                  >
                    <div className="min-w-0">
                      <p className="font-medium text-zinc-900">
                        {exp.target_column}{" "}
                        <span className="font-normal text-zinc-500">·</span>{" "}
                        {exp.problem_type}
                      </p>
                      <p className="truncate text-xs text-zinc-500">{exp.id}</p>
                      {best && bestValue != null && (
                        <p className="mt-1 text-xs text-emerald-700">
                          Best: {best.model_code} —{" "}
                          {formatMetricLabel(metricKey)}{" "}
                          {formatMetricValue(metricKey, bestValue)}
                        </p>
                      )}
                      {exp.created_at && (
                        <p className="mt-0.5 text-xs text-zinc-400">
                          {new Date(exp.created_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <StatusBadge status={String(exp.status)} />
                      <Button size="sm" asChild>
                        <Link href={`/experiments/${exp.id}`}>
                          View results
                        </Link>
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
