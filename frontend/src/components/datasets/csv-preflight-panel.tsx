"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import type { CsvPreflightResult } from "@/lib/csv-preflight";
import { AlertCircle, AlertTriangle } from "lucide-react";

export function CsvPreflightPanel({
  preflight,
}: {
  preflight: CsvPreflightResult;
}) {
  if (preflight.errors.length === 0 && preflight.warnings.length === 0) {
    return (
      <Alert className="border-emerald-200 bg-emerald-50/80">
        <AlertTitle className="text-emerald-900">Preflight check</AlertTitle>
        <AlertDescription className="text-sm text-emerald-800">
          No issues detected in the preview. Index-like columns (if any) are
          handled automatically during profiling. Full readiness is confirmed
          after background profiling.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-2">
      {preflight.errors.map((msg) => (
        <Alert key={msg} variant="destructive">
          <AlertCircle className="size-4" />
          <AlertTitle>Cannot upload</AlertTitle>
          <AlertDescription className="text-sm">{msg}</AlertDescription>
        </Alert>
      ))}
      {preflight.warnings.map((msg) => (
        <Alert
          key={msg}
          className="border-amber-200 bg-amber-50/80 text-amber-950"
        >
          <AlertTriangle className="size-4 text-amber-700" />
          <AlertTitle className="text-amber-900">Heads up</AlertTitle>
          <AlertDescription className="text-sm text-amber-800">
            {msg}
          </AlertDescription>
        </Alert>
      ))}
    </div>
  );
}
