"use client";

import { StatCard } from "@/components/shared/stat-card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { JsonCollapse } from "@/components/shared/json-collapse";
import type { DatasetProfile } from "@/lib/datasets/profile-types";

export function DatasetProfilePanel({ profile }: { profile: DatasetProfile }) {
  const names = profile.column_names ?? Object.keys(profile.dtypes ?? {});
  const missing = profile.missing ?? {};
  const stats = profile.column_stats ?? {};
  const maxMissing = Math.max(...Object.values(missing), 1);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Rows" value={profile.rows} />
        <StatCard label="Columns" value={profile.columns} />
        <StatCard
          label="Numeric columns"
          value={
            Object.values(stats).filter(
              (s) => s.dtype.includes("int") || s.dtype.includes("float"),
            ).length
          }
        />
        <StatCard
          label="Columns with missing"
          value={Object.values(missing).filter((v) => v > 0).length}
        />
      </div>

      <div className="rounded-lg border bg-white p-4">
        <h3 className="mb-4 text-sm font-semibold">Missing values by column</h3>
        <div className="space-y-2">
          {names.slice(0, 12).map((col) => {
            const count = missing[col] ?? 0;
            const pct = (count / maxMissing) * 100;
            return (
              <div
                key={col}
                className="grid grid-cols-[140px_1fr_48px] items-center gap-2 text-sm"
              >
                <span className="truncate text-zinc-600">{col}</span>
                <div className="h-2 rounded-full bg-zinc-100">
                  <div
                    className="h-2 rounded-full bg-zinc-400"
                    style={{ width: `${Math.min(pct, 100)}%` }}
                  />
                </div>
                <span className="text-right text-xs text-zinc-500">
                  {count}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Column</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Missing</TableHead>
              <TableHead>Unique</TableHead>
              <TableHead>Flags</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {names.map((col) => {
              const s = stats[col];
              const dtype = s?.dtype ?? profile.dtypes?.[col] ?? "—";
              return (
                <TableRow key={col}>
                  <TableCell className="font-medium">{col}</TableCell>
                  <TableCell>{dtype}</TableCell>
                  <TableCell>{missing[col] ?? 0}</TableCell>
                  <TableCell>{s?.nunique ?? "—"}</TableCell>
                  <TableCell className="space-x-1">
                    {s?.is_id_like && (
                      <Badge variant="outline" className="text-xs">
                        ID-like
                      </Badge>
                    )}
                    {s?.is_constant && (
                      <Badge variant="outline" className="text-xs">
                        Constant
                      </Badge>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      <JsonCollapse title="Advanced: raw profile JSON" data={profile} />
    </div>
  );
}
