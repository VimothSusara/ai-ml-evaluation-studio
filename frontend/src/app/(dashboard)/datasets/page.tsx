"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listDatasets, uploadDataset } from "@/lib/api/datasets";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { JobStatusCard } from "@/components/jobs/job-status-card";
import { useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import type { Job } from "@/types/api";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CsvPreviewTable } from "@/components/datasets/csv-preview-table";
import {
  formatFileSize,
  parseCsvPreview,
  type CsvPreview,
} from "@/lib/csv-preview";
import { assessCsvPreview } from "@/lib/csv-preflight";
import { CsvPreflightPanel } from "@/components/datasets/csv-preflight-panel";

export default function DatasetsPage() {
  const qc = useQueryClient();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { data, isLoading } = useQuery({
    queryKey: ["datasets"],
    queryFn: listDatasets,
  });
  const [profileJobId, setProfileJobId] = useState<string | null>(null);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<CsvPreview | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [parsing, setParsing] = useState(false);

  const upload = useMutation({
    mutationFn: (file: File) => uploadDataset(file),
    onSuccess: (res) => {
      setProfileJobId(res.job_id);
      setConfirmOpen(false);
      clearSelection();
      toast.message("Upload started — profiling in progress");
      qc.invalidateQueries({ queryKey: ["datasets"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  function clearSelection() {
    setPendingFile(null);
    setPreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function onFileSelected(file: File | undefined) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) {
      toast.error("Please select a CSV file");
      return;
    }
    setParsing(true);
    try {
      const p = await parseCsvPreview(file, 10);
      setPendingFile(file);
      setPreview(p);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not read CSV");
      clearSelection();
    } finally {
      setParsing(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  const datasets = data ?? [];

  const preflight = useMemo(
    () => (preview ? assessCsvPreview(preview) : null),
    [preview],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Datasets"
        description="Upload CSV files for automatic profiling, then open a dataset to train models."
      />

      <Card>
        <CardHeader>
          <CardTitle>Upload dataset (CSV)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            disabled={upload.isPending || parsing}
            onChange={(e) => onFileSelected(e.target.files?.[0])}
          />
          <p className="text-xs text-zinc-500">
            Select a CSV to preview the first 10 rows and run a quick preflight
            check, then confirm upload. Profiling runs in the background after
            you confirm.
          </p>

          {parsing && (
            <p className="text-sm text-zinc-500">Reading file preview…</p>
          )}

          {preview && pendingFile && !parsing && (
            <div className="space-y-3 rounded-lg border bg-zinc-50/50 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-zinc-600">
                  <span>
                    <span className="font-medium text-zinc-900">File:</span>{" "}
                    {preview.fileName}
                  </span>
                  <span>
                    <span className="font-medium text-zinc-900">Size:</span>{" "}
                    {formatFileSize(preview.fileSizeBytes)}
                  </span>
                  <span>
                    <span className="font-medium text-zinc-900">Columns:</span>{" "}
                    {preview.headers.length}
                  </span>
                  <span>
                    <span className="font-medium text-zinc-900">Rows (est.):</span>{" "}
                    {preview.estimatedRowCount.toLocaleString()}
                  </span>
                </div>
              </div>

              <p className="text-xs font-medium text-zinc-700">
                Preview (first {preview.rows.length} rows)
                {preview.headers.length > 6 && (
                  <span className="font-normal text-zinc-500">
                    {" "}
                    — scroll horizontally for more columns
                  </span>
                )}
              </p>
              <CsvPreviewTable preview={preview} />

              {preflight && (
                <div className="pt-2">
                  <CsvPreflightPanel preflight={preflight} />
                </div>
              )}

              <div className="flex flex-wrap gap-2 pt-1">
                <Button
                  onClick={() => {
                    if (preflight && !preflight.canUpload) {
                      toast.error(
                        "Fix preflight errors before uploading this file.",
                      );
                      return;
                    }
                    setConfirmOpen(true);
                  }}
                  disabled={preflight !== null && !preflight.canUpload}
                >
                  Upload & profile
                </Button>
                <Button
                  variant="outline"
                  onClick={clearSelection}
                  disabled={upload.isPending}
                >
                  Clear selection
                </Button>
              </div>
            </div>
          )}

          <JobStatusCard
            jobId={profileJobId}
            title="Profiling job"
            onComplete={(job: Job) => {
              qc.invalidateQueries({ queryKey: ["datasets"] });
              const result = job.result as { dataset_id?: string } | null;
              if (result?.dataset_id) {
                router.push(`/datasets/${result.dataset_id}`);
              }
            }}
          />
        </CardContent>
      </Card>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Confirm upload</DialogTitle>
            <DialogDescription>
              You reviewed the preview and preflight checks above. Upload this
              file and start background profiling?
            </DialogDescription>
          </DialogHeader>
          {preflight && preflight.warnings.length > 0 && (
            <ul className="list-inside list-disc space-y-1 text-xs text-amber-800">
              {preflight.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          )}
          {preview && (
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-zinc-500">File</dt>
                <dd className="truncate font-medium">{preview.fileName}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-zinc-500">Size</dt>
                <dd className="font-medium">
                  {formatFileSize(preview.fileSizeBytes)}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-zinc-500">Columns</dt>
                <dd className="font-medium">{preview.headers.length}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-zinc-500">Rows (est.)</dt>
                <dd className="font-medium">
                  {preview.estimatedRowCount.toLocaleString()}
                </dd>
              </div>
            </dl>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={
                !pendingFile ||
                upload.isPending ||
                (preflight !== null && !preflight.canUpload)
              }
              onClick={() => pendingFile && upload.mutate(pendingFile)}
            >
              {upload.isPending ? "Uploading…" : "Confirm upload"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Card>
        <CardHeader>
          <CardTitle>Your datasets</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-3">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          )}

          {!isLoading && datasets.length === 0 && (
            <EmptyState
              title="No datasets yet"
              description="Upload a CSV file above to create your first dataset."
            />
          )}

          {!isLoading && datasets.length > 0 && (
            <ul className="divide-y">
              {datasets.map((ds) => (
                <li
                  key={ds.id}
                  className="flex flex-wrap items-center justify-between gap-3 py-4 first:pt-0"
                >
                  <div className="min-w-0">
                    <p className="font-medium text-zinc-900">{ds.name}</p>
                    <p className="truncate text-xs text-zinc-500">{ds.id}</p>
                    {ds.created_at && (
                      <p className="mt-1 text-xs text-zinc-400">
                        {new Date(ds.created_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={ds.status} />
                    <Button size="sm" asChild>
                      <Link href={`/datasets/${ds.id}`}>
                        {ds.status === "profiled" ? "Explore" : "Open"}
                      </Link>
                    </Button>
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
