"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  exportExperimentModel,
  getExperimentInferenceSchema,
  predictExperiment,
} from "@/lib/api/inference";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useState } from "react";
import { toast } from "sonner";
import type { Experiment, PredictResponse } from "@/types/api";
import { PredictionResult } from "./prediction-result";
import {
  formatFeatureLabel,
  isIndexLikeFeature,
} from "@/lib/predictions/format";

export function ModelInferencePanel({
  experiment,
}: {
  experiment: Experiment;
}) {
  const completed = experiment.status === "completed";
  const { data: schema, isLoading } = useQuery({
    queryKey: ["inference-schema", experiment.id],
    queryFn: () => getExperimentInferenceSchema(experiment.id),
    enabled: completed,
  });

  const [values, setValues] = useState<Record<string, string>>({});
  const [lastResult, setLastResult] = useState<PredictResponse | null>(null);

  const hasIndexLikeFeatures = (schema?.feature_columns ?? []).some(
    isIndexLikeFeature,
  );

  const predictMut = useMutation({
    mutationFn: () => {
      const row: Record<string, string | number> = {};
      for (const col of schema?.feature_columns ?? []) {
        const raw = values[col] ?? "";
        const num = Number(raw);
        row[col] =
          raw !== "" && !Number.isNaN(num) && raw.trim() !== "" ? num : raw;
      }
      return predictExperiment(experiment.id, [row]);
    },
    onSuccess: (res) => {
      setLastResult(res);
      toast.success("Prediction complete");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const downloadJoblib = useMutation({
    mutationFn: () => exportExperimentModel(experiment.id, "joblib"),
    onSuccess: (res) => {
      if (res.download_url) window.open(res.download_url, "_blank");
      else toast.error("No download URL returned");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const downloadManifest = useMutation({
    mutationFn: () => exportExperimentModel(experiment.id, "manifest"),
    onSuccess: (res) => {
      const blob = new Blob([JSON.stringify(res.manifest, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${res.model_code}-manifest.json`;
      a.click();
      URL.revokeObjectURL(url);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  if (!completed) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Use trained model</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-zinc-500">
          Download the trained pipeline or enter one row of feature values.
          Do not include the target column (
          <strong>{experiment.target_column}</strong>).
        </p>

        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            disabled={downloadJoblib.isPending}
            onClick={() => downloadJoblib.mutate()}
          >
            Download .joblib
          </Button>
          <Button
            variant="outline"
            disabled={downloadManifest.isPending}
            onClick={() => downloadManifest.mutate()}
          >
            Download manifest.json
          </Button>
        </div>

        {hasIndexLikeFeatures && (
          <Alert className="border-amber-200 bg-amber-50">
            <AlertTitle className="text-amber-900">
              Index column detected
            </AlertTitle>
            <AlertDescription className="text-sm text-amber-800">
              This model was trained with a CSV index column (e.g.{" "}
              <code className="text-xs">#</code> or{" "}
              <code className="text-xs">Unnamed: 0</code>). Re-upload the CSV
              without that column and train again for cleaner features. For
              now, use the row number (0, 1, 2, …) if required.
            </AlertDescription>
          </Alert>
        )}

        {isLoading && <p className="text-sm text-zinc-500">Loading schema…</p>}

        {schema && (
          <>
            <div className="rounded-md border bg-zinc-50 px-3 py-2 text-xs text-zinc-600">
              <span className="font-medium text-zinc-800">Model:</span>{" "}
              {schema.model_code}
              <span className="mx-2">·</span>
              <span className="font-medium text-zinc-800">Features:</span>{" "}
              {schema.feature_columns.length} columns
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {schema.feature_columns.map((col) => (
                <div key={col} className="space-y-1">
                  <Label htmlFor={`feat-${col}`} className="text-xs leading-snug">
                    {formatFeatureLabel(col)}
                  </Label>
                  <Input
                    id={`feat-${col}`}
                    value={values[col] ?? ""}
                    onChange={(e) =>
                      setValues((v) => ({ ...v, [col]: e.target.value }))
                    }
                    placeholder={
                      isIndexLikeFeature(col) ? "e.g. 0" : "Enter value"
                    }
                  />
                </div>
              ))}
            </div>
            <Button
              disabled={predictMut.isPending}
              onClick={() => predictMut.mutate()}
            >
              {predictMut.isPending ? "Predicting…" : "Run prediction"}
            </Button>
          </>
        )}

        {lastResult && (
          <PredictionResult
            result={lastResult}
            problemType={experiment.problem_type}
          />
        )}
      </CardContent>
    </Card>
  );
}
