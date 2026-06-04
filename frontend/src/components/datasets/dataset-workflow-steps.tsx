"use client";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

export type WorkflowStepState = "complete" | "current" | "upcoming";

export interface WorkflowStep {
  id: string;
  label: string;
  description?: string;
  state: WorkflowStepState;
}

function StepDot({ state }: { state: WorkflowStepState }) {
  if (state === "complete") {
    return (
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600 text-white">
        <Check className="h-4 w-4" />
      </span>
    );
  }
  if (state === "current") {
    return (
      <span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-zinc-900 bg-white text-sm font-semibold text-zinc-900">
        •
      </span>
    );
  }
  return (
    <span className="flex h-8 w-8 items-center justify-center rounded-full border border-zinc-200 bg-zinc-50 text-sm text-zinc-400">
      •
    </span>
  );
}

export function DatasetWorkflowSteps({ steps }: { steps: WorkflowStep[] }) {
  return (
    <nav
      aria-label="Dataset workflow"
      className="rounded-lg border bg-white px-4 py-5"
    >
      <ol className="flex flex-col gap-4 sm:flex-row sm:items-start sm:gap-0">
        {steps.map((step, index) => (
          <li
            key={step.id}
            className={cn(
              "flex flex-1 items-start gap-3 sm:flex-col sm:items-center sm:text-center",
              index < steps.length - 1 &&
                "sm:relative sm:pb-0 sm:after:absolute sm:after:left-[calc(50%+1rem)] sm:after:top-4 sm:after:h-px sm:after:w-[calc(100%-2rem)] sm:after:bg-zinc-200",
            )}
          >
            <StepDot state={step.state} />
            <div className="min-w-0 sm:px-2">
              <p
                className={cn(
                  "text-sm font-medium",
                  step.state === "upcoming" ? "text-zinc-400" : "text-zinc-900",
                )}
              >
                {step.label}
              </p>
              {step.description && (
                <p className="mt-0.5 text-xs text-zinc-500">
                  {step.description}
                </p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </nav>
  );
}

/** Build step states from dataset detail page state */
export function buildDatasetWorkflowSteps(opts: {
  profiled: boolean;
  hasProfile: boolean;
  targetSelected: boolean;
  validationReady: boolean;
  hasRecommendations: boolean;
  trainingActive: boolean;
}): WorkflowStep[] {
  const {
    profiled,
    hasProfile,
    targetSelected,
    validationReady,
    hasRecommendations,
    trainingActive,
  } = opts;

  const exploreState: WorkflowStepState = hasProfile
    ? "complete"
    : profiled
      ? "current"
      : "upcoming";

  const targetState: WorkflowStepState = validationReady
    ? "complete"
    : profiled && (targetSelected || !hasProfile)
      ? "current"
      : profiled
        ? "current"
        : "upcoming";

  const trainState: WorkflowStepState = trainingActive
    ? "current"
    : hasRecommendations && validationReady
      ? "current"
      : validationReady
        ? "current"
        : "upcoming";

  return [
    {
      id: "explore",
      label: "Explore data",
      description: hasProfile ? "Profile ready" : "Waiting for profile",
      state: exploreState,
    },
    {
      id: "target",
      label: "Choose target",
      description: validationReady
        ? "Ready to train"
        : targetSelected
          ? "Validate target"
          : "Select a column",
      state: targetState,
    },
    {
      id: "train",
      label: "Train models",
      description: trainingActive
        ? "Training in progress"
        : hasRecommendations
          ? "Pick models & train"
          : "Get recommendations first",
      state: trainState,
    },
  ];
}
