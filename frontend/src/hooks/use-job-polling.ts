"use client";

import { useQuery } from "@tanstack/react-query";
import { getJob } from "@/lib/api/jobs";
import type { JobStatus } from "@/types/api";

const TERMINAL: JobStatus[] = ["completed", "failed"];

export function useJobPolling(jobId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId!),
    enabled: enabled && !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status || TERMINAL.includes(status as JobStatus)) return false;
      return 2000;
    },
  });
}