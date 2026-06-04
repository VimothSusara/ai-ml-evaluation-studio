"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listJobs } from "@/lib/api/jobs";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";

type Filter = "active" | "all";

export default function JobsPage() {
  const [filter, setFilter] = useState<Filter>("active");

  const { data, isLoading } = useQuery({
    queryKey: ["jobs", filter],
    queryFn: () =>
      listJobs(
        filter === "active" ? { active_only: true, limit: 50 } : { limit: 50 },
      ),
    refetchInterval: (q) => {
      const jobs = q.state.data ?? [];
      const hasActive = jobs.some(
        (j) => j.status === "queued" || j.status === "running",
      );
      return hasActive || filter === "active" ? 3000 : false;
    },
  });

  const jobs = data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Jobs"
        description="Background profiling and training tasks. With a single worker, jobs run one at a time—new tasks wait in the queue."
      />

      <div className="flex gap-2">
        <Button
          variant={filter === "active" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("active")}
        >
          Active
        </Button>
        <Button
          variant={filter === "all" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("all")}
        >
          Recent (all)
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {filter === "active" ? "Queued & running" : "Recent jobs"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-3">
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </div>
          )}

          {!isLoading && jobs.length === 0 && (
            <EmptyState
              title={filter === "active" ? "No active jobs" : "No jobs yet"}
              description={
                filter === "active"
                  ? "Upload a dataset or start training to see jobs here."
                  : "Completed jobs will appear in this list."
              }
            />
          )}

          {!isLoading && jobs.length > 0 && (
            <ul className="divide-y">
              {jobs.map((job) => (
                <li
                  key={job.id}
                  className="flex flex-wrap items-start justify-between gap-3 py-4 first:pt-0"
                >
                  <div className="min-w-0 space-y-1">
                    <p className="font-medium text-zinc-900">
                      {job.context?.label ?? job.job_type}
                    </p>
                    {job.context?.dataset_name && (
                      <p className="text-sm text-zinc-600">
                        Dataset: {job.context.dataset_name}
                      </p>
                    )}
                    {job.context?.target_column && (
                      <p className="text-sm text-zinc-600">
                        Target: {job.context.target_column}
                        {job.context.problem_type
                          ? ` · ${job.context.problem_type}`
                          : ""}
                      </p>
                    )}
                    <p className="truncate text-xs text-zinc-400">{job.id}</p>
                    {job.error && (
                      <p className="text-sm text-red-600">{job.error}</p>
                    )}
                    {job.created_at && (
                      <p className="text-xs text-zinc-400">
                        {new Date(job.created_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <StatusBadge status={job.status} />
                    {job.context?.dataset_id && (
                      <Button size="sm" variant="outline" asChild>
                        <Link href={`/datasets/${job.context.dataset_id}`}>
                          Dataset
                        </Link>
                      </Button>
                    )}
                    {job.context?.experiment_id &&
                      job.status === "completed" && (
                        <Button size="sm" variant="outline" asChild>
                          <Link
                            href={`/experiments/${job.context.experiment_id}`}
                          >
                            Results
                          </Link>
                        </Button>
                      )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
