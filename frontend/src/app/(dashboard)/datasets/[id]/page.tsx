"use client";

import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getDataset,
  getDatasetColumns,
  getRecommendations,
  validateDataset,
} from "@/lib/api/datasets";
import { trainExperiment } from "@/lib/api/experiments";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { JobStatusCard } from "@/components/jobs/job-status-card";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import type { Job, ModelRecommendation, ValidationResponse } from "@/types/api";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { DatasetProfilePanel } from "@/components/datasets/dataset-profile-panel";
import { ValidationPanel } from "@/components/datasets/validation-panel";
import { parseProfile } from "@/lib/datasets/profile-types";
import {
  DatasetWorkflowSteps,
  buildDatasetWorkflowSteps,
} from "@/components/datasets/dataset-workflow-steps";
import {
  StepChecklist,
  WorkflowStepCard,
} from "@/components/datasets/workflow-step-card";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { DatasetReadinessPanel } from "@/components/datasets/dataset-readiness-panel";

export default function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();

  const { data: dataset, isLoading } = useQuery({
    queryKey: ["dataset", id],
    queryFn: () => getDataset(id),
  });

  const { data: columns } = useQuery({
    queryKey: ["dataset-columns", id],
    queryFn: () => getDatasetColumns(id),
    enabled: dataset?.status === "profiled",
  });

  const [target, setTarget] = useState("");
  const [validation, setValidation] = useState<ValidationResponse | null>(null);
  const [recommendations, setRecommendations] = useState<ModelRecommendation[]>(
    [],
  );
  const [selectedModels, setSelectedModels] = useState<Record<string, boolean>>(
    {},
  );
  const [trainJobId, setTrainJobId] = useState<string | null>(null);
  const [trainConfirmOpen, setTrainConfirmOpen] = useState(false);

  const validateMut = useMutation({
    mutationFn: () => validateDataset(id, { target_column: target }),
    onSuccess: (res) => {
      setValidation(res);
      setRecommendations([]);
      setSelectedModels({});
      toast.success(
        res.ready_to_train
          ? "Target validated — continue to models"
          : "Validation needs attention",
      );
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const recommendMut = useMutation({
    mutationFn: () => getRecommendations(id, { target_column: target }),
    onSuccess: (res) => {
      setRecommendations(res.recommendations);
      const init: Record<string, boolean> = {};
      res.recommendations.forEach((r) => {
        init[r.model_code] = r.is_default;
      });
      setSelectedModels(init);
      toast.success("Model recommendations loaded");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const trainMut = useMutation({
    mutationFn: () => {
      const model_codes = Object.entries(selectedModels)
        .filter(([, v]) => v)
        .map(([k]) => k);
      return trainExperiment({
        dataset_id: id,
        target_column: target,
        model_codes: model_codes.length ? model_codes : null,
      });
    },
    onSuccess: (res) => {
      setTrainConfirmOpen(false);
      setTrainJobId(res.job_id);
      toast.message("Training started — you will be redirected when complete");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const profiled = dataset?.status === "profiled";
  const profile = parseProfile(dataset?.profile ?? null);
  const validationReady = !!validation?.ready_to_train;
  const hasRecommendations = recommendations.length > 0;
  const selectedModelNames = recommendations.filter(
    (r) => selectedModels[r.model_code],
  );

  const workflowSteps = useMemo(
    () =>
      buildDatasetWorkflowSteps({
        profiled: !!profiled,
        hasProfile: !!profile,
        targetSelected: !!target,
        validationReady,
        hasRecommendations,
        trainingActive: !!trainJobId,
      }),
    [
      profiled,
      profile,
      target,
      validationReady,
      hasRecommendations,
      trainJobId,
    ],
  );

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={dataset?.name ?? "Dataset"}
        description="Follow the steps below: choose a target, validate, pick models, then train."
        badge={
          dataset?.status ? <StatusBadge status={dataset.status} /> : undefined
        }
      />

      <DatasetWorkflowSteps steps={workflowSteps} />

      {profiled && (
        <StepChecklist
          items={[
            { label: "Review dataset overview", done: !!profile },
            {
              label: "Select and validate target column",
              done: validationReady,
            },
            { label: "Load model recommendations", done: hasRecommendations },
            {
              label: "Train and view experiment results",
              done: !!trainJobId,
            },
          ]}
        />
      )}

      {profile && (
        <WorkflowStepCard
          step={1}
          title="Explore your data"
          description="Review row counts, missing values, and column types before choosing a target."
          done={!!profile}
          active={profiled && !target}
        >
          <DatasetProfilePanel profile={profile} />
          <div className="mt-6">
            <DatasetReadinessPanel profile={profile} />
          </div>
        </WorkflowStepCard>
      )}

      {!profiled && dataset?.status && (
        <EmptyState
          title="Profiling in progress"
          description="Wait until status is “profiled”, then refresh to continue with target selection and training."
        />
      )}

      {profiled && (
        <WorkflowStepCard
          step={2}
          title="Choose target column"
          description="Pick the column you want to predict, then validate before loading models."
          done={validationReady}
          active={!validationReady}
        >
          <div className="max-w-md space-y-4">
            <div className="space-y-2">
              <Label htmlFor="target-column">Target column</Label>
              <Select value={target} onValueChange={setTarget}>
                <SelectTrigger id="target-column" className="w-full">
                  <SelectValue placeholder="Select column to predict" />
                </SelectTrigger>
                <SelectContent>
                  {(columns?.columns ?? profile?.column_names ?? []).map(
                    (col) => (
                      <SelectItem key={col} value={col}>
                        {col}
                      </SelectItem>
                    ),
                  )}
                </SelectContent>
              </Select>
              {!columns?.columns?.length &&
                !profile?.column_names?.length && (
                  <p className="text-xs text-zinc-500">
                    Loading columns… refresh if this persists.
                  </p>
                )}
            </div>
            <Button
              disabled={!target || validateMut.isPending}
              onClick={() => validateMut.mutate()}
            >
              {validateMut.isPending ? "Validating…" : "Validate target"}
            </Button>
            {validation && <ValidationPanel validation={validation} />}
          </div>
        </WorkflowStepCard>
      )}

      {profiled && validationReady && (
        <WorkflowStepCard
          step={3}
          title="Select models to compare"
          description="Load recommended algorithms for your problem type, then choose which to train."
          done={hasRecommendations}
          active={!hasRecommendations}
        >
          {!hasRecommendations && (
            <Button
              disabled={recommendMut.isPending}
              onClick={() => recommendMut.mutate()}
            >
              {recommendMut.isPending
                ? "Loading recommendations…"
                : "Load recommended models"}
            </Button>
          )}

          {hasRecommendations && (
            <div className="space-y-3">
              {recommendations.map((r) => (
                <label
                  key={r.model_code}
                  className="flex cursor-pointer items-start gap-3 rounded-lg border bg-zinc-50/50 p-3"
                >
                  <Checkbox
                    className="mt-0.5"
                    checked={!!selectedModels[r.model_code]}
                    onCheckedChange={(v) =>
                      setSelectedModels((s) => ({
                        ...s,
                        [r.model_code]: !!v,
                      }))
                    }
                  />
                  <span>
                    <span className="font-medium">{r.display_name}</span>
                    {r.is_default && (
                      <span className="ml-2 text-xs text-emerald-700">
                        Default
                      </span>
                    )}
                    {r.reason && (
                      <span className="mt-1 block text-xs text-zinc-500">
                        {r.reason}
                      </span>
                    )}
                  </span>
                </label>
              ))}
            </div>
          )}
        </WorkflowStepCard>
      )}

      {profiled && validationReady && hasRecommendations && (
        <WorkflowStepCard
          step={4}
          title="Train and evaluate"
          description="Start training for selected models. Results appear on the experiment page when complete."
          done={!!trainJobId}
          active={!trainJobId}
        >
          <Button
            disabled={
              selectedModelNames.length === 0 ||
              trainMut.isPending ||
              !!trainJobId
            }
            onClick={() => setTrainConfirmOpen(true)}
          >
            Review & start training
          </Button>

          <JobStatusCard
            jobId={trainJobId}
            title="Training job"
            onComplete={(job: Job) => {
              qc.invalidateQueries({ queryKey: ["experiments"] });
              qc.invalidateQueries({ queryKey: ["dataset", id] });
              const result = job.result as { experiment_id?: string } | null;
              if (result?.experiment_id) {
                router.push(`/experiments/${result.experiment_id}`);
              }
            }}
          />
        </WorkflowStepCard>
      )}

      <Dialog open={trainConfirmOpen} onOpenChange={setTrainConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Start training?</DialogTitle>
            <DialogDescription>
              This runs in the background and may take a minute. You will be
              redirected to experiment results when finished.
            </DialogDescription>
          </DialogHeader>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-500">Dataset</dt>
              <dd className="font-medium">{dataset?.name}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-500">Target</dt>
              <dd className="font-medium">{target}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-500">Problem type</dt>
              <dd className="font-medium">{validation?.problem_type ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-zinc-500">Models</dt>
              <dd className="mt-1 font-medium">
                {selectedModelNames.length > 0
                  ? selectedModelNames.map((m) => m.display_name).join(", ")
                  : "None selected"}
              </dd>
            </div>
          </dl>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setTrainConfirmOpen(false)}
            >
              Cancel
            </Button>
            <Button
              disabled={selectedModelNames.length === 0 || trainMut.isPending}
              onClick={() => trainMut.mutate()}
            >
              {trainMut.isPending ? "Starting…" : "Start training"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
