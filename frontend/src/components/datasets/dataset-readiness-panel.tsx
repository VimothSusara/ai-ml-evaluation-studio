"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import type { DatasetProfile } from "@/lib/datasets/profile-types";
import { CheckCircle2, AlertTriangle } from "lucide-react";

export function DatasetReadinessPanel({
  profile,
}: {
  profile: DatasetProfile;
}) {
  const sanitization = profile.sanitization;
  if (!sanitization) {
    return (
      <Alert>
        <AlertTitle>Data readiness</AlertTitle>
        <AlertDescription className="text-sm">
          Re-profile this dataset to run automatic cleaning checks (index
          columns, readiness for training).
        </AlertDescription>
      </Alert>
    );
  }

  const ready = sanitization.ready_for_ml;

  return (
    <div className="space-y-3 rounded-lg border bg-white p-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold text-zinc-900">Data readiness</h3>
        <Badge
          variant="outline"
          className={
            ready
              ? "border-emerald-200 bg-emerald-50 text-emerald-800"
              : "border-amber-200 bg-amber-50 text-amber-800"
          }
        >
          {ready ? "Ready for ML" : "Needs attention"}
        </Badge>
      </div>

      {ready ? (
        <div className="flex items-start gap-2 text-sm text-emerald-800">
          <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
          <p>
            Automatic cleaning passed. You can select a target column and train
            models.
          </p>
        </div>
      ) : (
        <div className="flex items-start gap-2 text-sm text-amber-800">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          <p>
            After removing index/junk columns, this file does not have enough
            usable columns or rows. Upload a cleaner CSV or add more data.
          </p>
        </div>
      )}

      {sanitization.dropped_columns.length > 0 && (
        <div className="rounded-md border bg-zinc-50 p-3">
          <p className="text-xs font-medium text-zinc-700">
            Columns removed automatically
          </p>
          <ul className="mt-2 space-y-1 text-xs text-zinc-600">
            {sanitization.dropped_columns.map((d) => (
              <li key={d.column}>
                <span className="font-medium text-zinc-800">{d.column}</span>
                {" — "}
                {d.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {sanitization.warnings.length > 0 && (
        <ul className="list-inside list-disc text-xs text-zinc-600">
          {sanitization.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
