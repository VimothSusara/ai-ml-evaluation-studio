"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getExperiment } from "@/lib/api/experiments";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { ExperimentResults } from "@/components/experiments/experiment-results";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export default function ExperimentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: exp, isLoading } = useQuery({
    queryKey: ["experiment", id],
    queryFn: () => getExperiment(id),
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      return s === "running" || s === "queued" ? 3000 : false;
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (!exp) return <EmptyState title="Experiment not found" />;

  const running = exp.status === "running" || exp.status === "queued";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Experiment results"
        description={`Target: ${exp.target_column} · ${exp.problem_type}`}
        badge={<StatusBadge status={String(exp.status)} />}
      />

      <Button variant="outline" size="sm" asChild>
        <Link href={`/datasets/${exp.dataset_id}`}>← Back to dataset</Link>
      </Button>

      {running && (
        <EmptyState
          title="Training in progress"
          description="Results will update automatically. Metrics and charts appear when training completes."
        />
      )}

      {!running && exp.model_runs.length === 0 && (
        <EmptyState title="No model runs yet" />
      )}

      {!running && exp.model_runs.length > 0 && (
        <ExperimentResults experiment={exp} />
      )}
    </div>
  );
}