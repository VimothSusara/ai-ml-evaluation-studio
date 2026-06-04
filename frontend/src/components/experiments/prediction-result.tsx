"use client";

import { Badge } from "@/components/ui/badge";
import type { PredictResponse } from "@/types/api";
import { topProbabilities } from "@/lib/predictions/format";
import { cn } from "@/lib/utils";

export function PredictionResult({
  result,
  problemType,
}: {
  result: PredictResponse;
  problemType: string;
}) {
  const item = result.predictions[0];
  if (!item) return null;

  const isClassification = problemType === "classification";
  const ranked = topProbabilities(item.probabilities, 3);

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            Model output
          </p>
          <p className="text-sm text-zinc-600">
            {result.model_code} · {result.problem_type}
          </p>
        </div>
        <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">
          {isClassification ? "Predicted class" : "Predicted value"}
        </Badge>
      </div>

      <div className="rounded-md border border-emerald-200 bg-emerald-50/80 px-4 py-3">
        <p className="text-xs text-emerald-800">Primary prediction</p>
        <p className="mt-1 text-2xl font-semibold tracking-tight text-emerald-950">
          {String(item.prediction)}
        </p>
        {isClassification && ranked[0] && (
          <p className="mt-1 text-sm text-emerald-700">
            {(ranked[0].score * 100).toFixed(1)}% confidence
          </p>
        )}
      </div>

      {isClassification && ranked.length > 0 && (
        <div className="mt-4 space-y-3">
          <p className="text-sm font-medium text-zinc-800">
            Top {ranked.length} classes by confidence
          </p>
          {ranked.map((row, index) => (
            <div key={row.label} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span
                  className={cn(
                    "font-medium",
                    index === 0 ? "text-emerald-800" : "text-zinc-700",
                  )}
                >
                  {index + 1}. {row.label}
                </span>
                <span className="tabular-nums text-zinc-600">
                  {(row.score * 100).toFixed(1)}%
                </span>
              </div>
              <div className="h-2 overflow-full rounded-full bg-zinc-100">
                <div
                  className={cn(
                    "h-2 rounded-full",
                    index === 0 ? "bg-emerald-500" : "bg-zinc-400",
                  )}
                  style={{ width: `${row.percent}%` }}
                />
              </div>
            </div>
          ))}
          {item.probabilities &&
            Object.keys(item.probabilities).length > 3 && (
              <p className="text-xs text-zinc-500">
                Showing top 3 of {Object.keys(item.probabilities).length}{" "}
                classes.
              </p>
            )}
        </div>
      )}

      {!isClassification && (
        <p className="mt-3 text-sm text-zinc-600">
          Regression models return a single numeric value (no class
          probabilities).
        </p>
      )}
    </div>
  );
}