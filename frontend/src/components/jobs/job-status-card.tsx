"use client";

import { useJobPolling } from "@/hooks/use-job-polling";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { StatusBadge } from "@/components/shared/status-badge";
import { Progress } from "@/components/ui/progress";
import { useEffect, useRef } from "react";
import { toast } from "sonner";
import type { Job } from "@/types/api";

export function JobStatusCard({
  jobId,
  title,
  onComplete,
}: {
  jobId: string | null;
  title: string;
  onComplete?: (job: Job) => void;
}) {
  const { data, isError, error } = useJobPolling(jobId);
  const notified = useRef<string | null>(null);

  useEffect(() => {
    if (!data?.status || data.status === notified.current) return;
    if (data.status === "completed") {
      notified.current = "completed";
      toast.success(`${title} completed`);
      onComplete?.(data);
    }
    if (data.status === "failed") {
      notified.current = "failed";
      toast.error(data.error ?? `${title} failed`);
    }
  }, [data, title, onComplete]);

  if (!jobId) return null;

  const running = data?.status === "running" || data?.status === "queued";

  return (
    <Alert className="bg-white">
      <AlertTitle className="flex items-center gap-2">
        {title}
        {data?.status && <StatusBadge status={data.status} />}
      </AlertTitle>
      <AlertDescription className="space-y-2">
        {running && <Progress className="h-2 animate-pulse" />}
        {isError && (
          <p className="text-sm text-red-600">{(error as Error).message}</p>
        )}
        {data?.error && <p className="text-sm text-red-600">{data.error}</p>}
      </AlertDescription>
    </Alert>
  );
}
