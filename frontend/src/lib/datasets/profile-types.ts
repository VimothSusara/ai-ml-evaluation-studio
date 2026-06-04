export interface ColumnStat {
  dtype: string;
  missing: number;
  nunique: number;
  is_constant?: boolean;
  is_id_like?: boolean;
  is_likely_text?: boolean;
  value_counts?: Record<string, number>;
}

export interface DroppedColumn {
  column: string;
  reason: string;
}

export interface ProfileSanitization {
  dropped_columns: DroppedColumn[];
  ready_for_ml: boolean;
  warnings: string[];
}

export interface DatasetProfile {
  rows: number;
  columns: number;
  column_names?: string[];
  dtypes?: Record<string, string>;
  missing?: Record<string, number>;
  column_stats?: Record<string, ColumnStat>;
  sanitization?: ProfileSanitization;
}

export function parseProfile(
  raw: Record<string, unknown> | null,
): DatasetProfile | null {
  if (!raw) return null;
  return raw as DatasetProfile;
}