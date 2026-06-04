import type { PredictionItem } from "@/types/api";

export interface RankedProbability {
  label: string;
  score: number;
  percent: number;
}

export function topProbabilities(
  probabilities: Record<string, number> | null | undefined,
  limit = 3,
): RankedProbability[] {
  if (!probabilities) return [];
  const entries = Object.entries(probabilities).sort(([, a], [, b]) => b - a);
  const top = entries.slice(0, limit);
  const max = top[0]?.[1] ?? 1;
  return top.map(([label, score]) => ({
    label,
    score,
    percent: max > 0 ? (score / max) * 100 : 0,
  }));
}

export function formatFeatureLabel(column: string): string {
  const lower = column.toLowerCase();
  if (lower.startsWith("unnamed") || column.trim() === "#") {
    return `${column} (CSV index — retrain after re-upload without index column)`;
  }
  return column;
}

export function isIndexLikeFeature(column: string): boolean {
  const lower = column.toLowerCase().trim();
  return lower.startsWith("unnamed") || lower === "#";
}